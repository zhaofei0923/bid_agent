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
            from app.agents.embedding_client import get_embedding_client
            from app.agents.llm_client import Message as LLMMessage
            from app.agents.llm_client import get_llm_client
            from app.agents.mcp.bid_document_search import (
                _extract_keywords,
                bid_document_search,
                keyword_search_chunks,
            )
            from app.agents.mcp.knowledge_search import knowledge_search

            from app.agents.embedding_client import get_translator
            from app.agents.rag import _is_chinese

            llm = get_llm_client()
            emb_client = get_embedding_client()

            # 若问题为中文，先翻译为英文再生成 embedding（中英向量空间不同，翻译可显著提升相关性）
            retrieval_query = request.message
            if _is_chinese(request.message):
                try:
                    retrieval_query = await get_translator().translate_zh_to_en(request.message)
                except Exception:
                    pass  # 静默 fallback 到原中文

            # Generate embedding for the question
            emb_result = await emb_client.embed_text(retrieval_query)

            if use_kb:
                # Retrieve context from knowledge base
                results = await knowledge_search(
                    db=db,
                    query_embedding=emb_result.embedding,
                    institution=institution,
                    top_k=5,
                )
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
            else:
                # ── 招标文件检索：向量检索 + 关键词全量检索，合并去重 ──────────
                # 1. 向量语义检索（top_k=10，捕获语义相关段落）
                vector_results = await bid_document_search(
                    db=db,
                    project_id=str(project_id),
                    query_embedding=emb_result.embedding,
                    top_k=10,
                )
                # 2. 关键词全量检索（ILIKE，合并中英文关键词，捕获精确术语如金额、条款号）
                kw_combined = (
                    request.message
                    if retrieval_query == request.message
                    else f"{request.message} {retrieval_query}"
                )
                keywords = _extract_keywords(kw_combined)
                kw_results = await keyword_search_chunks(
                    db=db,
                    project_id=str(project_id),
                    keywords=keywords,
                    top_k=10,
                )
                # 3. 合并去重（向量结果优先，关键词结果补充）
                seen_ids: set[str] = {r["id"] for r in vector_results}
                merged = list(vector_results)
                for r in kw_results:
                    if r["id"] not in seen_ids:
                        seen_ids.add(r["id"])
                        merged.append(r)

                # 4. 日期类问题额外追加 BDS 章节定向检索
                #    BDS (Bid Data Sheet) 是 ADB 标书中专门列所有关键日期的章节
                _DATE_SIGNALS = {"日期", "截止", "开标", "有效期", "时间节点", "关键日期", "何时", "什么时候"}
                if any(s in request.message for s in _DATE_SIGNALS):
                    for date_query in [
                        "submission deadline bid closing date opening of bids",
                        "bid validity period clarification deadline",
                    ]:
                        date_emb = await emb_client.embed_text(date_query)
                        date_chunks = await bid_document_search(
                            db=db,
                            project_id=str(project_id),
                            query_embedding=date_emb.embedding,
                            section_types=["section_2_bds", "section_1_itb"],
                            top_k=8,
                            score_threshold=0.2,
                        )
                        for c in date_chunks:
                            if c["id"] not in seen_ids:
                                seen_ids.add(c["id"])
                                merged.append(c)

                results = merged

                system_prompt = (
                    "你是一位专业的招标文件分析助手，负责帮助用户深入理解招标文件内容。\n"
                    "招标文件通常为英文，请注意中英文术语对应关系，准确提取关键信息。\n"
                    "规则：\n"
                    "1. 仅基于提供的参考资料回答，不编造信息\n"
                    "2. 如参考资料中有相关内容，必须直接引用原文并标注[来源N]\n"
                    "3. 引用金额、日期、条款编号时确保准确，抄录原文数字\n"
                    "4. 如确实找不到答案，明确告知用户，并说明可能在哪个章节查找\n"
                    "5. 使用简洁的中文回答，专业术语保留英文原文并附中文说明"
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

            # Build context with metadata so LLM can cite sources precisely
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
            user_msg = f"参考资料:\n{context_block}\n\n用户问题: {request.message}"

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
