"""Bid Guidance workflow — LangGraph state graph.

8-node graph: intake → analyze → extract → build → router ↔ guidance/review → quality → END
"""

import json
import logging
from typing import Annotated, Any, Literal, Sequence, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from sqlalchemy import select

from app.agents.llm_client import get_llm_client
from app.agents.skills.base import SkillContext
from app.agents.skills.quality_review import QualityReview
from app.agents.skills.review_draft import ReviewDraft
from app.agents.skills.section_guidance import SectionGuidance

logger = logging.getLogger(__name__)

# ── State Definition ─────────────────────────────────


class BidGuidanceState(TypedDict):
    # Input
    project_id: str
    user_id: str
    db: Any  # AsyncSession — passed via config at runtime

    # Analysis results (filled by Skill nodes)
    tor_analysis: dict
    scoring_criteria: list[dict]

    # Document structure
    document_structure: dict          # {title, sections: [...]}
    section_guidance: dict[str, dict]  # {section_id: guidance_data}

    # User drafts & reviews
    user_drafts: dict[str, str]       # {section_id: content}
    review_results: dict[str, dict]   # {section_id: review_data}

    # Control
    current_step: str
    errors: list[str]

    # Chat messages (human ↔ assistant)
    messages: Annotated[Sequence[BaseMessage], add_messages]


# ── Node Functions ────────────────────────────────────


async def intake_documents_node(state: BidGuidanceState) -> dict:
    """Load bid analysis results from DB."""
    project_id = state.get("project_id", "")
    db = state.get("db")

    if not db or not project_id:
        return {"current_step": "intake_complete", "tor_analysis": {}}

    try:
        from app.models.bid_analysis import BidAnalysis
        result = await db.execute(
            select(BidAnalysis).where(BidAnalysis.project_id == project_id)
        )
        analysis = result.scalar_one_or_none()
        if analysis:
            tor_analysis = {
                "qualification_requirements": analysis.qualification_requirements,
                "evaluation_criteria": analysis.evaluation_criteria,
                "key_dates": analysis.key_dates,
                "submission_checklist": analysis.submission_checklist,
                "commercial_terms": analysis.commercial_terms,
                "evaluation_methodology": analysis.evaluation_methodology,
            }
            return {"current_step": "intake_complete", "tor_analysis": tor_analysis}
    except Exception:
        logger.exception("Failed to load bid analysis for project %s", project_id)

    return {"current_step": "intake_complete", "tor_analysis": {}}


async def analyze_tor_node(state: BidGuidanceState) -> dict:
    """Run analysis if results not loaded from DB."""
    tor_analysis = state.get("tor_analysis", {})
    if tor_analysis:
        return {"current_step": "analysis_complete"}
    return {"current_step": "analysis_complete", "tor_analysis": {}}


async def extract_criteria_node(state: BidGuidanceState) -> dict:
    """Refine evaluation criteria into a structured scoring list."""
    tor = state.get("tor_analysis", {})
    eval_criteria = tor.get("evaluation_criteria") or {}

    technical_criteria = eval_criteria.get("technical_criteria", [])
    if technical_criteria:
        criteria = [
            {
                "criterion": c.get("criterion", ""),
                "weight": c.get("weight", 0),
                "sub_criteria": c.get("sub_criteria", []),
            }
            for c in technical_criteria
        ]
    else:
        criteria = [
            {"criterion": "公司经验", "weight": 30, "sub_criteria": []},
            {"criterion": "关键人员", "weight": 40, "sub_criteria": []},
            {"criterion": "方法论", "weight": 20, "sub_criteria": []},
            {"criterion": "工作计划", "weight": 10, "sub_criteria": []},
        ]

    return {"scoring_criteria": criteria, "current_step": "criteria_extracted"}


