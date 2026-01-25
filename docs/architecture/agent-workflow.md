# BidAgent Agent工作流设计

## 1. 概述

BidAgent采用LangGraph构建多Agent协作工作流，实现从招标文档分析到标书生成的全流程自动化。

### 核心理念
- **状态机驱动**: 清晰的状态转换，便于调试和恢复
- **人机协作**: 关键节点支持人工审核和干预
- **模块化设计**: Agent职责单一，可独立升级
- **可观测性**: 完整的执行日志和中间状态

## 2. 整体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          BidAgent Workflow System                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌───────────┐ │
│  │   Intake    │────▶│  Analysis   │────▶│  Planning   │────▶│ Generation│ │
│  │   Agent     │     │   Agent     │     │   Agent     │     │   Agent   │ │
│  └─────────────┘     └─────────────┘     └─────────────┘     └───────────┘ │
│        │                   │                   │                   │        │
│        ▼                   ▼                   ▼                   ▼        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Shared State (LangGraph)                        │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │   │
│  │  │Documents│ │Analysis │ │  Plan   │ │ Drafts  │ │ History │       │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│        │                   │                   │                   │        │
│        ▼                   ▼                   ▼                   ▼        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                           Tool Layer                                 │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │   │
│  │  │PDF Parse│ │Embedding│ │ Search  │ │Template │ │ Export  │       │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │
                                     ▼
                    ┌────────────────────────────────┐
                    │        LLM Layer               │
                    │  ┌──────────┐ ┌──────────┐    │
                    │  │DeepSeek  │ │DeepSeek  │    │
                    │  │   V3    │ │   R1     │    │
                    │  │(通用)    │ │(复杂推理) │    │
                    │  └──────────┘ └──────────┘    │
                    └────────────────────────────────┘
```

## 3. 主工作流: 标书生成 (Bid Generation)

### 3.1 状态图

```
                              ┌──────────────┐
                              │    START     │
                              └──────┬───────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │   intake_documents    │
                         │   (文档上传与解析)      │
                         └───────────┬───────────┘
                                     │
                              ┌──────┴──────┐
                              │  解析成功?   │
                              └──────┬──────┘
                             Yes     │     No
                      ┌──────────────┴──────────────┐
                      │                             │
                      ▼                             ▼
         ┌───────────────────────┐      ┌──────────────────┐
         │   analyze_tor        │      │   error_handler  │
         │   (分析TOR要求)       │      └──────────────────┘
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   extract_criteria   │
         │   (提取评分标准)       │
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   create_outline      │
         │   (生成文档大纲)       │
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   human_review       │◀─────────┐
         │   (人工审核大纲)       │          │
         └───────────┬───────────┘          │
                     │                      │
              ┌──────┴──────┐               │
              │  审核通过?   │               │
              └──────┬──────┘               │
             Yes     │     No               │
      ┌──────────────┴──────────────────────┘
      │                             
      ▼                             
┌───────────────────────┐
│   generate_sections   │◀────┐
│   (生成各章节内容)      │     │
└───────────┬───────────┘     │
            │                  │
            ▼                  │
┌───────────────────────┐     │
│   quality_check       │     │
│   (质量检查)           │     │
└───────────┬───────────┘     │
            │                  │
     ┌──────┴──────┐          │
     │  质量达标?   │──────────┘
     └──────┬──────┘    No (重新生成)
            │ Yes
            ▼
┌───────────────────────┐
│   compile_document    │
│   (汇编完整文档)       │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│   final_review        │
│   (最终审核)           │
└───────────┬───────────┘
            │
            ▼
      ┌──────────┐
      │   END    │
      └──────────┘
