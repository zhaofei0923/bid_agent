# M5 - 标书生成任务规格书

## 概述
| 属性 | 值 |
|------|-----|
| 里程碑 | M5 - Bid Generation |
| 周期 | Week 7-8 |
| 任务总数 | 12 |
| Opus 4.5 任务 | 4 |
| Mini-Agent 任务 | 8 |

## 目标
- 实现LangGraph标书生成工作流
- 创建TOR分析Agent
- 实现内容生成Agent
- 建立人机协作机制

---

## 任务列表

### M5-01: Agent工作流架构设计 (Opus 4.5)
**优先级**: P0  
**预估时间**: 4小时  
**执行者**: Opus 4.5

#### 描述
设计完整的标书生成LangGraph工作流。

#### 详细参考
参见 [Agent工作流设计文档](../../architecture/agent-workflow.md)

#### 验收标准
- [ ] 状态机设计完成
- [ ] 节点定义清晰
- [ ] 条件边逻辑明确
- [ ] 人工干预点确定

#### 输出文件
- `backend/app/agents/workflows/bid_generation/state.py`
- `backend/app/agents/workflows/bid_generation/graph.py`

#### 依赖
- M3-03, M4-06

---

### M5-02: 工作流状态定义 (Mini-Agent)
**优先级**: P0  
**预估时间**: 2小时  
**执行者**: Mini-Agent

#### 描述
实现LangGraph工作流状态类型定义。

#### 代码实现
```python
# app/agents/workflows/bid_generation/state.py
from typing import TypedDict, Annotated, Sequence, Optional, List, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class TORAnalysis(TypedDict):
    """TOR分析结果"""
    project_title: str
    objectives: List[str]
    scope_of_work: List[Dict[str, str]]
    deliverables: List[Dict[str, str]]
    qualifications: List[str]
    timeline: Dict[str, Any]
    evaluation_criteria: List[Dict[str, Any]]

class ScoringCriterion(TypedDict):
    """评分标准"""
    criterion: str
    weight: int
    sub_criteria: List[Dict[str, Any]]
    winning_strategy: str

class DocumentSection(TypedDict):
    """文档章节"""
    id: str
    title: str
    word_count_target: int
    subsections: List[Dict[str, str]]
    key_points: List[str]
    linked_criteria: List[str]

class DocumentOutline(TypedDict):
    """文档大纲"""
    title: str
    sections: List[DocumentSection]

class QualityScore(TypedDict):
    """质量评分"""
    score: float
    feedback: str
    improvements: List[str]

class BidGenerationState(TypedDict):
    """标书生成工作流状态"""
    
    # === 基本信息 ===
    project_id: str
    user_id: str
    language: str  # zh, en
    
    # === 输入文档 ===
    documents: List[Dict[str, Any]]
    parsed_documents: Dict[str, str]  # {doc_id: content}
    
    # === 分析结果 ===
    tor_analysis: Optional[TORAnalysis]
    scoring_criteria: Optional[List[ScoringCriterion]]
    
    # === 生成计划 ===
    document_outline: Optional[DocumentOutline]
    
    # === 生成内容 ===
    generated_sections: Dict[str, str]  # {section_id: content}
    quality_scores: Dict[str, QualityScore]  # {section_id: score}
    
    # === 最终输出 ===
    final_document: Optional[str]
    export_path: Optional[str]
    
    # === 工作流控制 ===
    current_step: str
    retry_count: int
    max_retries: int
    errors: List[str]
    
    # === 人机交互 ===
    waiting_for_review: bool
    review_data: Optional[Dict[str, Any]]
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # === 计费 ===
    credits_consumed: int
    token_usage: Dict[str, int]  # {step: tokens}
```

#### 依赖
- M5-01

---

### M5-03: TOR分析节点 (Opus 4.5)
**优先级**: P0  
**预估时间**: 4小时  
**执行者**: Opus 4.5

#### 描述
实现TOR文档分析节点，提取关键信息。

#### 验收标准
- [ ] 提取项目目标
- [ ] 提取工作范围
- [ ] 提取资质要求
- [ ] 提取评分标准
- [ ] 支持中英文TOR

