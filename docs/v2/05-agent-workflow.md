# BidAgent V2 — Agent 工作流设计

> 版本: 2.0.0 | 日期: 2026-02-11 | 状态: Draft

## 1. 架构概述

V2 Agent 系统采用 **三层架构**: MCP Tools (数据检索) → Skills (分析能力) → LangGraph Workflows (编排)。

```
┌─────────────────────────────────────────────────────┐
│                  LangGraph Workflows                │
│  ┌─────────────────┐  ┌──────────────────────┐     │
│  │ Bid Generation   │  │ Bid Analysis (新增)  │     │
│  │ (8-node graph)   │  │ (pipeline)          │     │
│  └────────┬─────────┘  └────────┬─────────────┘     │
└───────────┼──────────────────────┼───────────────────┘
            │                      │
┌───────────┴──────────────────────┴───────────────────┐
│                  Skills Layer                         │
│  AnalyzeQualification | EvaluateCriteria | ...       │
│  SectionGuidance | ReviewDraft | QualityReview | ExtractDates      │
└───────────┬──────────────────────┬───────────────────┘
            │                      │
┌───────────┴──────────────────────┴───────────────────┐
│                  MCP Tools Layer                      │
│  knowledge_search | bid_document_search              │
│  opportunity_query | web_search (future)             │
└───────────┬──────────────────────┬───────────────────┘
            │                      │
     ┌──────┴──────┐        ┌─────┴──────┐
     │ pgvector DB │        │ DeepSeek   │
     │ Embedding   │        │ LLM API    │
     └─────────────┘        └────────────┘
```

---

## 2. LLM Client

### 2.1 接口定义

```python
@dataclass
class LLMResponse:
    content: str
    model: str
    usage: dict[str, int]  # {prompt_tokens, completion_tokens, total_tokens}
    finish_reason: str

@dataclass
class Message:
    role: Literal["system", "user", "assistant"]
    content: str

class LLMClient:
    """DeepSeek API 封装 (OpenAI 兼容)"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=f"{settings.LLM_BASE_URL}/v1",
            http_client=httpx.AsyncClient(proxy=None),
        )
        self.model = settings.LLM_MODEL  # deepseek-v4-pro
    
    async def chat(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> LLMResponse: ...
    
    async def chat_stream(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AsyncIterator[str]: ...
    
    async def generate_with_context(
        self,
        question: str,
        context: list[str],
        system_prompt: str | None = None,
        temperature: float = 0.3,
    ) -> LLMResponse:
        """RAG 专用: 将检索上下文注入 prompt 后调用 LLM"""
        ...
    
    async def summarize(self, text: str, max_length: int = 500) -> str: ...
    
    async def extract_json(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 4000,
    ) -> dict:
        """调用 LLM 并解析 JSON 响应 (自动清理 markdown 代码块)"""
        ...
```

### 2.2 模型选择策略

| 场景 | 模型 | Temperature | Max Tokens |
|------|------|-------------|------------|
| 通用聊天/问答 | deepseek-v4-pro | 0.7 | 2000 |
| JSON 结构化分析 | deepseek-v4-pro | 0.2 | 4000 |
| 快速审查 | deepseek-v4-pro | 0.1 | 500 |
| 投标计划生成 | deepseek-v4-pro | 0.5 | 4000 |
| 预测/推理 | deepseek-v4-pro | 0.3 | 4000 |
| 章节内容生成 | deepseek-v4-pro | 0.7 | 8000 |

---

## 3. MCP Tools 详细设计

### 3.1 knowledge_search — 知识库搜索

```python
@mcp_tool(name="knowledge_search")
async def knowledge_search(
    query: str,
    institution: str | None = None,    # "adb" | "wb" | "un"
    kb_type: str | None = None,        # "guide" | "review" | "template"
    top_k: int = 5,
    score_threshold: float = 0.5,
) -> list[dict]:
    """从知识库中搜索 ADB/WB 采购准则和参考文档
    
    Implementation:
    1. embed_query(query) → vector
    2. pgvector SELECT WHERE knowledge_bases.institution = ? 
       ORDER BY embedding <=> vector LIMIT top_k
    3. 过滤 similarity < score_threshold
    4. 返回 [{content, score, source_document, page_number}]
    """
```