```

### 3.2 状态定义

```python
# app/agents/workflows/bid_generation/state.py
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class BidGenerationState(TypedDict):
    """标书生成工作流状态"""
    
    # 基本信息
    project_id: str
    user_id: str
    
    # 输入文档
    documents: list[dict]  # 上传的文档列表
    parsed_documents: dict[str, str]  # 解析后的文本内容
    
    # 分析结果
    tor_analysis: dict  # TOR分析结果
    # {
    #   "project_title": "...",
    #   "objectives": [...],
    #   "scope_of_work": [...],
    #   "deliverables": [...],
    #   "qualifications": [...],
    #   "timeline": {...},
    #   "evaluation_criteria": [...]
    # }
    
    scoring_criteria: list[dict]  # 评分标准
    # [
    #   {"criterion": "Technical Approach", "weight": 40, "sub_criteria": [...]},
    #   {"criterion": "Team Composition", "weight": 30, "sub_criteria": [...]},
    #   ...
    # ]
    
    # 生成计划
    document_outline: dict  # 文档大纲
    # {
    #   "sections": [
    #     {"id": "1", "title": "Technical Approach", "subsections": [...]},
    #     ...
    #   ]
    # }
    
    # 生成内容
    generated_sections: dict[str, str]  # 各章节内容
    quality_scores: dict[str, float]  # 质量评分
    
    # 最终输出
    final_document: str  # 完整文档
    export_path: str  # 导出路径
    
    # 工作流控制
    current_step: str
    retry_count: int
    errors: list[str]
    
    # 对话历史 (用于人机交互)
    messages: Annotated[Sequence[BaseMessage], add_messages]
```

### 3.3 节点实现

```python
# app/agents/workflows/bid_generation/nodes.py
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from app.agents.llm_client import get_llm
from .state import BidGenerationState

# ============ 文档接入节点 ============

async def intake_documents(state: BidGenerationState) -> BidGenerationState:
    """
    解析上传的文档，提取文本内容
    """
    from app.services.document_service import parse_document
    
    parsed = {}
    errors = []
    
    for doc in state["documents"]:
        try:
            content = await parse_document(doc["file_path"])
            parsed[doc["id"]] = content
        except Exception as e:
            errors.append(f"Failed to parse {doc['name']}: {str(e)}")
    
    return {
        **state,
        "parsed_documents": parsed,
        "errors": state.get("errors", []) + errors,
        "current_step": "intake_documents"
    }


# ============ TOR分析节点 ============

async def analyze_tor(state: BidGenerationState) -> BidGenerationState:
    """
    分析TOR文档，提取关键信息
    """
    llm = get_llm("deepseek-v3")
    
    # 获取TOR文档内容
    tor_content = None
    for doc_id, content in state["parsed_documents"].items():
        doc = next((d for d in state["documents"] if d["id"] == doc_id), None)
        if doc and doc["type"] == "tor":
            tor_content = content
            break
    
    if not tor_content:
        return {**state, "errors": state["errors"] + ["No TOR document found"]}
    
    prompt = ChatPromptTemplate.from_template("""
    You are an expert consultant analyzing Terms of Reference (TOR) documents.
    
    Analyze the following TOR and extract key information in JSON format:
    
    TOR Content:
    {tor_content}
    
    Extract:
    1. project_title: The project title
    2. objectives: List of project objectives
    3. scope_of_work: Detailed scope of work items
    4. deliverables: Expected deliverables with timelines
    5. qualifications: Required consultant qualifications
    6. timeline: Project timeline and milestones
    7. evaluation_criteria: How proposals will be evaluated
    
    Return as valid JSON.
    """)
    
    chain = prompt | llm
    result = await chain.ainvoke({"tor_content": tor_content[:30000]})
    
    import json
    tor_analysis = json.loads(result.content)
    
    return {
        **state,
        "tor_analysis": tor_analysis,
        "current_step": "analyze_tor"
    }


# ============ 评分标准提取节点 ============

async def extract_criteria(state: BidGenerationState) -> BidGenerationState:
    """
    深入分析评分标准，为内容生成提供指导
    """
    llm = get_llm("deepseek-r1")  # 使用R1进行复杂推理
    
    prompt = ChatPromptTemplate.from_template("""
    Based on the TOR analysis, create a detailed scoring criteria breakdown.
    
    TOR Analysis:
    {tor_analysis}
    
    For each evaluation criterion:
    1. Identify the weight/importance
    2. Break down into sub-criteria
    3. Determine what content would score highest
    4. Note any mandatory requirements
    
    Return as JSON array with structure:
    [
      {{
        "criterion": "Technical Approach",
        "weight": 40,
        "sub_criteria": [
          {{"name": "...", "weight": 15, "key_points": [...], "mandatory": true/false}}
        ],
        "winning_strategy": "..."
      }}
    ]
    """)
    
    chain = prompt | llm
    result = await chain.ainvoke({"tor_analysis": state["tor_analysis"]})
    
    import json
    scoring_criteria = json.loads(result.content)
    
    return {
        **state,
        "scoring_criteria": scoring_criteria,
        "current_step": "extract_criteria"
    }


