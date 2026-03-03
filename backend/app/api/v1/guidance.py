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
    await project_svc.get_by_id(project_id, current_user.id)

    async def event_generator():
        try:
            from app.agents.embedding_client import get_embedding_client
            from app.agents.llm_client import get_llm_client
            from app.agents.mcp.bid_document_search import bid_document_search

            llm = get_llm_client()
            emb_client = get_embedding_client()

            # Generate embedding for the question
            emb_result = await emb_client.embed_text(request.message)

            # Retrieve context using vector similarity
            doc_results = await bid_document_search(
                db=db,
                project_id=str(project_id),
                query_embedding=emb_result.embedding,
                top_k=5,
            )
            context = [c.get("content", "") for c in doc_results]

            # Build messages
            system_prompt = (
                "你是一位专业的投标文件分析助手。基于提供的上下文回答问题。"
                "引用关键信息时标注来源编号。"
            )
            context_block = "\n\n".join(
                f"[来源 {i + 1}]\n{c}" for i, c in enumerate(context)
            )
            user_msg = (
                f"参考资料:\n{context_block}\n\n用户问题: {request.message}"
            )

            from app.agents.llm_client import Message as LLMMessage
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
                    f"已检索到{len(doc_results)}个相关片段，请直接查阅候选内容。"
                )
                yield f"data: {json.dumps({'type': 'content', 'content': fallback})}\n\n"

            # Send sources after content
            sources_data = json.dumps(
                {
                    "type": "sources",
                    "sources": [
                        {
                            "content": s.get("content", "")[:200],
                            "filename": s.get("filename", ""),
                            "section_title": s.get("section_title", ""),
                            "page_number": s.get("page_number"),
                            "score": s.get("score", 0),
                        }
                        for s in doc_results
                    ],
                }
            )
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