async def build_structure_node(state: BidGuidanceState) -> dict:
    """Build the proposal document structure using LLM."""
    llm = get_llm_client()
    criteria = state.get("scoring_criteria", [])
    tor = state.get("tor_analysis", {})

    criteria_text = json.dumps(criteria, ensure_ascii=False, indent=2)
    tor_text = json.dumps(
        {k: v for k, v in tor.items() if v},
        ensure_ascii=False,
    )[:2000]

    prompt = f"""请根据以下评分标准，设计技术标书的章节结构。

=== 评分标准 ===
{criteria_text}

=== 招标分析摘要 ===
{tor_text}

请以JSON格式返回：
{{
  "title": "Technical Proposal",
  "sections": [
    {{
      "id": "section_id",
      "title": "章节名称",
      "scoring_weight": 30,
      "word_count_target": 2000,
      "key_points": ["要点1", "要点2"],
      "format_requirements": "格式要求"
    }}
  ]
}}"""

    try:
        result = await llm.extract_json(
            prompt=prompt,
            system_prompt="你是专业的投标文件结构设计专家。请根据评分标准设计标书的章节结构。以JSON格式返回。",
            temperature=0.3,
            max_tokens=2000,
        )
        structure = result.data
        if structure.get("parse_error"):
            structure = _default_structure()
    except Exception:
        logger.exception("Structure build failed")
        structure = _default_structure()

    return {"document_structure": structure, "current_step": "structure_ready"}


def _default_structure() -> dict:
    return {
        "title": "Technical Proposal",
        "sections": [
            {"id": "firm_experience", "title": "公司经验", "scoring_weight": 30,
             "word_count_target": 2000, "key_points": ["类似项目经验", "客户参考"],
             "format_requirements": "按项目列表形式呼现"},
            {"id": "key_personnel", "title": "关键人员", "scoring_weight": 40,
             "word_count_target": 2500, "key_points": ["学历资质", "相关经验", "项目角色"],
             "format_requirements": "每人单独简历，1-2页"},
            {"id": "methodology", "title": "技术方法论", "scoring_weight": 20,
             "word_count_target": 3000, "key_points": ["理解TOR", "方法论", "创新点"],
             "format_requirements": "配合工作流程图"},
            {"id": "work_plan", "title": "工作计划", "scoring_weight": 10,
             "word_count_target": 800, "key_points": ["时间表", "里程碑"],
             "format_requirements": "甘特图格式"},
        ],
    }


async def guidance_router_node(state: BidGuidanceState) -> dict:
    """Wait for user input — this is a pass-through node for routing."""
    return {"current_step": "awaiting_input"}


async def provide_guidance_node(state: BidGuidanceState) -> dict:
    """Provide section-specific writing guidance using SectionGuidance skill."""
    llm = get_llm_client()
    messages = state.get("messages", [])
    structure = state.get("document_structure", {})
    project_id = state.get("project_id", "")
    db = state.get("db")

    last_human = next(
        (m.content for m in reversed(list(messages)) if isinstance(m, HumanMessage)),
        "",
    )

    # Find which section was requested
    sections = structure.get("sections", _default_structure()["sections"])
    section_config = sections[0] if sections else {}
    if last_human:
        content_lower = last_human.lower()
        for sec in sections:
            if (
                sec.get("title", "").lower() in content_lower
                or sec.get("id", "") in content_lower
            ):
                section_config = sec
                break

    ctx = SkillContext(
        project_id=project_id,
        db=db,
        llm_client=llm,
        parameters={
            "section_config": section_config,
            "bid_context": "",
            "template_context": "",
        },
    )

    skill = SectionGuidance()
    result = await skill.execute(ctx)

    guidance_text = (
        result.data.get("guidance", "")
        if result.success
        else "暂时无法生成指导内容，请稍后再试。"
    )

    return {
        "current_step": "guidance_provided",
        "messages": [AIMessage(content=guidance_text)],
    }


async def review_draft_node(state: BidGuidanceState) -> dict:
    """Review user-submitted draft using ReviewDraft skill."""
    llm = get_llm_client()
    messages = state.get("messages", [])
    project_id = state.get("project_id", "")
    db = state.get("db")
    tor = state.get("tor_analysis", {})

    last_human_content = next(
        (m.content for m in reversed(list(messages)) if isinstance(m, HumanMessage)),
        "",
    )

    ctx = SkillContext(
        project_id=project_id,
        db=db,
        llm_client=llm,
        parameters={
            "draft_content": last_human_content,
            "section_requirements": json.dumps(tor.get("submission_checklist") or {}, ensure_ascii=False)[:500],
            "scoring_context": json.dumps(state.get("scoring_criteria", []), ensure_ascii=False)[:500],
        },
    )

    skill = ReviewDraft()
    result = await skill.execute(ctx)

    feedback_text = (
        json.dumps(result.data, ensure_ascii=False, indent=2)
        if result.success
        else "审查暂时不可用，请稍后再试。"
    )

    return {
        "current_step": "draft_reviewed",
        "messages": [AIMessage(content=f"## 草稿审查反馈\n\n{feedback_text}")],
    }