# ============ 大纲生成节点 ============

async def create_outline(state: BidGenerationState) -> BidGenerationState:
    """
    根据TOR要求和评分标准生成文档大纲
    """
    llm = get_llm("deepseek-v3")
    
    prompt = ChatPromptTemplate.from_template("""
    Create a comprehensive proposal outline based on TOR requirements and scoring criteria.
    
    TOR Analysis:
    {tor_analysis}
    
    Scoring Criteria:
    {scoring_criteria}
    
    Generate a detailed document outline with:
    1. Main sections aligned with evaluation criteria
    2. Subsections covering all required content
    3. Estimated word count per section
    4. Key points to address in each section
    
    Return as JSON:
    {{
      "title": "Proposal Title",
      "sections": [
        {{
          "id": "1",
          "title": "Section Title",
          "word_count_target": 500,
          "subsections": [...],
          "key_points": [...],
          "linked_criteria": ["Technical Approach"]
        }}
      ]
    }}
    """)
    
    chain = prompt | llm
    result = await chain.ainvoke({
        "tor_analysis": state["tor_analysis"],
        "scoring_criteria": state["scoring_criteria"]
    })
    
    import json
    outline = json.loads(result.content)
    
    return {
        **state,
        "document_outline": outline,
        "current_step": "create_outline"
    }


# ============ 人工审核节点 ============

def should_continue_after_review(state: BidGenerationState) -> str:
    """
    判断人工审核后的下一步
    """
    # 检查最后一条消息是否为审核通过
    if state.get("messages"):
        last_message = state["messages"][-1]
        if hasattr(last_message, "content"):
            if "approved" in last_message.content.lower():
                return "generate"
            elif "revise" in last_message.content.lower():
                return "revise_outline"
    
    # 默认等待人工输入
    return "wait"


# ============ 内容生成节点 ============

async def generate_sections(state: BidGenerationState) -> BidGenerationState:
    """
    并行生成各章节内容
    """
    import asyncio
    from app.agents.prompts.generation import get_section_prompt
    
    llm = get_llm("deepseek-v3")
    outline = state["document_outline"]
    
    async def generate_section(section: dict) -> tuple[str, str]:
        prompt = get_section_prompt(
            section=section,
            tor_analysis=state["tor_analysis"],
            scoring_criteria=state["scoring_criteria"]
        )
        result = await llm.ainvoke(prompt)
        return section["id"], result.content
    
    # 并行生成所有章节
    tasks = [generate_section(s) for s in outline["sections"]]
    results = await asyncio.gather(*tasks)
    
    generated = dict(results)
    
    return {
        **state,
        "generated_sections": generated,
        "current_step": "generate_sections"
    }


# ============ 质量检查节点 ============

async def quality_check(state: BidGenerationState) -> BidGenerationState:
    """
    检查生成内容的质量
    """
    llm = get_llm("deepseek-r1")
    
    quality_scores = {}
    
    for section_id, content in state["generated_sections"].items():
        section = next(
            (s for s in state["document_outline"]["sections"] if s["id"] == section_id),
            None
        )
        
        prompt = ChatPromptTemplate.from_template("""
        Evaluate this proposal section against the criteria:
        
        Section: {section_title}
        Content: {content}
        
        Scoring Criteria: {criteria}
        
        Score from 0-100 and provide brief feedback.
        Return JSON: {{"score": 85, "feedback": "...", "improvements": [...]}}
        """)
        
        chain = prompt | llm
        result = await chain.ainvoke({
            "section_title": section["title"] if section else "Unknown",
            "content": content[:10000],
            "criteria": state["scoring_criteria"]
        })
        
        import json
        quality_scores[section_id] = json.loads(result.content)
    
    return {
        **state,
        "quality_scores": quality_scores,
        "current_step": "quality_check"
    }