#### 代码实现
```python
# app/agents/workflows/bid_generation/nodes/analyze.py
from langchain_core.prompts import ChatPromptTemplate
from app.agents.langchain_client import get_deepseek_chat
from app.agents.prompts import prompt_manager
from ..state import BidGenerationState
import json

async def analyze_tor(state: BidGenerationState) -> BidGenerationState:
    """
    分析TOR文档，提取关键信息
    """
    # 获取TOR内容
    tor_content = None
    for doc_id, content in state["parsed_documents"].items():
        doc = next((d for d in state["documents"] if d["id"] == doc_id), None)
        if doc and doc["type"] == "tor":
            tor_content = content
            break
    
    if not tor_content:
        return {
            **state,
            "errors": state["errors"] + ["未找到TOR文档"],
            "current_step": "analyze_tor_failed"
        }
    
    # 获取Prompt模板
    template = prompt_manager.get("tor_analysis", state["language"])
    prompt = ChatPromptTemplate.from_template(template.template)
    
    # 调用LLM
    llm = get_deepseek_chat("deepseek-v3")
    chain = prompt | llm
    
    result = await chain.ainvoke({
        "tor_content": tor_content[:50000]  # 限制长度
    })
    
    # 解析JSON结果
    try:
        tor_analysis = json.loads(result.content)
    except json.JSONDecodeError:
        # 尝试提取JSON部分
        import re
        json_match = re.search(r'\{[\s\S]*\}', result.content)
        if json_match:
            tor_analysis = json.loads(json_match.group())
        else:
            return {
                **state,
                "errors": state["errors"] + ["TOR分析结果解析失败"],
                "current_step": "analyze_tor_failed"
            }
    
    return {
        **state,
        "tor_analysis": tor_analysis,
        "current_step": "analyze_tor",
        "token_usage": {
            **state.get("token_usage", {}),
            "analyze_tor": result.response_metadata.get("token_usage", {}).get("total_tokens", 0)
        }
    }


async def extract_criteria(state: BidGenerationState) -> BidGenerationState:
    """
    深入分析评分标准
    """
    llm = get_deepseek_chat("deepseek-r1")  # 使用R1进行深度分析
    
    template = prompt_manager.get("scoring_analysis", state["language"])
    prompt = ChatPromptTemplate.from_template(template.template)
    
    chain = prompt | llm
    result = await chain.ainvoke({
        "tor_analysis": json.dumps(state["tor_analysis"], ensure_ascii=False)
    })
    
    scoring_criteria = json.loads(result.content)
    
    return {
        **state,
        "scoring_criteria": scoring_criteria,
        "current_step": "extract_criteria"
    }
```

#### Prompt模板
```yaml
# prompts/templates/zh/tor_analysis.yaml
template: |
  你是一位资深的国际咨询顾问，擅长分析投标文件。
  
  ## 任务
  分析以下任务书(TOR)文档，提取关键信息。
  
  ## TOR文档内容
  $tor_content
  
  ## 提取要求
  请提取以下信息，以JSON格式返回：
  
  1. **project_title**: 项目名称
  2. **objectives**: 项目目标（数组）
  3. **scope_of_work**: 工作范围（数组，每项包含task和description）
  4. **deliverables**: 交付物（数组，每项包含name和deadline）
  5. **qualifications**: 资质要求（数组）
  6. **timeline**: 项目时间安排
  7. **evaluation_criteria**: 评分标准（数组，每项包含criterion和weight）
  
  ## 注意事项
  - 确保提取完整准确
  - 保持原文关键术语
  - 如信息不明确，标注"未明确"
  
  ## JSON输出

input_variables:
  - tor_content
```

#### 依赖
- M3-07, M4-06

---

### M5-04: 大纲生成节点 (Mini-Agent)
**优先级**: P0  
**预估时间**: 3小时  
**执行者**: Mini-Agent

#### 描述
实现文档大纲生成节点。

#### 验收标准
- [ ] 根据评分标准生成大纲
- [ ] 章节安排合理
- [ ] 包含字数建议
- [ ] 支持自定义调整

#### 依赖
- M5-03

---

### M5-05: 人工审核节点 (Mini-Agent)
**优先级**: P0  
**预估时间**: 3小时  
**执行者**: Mini-Agent

#### 描述
实现人工审核交互节点。

#### 验收标准
- [ ] 暂停等待审核
- [ ] 接收审核结果
- [ ] 支持修改建议
- [ ] 状态正确恢复