async def quality_check_node(state: BidGuidanceState) -> dict:
    """Final quality review using QualityReview(mode="full")."""
    llm = get_llm_client()
    messages = state.get("messages", [])
    project_id = state.get("project_id", "")
    db = state.get("db")
    tor = state.get("tor_analysis", {})

    proposal_content = "\n\n".join(
        m.content for m in messages if isinstance(m, HumanMessage)
    )[-4000:]

    ctx = SkillContext(
        project_id=project_id,
        db=db,
        llm_client=llm,
        parameters={
            "proposal_content": proposal_content,
            "bid_requirements": json.dumps(tor, ensure_ascii=False)[:1000],
            "mode": "full",
        },
    )

    skill = QualityReview()
    result = await skill.execute(ctx)

    review_text = (
        json.dumps(result.data, ensure_ascii=False, indent=2)
        if result.success
        else "质量审查暂时不可用，请稍后再试。"
    )

    return {
        "current_step": "quality_checked",
        "messages": [AIMessage(content=f"## 全文质量审查报告\n\n{review_text}")],
    }


# ── Routing Logic ─────────────────────────────────────


def route_user_intent(
    state: BidGuidanceState,
) -> Literal["provide_guidance", "review_draft", "quality_check", "wait"]:
    """Route based on the last user message's intent."""
    messages = state.get("messages", [])
    if not messages:
        return "wait"

    last_msg = messages[-1]
    if not isinstance(last_msg, HumanMessage):
        return "wait"

    content = last_msg.content.lower()

    # Intent detection (rule-based; could upgrade to LLM classifier)
    guidance_keywords = ["指导", "怎么写", "如何写", "guide", "how to write", "编写"]
    review_keywords = ["审查", "检查", "review", "请看看", "帮我看"]
    quality_keywords = ["最终审查", "全文检查", "final review", "完整审查", "提交前"]

    if any(w in content for w in quality_keywords):
        return "quality_check"
    if any(w in content for w in review_keywords):
        return "review_draft"
    if any(w in content for w in guidance_keywords):
        return "provide_guidance"

    return "wait"


# ── Graph Construction ────────────────────────────────


def build_bid_guidance_graph() -> StateGraph:
    """Construct and return the bid guidance workflow graph."""
    workflow = StateGraph(BidGuidanceState)

    # Add nodes
    workflow.add_node("intake_documents", intake_documents_node)
    workflow.add_node("analyze_tor", analyze_tor_node)
    workflow.add_node("extract_criteria", extract_criteria_node)
    workflow.add_node("build_structure", build_structure_node)
    workflow.add_node("guidance_router", guidance_router_node)
    workflow.add_node("provide_guidance", provide_guidance_node)
    workflow.add_node("review_draft", review_draft_node)
    workflow.add_node("quality_check", quality_check_node)

    # Linear edges for analysis phase
    workflow.add_edge(START, "intake_documents")
    workflow.add_edge("intake_documents", "analyze_tor")
    workflow.add_edge("analyze_tor", "extract_criteria")
    workflow.add_edge("extract_criteria", "build_structure")
    workflow.add_edge("build_structure", "guidance_router")

    # Conditional routing from guidance_router
    workflow.add_conditional_edges(
        "guidance_router",
        route_user_intent,
        {
            "provide_guidance": "provide_guidance",
            "review_draft": "review_draft",
            "quality_check": "quality_check",
            "wait": END,
        },
    )

    # Return edges
    workflow.add_edge("provide_guidance", "guidance_router")
    workflow.add_edge("review_draft", "guidance_router")
    workflow.add_edge("quality_check", END)

    return workflow


def compile_bid_guidance_workflow(checkpointer=None):
    """Compile the workflow with optional checkpointer (e.g. RedisSaver)."""
    graph = build_bid_guidance_graph()
    return graph.compile(checkpointer=checkpointer)