def should_regenerate(state: BidGenerationState) -> str:
    """
    判断是否需要重新生成
    """
    scores = state.get("quality_scores", {})
    
    # 检查是否有低分章节
    low_scores = [
        sid for sid, data in scores.items() 
        if data.get("score", 0) < 70
    ]
    
    if low_scores and state.get("retry_count", 0) < 3:
        return "regenerate"
    
    return "compile"


# ============ 文档汇编节点 ============

async def compile_document(state: BidGenerationState) -> BidGenerationState:
    """
    汇编完整文档
    """
    outline = state["document_outline"]
    sections = state["generated_sections"]
    
    # 按大纲顺序组装文档
    document_parts = [f"# {outline['title']}\n\n"]
    
    for section in outline["sections"]:
        content = sections.get(section["id"], "")
        document_parts.append(f"## {section['title']}\n\n{content}\n\n")
    
    final_document = "".join(document_parts)
    
    return {
        **state,
        "final_document": final_document,
        "current_step": "compile_document"
    }
```

### 3.4 工作流构建

```python
# app/agents/workflows/bid_generation/graph.py
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from .state import BidGenerationState
from .nodes import (
    intake_documents,
    analyze_tor,
    extract_criteria,
    create_outline,
    generate_sections,
    quality_check,
    compile_document,
    should_continue_after_review,
    should_regenerate
)

def create_bid_generation_workflow():
    """
    创建标书生成工作流
    """
    workflow = StateGraph(BidGenerationState)
    
    # 添加节点
    workflow.add_node("intake_documents", intake_documents)
    workflow.add_node("analyze_tor", analyze_tor)
    workflow.add_node("extract_criteria", extract_criteria)
    workflow.add_node("create_outline", create_outline)
    workflow.add_node("human_review", lambda x: x)  # 人工审核节点
    workflow.add_node("generate_sections", generate_sections)
    workflow.add_node("quality_check", quality_check)
    workflow.add_node("compile_document", compile_document)
    
    # 设置入口
    workflow.set_entry_point("intake_documents")
    
    # 添加边
    workflow.add_edge("intake_documents", "analyze_tor")
    workflow.add_edge("analyze_tor", "extract_criteria")
    workflow.add_edge("extract_criteria", "create_outline")
    workflow.add_edge("create_outline", "human_review")
    
    # 条件边: 人工审核后
    workflow.add_conditional_edges(
        "human_review",
        should_continue_after_review,
        {
            "generate": "generate_sections",
            "revise_outline": "create_outline",
            "wait": "human_review"
        }
    )
    
    workflow.add_edge("generate_sections", "quality_check")
    
    # 条件边: 质量检查后
    workflow.add_conditional_edges(
        "quality_check",
        should_regenerate,
        {
            "regenerate": "generate_sections",
            "compile": "compile_document"
        }
    )
    
    workflow.add_edge("compile_document", END)
    
    # 编译工作流 (带检查点)
    memory = SqliteSaver.from_conn_string(":memory:")
    return workflow.compile(checkpointer=memory)


# 工作流实例
bid_generation_graph = create_bid_generation_workflow()
```

## 4. 辅助工作流

### 4.1 文档问答工作流

```python
# app/agents/workflows/qa_agent.py
from langgraph.graph import StateGraph, END
from typing import TypedDict

class QAState(TypedDict):
    question: str
    project_id: str
    context_chunks: list[str]
    answer: str
    sources: list[dict]

async def retrieve_context(state: QAState) -> QAState:
    """
    基于问题检索相关文档片段
    """
    from app.services.embedding_service import similarity_search
    
    chunks = await similarity_search(
        query=state["question"],
        project_id=state["project_id"],
        limit=5
    )
    
    return {
        **state,
        "context_chunks": [c["content"] for c in chunks],
        "sources": [{"doc": c["document_name"], "chunk": c["id"]} for c in chunks]
    }

async def generate_answer(state: QAState) -> QAState:
    """
    基于上下文生成回答
    """
    from app.agents.llm_client import get_llm
    from langchain_core.prompts import ChatPromptTemplate
    
    llm = get_llm("deepseek-v3")
    
    prompt = ChatPromptTemplate.from_template("""
    Answer the question based on the provided context.
    
    Context:
    {context}
    
    Question: {question}
    
    Provide a clear, concise answer. If the context doesn't contain enough information,
    say so and suggest what additional information might be needed.
    """)
    
    chain = prompt | llm
    result = await chain.ainvoke({
        "context": "\n\n".join(state["context_chunks"]),
        "question": state["question"]
    })
    
    return {**state, "answer": result.content}