#### 代码实现
```python
# app/agents/workflows/bid_generation/nodes/review.py
from ..state import BidGenerationState

async def human_review(state: BidGenerationState) -> BidGenerationState:
    """
    人工审核节点 - 等待用户确认大纲
    """
    return {
        **state,
        "current_step": "human_review",
        "waiting_for_review": True,
        "review_data": {
            "type": "outline_review",
            "outline": state["document_outline"],
            "message": "请审核文档大纲，确认后继续生成"
        }
    }


def should_continue_after_review(state: BidGenerationState) -> str:
    """
    判断审核后的下一步
    """
    if not state.get("messages"):
        return "wait"
    
    last_message = state["messages"][-1]
    content = last_message.content.lower() if hasattr(last_message, "content") else ""
    
    if "approved" in content or "通过" in content:
        return "generate"
    elif "revise" in content or "修改" in content:
        return "revise_outline"
    
    return "wait"
```

#### 依赖
- M5-04

---

### M5-06: 内容生成节点 (Opus 4.5)
**优先级**: P0  
**预估时间**: 6小时  
**执行者**: Opus 4.5

#### 描述
实现各章节内容生成节点，这是核心功能。

#### 验收标准
- [ ] 按大纲生成内容
- [ ] 引用相关文档
- [ ] 符合评分标准
- [ ] 支持并行生成
- [ ] 内容质量可控

#### 代码实现
```python
# app/agents/workflows/bid_generation/nodes/generate.py
import asyncio
from typing import List, Dict
from langchain_core.prompts import ChatPromptTemplate
from app.agents.langchain_client import get_deepseek_chat
from app.services.embedding_service import EmbeddingService
from ..state import BidGenerationState, DocumentSection

async def generate_sections(state: BidGenerationState) -> BidGenerationState:
    """
    并行生成各章节内容
    """
    outline = state["document_outline"]
    sections = outline["sections"]
    
    # 并行生成
    tasks = [
        generate_single_section(section, state)
        for section in sections
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    generated = {}
    errors = []
    
    for section, result in zip(sections, results):
        if isinstance(result, Exception):
            errors.append(f"生成{section['title']}失败: {str(result)}")
        else:
            generated[section["id"]] = result
    
    return {
        **state,
        "generated_sections": generated,
        "errors": state["errors"] + errors,
        "current_step": "generate_sections"
    }


async def generate_single_section(
    section: DocumentSection,
    state: BidGenerationState,
    db = None
) -> str:
    """
    生成单个章节内容
    """
    llm = get_deepseek_chat("deepseek-v3")
    
    # 检索相关内容
    context = ""
    if db:
        embedding_service = EmbeddingService(db)
        relevant_chunks = await embedding_service.similarity_search(
            query=f"{section['title']} {' '.join(section.get('key_points', []))}",
            project_id=state["project_id"],
            limit=5
        )
        context = "\n\n".join([c["content"] for c in relevant_chunks])
    
    # 获取相关评分标准
    linked_criteria = section.get("linked_criteria", [])
    relevant_criteria = [
        c for c in state["scoring_criteria"]
        if c["criterion"] in linked_criteria
    ]
    
    prompt = ChatPromptTemplate.from_template("""
    你是一位专业的咨询顾问，正在撰写投标书的一个章节。
    
    ## 项目背景
    {project_summary}
    
    ## 章节信息
    - 章节标题: {section_title}
    - 目标字数: {word_count}
    - 关键要点: {key_points}
    
    ## 评分标准
    {scoring_criteria}
    
    ## 参考资料
    {context}
    
    ## 写作要求
    1. 直接回应评分标准中的每一项
    2. 使用具体的数据和案例
    3. 展示专业性和理解深度
    4. 语言简洁专业
    5. 使用Markdown格式
    
    ## 请撰写该章节内容
    """)
    
    chain = prompt | llm
    result = await chain.ainvoke({
        "project_summary": state["tor_analysis"].get("project_title", ""),
        "section_title": section["title"],
        "word_count": section.get("word_count_target", 500),
        "key_points": ", ".join(section.get("key_points", [])),
        "scoring_criteria": relevant_criteria,
        "context": context,
    })
    
    return result.content
```

#### 依赖
- M5-05, M4-06