**SQL 查询模式**:
```sql
SELECT c.content, c.page_number,
       1 - (c.embedding <=> $1::vector) AS similarity,
       d.filename AS source_document
FROM knowledge_chunks c
JOIN knowledge_documents d ON c.document_id = d.id
JOIN knowledge_bases kb ON d.knowledge_base_id = kb.id
WHERE ($2 IS NULL OR kb.institution = $2)
  AND ($3 IS NULL OR kb.kb_type = $3)
ORDER BY c.embedding <=> $1::vector
LIMIT $4
```

### 3.2 bid_document_search — 招标文件搜索

```python
@mcp_tool(name="bid_document_search")
async def bid_document_search(
    project_id: str,
    query: str,
    section_types: list[str] | None = None,
    top_k: int = 5,
    score_threshold: float = 0.3,
) -> list[dict]:
    """从项目招标文件中搜索相关内容分块
    
    Implementation:
    1. embed_query(query) → vector
    2. pgvector SELECT WHERE bid_documents.project_id = ?
       AND bid_documents.status = 'completed'
       AND embedding IS NOT NULL
       [AND section_type = ANY(section_types)]
       ORDER BY embedding <=> vector LIMIT top_k
    3. 过滤 similarity < score_threshold
    4. 返回 [{content, score, section_type, section_title, page_number, clause_reference, filename}]
    """
```

### 3.3 opportunity_query — 招标机会查询

```python
@mcp_tool(name="opportunity_query")
async def opportunity_query(
    opportunity_id: str | None = None,
    search: str | None = None,
    source: str | None = None,
    fields: list[str] | None = None,
) -> dict | list[dict]:
    """查询招标机会数据库
    
    - opportunity_id: 精确查询
    - search: 关键词搜索 (TSVECTOR)
    - source: 按来源过滤
    """
```

---

## 4. Skills 详细设计

### 4.1 基础接口

```python
class SkillContext:
    """Skill 执行上下文"""
    project_id: UUID
    db: AsyncSession
    llm_client: LLMClient
    embedding_client: ResilientEmbeddingClient
    parameters: dict  # Skill 特定参数

class SkillResult:
    """Skill 执行结果"""
    success: bool
    data: dict           # 结构化输出
    tokens_consumed: int
    sources: list[dict]  # 引用来源 [{source, page, content_preview}]
    error: str | None

class Skill(ABC):
    name: str
    description: str
    
    @abstractmethod
    async def execute(self, context: SkillContext) -> SkillResult: ...
```

### 4.2 AnalyzeQualification — 资质要求分析

```python
class AnalyzeQualification(Skill):
    name = "analyze_qualification"
    description = "分析招标文件中的资质要求"
    
    async def execute(self, ctx: SkillContext) -> SkillResult:
        # 1. 多维度检索招标文件
        doc_chunks = await bid_document_search(
            project_id=ctx.project_id,
            query="qualification criteria eligibility minimum experience financial capacity",
            section_types=["section_3_qualification", "section_2_bds", "section_1_itb"],
            top_k=10,
        )
        
        # 2. 检索知识库参考
        kb_chunks = await knowledge_search(
            query="ADB qualification criteria consulting services",
            institution="adb",
            top_k=3,
        )
        
        # 3. 组装上下文
        bid_context = format_chunks(doc_chunks, "来源")
        kb_context = format_chunks(kb_chunks, "ADB指南")
        
        # 4. LLM 结构化提取
        result = await ctx.llm_client.extract_json(
            prompt=QUALIFICATION_EXTRACTION_PROMPT.format(
                bid_document_context=bid_context,
                knowledge_context=kb_context,
            ),
            system_prompt=SYSTEM_PROMPT_ADB_ANALYST,
            temperature=0.2,
        )
        
        return SkillResult(
            success=True,
            data=result,  # {qualification_requirements, joint_venture, domestic_preference}
            tokens_consumed=...,
            sources=doc_chunks + kb_chunks,
        )
```

