"""Guidance API — Q&A and SSE chat with the bid guidance workflow."""

import json
import logging
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

            llm = get_llm_client()
            emb_client = get_embedding_client()

            # Generate embedding for the question
            emb_result = await emb_client.embed_text(request.message)

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
                # 2. 关键词全量检索（ILIKE，捕获精确术语如金额、条款号、英文专有名词）
                keywords = _extract_keywords(request.message)
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