---

### M5-07: 质量检查节点 (Mini-Agent)
**优先级**: P1  
**预估时间**: 3小时  
**执行者**: Mini-Agent

#### 描述
实现生成内容质量检查节点。

#### 验收标准
- [ ] 评估内容质量
- [ ] 提供改进建议
- [ ] 决定是否重新生成
- [ ] 质量分数计算

#### 依赖
- M5-06

---

### M5-08: 文档汇编节点 (Mini-Agent)
**优先级**: P1  
**预估时间**: 2小时  
**执行者**: Mini-Agent

#### 描述
实现最终文档汇编节点。

#### 验收标准
- [ ] 按顺序合并章节
- [ ] 添加目录
- [ ] 格式统一
- [ ] 生成完整Markdown

#### 依赖
- M5-07

---

### M5-09: 工作流图构建 (Opus 4.5)
**优先级**: P0  
**预估时间**: 3小时  
**执行者**: Opus 4.5

#### 描述
使用LangGraph构建完整工作流图。

#### 代码实现
```python
# app/agents/workflows/bid_generation/graph.py
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from .state import BidGenerationState
from .nodes.analyze import analyze_tor, extract_criteria
from .nodes.outline import create_outline
from .nodes.review import human_review, should_continue_after_review
from .nodes.generate import generate_sections
from .nodes.quality import quality_check, should_regenerate
from .nodes.compile import compile_document

def create_bid_generation_workflow():
    """创建标书生成工作流"""
    
    workflow = StateGraph(BidGenerationState)
    
    # === 添加节点 ===
    workflow.add_node("analyze_tor", analyze_tor)
    workflow.add_node("extract_criteria", extract_criteria)
    workflow.add_node("create_outline", create_outline)
    workflow.add_node("human_review", human_review)
    workflow.add_node("generate_sections", generate_sections)
    workflow.add_node("quality_check", quality_check)
    workflow.add_node("compile_document", compile_document)
    
    # === 设置入口 ===
    workflow.set_entry_point("analyze_tor")
    
    # === 线性边 ===
    workflow.add_edge("analyze_tor", "extract_criteria")
    workflow.add_edge("extract_criteria", "create_outline")
    workflow.add_edge("create_outline", "human_review")
    workflow.add_edge("generate_sections", "quality_check")
    workflow.add_edge("compile_document", END)
    
    # === 条件边 ===
    
    # 人工审核后
    workflow.add_conditional_edges(
        "human_review",
        should_continue_after_review,
        {
            "generate": "generate_sections",
            "revise_outline": "create_outline",
            "wait": "human_review",  # 继续等待
        }
    )
    
    # 质量检查后
    workflow.add_conditional_edges(
        "quality_check",
        should_regenerate,
        {
            "regenerate": "generate_sections",
            "compile": "compile_document",
        }
    )
    
    # === 编译 ===
    memory = SqliteSaver.from_conn_string(":memory:")
    return workflow.compile(checkpointer=memory)


# 全局工作流实例
bid_generation_graph = create_bid_generation_workflow()
```

#### 依赖
- M5-02 ~ M5-08

---

### M5-10: 生成API接口 (Mini-Agent)
**优先级**: P0  
**预估时间**: 4小时  
**执行者**: Mini-Agent

#### 描述
实现标书生成相关API接口。

#### 验收标准
- [ ] POST /projects/{id}/analyze 分析TOR
- [ ] POST /projects/{id}/generate 开始生成
- [ ] GET /projects/{id}/generate/status 查询状态
- [ ] POST /projects/{id}/generate/review 提交审核