**输出结构**:
```json
{
  "qualification_requirements": [
    {
      "category": "Legal",
      "requirements": ["在经营所在国依法注册", "..."],
      "evidence_required": ["公司注册证书", "..."],
      "source_reference": "ITB 4.1"
    },
    {"category": "Financial", "...": "..."},
    {"category": "Technical", "...": "..."},
    {"category": "Experience", "...": "..."}
  ],
  "joint_venture_requirements": {"allowed": true, "max_members": 3, "...": "..."},
  "domestic_preference": {"applicable": false}
}
```

### 4.3 EvaluateCriteria — 评分标准提取

```python
class EvaluateCriteria(Skill):
    name = "evaluate_criteria"
    
    async def execute(self, ctx: SkillContext) -> SkillResult:
        # 搜索维度: evaluation criteria scoring methodology weight
        # Section 类型: section_3, section_2_bds
        # KB 查询: QCBS quality cost based selection
        ...
```

**输出结构**:
```json
{
  "evaluation_method": "QCBS",
  "technical_weight": 80,
  "financial_weight": 20,
  "technical_criteria": [
    {"criterion": "公司经验", "weight": 30, "sub_criteria": [...]}
  ],
  "financial_evaluation": {"formula": "..."},
  "qualification_thresholds": {"technical_minimum": 75}
}
```

### 4.4 ExtractDates — 关键日期提取

**搜索维度**: deadline, bid opening, clarification, validity, pre-bid meeting, contract duration

**输出**: `{submission_deadline, bid_opening, clarification_deadline, bid_validity_period, pre_bid_meeting, contract_duration, time_analysis}`

### 4.5 ExtractSubmission — 提交要求提取

**搜索维度**: submission requirements format copies, bid security guarantee

**输出**: `{format, copies, submission_method, language, bid_security, required_documents[]}`

### 4.6 AnalyzeBDS — BDS 修改识别

**搜索维度**: BDS bid data sheet modifications, ITB reference

**输出**: `{bds_modifications: [{itb_clause, modification_type, original_provision, modified_provision}]}`

### 4.7 AnalyzeCommercial — 商务条款分析

**搜索维度**: payment terms warranty insurance dispute

**输出**: `{payment_terms, performance_security, warranty, penalty, insurance, dispute_resolution}`

### 4.8 AssessRisk — 风险评估

```python
class AssessRisk(Skill):
    name = "assess_risk"
    
    async def execute(self, ctx: SkillContext) -> SkillResult:
        # 输入: 其他 Skills 的结果 (通过 ctx.parameters)
        qualification = ctx.parameters["qualification_requirements"]
        criteria = ctx.parameters["evaluation_criteria"]
        dates = ctx.parameters["key_dates"]
        bds = ctx.parameters["bds_modifications"]
        
        # 检索知识库中的风险参考
        kb_chunks = await knowledge_search(
            query="ADB bid risk assessment common pitfalls",
            institution="adb",
        )
        
        # LLM 5维风险评估
        result = await ctx.llm_client.extract_json(
            prompt=RISK_ASSESSMENT_PROMPT.format(...),
            ...
        )
        return SkillResult(data=result)
```

**输出**: `{risk_dimensions: [{dimension, risk_level, issues[], mitigations[]}], overall_risk_level, bid_no_bid_recommendation}`

### 4.9 SectionGuidance — 章节编写指导

