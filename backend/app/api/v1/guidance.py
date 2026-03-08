"""Guidance API — Q&A and SSE chat with the bid guidance workflow."""

import json
import logging
import re
import uuid
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.rag import answer_question
from app.core.credits import (
    deduct_credits,
    require_credits,
)
from app.core.security import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.guidance import GuidanceRequest, GuidanceResponse
from app.services.project_service import ProjectService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/{project_id}/guidance", response_model=GuidanceResponse)
async def get_guidance(
    project_id: UUID,
    request: GuidanceRequest,
    cost_info: dict = Depends(require_credits("guidance_qa")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get AI guidance for a specific question (non-streaming).

    Uses RAG over the project's bid documents + knowledge base.
    Deducts 5 credits per call.
    """
    project_svc = ProjectService(db)
    await project_svc.get_by_id(project_id, current_user.id)

    result = await answer_question(
        project_id=str(project_id),
        question=request.message,       # GuidanceRequest.message (not .question)
        db=db,
        use_knowledge_base=False,       # use_knowledge_base not in schema; default False
    )

    # Deduct credits after successful invocation
    await deduct_credits(
        current_user,
        cost_info["action"],
        cost_info["cost"],
        db,
        reference_id=str(project_id),
    )

    response = GuidanceResponse(
        id=uuid.uuid4(),
        project_id=project_id,
        role="assistant",
        content=result.get("answer", ""),   # rag returns "answer" key
        skill_used="rag_qa",
        sources=[
            {
                "content": s.get("content", "")[:200],
                "section_title": s.get("section_title", ""),
                "page_number": s.get("page_number"),
            }
            for s in result.get("sources", [])
        ],
        tokens_consumed=result.get("tokens_consumed", 0),
        created_at=datetime.now(UTC),
    )
    return response


@router.post("/{project_id}/guidance/stream")
async def stream_guidance(
    project_id: UUID,
    request: GuidanceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stream AI guidance via Server-Sent Events (SSE).

    Returns text/event-stream with JSON data chunks.
    """
    project_svc = ProjectService(db)
    project = await project_svc.get_by_id(project_id, current_user.id)
    use_kb = request.context_type == "knowledge_base"
    institution: str = getattr(project, "institution", None) or "adb"

    async def event_generator():
        try:
            import json as _json
            from datetime import UTC, datetime

            from sqlalchemy import select as _sql_sel

            from app.agents.embedding_client import (
                get_embedding_client,
                get_query_analyzer,
            )
            from app.agents.llm_client import Message as LLMMessage
            from app.agents.llm_client import get_llm_client
            from app.agents.mcp.bid_document_search import (
                _extract_keywords,
                bid_document_search,
                keyword_search_chunks,
            )
            from app.agents.mcp.knowledge_search import knowledge_search
            from app.models.bid_analysis import BidAnalysis as BidAnalysisCls

            llm = get_llm_client()
            emb_client = get_embedding_client()
            analyzer = get_query_analyzer()

            # ── Step 1: 混元 Lite 意图分析 + 翻译 + 检索 query 生成 ────────────
            # 对中英文问题统一处理：生成优化的向量检索 query、ILIKE 关键词、意图分类
            query_info = await analyzer.analyze(request.message)
            intent = query_info["intent"]
            search_queries = query_info["search_queries"]   # 2-3条英文优化 query
            en_keywords = query_info["keywords"]            # 英文 ILIKE 关键词

            # ── Step 2a: 知识库路径 ────────────────────────────────────────────
            if use_kb:
                # 多路向量检索：对每条 search_queries 分别 embed + search，合并去重
                kb_seen: set[str] = set()
                kb_merged: list[dict] = []
                for q in search_queries:
                    emb = await emb_client.embed_text(q)
                    chunks = await knowledge_search(
                        db=db,
                        query_embedding=emb.embedding,
                        institution=institution,
                        top_k=5,
                    )
                    for c in chunks:
                        cid = c.get("id") or c.get("source_document", "") + str(c.get("page_number"))
                        if cid not in kb_seen:
                            kb_seen.add(cid)
                            kb_merged.append(c)

                results = kb_merged[:10]
                system_prompt = (
                    "你是一位专业的投标编制顾问，熟悉ADB/WB/AfDB采购指南和标准招标文件。"
                    "基于提供的知识库文档，为用户提供具体、可操作的标书编制建议。"
                    "引用关键指南时标注来源编号。"
                )
                sources_payload = [
                    {
                        "content": s.get("content", "")[:200],
                        "filename": s.get("source_document", ""),
                        "section_title": "",
                        "page_number": s.get("page_number"),
                        "score": s.get("score", 0),
                    }
                    for s in results
                ]
                analysis_prefix = ""

            # ── Step 2b: 招标文件路径 ──────────────────────────────────────────
            else:
                # 2b-1. 多路向量检索（每条 search_query 独立 embed + search，合并去重）
                seen_ids: set[str] = set()
                merged: list[dict] = []
                for q in search_queries:
                    emb = await emb_client.embed_text(q)
                    chunks = await bid_document_search(
                        db=db,
                        project_id=str(project_id),
                        query_embedding=emb.embedding,
                        top_k=8,
                    )
                    for c in chunks:
                        if c["id"] not in seen_ids:
                            seen_ids.add(c["id"])
                            merged.append(c)

                # 2b-2. 关键词 ILIKE 检索（合并混元生成的英文词 + 本地中文扩展词）
                local_kws = _extract_keywords(request.message)
                all_keywords = list({*en_keywords, *local_kws})
                if all_keywords:
                    kw_results = await keyword_search_chunks(
                        db=db,
                        project_id=str(project_id),
                        keywords=all_keywords,
                        top_k=10,
                    )
                    for c in kw_results:
                        if c["id"] not in seen_ids:
                            seen_ids.add(c["id"])
                            merged.append(c)

                # 2b-3. Intent 驱动章节定向检索 + 年份关键词（精准命中表格行）
                _intent_section_map: dict[str, list[str]] = {
                    "dates": ["section_2_bds", "section_1_itb"],
                    "qualification": ["section_3", "section_2_bds", "section_1_itb"],
                    "evaluation": ["section_3", "section_2_bds"],
                    "submission": ["section_2_bds", "section_1_itb", "section_4_forms"],
                    "bds": ["section_2_bds", "section_1_itb"],
                    "commercial": ["section_2_bds", "part_3_contract"],
                }
                if intent in _intent_section_map:
                    section_types = _intent_section_map[intent]
                    for q in search_queries:
                        emb = await emb_client.embed_text(q)
                        directed = await bid_document_search(
                            db=db,
                            project_id=str(project_id),
                            query_embedding=emb.embedding,
                            section_types=section_types,
                            top_k=8,
                            score_threshold=0.2,
                        )
                        for c in directed:
                            if c["id"] not in seen_ids:
                                seen_ids.add(c["id"])
                                merged.append(c)

                # 日期 intent 额外追加年份关键词搜索（直接命中含具体日期的表格行）
                if intent == "dates":
                    _now = datetime.now(UTC)
                    year_kws = [str(_now.year), str(_now.year + 1), str(_now.year - 1)]
                    year_chunks = await keyword_search_chunks(
                        db=db,
                        project_id=str(project_id),
                        keywords=year_kws,
                        top_k=10,
                    )
                    for c in year_chunks:
                        if c["id"] not in seen_ids:
                            seen_ids.add(c["id"])
                            merged.append(c)

                results = merged

                # 2b-4. 结构化分析数据注入（最高可信度来源）
                # BidAnalysis 表已通过专用 Skill 做过精确提取，直接复用结果
                _intent_field_map = {
                    "dates": "key_dates",
                    "qualification": "qualification_requirements",
                    "evaluation": "evaluation_criteria",
                    "submission": "submission_checklist",
                    "bds": "bds_modifications",
                    "commercial": "commercial_terms",
                }
                analysis_prefix = ""
                if intent in _intent_field_map:
                    _field = _intent_field_map[intent]
                    _ana_row = await db.execute(
                        _sql_sel(getattr(BidAnalysisCls, _field)).where(
                            BidAnalysisCls.project_id == project_id
                        )
                    )
                    _field_data = _ana_row.scalar_one_or_none()
                    if _field_data and isinstance(_field_data, dict):
                        if intent == "dates" and _field_data.get("key_dates"):
                            _lines = [
                                "[高可信度] 招标文件关键日期（已完成结构化提取，可直接引用）:"
                            ]
                            for _kd in _field_data["key_dates"]:
                                _ref = (
                                    f" [{_kd['source_reference']}]"
                                    if _kd.get("source_reference")
                                    else ""
                                )
                                _lines.append(
                                    f"  • {_kd.get('event', '?')}: "
                                    f"{_kd.get('date', '?')}{_ref}"
                                )
                            if _field_data.get("warnings"):
                                _lines.append("  注意事项:")
                                for _w in _field_data["warnings"]:
                                    _lines.append(f"    ⚠ {_w}")
                            analysis_prefix = "\n".join(_lines) + "\n\n"
                        else:
                            analysis_prefix = (
                                "[高可信度] 招标文件结构化分析数据（已完成提取，可直接引用）:\n"
                                + _json.dumps(_field_data, ensure_ascii=False, indent=2)[:2000]
                                + "\n\n"
                            )

                system_prompt = (
                    "你是一位专业的招标文件分析助手，负责帮助用户深入理解招标文件内容。\n"
                    "招标文件通常为英文，请注意中英文术语对应关系，准确提取关键信息。\n"
                    "规则：\n"
                    "1. 优先引用[高可信度]标注的结构化数据，这些是已精确提取的可靠信息\n"
                    "2. 仅基于提供的参考资料回答，不编造信息\n"
                    "3. 如参考资料中有相关内容，必须直接引用原文并标注[来源N]\n"
                    "4. 引用金额、日期、条款编号时确保准确，抄录原文数字\n"
                    "5. 如确实找不到答案，明确告知用户，并说明可能在哪个章节查找\n"
                    "6. 使用简洁的中文回答，专业术语保留英文原文并附中文说明"
                )
                sources_payload = [
                    {
                        "content": s.get("content", "")[:200],
                        "filename": s.get("filename", ""),
                        "section_title": s.get("section_title", ""),
                        "page_number": s.get("page_number"),
                        "score": s.get("score", 0),
                    }
                    for s in results
                ]

            # ── Step 3: 构建 LLM 上下文 ───────────────────────────────────────
            context_block = "\n\n".join(
                "[来源 {n}] {section}（{filename}，第{page}页）:\n{content}".format(
                    n=i + 1,
                    section=c.get("section_title") or c.get("section_type") or "未知章节",
                    filename=c.get("filename") or c.get("source_document") or "",
                    page=c.get("page_number") or "?",
                    content=c.get("content", ""),
                )
                for i, c in enumerate(results)
            )
            # analysis_prefix 放前面（LLM 上下文前部权重更高）
            user_msg = f"参考资料:\n{analysis_prefix}{context_block}\n\n用户问题: {request.message}"

            messages = [
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content=user_msg),
            ]

            # Stream response — catch LLM errors (e.g., invalid API key)
            try:
                async for chunk in llm.chat_stream(messages):
                    event_data = json.dumps({"type": "content", "content": chunk})
                    yield f"data: {event_data}\n\n"
            except Exception as llm_exc:
                # Yield a graceful fallback content event instead of aborting stream
                fallback = (
                    f"LLM服务暂时不可用（{type(llm_exc).__name__}）。\n"
                    f"已检索到{len(results)}个相关片段，请直接查阅候选内容。"
                )
                yield f"data: {json.dumps({'type': 'content', 'content': fallback})}\n\n"

            # Send sources after content
            sources_data = json.dumps({"type": "sources", "sources": sources_payload})
            yield f"data: {sources_data}\n\n"

            # Done event
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            logger.exception("Streaming guidance error")
            error_data = json.dumps({"type": "error", "message": str(e)})
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── Submission Checklist ──────────────────────────────────────────────────────


def _safe_int(value: object) -> int | None:
    """Coerce LLM-returned value to int, returning None on failure."""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@router.post("/{project_id}/checklist/generate")
async def generate_checklist(
    project_id: UUID,
    force_refresh: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate (or return cached) submission checklist by RAG-parsing the tender document.

    The result is cached in BidAnalysis.submission_checklist to avoid repeated LLM calls.
    """
    from sqlalchemy import select

    from app.agents.embedding_client import get_embedding_client
    from app.agents.llm_client import Message as LLMMessage
    from app.agents.llm_client import get_llm_client
    from app.agents.mcp.bid_document_search import (
        _extract_keywords,
        bid_document_search,
        keyword_search_chunks,
    )
    from app.agents.prompts.checklist import CHECKLIST_EXTRACT_PROMPT
    from app.models.bid_analysis import BidAnalysis
    from app.schemas.checklist import (
        ChecklistItem,
        ChecklistSection,
        ChecklistSource,
        SubmissionChecklistResponse,
    )

    # Authorise access
    project_svc = ProjectService(db)
    project = await project_svc.get_by_id(project_id, current_user.id)
    institution: str = getattr(project, "institution", None) or "adb"

    # ── 1. Check cache ──────────────────────────────────────────
    result_row = await db.execute(
        select(BidAnalysis).where(BidAnalysis.project_id == project_id)
    )
    analysis: BidAnalysis | None = result_row.scalar_one_or_none()

    if (
        not force_refresh
        and analysis is not None
        and analysis.submission_checklist
        and isinstance(analysis.submission_checklist, dict)
        and analysis.submission_checklist.get("sections")
    ):
        cached = analysis.submission_checklist
        try:
            cached_sections = [ChecklistSection(**s) for s in cached["sections"]]
        except Exception:
            logger.warning("Cached checklist data is malformed, regenerating")
            cached_sections = None

        if cached_sections is not None:
            return SubmissionChecklistResponse(
                project_id=project_id,
                institution=institution,
                sections=cached_sections,
                generated_at=cached.get("generated_at", datetime.now(UTC).isoformat()),
                cached=True,
            )

    try:
        # ── 2. RAG retrieval ──────────────────────────────────────
        emb_client = get_embedding_client()
        seed_query = (
            "documents required submission proposal contents technical financial administrative"
        )
        emb_result = await emb_client.embed_text(seed_query)

        try:
            vector_results = await bid_document_search(
                db=db,
                project_id=str(project_id),
                query_embedding=emb_result.embedding,
                top_k=12,
            )
        except Exception as exc:
            logger.warning("bid_document_search failed, proceeding without vector results: %s", exc)
            vector_results = []

        keywords = [
            *_extract_keywords(seed_query),
            "Section 8",
            "documents required",
            "submission",
            "proposal content",
            "Technical Proposal",
            "Financial Proposal",
            "表格",
            "格式要求",
            "需提交",
            "应提供",
        ]
        kw_results = await keyword_search_chunks(
            db=db,
            project_id=str(project_id),
            keywords=keywords,
            top_k=12,
        )
        seen_ids: set[str] = {r["id"] for r in vector_results}
        merged = list(vector_results)
        for r in kw_results:
            if r["id"] not in seen_ids:
                seen_ids.add(r["id"])
                merged.append(r)

        if not merged:
            logger.warning("No bid document chunks found for project %s", project_id)

        context_block = "\n\n".join(
            "[参考 {n}] {section}（{filename}，第{page}页）:\n{content}".format(
                n=i + 1,
                section=c.get("section_title") or c.get("section_type") or "未知章节",
                filename=c.get("filename") or c.get("source_document") or "",
                page=c.get("page_number") or "?",
                content=c.get("content", ""),
            )
            for i, c in enumerate(merged)
        )

        # ── 3. LLM JSON extraction ────────────────────────────────
        llm = get_llm_client()
        prompt = CHECKLIST_EXTRACT_PROMPT.format(context=context_block)
        messages = [LLMMessage(role="user", content=prompt)]

        raw_json = ""
        async for chunk in llm.chat_stream(messages, max_tokens=4000):
            raw_json += chunk

        # Parse JSON — strip accidental markdown fences
        raw_json = re.sub(r"^```(?:json)?\s*", "", raw_json.strip(), flags=re.MULTILINE)
        raw_json = re.sub(r"\s*```$", "", raw_json.strip(), flags=re.MULTILINE)

        try:
            parsed = json.loads(raw_json)
        except json.JSONDecodeError:
            logger.warning("Checklist LLM response is not valid JSON, using empty list. raw=%r", raw_json[:200])
            parsed = {"sections": []}

        sections_raw = parsed.get("sections", [])
        sections = []
        for sec in sections_raw:
            items = []
            for it in sec.get("items", []):
                src_raw = it.get("source") or {}
                if not isinstance(src_raw, dict):
                    src_raw = {}
                try:
                    items.append(
                        ChecklistItem(
                            id=str(it.get("id") or ""),
                            title=str(it.get("title") or ""),
                            required=bool(it.get("required", True)),
                            copies=_safe_int(it.get("copies")),
                            format_hint=str(it["format_hint"]) if it.get("format_hint") else None,
                            guidance=str(it.get("guidance") or ""),
                            source=ChecklistSource(
                                filename=str(src_raw.get("filename") or ""),
                                page_number=_safe_int(src_raw.get("page_number")),
                                section_title=str(src_raw.get("section_title") or ""),
                                excerpt=str(src_raw.get("excerpt") or ""),
                            ),
                        )
                    )
                except Exception as exc:
                    logger.warning("Skipping malformed checklist item %r: %s", it, exc)
            try:
                sections.append(
                    ChecklistSection(
                        id=str(sec.get("id") or ""),
                        title=str(sec.get("title") or ""),
                        icon=str(sec.get("icon") or "📄"),
                        items=items,
                    )
                )
            except Exception as exc:
                logger.warning("Skipping malformed checklist section %r: %s", sec, exc)

        generated_at = datetime.now(UTC)

        # ── 4. Upsert cache ───────────────────────────────────────
        checklist_data = {
            "sections": [s.model_dump() for s in sections],
            "generated_at": generated_at.isoformat(),
        }
        try:
            if analysis is None:
                new_analysis = BidAnalysis(
                    project_id=project_id,
                    submission_checklist=checklist_data,
                )
                db.add(new_analysis)
            else:
                analysis.submission_checklist = checklist_data
            await db.commit()
        except Exception as exc:
            logger.error("Failed to persist checklist for project %s: %s", project_id, exc)
            await db.rollback()

        return SubmissionChecklistResponse(
            project_id=project_id,
            institution=institution,
            sections=sections,
            generated_at=generated_at,
            cached=False,
        )

    except Exception as exc:
        logger.exception("generate_checklist failed for project %s: %s", project_id, exc)
        raise