def create_qa_workflow():
    workflow = StateGraph(QAState)
    
    workflow.add_node("retrieve", retrieve_context)
    workflow.add_node("generate", generate_answer)
    
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)
    
    return workflow.compile()

qa_graph = create_qa_workflow()
```

### 4.2 文档分析工作流

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  parse_pdf    │────▶│  chunk_text   │────▶│  embed_chunks │
└───────────────┘     └───────────────┘     └───────────────┘
                                                    │
                                                    ▼
                                            ┌───────────────┐
                                            │  store_db     │
                                            └───────────────┘
```

## 5. Agent 工具定义

### 5.1 工具列表

```python
# app/agents/tools/__init__.py
from langchain_core.tools import tool
from typing import List

@tool
def search_documents(query: str, project_id: str) -> List[dict]:
    """
    Search through project documents using semantic similarity.
    
    Args:
        query: Search query
        project_id: Project UUID
    
    Returns:
        List of relevant document chunks with metadata
    """
    from app.services.embedding_service import similarity_search
    return similarity_search(query, project_id)


@tool
def get_company_profile(company_id: str) -> dict:
    """
    Retrieve company profile information for proposal.
    
    Args:
        company_id: Company UUID
    
    Returns:
        Company profile including experience, team, certifications
    """
    from app.services.company_service import get_profile
    return get_profile(company_id)


@tool
def get_expert_cv(expert_id: str) -> dict:
    """
    Retrieve expert CV information.
    
    Args:
        expert_id: Expert UUID
    
    Returns:
        Expert CV including education, experience, publications
    """
    from app.services.expert_service import get_cv
    return get_cv(expert_id)


@tool  
def search_past_projects(criteria: dict) -> List[dict]:
    """
    Search past project experience matching criteria.
    
    Args:
        criteria: Search criteria including sector, location, value
    
    Returns:
        List of matching past projects
    """
    from app.services.project_service import search_experience
    return search_experience(criteria)


@tool
def calculate_timeline(tasks: List[dict], start_date: str) -> dict:
    """
    Calculate project timeline and milestones.
    
    Args:
        tasks: List of tasks with durations
        start_date: Project start date
    
    Returns:
        Timeline with milestones and Gantt chart data
    """
    from app.services.planning_service import create_timeline
    return create_timeline(tasks, start_date)
```

### 5.2 工具注册

```python
# app/agents/tools/registry.py
from langchain.agents import AgentExecutor
from langchain_core.tools import BaseTool
from .search import search_documents, search_past_projects
from .retrieval import get_company_profile, get_expert_cv
from .planning import calculate_timeline

def get_tools_for_agent(agent_type: str) -> list[BaseTool]:
    """
    根据Agent类型返回可用工具
    """
    tool_registry = {
        "analysis": [search_documents],
        "generation": [
            search_documents,
            get_company_profile,
            get_expert_cv,
            search_past_projects
        ],
        "planning": [calculate_timeline],
        "qa": [search_documents, search_past_projects]
    }
    
    return tool_registry.get(agent_type, [])
```

## 6. Prompt 模板

### 6.1 TOR分析Prompt

```python
# app/agents/prompts/analysis.py

TOR_ANALYSIS_PROMPT = """
You are an expert consultant who has won hundreds of international bids.

## Task
Analyze the following Terms of Reference (TOR) document and extract all critical information that will be needed to prepare a winning proposal.

## TOR Document
{tor_content}

## Required Analysis

### 1. Project Overview
- Project title and reference number
- Executing agency and client
- Project location(s) and duration
- Estimated budget (if mentioned)

### 2. Objectives & Scope
- Primary objectives
- Detailed scope of work
- Expected deliverables with timelines

### 3. Consultant Requirements
- Required qualifications
- Key expert positions
- Experience requirements (years, similar projects)
- Language requirements

### 4. Evaluation Criteria
- Technical evaluation criteria and weights
- Financial evaluation criteria
- Any mandatory requirements

### 5. Submission Requirements
- Proposal format and page limits
- Required annexes and forms
- Submission deadline and method

### 6. Key Success Factors
- What differentiates winning from losing proposals
- Potential risks and how to address them
- Unique opportunities to stand out

## Output Format
Provide your analysis as structured JSON.
"""
```