```python
class SectionGuidance(Skill):
    name = "section_guidance"
    
    async def execute(self, ctx: SkillContext) -> SkillResult:
        section_config = ctx.parameters["section_config"]
        # {id, title, word_count_target, subsections, key_points, linked_criteria}
        
        # 1. 检索与该章节相关的招标文件内容
        doc_chunks = await bid_document_search(
            project_id=ctx.project_id,
            query=section_config["title"],
            top_k=5,
        )
        
        # 2. 检索知识库模板参考
        kb_chunks = await knowledge_search(
            query=f"proposal {section_config['title']} template best practices",
            kb_type="template",
        )
        
        # 3. LLM 生成编写指导
        guidance = await ctx.llm_client.chat(
            messages=[
                Message("system", "你是专业的投标顾问，提供标书章节编写指导..."),
                Message("user", SECTION_GUIDANCE_PROMPT.format(...)),
            ],
            temperature=0.3,
            max_tokens=4000,
        )
        return SkillResult(data={
            "section_id": ...,
            "guidance": guidance,
            "format_requirements": ...,   # 格式要求
            "content_outline": ...,       # 内容要点
            "scoring_alignment": ...,     # 评分对标建议
            "template_references": ...,   # 模板参考片段
            "common_pitfalls": ...,       # 常见错误提醒
        })
```

**输出**: 针对特定章节的完整编写指导，包含格式规范、内容要点、评分对标、模板参考和常见错误提醒。

### 4.10 ReviewDraft — 草稿审查

```python
class ReviewDraft(Skill):
    name = "review_draft"
    
    async def execute(self, ctx: SkillContext) -> SkillResult:
        draft_content = ctx.parameters["draft_content"]
        section_config = ctx.parameters.get("section_config", {})
        bid_requirements = ctx.parameters.get("bid_requirements", {})
        
        # 检索对应的招标要求
        doc_chunks = await bid_document_search(
            project_id=ctx.project_id,
            query=section_config.get("title", "requirements"),
            top_k=5,
        )
        
        # LLM 审查用户草稿
        review = await ctx.llm_client.extract_json(
            prompt=DRAFT_REVIEW_PROMPT.format(
                draft=draft_content,
                requirements=doc_chunks,
                section_config=section_config,
            ),
            temperature=0.2,
            max_tokens=4000,
        )
        return SkillResult(data=review)
```

**输出**:
```json
{
  "overall_score": 75,
  "format_compliance": {"score": 80, "issues": []},
  "content_completeness": {"score": 70, "missing_points": []},
  "scoring_alignment": {"score": 75, "suggestions": []},
  "language_quality": {"score": 80, "improvements": []},
  "specific_feedback": ["...", "..."],
  "priority_improvements": ["...", "..."]
}
```

### 4.11 QualityReview — 质量审查

```python
class QualityReview(Skill):
    name = "quality_review"
    
    async def execute(self, ctx: SkillContext) -> SkillResult:
        # 两种模式: full / quick
        mode = ctx.parameters.get("mode", "full")
        proposal_content = ctx.parameters["proposal_content"]  # 用户编写的投标文件
        bid_requirements = ctx.parameters.get("bid_requirements", {})
        
        if mode == "quick":
            # temperature=0.1, max_tokens=500
            return await self._quick_review(ctx, proposal_content)
        else:
            # 4 维度: completeness, compliance, consistency, risks
            # temperature=0.2, max_tokens=4000
            return await self._full_review(ctx, proposal_content, bid_requirements)
```

**Full Review 输出**:
```json
{
  "completeness": {"score": 85, "missing_sections": [], "missing_attachments": []},
  "compliance": {"score": 90, "issues": []},
  "consistency": {"score": 80, "issues": []},
  "risks": {"score": 75, "items": []},
  "overall_score": 82,
  "win_probability": "medium",
  "critical_improvements": []
}
```

---

## 5. LangGraph Workflows

### 5.1 标书编制指导工作流

> **核心变更**: V2 不再由 AI 直接生成标书文档，而是通过 Q&A 驱动的指导模式帮助用户自行编写。LangGraph 工作流用于管理分析阶段和智能路由，问答交互在 Chat 层完成。

#### State 定义

