"""Reading tips API — generate reading guidance and bidding suggestions
based on ADB/WB knowledge base RAG."""

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


# ── System prompts per institution ──────────────────────────
_SYSTEM_PROMPTS: dict[str, str] = {
    "adb": (
        "你是一位精通亚洲开发银行（ADB）采购规程和标准招标文件（SBD）的投标顾问。"
        "根据用户提供的招标文件概览和知识库参考资料，给出两部分建议：\n"
        "1. **招标文件阅读建议**：建议阅读顺序、每个章节重点关注项\n"
        "2. **投标文件编制建议**：根据 ADB SBD 结构给出编制要点和注意事项\n"
        "ADB SBD 通常包含 Section 1 ITB（投标人须知）、Section 2 BDS（投标数据表）、"
        "Section 3 Evaluation/Qualification Criteria、Section 4 Bidding Forms、"
        "Part 2 Requirements (TOR/SOW)、Part 3 Contract。"
        "BDS 是对 ITB 的项目特定修改，冲突时以 BDS 为准。"
        "回答请使用中文，结构化输出，引用知识库时标注来源编号。"
    ),
    "wb": (
        "你是一位精通世界银行（WB）采购规程和标准采购文件（SPD）的投标顾问。"
        "根据用户提供的招标文件概览和知识库参考资料，给出两部分建议：\n"
        "1. **招标文件阅读建议**：建议阅读顺序、每个章节重点关注项\n"
        "2. **投标文件编制建议**：根据 WB SPD 结构给出编制要点和注意事项\n"
        "WB SPD 通常包含 Section I Instructions to Consultants、Section II Data Sheet、"
        "Section III Technical Proposal Forms、Section IV Financial Proposal Forms、"
        "Section V Eligible Countries、Section VI Standard Forms of Contract。"
        "重点关注 PPSD 选择方式（QCBS/CQS/FBS/LCS/SSS）和 ESF 合规要求。"
        "回答请使用中文，结构化输出，引用知识库时标注来源编号。"
    ),
    "afdb": (
        "你是一位精通非洲开发银行（AfDB）采购规程的投标顾问。"
        "根据用户提供的招标文件概览和知识库参考资料，给出两部分建议：\n"
        "1. **招标文件阅读建议**：建议阅读顺序、每个章节重点关注项\n"
        "2. **投标文件编制建议**：根据 AfDB 采购文件结构给出编制要点和注意事项\n"
        "回答请使用中文，结构化输出，引用知识库时标注来源编号。"
    ),
}

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

    Uses the project's institution type and combined_ai_overview to retrieve
    relevant ADB/WB/AfDB guidelines and produce targeted advice.

    Costs 5 credits (same as guidance_qa).
    """
    project_svc = ProjectService(db)
    project = await project_svc.get_by_id(project_id, current_user.id)

    institution: str = getattr(project, "institution", None) or "adb"
    overview: str = getattr(project, "combined_ai_overview", None) or ""

    # ── Step 1: multi-query RAG over knowledge base ──
    emb_client = get_embedding_client()
    queries = _SEARCH_QUERIES.get(institution, _SEARCH_QUERIES["adb"])

    seen: set[str] = set()
    merged: list[dict] = []
    for q in queries:
        emb = await emb_client.embed_text(q)
        chunks = await knowledge_search(
            db=db,
            query_embedding=emb.embedding,
            institution=institution,
            top_k=5,
            score_threshold=0.3,
        )
        for c in chunks:
            cid = c.get("source_document", "") + str(c.get("page_number"))
            if cid not in seen:
                seen.add(cid)
                merged.append(c)

    top_results = merged[:12]

    # ── Step 2: build context ──
    kb_context = "\n\n".join(
        f"[来源{i + 1}] {r['source_document']} (P{r.get('page_number', '?')})\n{r['content']}"
        for i, r in enumerate(top_results)
    )

    overview_snippet = overview[:3000] if overview else "（暂无文档概览）"

    # ── Step 3: LLM synthesis ──
    system_prompt = _SYSTEM_PROMPTS.get(institution, _SYSTEM_PROMPTS["adb"])
    user_prompt = (
        f"## 招标文件概览\n\n{overview_snippet}\n\n"
        f"## 知识库参考资料\n\n{kb_context}\n\n"
        "请基于以上信息，分两部分回答：\n"
        "### 一、招标文件阅读建议\n"
        "（建议阅读顺序、每个章节的重点关注事项）\n\n"
        "### 二、投标文件编制建议\n"
        "（针对该项目类型和评标方式的编制要点、常见陷阱和提分技巧）"
    )

    llm = get_llm_client()
    result = await llm.chat(
        messages=[
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_prompt),
        ],
        temperature=0.4,
        max_tokens=3000,
    )

    full_text = result.content or ""

    # Split on the two headings
    reading_tips = full_text
    bidding_suggestions = ""

    marker = "### 二、投标文件编制建议"
    if marker in full_text:
        parts = full_text.split(marker, 1)
        reading_tips = parts[0].strip()
        bidding_suggestions = (marker + parts[1]).strip()
    elif "## 二" in full_text:
        parts = full_text.split("## 二", 1)
        reading_tips = parts[0].strip()
        bidding_suggestions = ("## 二" + parts[1]).strip()

    # ── Step 4: deduct credits ──
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
