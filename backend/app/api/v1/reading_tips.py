"""Reading tips API — generate reading guidance and bidding suggestions
based on ADB/WB knowledge base RAG.

Performance: embeddings, RAG searches, and LLM calls are parallelised
via asyncio.gather() to keep total latency under ~25 s.
"""

import asyncio
import logging
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.embedding_client import get_embedding_client
from app.agents.llm_client import Message as LLMMessage
from app.agents.llm_client import get_llm_client
from app.agents.mcp.knowledge_search import knowledge_search
from app.core.credits import deduct_credits, require_credits
from app.core.security import get_current_user
from app.database import get_db
from app.models.user import User
from app.services.project_service import ProjectService

logger = logging.getLogger(__name__)
router = APIRouter()


class ReadingTipsSource(BaseModel):
    content: str
    source_document: str
    page_number: int | None = None
    score: float = 0.0


class ReadingTipsResponse(BaseModel):
    reading_tips: str
    bidding_suggestions: str
    sources: list[ReadingTipsSource]


# ── Institution-specific base context (shared between the two LLM calls) ──
_INST_CONTEXT: dict[str, str] = {
    "adb": (
        "ADB SBD 通常包含 Section 1 ITB（投标人须知）、Section 2 BDS（投标数据表）、"
        "Section 3 Evaluation/Qualification Criteria、Section 4 Bidding Forms、"
        "Part 2 Requirements (TOR/SOW)、Part 3 Contract。"
        "BDS 是对 ITB 的项目特定修改，冲突时以 BDS 为准。"
    ),
    "wb": (
        "WB SPD 通常包含 Section I Instructions to Consultants、Section II Data Sheet、"
        "Section III Technical Proposal Forms、Section IV Financial Proposal Forms、"
        "Section V Eligible Countries、Section VI Standard Forms of Contract。"
        "重点关注 PPSD 选择方式（QCBS/CQS/FBS/LCS/SSS）和 ESF 合规要求。"
    ),
    "afdb": "AfDB 采购文件结构通常包含投标人须知、数据表、评标标准和合同条款等部分。",
}

_INST_NAMES: dict[str, str] = {
    "adb": "亚洲开发银行（ADB）",
    "wb": "世界银行（WB）",
    "afdb": "非洲开发银行（AfDB）",
}


def _system_reading(institution: str) -> str:
    name = _INST_NAMES.get(institution, institution.upper())
    ctx = _INST_CONTEXT.get(institution, "")
    return (
        f"你是一位精通{name}采购规程的投标顾问。"
        f"{ctx}"
        "请根据招标文件概览和知识库参考资料，给出**招标文件阅读建议**："
        "建议阅读顺序、每个章节的重点关注事项。"
        "回答请使用中文，结构化输出，引用知识库时标注来源编号。"
    )


def _system_bidding(institution: str) -> str:
    name = _INST_NAMES.get(institution, institution.upper())
    ctx = _INST_CONTEXT.get(institution, "")
    return (
        f"你是一位精通{name}采购规程的投标顾问。"
        f"{ctx}"
        "请根据招标文件概览和知识库参考资料，给出**投标文件编制建议**："
        "针对该项目类型和评标方式的编制要点、常见陷阱和提分技巧。"
        "回答请使用中文，结构化输出，引用知识库时标注来源编号。"
    )


# ── RAG queries per institution ─────────────────────────────
_SEARCH_QUERIES: dict[str, list[str]] = {
    "adb": [
        "ADB standard bidding document reading guide structure",
        "ADB bid proposal preparation tips BDS ITB",
        "ADB evaluation criteria scoring methodology QCBS",
    ],
    "wb": [
        "World Bank standard procurement document reading guide",
        "World Bank proposal preparation tips QCBS CQS",
        "World Bank ESF environmental social framework procurement",
    ],
    "afdb": [
        "AfDB procurement document structure guide",
        "AfDB bid preparation requirements evaluation",
    ],
}


@router.post("/{project_id}/reading-tips", response_model=ReadingTipsResponse)
async def get_reading_tips(
    project_id: UUID,
    cost_info: dict = Depends(require_credits("guidance_qa")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReadingTipsResponse:
    """Generate reading tips and bidding suggestions via knowledge base RAG.

    Embeddings, RAG searches, and LLM calls are parallelised to avoid timeout.
    Costs 5 credits (same as guidance_qa).
    """
    project_svc = ProjectService(db)
    project = await project_svc.get_by_id(project_id, current_user.id)

    institution: str = getattr(project, "institution", None) or "adb"
    overview: str = getattr(project, "combined_ai_overview", None) or ""

    # ── Step 1: parallel embedding of all search queries ──
    emb_client = get_embedding_client()
    queries = _SEARCH_QUERIES.get(institution, _SEARCH_QUERIES["adb"])
    emb_results = await asyncio.gather(
        *[emb_client.embed_text(q) for q in queries]
    )

    # ── Step 2: parallel RAG search ──
    search_tasks = [
        knowledge_search(
            db=db,
            query_embedding=emb.embedding,
            institution=institution,
            top_k=5,
            score_threshold=0.3,
        )
        for emb in emb_results
    ]
    search_results = await asyncio.gather(*search_tasks)

    # De-duplicate results
    seen: set[str] = set()
    merged: list[dict] = []
    for chunks in search_results:
        for c in chunks:
            cid = c.get("source_document", "") + str(c.get("page_number"))
            if cid not in seen:
                seen.add(cid)
                merged.append(c)
    top_results = merged[:12]

    # ── Step 3: build shared context ──
    kb_context = "\n\n".join(
        f"[来源{i + 1}] {r['source_document']} (P{r.get('page_number', '?')})\n{r['content']}"
        for i, r in enumerate(top_results)
    )
    overview_snippet = overview[:3000] if overview else "（暂无文档概览）"
    shared_context = (
        f"## 招标文件概览\n\n{overview_snippet}\n\n"
        f"## 知识库参考资料\n\n{kb_context}"
    )

    # ── Step 4: two parallel LLM calls ──
    llm = get_llm_client()

    async def _call_reading() -> str:
        r = await llm.chat(
            messages=[
                LLMMessage(role="system", content=_system_reading(institution)),
                LLMMessage(
                    role="user",
                    content=(
                        f"{shared_context}\n\n"
                        "请给出**招标文件阅读建议**（建议阅读顺序、每个章节的重点关注事项）。"
                    ),
                ),
            ],
            temperature=0.4,
            max_tokens=2000,
        )
        return r.content or ""

    async def _call_bidding() -> str:
        r = await llm.chat(
            messages=[
                LLMMessage(role="system", content=_system_bidding(institution)),
                LLMMessage(
                    role="user",
                    content=(
                        f"{shared_context}\n\n"
                        "请给出**投标文件编制建议**（编制要点、常见陷阱和提分技巧）。"
                    ),
                ),
            ],
            temperature=0.4,
            max_tokens=2000,
        )
        return r.content or ""

    reading_tips, bidding_suggestions = await asyncio.gather(
        _call_reading(), _call_bidding()
    )

    # ── Step 5: deduct credits ──
    await deduct_credits(
        current_user,
        cost_info["action"],
        cost_info["cost"],
        db,
        reference_id=str(project_id),
    )

    sources = [
        ReadingTipsSource(
            content=r["content"][:200],
            source_document=r.get("source_document", ""),
            page_number=r.get("page_number"),
            score=r.get("score", 0),
        )
        for r in top_results
    ]

    return ReadingTipsResponse(
        reading_tips=reading_tips,
        bidding_suggestions=bidding_suggestions,
        sources=sources,
    )