```python
class BidGuidanceState(TypedDict):
    # 输入
    project_id: str
    user_id: str
    documents: list[dict]             # [{id, name, type}]
    parsed_documents: dict[str, str]  # {doc_id: content}
    
    # 分析结果 (由 Skills 填充)
    tor_analysis: dict
    scoring_criteria: list[dict]
    
    # 编制指导
    document_structure: dict          # {title, sections: [{id, title, requirements, scoring_weight}]}
    section_guidance: dict[str, dict] # {section_id: {guidance, format_req, content_outline, ...}}
    
    # 用户草稿与审查
    user_drafts: dict[str, str]       # {section_id: user_drafted_content}
    review_results: dict[str, dict]   # {section_id: {score, feedback, improvements}}
    
    # 控制
    current_step: str
    errors: list[str]
    
    # 人机交互 (Q&A 对话)
    messages: Annotated[Sequence[BaseMessage], add_messages]
```

#### Graph 定义

```python
workflow = StateGraph(BidGuidanceState)

# 添加节点
workflow.add_node("intake_documents", intake_documents_node)
workflow.add_node("analyze_tor", analyze_tor_node)
workflow.add_node("extract_criteria", extract_criteria_node)
workflow.add_node("build_structure", build_structure_node)
workflow.add_node("guidance_router", guidance_router_node)
workflow.add_node("provide_guidance", provide_guidance_node)
workflow.add_node("review_draft", review_draft_node)
workflow.add_node("quality_check", quality_check_node)

# 添加边
workflow.add_edge(START, "intake_documents")
workflow.add_edge("intake_documents", "analyze_tor")
workflow.add_edge("analyze_tor", "extract_criteria")
workflow.add_edge("extract_criteria", "build_structure")
workflow.add_edge("build_structure", "guidance_router")

# 智能路由: 根据用户消息意图分发
workflow.add_conditional_edges("guidance_router", route_user_intent, {
    "provide_guidance": "provide_guidance",
    "review_draft": "review_draft",
    "quality_check": "quality_check",
    "wait": "guidance_router",        # 等待用户输入
})

# 指导/审查完成后回到路由等待下一轮交互
workflow.add_edge("provide_guidance", "guidance_router")
workflow.add_edge("review_draft", "guidance_router")
workflow.add_edge("quality_check", END)
```

#### 工作流图

```
START
  │
  ▼
┌─────────────────┐
│ intake_documents │  解析上传的 PDF，提取文本
└────────┬────────┘
         ▼
┌─────────────────┐
│   analyze_tor   │  Skill: AnalyzeQualification + EvaluateCriteria + ExtractDates + ...
└────────┬────────┘
         ▼
┌─────────────────┐
│ extract_criteria │  细化评分标准，构建 scoring_criteria 列表
└────────┬────────┘
         ▼
┌─────────────────┐
│ build_structure  │  基于分析结果构建投标文件结构（章节 + 评分权重 + 格式要求）
└────────┬────────┘
         ▼
┌─────────────────┐     ┌──────────────────┐
│ guidance_router  │────►│ provide_guidance  │  Skill: SectionGuidance
│ (等待用户消息)    │     │ (提供编写指导)      │
│                 │     └────────┬─────────┘
│                 │◄─────────────┘
│                 │
│                 │────►┌──────────────────┐
│                 │     │  review_draft    │  Skill: ReviewDraft
│                 │     │ (审查用户草稿)     │
│                 │◄────└──────────────────┘
│                 │
│                 │────►┌──────────────────┐
│ "quality_check" │     │  quality_check   │  Skill: QualityReview (全文审查)
└─────────────────┘     └────────┬─────────┘
                                 ▼
                               END
```

#### 智能路由

```python
def route_user_intent(state: BidGuidanceState) -> str:
    """根据用户消息意图智能路由"""
    last_msg = state["messages"][-1] if state["messages"] else None
    if not last_msg or not isinstance(last_msg, HumanMessage):
        return "wait"
    
    content = last_msg.content.lower()
    
    # 意图识别 (LLM 或规则)
    if any(w in content for w in ["指导", "怎么写", "如何写", "guide", "how to write", "编写"]):
        return "provide_guidance"
    if any(w in content for w in ["审查", "检查", "review", "请看看", "帮我看"]):
        return "review_draft"
    if any(w in content for w in ["最终审查", "全文检查", "final review", "完整审查", "提交前"]):
        return "quality_check"
    
    # 默认: 简单问题直接在 prompt 层回答，不走 Skill
    return "wait"
```

