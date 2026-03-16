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
            from sqlalchemy import text as _sql_text

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
                if institution == "wb":
                    system_prompt = (
                        "你是一位专业的投标编制顾问，精通世界银行（WB）采购规程和标准采购文件（SPD）。"
                        "基于提供的知识库文档，为用户提供具体、可操作的标书编制建议。"
                        "重点关注：WB SPD Section I-VI 结构、PPSD 选择方式（QCBS/CQS/FBS/LCS/SSS）、"
                        "ESF（环境与社会框架）合规要求。引用关键指南时标注来源编号。"
                    )
                else:
                    system_prompt = (
                        "你是一位专业的投标编制顾问，精通亚洲开发银行（ADB）采购规程和标准招标文件（SBD）。"
                        "基于提供的知识库文档，为用户提供具体、可操作的标书编制建议。"
                        "ADB SBD 有两种主要类型："
                        "(1) 货物/工厂/工程采购：Section 4 含投标函、价格表、资格表格（ELI/CON/FIN/EXP）；"
                        "(2) 咨询服务采购：Section 4 含 TECH-1~6、FIN-1~4、ELI-1/2 表格。"
                        "请根据实际项目类型匹配对应的表格体系。"
                        "重点关注：BDS 对 ITB 的项目特定修改、评审标准和方法。引用关键指南时标注来源编号。"
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

                # 2b-4. BDS 优先排序 + 截取
                # BDS 是对 ITB 的项目特定修改，冲突时以 BDS 为准，故排在前面
                _section_priority = {"section_2_bds": 0, "section_1_itb": 1}
                merged.sort(
                    key=lambda c: (
                        _section_priority.get(c.get("section_type", ""), 9),
                        -(c.get("score") or 0),
                    )
                )
                results = merged[:15]

                # 2b-5. 邻居 chunk 上下文扩展（修复分块边界截断问题）
                # PDF 表格中的数字可能在分块时被截断（如 "US$ 850,000" → "US$ 8" | "50,000"）
                # 对每个检索到的 chunk 获取前一个 chunk 尾部 300 字符并拼接，恢复完整上下文
                if results:
                    _cid_params = {}
                    _cast_exprs = []
                    for _idx, _r in enumerate(results):
                        _pname = f"cid_{_idx}"
                        _cid_params[_pname] = _r["id"]
                        _cast_exprs.append(f"cast(:{_pname} as uuid)")
                    _neighbor_sql = _sql_text(
                        "SELECT c1.id::text AS chunk_id, "
                        "RIGHT(c2.content, 300) AS prev_tail "
                        "FROM bid_document_chunks c1 "
                        "JOIN bid_document_chunks c2 "
                        "ON c2.bid_document_id = c1.bid_document_id "
                        "AND c2.section_id IS NOT DISTINCT FROM c1.section_id "
                        "AND c2.chunk_index = c1.chunk_index - 1 "
                        f"WHERE c1.id IN ({', '.join(_cast_exprs)})"
                    )
                    try:
                        _nb_rows = await db.execute(_neighbor_sql, _cid_params)
                        _prev_tails = {
                            str(row[0]): row[1] for row in _nb_rows
                        }
                        for _r in results:
                            _tail = _prev_tails.get(_r["id"])
                            if _tail:
                                _r["content"] = (
                                    f"[...前文续] {_tail.strip()}\n"
                                    + _r["content"]
                                )
                    except Exception:
                        logger.warning("邻居 chunk 扩展失败，跳过", exc_info=True)

                # 2b-6. 结构化分析数据注入（最高可信度来源）
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

                if institution == "wb":
                    system_prompt = (
                        "你是一位专业的世界银行（WB）招标文件分析助手，负责帮助用户深入理解招标文件内容。\n"
                        "你精通 WB 标准采购文件（SPD）结构，包括 Section I-VI、Data Sheet、\n"
                        "Form TECH/FIN 系列表格，以及 PPSD、ESF 合规要求。\n"
                        "招标文件通常为英文，请注意中英文术语对应关系，准确提取关键信息。\n"
                        "重要原则：Data Sheet（投标资料表）是对标准条款的项目特定修改，\n"
                        "当 Data Sheet 与标准条款内容冲突时，必须以 Data Sheet 为准。\n"
                        "规则：\n"
                        "1. 优先引用[高可信度]标注的结构化数据，这些是已精确提取的可靠信息\n"
                        "2. 仅基于提供的参考资料回答，不编造信息\n"
                        "3. 引用时必须标注来源的章节和页码，格式：[来源N, 章节名, 第X页]\n"
                        "4. 引用金额、日期、条款编号时确保准确，直接抄录原文数字，不做换算\n"
                        "5. Data Sheet 中的具体数值优先于标准条款中的通用描述\n"
                        "6. 如确实找不到答案，明确告知用户，并说明可能在哪个章节查找\n"
                        "7. 使用简洁的中文回答，专业术语保留英文原文并附中文说明\n"
                        "8. WB 项目特别关注 ESF 合规、劳工管理、环境社会承诺等要求"
                    )
                else:
                    system_prompt = (
                        "你是一位专业的亚洲开发银行（ADB）招标文件分析助手，负责帮助用户深入理解招标文件内容。\n"
                        "你精通 ADB 标准招标文件（SBD）结构，包括 Section 1-5、BDS 和 Section 3 评审标准。\n"
                        "ADB SBD Section 4 有两种表格体系：\n"
                        "- 货物/工厂/工程采购：投标函（Letter of Technical/Price Bid）、价格表（Price Schedules）、"
                        "资格表格（ELI/CON/FIN/EXP）\n"
                        "- 咨询服务采购：技术建议书（TECH-1~6）、财务建议书（FIN-1~4）、资格声明（ELI-1/2）\n"
                        "请根据实际项目采购类型使用正确的表格体系。\n\n"
                        "招标文件通常为英文，请注意中英文术语对应关系，准确提取关键信息。\n"
                        "重要原则：BDS（Bid Data Sheet，投标资料表）是对ITB（Instructions to Bidders）\n"
                        "的项目特定修改，当BDS与ITB内容冲突时，必须以BDS为准。\n"
                        "规则：\n"
                        "1. 优先引用[高可信度]标注的结构化数据，这些是已精确提取的可靠信息\n"
                        "2. 仅基于提供的参考资料回答，不编造信息\n"
                        "3. 引用时必须标注来源的章节和页码，格式：[来源N, 章节名, 第X页]\n"
                        "4. 引用金额、日期、条款编号时确保准确，直接抄录原文数字，不做换算\n"
                        "5. BDS中的具体数值优先于ITB中的通用描述\n"
                        "6. 如确实找不到答案，明确告知用户，并说明可能在哪个章节查找\n"
                        "7. 使用简洁的中文回答，专业术语保留英文原文并附中文说明"
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
    from app.agents.prompts.checklist_templates import get_institution_template
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
        # ── 2. RAG retrieval (institution-specific) ──────────────────
        import asyncio

        emb_client = get_embedding_client()

        # Institution-specific seed queries & keywords
        # Cover BOTH procurement types (Goods/Plant/Works + Consulting)
        # since the LLM will determine the actual type from document content.
        if institution == "wb":
            seed_query = (
                "documents required submission bidding forms Section IV Section III "
                "Letter of Bid Price Schedule qualification criteria ELI CON FIN EXP "
                "Technical Proposal Financial Proposal TECH FIN forms SPD Data Sheet"
            )
            extra_keywords = [
                # Goods/Works forms
                "Letter of Bid", "Price Schedule", "Form ELI", "Form CON",
                "Form FIN", "Form EXP", "Bid-Securing Declaration",
                "Manufacturer's Authorization",
                # Consulting forms
                "Form TECH", "Form FIN", "SPD", "Data Sheet",
                # Common
                "Section III", "Section IV", "qualification",
                "ESF", "Labor Management", "ESMP",
            ]
            section4_query = (
                "Section IV Bidding Forms Letter of Bid Price Schedule "
                "qualification forms ELI CON FIN EXP TECH"
            )
        else:
            # ADB (default) — cover Goods/Plant/Works + Consulting
            seed_query = (
                "documents required submission bidding forms standard forms "
                "Section 4 Section 3 BDS ITB Letter of Bid Price Schedule "
                "qualification criteria ELI CON FIN EXP "
                "Technical Proposal Financial Proposal TECH FIN forms"
            )
            extra_keywords = [
                # Goods/Plant/Works forms
                "Letter of Technical Bid", "Letter of Price Bid", "Price Schedule",
                "Form ELI", "Form CON", "Form FIN", "Form EXP",
                "Manufacturer's Authorization", "Bid-Securing Declaration",
                "qualification criteria", "bidding forms",
                # Consulting forms
                "TECH-1", "TECH-2", "TECH-3", "TECH-4", "TECH-5", "TECH-6",
                "FIN-1", "FIN-2", "FIN-3", "FIN-4", "ELI-1", "ELI-2",
                # Common
                "Section 4", "Section 3", "BDS", "ITB",
            ]
            section4_query = (
                "Section 4 Bidding Forms Letter of Bid Price Schedule "
                "qualification forms ELI CON FIN EXP TECH"
            )

        # ── Parallel embeddings (independent HTTP calls) ────────
        emb_result, s4_emb = await asyncio.gather(
            emb_client.embed_text(seed_query),
            emb_client.embed_text(section4_query),
        )

        # ── Vector search #1: broad seed query ────────────────────
        try:
            vector_results = await bid_document_search(
                db=db,
                project_id=str(project_id),
                query_embedding=emb_result.embedding,
                top_k=24,
            )
        except Exception as exc:
            logger.warning("bid_document_search failed, proceeding without vector results: %s", exc)
            vector_results = []

        # ── Vector search #2: Section 4 / forms focused ──────────
        try:
            s4_results = await bid_document_search(
                db=db,
                project_id=str(project_id),
                query_embedding=s4_emb.embedding,
                top_k=20,
            )
        except Exception as exc:
            logger.warning("Section 4 vector search failed: %s", exc)
            s4_results = []

        seen_ids: set[str] = {r["id"] for r in vector_results}
        merged = list(vector_results)
        for r in s4_results:
            if r["id"] not in seen_ids:
                seen_ids.add(r["id"])
                merged.append(r)

        # ── Vector search #3: section_type directed (for new docs with section classification) ──
        try:
            s4_directed = await bid_document_search(
                db=db,
                project_id=str(project_id),
                query_embedding=s4_emb.embedding,
                section_types=["section_4_forms", "section_3_qualification", "section_2_bds"],
                top_k=15,
                score_threshold=0.2,
            )
            for r in s4_directed:
                if r["id"] not in seen_ids:
                    seen_ids.add(r["id"])
                    merged.append(r)
        except Exception as exc:
            logger.warning("Section-type directed search failed: %s", exc)

        # ── Keyword search ────────────────────────────────────────
        keywords = [
            *_extract_keywords(seed_query),
            *extra_keywords,
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
            top_k=24,
        )
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
        institution_template = get_institution_template(institution)
        prompt = CHECKLIST_EXTRACT_PROMPT.format(
            context=context_block,
            institution_template=institution_template,
        )
        messages = [LLMMessage(role="user", content=prompt)]

        raw_json = ""
        async for chunk in llm.chat_stream(messages, max_tokens=6000):
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
                            form_reference=str(it["form_reference"]) if it.get("form_reference") else None,
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