#### API实现
```python
# app/api/v1/generation.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.workflows.bid_generation.graph import bid_generation_graph
from app.services.document_service import get_project_documents
from app.schemas.generation import GenerationRequest, GenerationStatus
from app.api.deps import get_db, get_current_user

router = APIRouter()

# 存储运行中的工作流状态
_workflow_states = {}

@router.post("/{project_id}/generate")
async def start_generation(
    project_id: str,
    request: GenerationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """启动标书生成"""
    # 获取项目文档
    documents = await get_project_documents(db, project_id)
    
    if not documents:
        raise HTTPException(400, "请先上传项目文档")
    
    # 初始状态
    initial_state = {
        "project_id": project_id,
        "user_id": str(current_user.id),
        "language": current_user.language,
        "documents": [d.to_dict() for d in documents],
        "parsed_documents": {str(d.id): d.parsed_content for d in documents},
        "generated_sections": {},
        "quality_scores": {},
        "errors": [],
        "retry_count": 0,
        "max_retries": 3,
        "waiting_for_review": False,
        "credits_consumed": 0,
        "token_usage": {},
        "messages": [],
    }
    
    # 配置
    config = {"configurable": {"thread_id": project_id}}
    
    # 后台运行工作流
    background_tasks.add_task(
        run_workflow,
        bid_generation_graph,
        initial_state,
        config,
        project_id
    )
    
    return {
        "task_id": project_id,
        "status": "started",
        "message": "标书生成已启动"
    }


async def run_workflow(graph, initial_state, config, project_id):
    """运行工作流"""
    try:
        result = await graph.ainvoke(initial_state, config)
        _workflow_states[project_id] = result
    except Exception as e:
        _workflow_states[project_id] = {"error": str(e)}


@router.get("/{project_id}/generate/status")
async def get_generation_status(
    project_id: str,
    current_user = Depends(get_current_user),
) -> GenerationStatus:
    """查询生成状态"""
    config = {"configurable": {"thread_id": project_id}}
    
    try:
        state = bid_generation_graph.get_state(config)
        
        return {
            "task_id": project_id,
            "status": "running" if not state.values.get("waiting_for_review") else "waiting_review",
            "current_step": state.values.get("current_step", "unknown"),
            "waiting_for_review": state.values.get("waiting_for_review", False),
            "review_data": state.values.get("review_data"),
            "errors": state.values.get("errors", []),
            "credits_consumed": state.values.get("credits_consumed", 0),
        }
    except:
        if project_id in _workflow_states:
            final_state = _workflow_states[project_id]
            return {
                "task_id": project_id,
                "status": "completed" if "error" not in final_state else "failed",
                "current_step": final_state.get("current_step", "done"),
                "errors": final_state.get("errors", []),
            }
        
        raise HTTPException(404, "未找到生成任务")


@router.post("/{project_id}/generate/review")
async def submit_review(
    project_id: str,
    review: dict,
    current_user = Depends(get_current_user),
):
    """提交人工审核"""
    from langchain_core.messages import HumanMessage
    
    config = {"configurable": {"thread_id": project_id}}
    
    decision = review.get("decision", "")
    comments = review.get("comments", "")
    
    message = HumanMessage(content=f"{decision}: {comments}")
    
    # 继续工作流
    result = await bid_generation_graph.ainvoke(
        {"messages": [message], "waiting_for_review": False},
        config
    )
    
    return {
        "status": "continued",
        "current_step": result.get("current_step")
    }
```

#### 依赖
- M5-09

---

### M5-11: 生成文档管理 (Mini-Agent)
**优先级**: P1  
**预估时间**: 3小时  
**执行者**: Mini-Agent

#### 描述
实现生成文档的存储和管理。

#### 验收标准
- [ ] 保存生成文档
- [ ] 版本管理
- [ ] 编辑功能
- [ ] 导出功能

#### 依赖
- M5-10

---

### M5-12: 文档导出 (Mini-Agent)
**优先级**: P1  
**预估时间**: 4小时  
**执行者**: Mini-Agent

#### 描述
实现生成文档导出为PDF/DOCX。

#### 验收标准
- [ ] 导出PDF
- [ ] 导出DOCX
- [ ] 保持格式
- [ ] 支持模板

#### 依赖
- M5-11

---

## 里程碑检查点

### 完成标准
- [ ] 工作流可完整运行
- [ ] TOR分析准确
- [ ] 内容生成质量可接受
- [ ] 人工审核机制可用
- [ ] 导出功能可用

### 交付物
1. 完整的LangGraph工作流
2. 各环节Prompt模板
3. 生成管理API
4. 文档导出功能

---

## 质量指标

| 指标 | 目标 | 说明 |
|------|------|------|
| TOR分析准确率 | > 90% | 关键信息提取完整 |
| 内容相关性 | > 80% | 内容与TOR要求匹配 |
| 生成时间 | < 5分钟 | 完整生成耗时 |
| 用户满意度 | > 70% | 初版需要修改比例 |