#### 节点实现策略

| 节点 | 实现 |
|------|------|
| `intake_documents` | 从 DB 读取 ProjectDocument/BidDocument 的 parsed_content |
| `analyze_tor` | 调用 Skills: AnalyzeQualification, EvaluateCriteria, ExtractDates, AnalyzeBDS, AnalyzeCommercial, AssessRisk |
| `extract_criteria` | 处理 analyze_tor 结果，构建 scoring_criteria 列表 (fallback: 默认 4 维度) |
| `build_structure` | LLM 生成投标文件结构 JSON（章节列表 + 各章节的格式要求、评分权重） |
| `guidance_router` | 等待用户消息，基于意图识别分发到对应节点 |
| `provide_guidance` | `SectionGuidance.execute(section)` — 提供章节编写指导 |
| `review_draft` | `ReviewDraft.execute(draft)` — 审查用户编写的草稿，给出修改建议 |
| `quality_check` | `QualityReview(mode="full")` 全文审查，4 维度评分 |

#### 检查点 (V2 改进)

```python
from langgraph.checkpoint.redis import RedisSaver

# V2: 使用 Redis 持久化工作流状态 (替代 V1 内存 MemorySaver)
checkpointer = RedisSaver(redis_url=settings.REDIS_URL)
compiled_workflow = workflow.compile(checkpointer=checkpointer)
```

### 5.2 招标分析管道 (V2 新增)

独立于标书编制指导的分析管道，支持增量分析:

```python
async def run_bid_analysis_pipeline(
    project_id: str,
    steps: list[str] | None = None,
    force_refresh: bool = False,
) -> BidAnalysisResult:
    """
    8 步分析管道 (可选择性执行):
    1. qualification    → AnalyzeQualification
    2. evaluation       → EvaluateCriteria
    3. key_dates        → ExtractDates
    4. submission       → ExtractSubmission
    5. bds_modification → AnalyzeBDS
    6. methodology      → EvaluateMethodology (深度评标方法论)
    7. commercial       → AnalyzeCommercial
    8. risk_assessment  → AssessRisk (依赖步骤 1-5 结果)
    """
    if steps is None:
        steps = ALL_STEPS
    
    results = {}
    total_tokens = 0
    
    for step in steps:
        if not force_refresh and await has_cached_result(project_id, step):
            results[step] = await get_cached_result(project_id, step)
            continue
        
        skill = STEP_SKILL_MAP[step]
        ctx = SkillContext(
            project_id=project_id,
            parameters={**results},  # 前序结果作为参数
        )
        result = await skill.execute(ctx)
        results[step] = result.data
        total_tokens += result.tokens_consumed
    
    # 持久化到 bid_analyses 表
    await save_analysis(project_id, results, total_tokens)
    return results
```

---

## 6. RAG 模式

### 6.1 分析上下文组装

每个分析 Skill 按以下模式组装上下文:

```python
async def build_analysis_context(
    project_id: str,
    dimension: str,  # qualification/evaluation/dates/...
) -> tuple[str, str]:
    """构建分析上下文 (招标文件 + 知识库参考)"""
    
    # 维度配置
    config = DIMENSION_CONFIGS[dimension]
    
    # 1. 多 query 搜索招标文件
    all_chunks = []
    for query in config["doc_queries"]:
        chunks = await bid_document_search(
            project_id=project_id,
            query=query,
            section_types=config.get("section_types"),
            top_k=5,
            score_threshold=0.3,
        )
        all_chunks.extend(chunks)
    
    # 去重 + 排序 + 限制 15 个
    unique_chunks = deduplicate_by_id(all_chunks)
    top_chunks = sorted(unique_chunks, key=lambda c: c["score"], reverse=True)[:15]
    
    # 2. 搜索知识库参考
    kb_chunks = []
    for query in config["kb_queries"]:
        results = await knowledge_search(
            query=query,
            institution=config.get("institution", "adb"),
            top_k=3,
        )
        kb_chunks.extend(results)
    top_kb = sorted(kb_chunks, key=lambda c: c["score"], reverse=True)[:5]
    
    # 3. 格式化
    bid_context = "\n\n".join(
        f"[来源 {i+1}] {c['section_title']} ({c.get('clause_reference', '')}) - 第{c['page_number']}页\n{c['content']}"
        for i, c in enumerate(top_chunks)
    )
    
    kb_context = "\n\n".join(
        f"[ADB指南 {i+1}] {c['source_document']} - 第{c.get('page_number', '?')}页\n{c['content']}"
        for i, c in enumerate(top_kb)
    )
    
    return bid_context, kb_context
```

