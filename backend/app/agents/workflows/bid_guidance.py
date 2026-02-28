"""Bid Guidance workflow — LangGraph state graph.

8-node graph: intake → analyze → extract → build → router ↔ guidance/review → quality → END
"""

from typing import Annotated, Literal, Sequence, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

# ── State Definition ─────────────────────────────────


class BidGuidanceState(TypedDict):
    # Input
    project_id: str
    user_id: str
    documents: list[dict]           # [{id, name, type}]
    parsed_documents: dict[str, str]  # {doc_id: content}

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
    """Load and parse uploaded documents from DB."""
    # TODO: Read ProjectDocument/BidDocument parsed_content from DB
    return {"current_step": "intake_complete", "parsed_documents": {}}


async def analyze_tor_node(state: BidGuidanceState) -> dict:
    """Run analysis Skills: qualification, criteria, dates, BDS, commercial, risk."""
    # TODO: Call Skills in parallel / sequence with actual MCP tools
    return {
        "current_step": "analysis_complete",
        "tor_analysis": {"status": "placeholder"},
    }


async def extract_criteria_node(state: BidGuidanceState) -> dict:
    """Refine evaluation criteria into a structured scoring list."""
    _tor = state.get("tor_analysis", {})
    # TODO: Extract from tor_analysis or fallback to 4-dimension defaults
    criteria = [
        {"criterion": "公司经验", "weight": 30},
        {"criterion": "关键人员", "weight": 40},
        {"criterion": "方法论", "weight": 20},
        {"criterion": "工作计划", "weight": 10},
    ]
    return {"scoring_criteria": criteria, "current_step": "criteria_extracted"}


async def build_structure_node(state: BidGuidanceState) -> dict:
    """Build the proposal document structure (sections, scoring weights, format)."""
    # TODO: LLM call to generate structure based on analysis
    structure = {
        "title": "Technical Proposal",
        "sections": [
            {"id": "firm_experience", "title": "公司经验", "scoring_weight": 30},
            {"id": "key_personnel", "title": "关键人员", "scoring_weight": 40},
            {"id": "methodology", "title": "方法论", "scoring_weight": 20},
            {"id": "work_plan", "title": "工作计划", "scoring_weight": 10},
        ],
    }
    return {"document_structure": structure, "current_step": "structure_ready"}


async def guidance_router_node(state: BidGuidanceState) -> dict:
    """Wait for user input — this is a pass-through node for routing."""
    return {"current_step": "awaiting_input"}


async def provide_guidance_node(state: BidGuidanceState) -> dict:
    """Provide section-specific writing guidance using SectionGuidance skill."""
    # TODO: Invoke SectionGuidance.execute() with real context
    return {"current_step": "guidance_provided"}


async def review_draft_node(state: BidGuidanceState) -> dict:
    """Review user-submitted draft using ReviewDraft skill."""
    # TODO: Invoke ReviewDraft.execute() with user's draft
    return {"current_step": "draft_reviewed"}


async def quality_check_node(state: BidGuidanceState) -> dict:
    """Final quality review using QualityReview(mode="full")."""
    # TODO: Invoke QualityReview.execute() with full proposal
    return {"current_step": "quality_checked"}


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
            "wait": "guidance_router",
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