### 6.2 章节生成Prompt

```python
# app/agents/prompts/generation.py

SECTION_GENERATION_PROMPT = """
You are writing a section of a consulting proposal for an international development project.

## Context

### Project Summary
{project_summary}

### Scoring Criteria for This Section
{scoring_criteria}

### Section Requirements
- Section: {section_title}
- Target word count: {word_count}
- Key points to address: {key_points}

### Available Reference Materials
{reference_materials}

## Instructions

Write the {section_title} section that:

1. **Directly addresses** each evaluation criterion
2. **Demonstrates** relevant experience and expertise
3. **Uses specific examples** from past projects
4. **Shows understanding** of the client's needs
5. **Is concrete** - avoid vague statements

## Writing Style
- Professional but engaging
- Clear and well-structured
- Use bullet points for lists
- Include specific metrics and achievements
- Reference attached CVs/past projects where appropriate

## Output
Write the complete section content. Use markdown formatting.
"""

def get_section_prompt(section: dict, tor_analysis: dict, scoring_criteria: list) -> str:
    """
    为特定章节构建生成prompt
    """
    # 找到与该章节相关的评分标准
    linked_criteria = section.get("linked_criteria", [])
    relevant_criteria = [
        c for c in scoring_criteria 
        if c["criterion"] in linked_criteria
    ]
    
    return SECTION_GENERATION_PROMPT.format(
        project_summary=tor_analysis.get("project_title", ""),
        scoring_criteria=relevant_criteria,
        section_title=section["title"],
        word_count=section.get("word_count_target", 500),
        key_points=section.get("key_points", []),
        reference_materials=""  # TODO: 从知识库检索
    )
```

## 7. 调用示例

### 7.1 启动工作流

```python
# app/api/v1/generation.py
from fastapi import APIRouter, Depends
from app.agents.workflows.bid_generation.graph import bid_generation_graph
from app.schemas.generation import GenerationRequest

router = APIRouter()

@router.post("/projects/{project_id}/generate")
async def start_generation(
    project_id: str,
    request: GenerationRequest,
    current_user = Depends(get_current_user)
):
    """
    启动标书生成工作流
    """
    # 获取项目文档
    documents = await get_project_documents(project_id)
    
    # 初始状态
    initial_state = {
        "project_id": project_id,
        "user_id": str(current_user.id),
        "documents": documents,
        "parsed_documents": {},
        "errors": [],
        "retry_count": 0,
        "messages": []
    }
    
    # 配置
    config = {
        "configurable": {
            "thread_id": project_id
        }
    }
    
    # 异步执行工作流
    result = await bid_generation_graph.ainvoke(initial_state, config)
    
    return {
        "status": "completed",
        "final_document": result.get("final_document"),
        "quality_scores": result.get("quality_scores")
    }
```

### 7.2 人工干预

```python
@router.post("/projects/{project_id}/review")
async def submit_review(
    project_id: str,
    review: ReviewRequest,
    current_user = Depends(get_current_user)
):
    """
    提交人工审核结果
    """
    from langchain_core.messages import HumanMessage
    
    config = {"configurable": {"thread_id": project_id}}
    
    # 获取当前状态
    state = bid_generation_graph.get_state(config)
    
    # 添加审核消息
    review_message = HumanMessage(content=f"{review.decision}: {review.comments}")
    
    # 继续执行
    result = await bid_generation_graph.ainvoke(
        {"messages": [review_message]},
        config
    )
    
    return {"status": "continued", "current_step": result["current_step"]}
```

## 8. 监控与调试

### 8.1 LangSmith集成

```python
# app/config.py
import os

# LangSmith配置
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "bidagent-production"
os.environ["LANGCHAIN_API_KEY"] = "your-langsmith-key"
```

### 8.2 状态可视化

```python
# 获取工作流状态图
from IPython.display import Image
graph_image = bid_generation_graph.get_graph().draw_mermaid_png()
```

---

## 相关文档
- [系统架构](./system-overview.md)
- [数据模型](./data-model.md)
- [API契约](../api-contracts/openapi.yaml)