### 6.2 维度配置

| 维度 | 文档查询 | Section 类型 | 知识库查询 |
|------|---------|-------------|-----------|
| qualification | "qualification criteria eligibility", "minimum experience financial capacity", "joint venture consortium" | section_3, section_2_bds, section_1_itb | "ADB qualification criteria", "eligibility requirements bidder" |
| evaluation | "evaluation criteria scoring methodology weight", "technical proposal evaluation points" | section_3, section_2_bds | "QCBS quality cost based selection", "merit point criteria" |
| dates | "submission deadline bid opening date", "bid validity period" | section_2_bds, section_1_itb | "bid submission deadline requirements" |
| submission | "submission requirements format copies", "bid security guarantee" | section_2_bds, section_1_itb, section_4_forms | "bid submission format requirements" |
| bds | "BDS bid data sheet modifications", "ITB instruction reference" | section_2_bds, section_1_itb | "bid data sheet standard bidding document" |
| commercial | "payment terms warranty insurance penalty", "performance security" | section_2_bds, part_3_contract | "contract terms consulting services" |

### 6.3 问答 RAG

```python
async def answer_question(
    project_id: str,
    question: str,
    use_knowledge_base: bool = False,
    top_k: int = 5,
) -> dict:
    """RAG 问答"""
    # 1. 搜索招标文件
    doc_results = await bid_document_search(
        project_id=project_id,
        query=question,
        top_k=top_k,
    )
    
    # 2. 可选: 搜索知识库
    kb_results = []
    if use_knowledge_base:
        kb_results = await knowledge_search(query=question, top_k=3)
    
    # 3. 组装 context
    context = [chunk["content"] for chunk in doc_results + kb_results]
    
    # 4. LLM 生成回答
    response = await llm_client.generate_with_context(
        question=question,
        context=context,
        system_prompt=RAG_SYSTEM_PROMPT,
    )
    
    return {
        "answer": response.content,
        "sources": doc_results + kb_results,
    }
```

---

## 7. Prompt 模板管理

### 7.1 文件组织

```
backend/app/agents/prompts/
├── system_prompts.py       # 系统级人设 prompt
├── adb_analysis.py         # ADB 分析 prompt 模板
├── wb_analysis.py          # WB 分析 prompt 模板 (V2 新增)
├── guidance.py           # 标书编制指导 prompt
├── quality_review.py       # 质量审查 prompt
└── templates/              # Jinja2 模板 (可选，用于复杂 prompt)
```

### 7.2 核心 Prompt 清单

| Prompt | 模板变量 | 用途 |
|--------|---------|------|
| `SYSTEM_PROMPT_ADB_ANALYST` | — | ADB 投标专家人设 |
| `QUALIFICATION_EXTRACTION_PROMPT` | `{bid_document_context}`, `{knowledge_context}` | 资质要求提取 |
| `EVALUATION_CRITERIA_PROMPT` | `{bid_document_context}`, `{knowledge_context}` | 评分标准提取 |
| `KEY_DATES_PROMPT` | `{bid_document_context}`, `{knowledge_context}` | 关键日期提取 |
| `BDS_MODIFICATION_PROMPT` | `{bid_document_context}`, `{knowledge_context}` | BDS 修改识别 |
| `SUBMISSION_REQUIREMENTS_PROMPT` | `{bid_document_context}`, `{knowledge_context}` | 提交要求提取 |
| `EVALUATION_METHODOLOGY_PROMPT` | `{bid_document_context}`, `{knowledge_context}` | 评标方法论分析 |
| `COMMERCIAL_TERMS_PROMPT` | `{bid_document_context}`, `{knowledge_context}` | 商务条款分析 |
| `RISK_ASSESSMENT_PROMPT` | `{qualification}`, `{criteria}`, `{dates}`, `{bds}`, `{kb_context}` | 综合风险评估 |
| `QUALITY_REVIEW_PROMPT` | `{bid_requirements}`, `{proposal_content}`, `{evaluation_criteria}` | 完整质量审查 |
| `QUICK_QUALITY_REVIEW_PROMPT` | `{core_requirements}`, `{proposal_summary}` | 快速审查 |
| `PLAN_GENERATION_PROMPT` | `{analysis_summary}`, `{deadline}` | 投标计划生成 |
| `PREDICTION_PROMPT` | `{analysis_data}`, `{proposal_summary}` | 评标预测 |
| `SECTION_GENERATION_PROMPT` | `{section_config}`, `{project_context}`, `{criteria}`, `{doc_context}` | 章节内容生成 |
| `OUTLINE_CREATION_PROMPT` | `{tor_analysis}`, `{criteria}` | 大纲生成 |

### 7.3 Prompt 输出约定

所有结构化 Prompt 输出 JSON 格式:
- System prompt 结尾包含 `输出格式：使用 JSON 格式输出结构化结果`
- LLM Client 统一清理 ```` ```json ... ``` ```` 包裹
- 解析失败记录日志，返回 `None` 或 fallback 默认值

---

## 8. Embedding 流水线

### 8.1 文档向量化流程

```
                    ┌──── Celery Worker ────┐
PDF Upload          │                       │
    │               │   1. PDF → Text       │
    ▼               │   2. Text → Chunks    │
bid_documents ─────>│   3. Chunks → Embed   │
(status=pending)    │   4. Save vectors     │
                    │                       │
                    └───────────────────────┘
                              │
                              ▼
                    bid_document_chunks
                    (embedding = vector(1024))
```

### 8.2 分块策略

```python
class DocumentChunker:
    chunk_size: int = 1000       # 字符
    chunk_overlap: int = 200     # 重叠
    separators: list[str] = ["\n\n", "\n", ". ", " "]
    
    def chunk_text(self, text: str, metadata: dict) -> list[dict]:
        """RecursiveCharacterTextSplitter 策略"""
        ...
```

### 8.3 批量向量化

```python
async def vectorize_chunks(chunks: list[dict]) -> list[dict]:
    """批量向量化 (batch_size=16 for 混元)"""
    embedding_client = get_embedding_client()  # ResilientEmbeddingClient
    
    texts = [c["content"] for c in chunks]
    embeddings = await embedding_client.embed_texts(texts)  # 自动批处理
    
    for chunk, emb in zip(chunks, embeddings):
        chunk["embedding"] = emb.embedding
    
    return chunks
```

---

## 9. V1 → V2 工作流改进

| 方面 | V1 | V2 |
|------|-----|-----|
| 检查点 | `MemorySaver` (内存) | `RedisSaver` (持久化) |
| 数据检索 | 直接 SQL 查询 | MCP Tools 标准化 |
| 分析逻辑 | Service 层内联 | Skills 封装，可组合 |
| Prompt 管理 | 单文件 1096 行 | 按模块拆分 + 模板引擎 |
| 机构支持 | 仅 ADB (硬编码) | ADB/WB/UN (配置化) |
| 错误处理 | 无重试 | 指数退避 + 降级 |
| 流式输出 | 伪 SSE | 标准 `text/event-stream` |
| 并发控制 | 无限制 | LLM 并发上限 + 信号量 |
