# M3 - LLM服务任务规格书

## 概述
| 属性 | 值 |
|------|-----|
| 里程碑 | M3 - LLM Service |
| 周期 | Week 4 |
| 任务总数 | 10 |
| Opus 4.5 任务 | 3 |
| Mini-Agent 任务 | 7 |

## 目标
- 集成DeepSeek LLM API
- 实现统一的LLM调用接口
- 建立积分消费机制
- 实现基础Prompt模板

---

## 任务列表

### M3-01: LLM服务架构设计 (Opus 4.5)
**优先级**: P0  
**预估时间**: 3小时  
**执行者**: Opus 4.5

#### 描述
设计LLM服务架构，包括多模型支持、重试机制、缓存策略。

#### 验收标准
- [ ] 架构文档完成
- [ ] 接口定义清晰
- [ ] 错误处理策略
- [ ] 成本控制机制

#### 架构设计
```
┌─────────────────────────────────────────────────────────────┐
│                      LLM Service Layer                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   LLM Client                         │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐            │   │
│  │  │ Request │  │ Retry   │  │Response │            │   │
│  │  │ Builder │─▶│ Handler │─▶│ Parser  │            │   │
│  │  └─────────┘  └─────────┘  └─────────┘            │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│  ┌───────────────────────┼───────────────────────────────┐ │
│  │                    Features                            │ │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐ │ │
│  │  │ Caching │  │ Credits │  │Streaming│  │ Logging │ │ │
│  │  │ (Redis) │  │ Billing │  │ Support │  │  Trace  │ │ │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘ │ │
│  └─────────────────────────────────────────────────────────┘│
│                          │                                  │
└──────────────────────────┼──────────────────────────────────┘
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │ DeepSeek V3 │ │ DeepSeek R1 │ │  Fallback   │
    │  (通用)      │ │  (推理)      │ │  (OpenAI)   │
    └─────────────┘ └─────────────┘ └─────────────┘
```

#### 模型选择策略
| 任务类型 | 主模型 | 备选模型 | 原因 |
|---------|--------|---------|------|
| 文档分析 | DeepSeek-V3 | - | 性价比高 |
| 复杂推理 | DeepSeek-R1 | DeepSeek-V3 | 推理能力强 |
| 内容生成 | DeepSeek-V3 | - | 生成质量好 |
| 问答 | DeepSeek-V3 | - | 响应快速 |

#### 输出文件
- `docs/llm-service-design.md`

#### 依赖
无

---

### M3-02: DeepSeek Client封装 (Mini-Agent)
**优先级**: P0  
**预估时间**: 4小时  
**执行者**: Mini-Agent

#### 描述
实现DeepSeek API客户端封装，支持同步和异步调用。

#### 验收标准
- [ ] 支持chat completion
- [ ] 支持流式响应
- [ ] 错误重试机制
- [ ] 请求超时处理

#### 输出文件
- `backend/app/agents/llm_client.py`
- `backend/app/agents/models.py`

#### 核心代码
```python
# app/agents/llm_client.py
from typing import AsyncGenerator, Optional, List
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import settings
from app.core.logging import logger

class LLMClient:
    """LLM客户端封装"""
    
    MODELS = {
        "deepseek-v3": "deepseek-chat",
        "deepseek-r1": "deepseek-reasoner",
    }
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com/v1",
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def chat(
        self,
        messages: List[dict],
        model: str = "deepseek-v3",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> dict:
        """发送聊天请求"""
        try:
            response = await self.client.chat.completions.create(
                model=self.MODELS.get(model, model),
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            return {
                "content": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                "model": model,
            }
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            raise
    
    async def chat_stream(
        self,
        messages: List[dict],
        model: str = "deepseek-v3",
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式聊天请求"""
        response = await self.client.chat.completions.create(
            model=self.MODELS.get(model, model),
            messages=messages,
            stream=True,
            **kwargs
        )
        
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


# 便捷函数
_client: Optional[LLMClient] = None

def get_llm() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client

async def chat(messages: List[dict], **kwargs) -> dict:
    return await get_llm().chat(messages, **kwargs)
```

#### 依赖
- M3-01

---

### M3-03: LangChain集成 (Opus 4.5)
**优先级**: P0  
**预估时间**: 3小时  
**执行者**: Opus 4.5

#### 描述
将DeepSeek集成到LangChain，便于构建复杂工作流。

#### 验收标准
- [ ] 自定义ChatModel
- [ ] 支持LangChain工具调用
- [ ] 与LangGraph兼容
- [ ] 回调处理（token统计）

#### 输出文件
- `backend/app/agents/langchain_client.py`

#### 核心代码
```python
# app/agents/langchain_client.py
from typing import Any, List, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.callbacks import CallbackManagerForLLMRun
from openai import AsyncOpenAI
from app.config import settings

class DeepSeekChat(BaseChatModel):
    """DeepSeek LangChain ChatModel"""
    
    model: str = "deepseek-chat"
    temperature: float = 0.7
    max_tokens: int = 4096
    api_key: str = ""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_key = settings.DEEPSEEK_API_KEY
        self._client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com/v1",
        )
    
    @property
    def _llm_type(self) -> str:
        return "deepseek"
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        import asyncio
        return asyncio.run(self._agenerate(messages, stop, run_manager, **kwargs))
    
    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        message_dicts = [self._convert_message(m) for m in messages]
        
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=message_dicts,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stop=stop,
            **kwargs
        )
        
        content = response.choices[0].message.content
        generation = ChatGeneration(
            message=AIMessage(content=content),
            generation_info={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            }
        )
        
        return ChatResult(generations=[generation])
    
    def _convert_message(self, message: BaseMessage) -> dict:
        if message.type == "human":
            return {"role": "user", "content": message.content}
        elif message.type == "ai":
            return {"role": "assistant", "content": message.content}
        elif message.type == "system":
            return {"role": "system", "content": message.content}
        else:
            return {"role": "user", "content": message.content}


def get_deepseek_chat(model: str = "deepseek-v3") -> DeepSeekChat:
    """获取DeepSeek Chat实例"""
    model_map = {
        "deepseek-v3": "deepseek-chat",
        "deepseek-r1": "deepseek-reasoner",
    }
    return DeepSeekChat(model=model_map.get(model, model))
```

#### 依赖
- M3-02

---

### M3-04: 积分计费模块 (Mini-Agent)
**优先级**: P0  
**预估时间**: 4小时  
**执行者**: Mini-Agent

#### 描述
实现LLM调用的积分计费逻辑。

#### 验收标准
- [ ] 按token消费计费
- [ ] 调用前余额检查
- [ ] 事务性扣费
- [ ] 使用记录存储

#### 输出文件
- `backend/app/services/credit_service.py`
- `backend/app/models/credit.py`
- `backend/app/models/llm_usage.py`

#### 积分计费规则
```python
# app/config/credits.py

# 积分价格：1积分 ≈ ¥0.01
CREDIT_PRICING = {
    "deepseek-v3": {
        "input": 0.1,   # 每1K tokens消耗0.1积分
        "output": 0.2,  # 每1K tokens消耗0.2积分
    },
    "deepseek-r1": {
        "input": 0.4,
        "output": 0.8,
    },
}

def calculate_credits(
    model: str,
    prompt_tokens: int,
    completion_tokens: int
) -> int:
    """计算积分消耗"""
    pricing = CREDIT_PRICING.get(model, CREDIT_PRICING["deepseek-v3"])
    
    input_credits = (prompt_tokens / 1000) * pricing["input"]
    output_credits = (completion_tokens / 1000) * pricing["output"]
    
    return max(1, round(input_credits + output_credits))  # 最少1积分
```

#### 扣费服务
```python
# app/services/credit_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.user import User
from app.models.credit import CreditTransaction
from app.models.llm_usage import LLMUsage
from app.config.credits import calculate_credits

class CreditService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def check_balance(self, user_id: str, required: int) -> bool:
        """检查余额是否充足"""
        user = await self.db.get(User, user_id)
        return user and user.credits_balance >= required
    
    async def consume_credits(
        self,
        user_id: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        project_id: str = None,
        request_type: str = "chat",
    ) -> int:
        """消费积分"""
        credits_cost = calculate_credits(model, prompt_tokens, completion_tokens)
        
        # 更新用户余额
        result = await self.db.execute(
            update(User)
            .where(User.id == user_id, User.credits_balance >= credits_cost)
            .values(credits_balance=User.credits_balance - credits_cost)
            .returning(User.credits_balance)
        )
        
        new_balance = result.scalar_one_or_none()
        if new_balance is None:
            raise InsufficientCreditsError("积分不足")
        
        # 记录交易
        transaction = CreditTransaction(
            user_id=user_id,
            type="consume",
            amount=-credits_cost,
            balance_after=new_balance,
            reference_type="llm_usage",
            description=f"LLM调用: {model}",
        )
        self.db.add(transaction)
        
        # 记录LLM使用
        usage = LLMUsage(
            user_id=user_id,
            project_id=project_id,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            credits_cost=credits_cost,
            request_type=request_type,
        )
        self.db.add(usage)
        
        await self.db.commit()
        return credits_cost

class InsufficientCreditsError(Exception):
    pass
```

#### 依赖
- M1-01, M3-02

---

### M3-05: 调用计费装饰器 (Mini-Agent)
**优先级**: P0  
**预估时间**: 2小时  
**执行者**: Mini-Agent

#### 描述
创建装饰器，自动处理LLM调用的积分计费。

#### 验收标准
- [ ] 装饰器自动扣费
- [ ] 支持异步函数
- [ ] 余额不足时抛出异常
- [ ] 响应头返回消费信息

#### 代码实现
```python
# app/agents/billing.py
from functools import wraps
from fastapi import HTTPException
from app.services.credit_service import CreditService, InsufficientCreditsError

def with_credits(request_type: str = "chat"):
    """LLM调用计费装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从kwargs获取必要参数
            db = kwargs.get("db")
            user = kwargs.get("current_user")
            project_id = kwargs.get("project_id")
            
            if not db or not user:
                raise ValueError("Missing db or user")
            
            credit_service = CreditService(db)
            
            # 执行LLM调用
            result = await func(*args, **kwargs)
            
            # 扣费
            if "usage" in result:
                try:
                    credits_cost = await credit_service.consume_credits(
                        user_id=str(user.id),
                        model=result.get("model", "deepseek-v3"),
                        prompt_tokens=result["usage"]["prompt_tokens"],
                        completion_tokens=result["usage"]["completion_tokens"],
                        project_id=project_id,
                        request_type=request_type,
                    )
                    result["credits_consumed"] = credits_cost
                except InsufficientCreditsError:
                    raise HTTPException(
                        status_code=402,
                        detail="积分不足，请充值"
                    )
            
            return result
        return wrapper
    return decorator
```

#### 依赖
- M3-04

---

### M3-06: 响应缓存 (Mini-Agent)
**优先级**: P1  
**预估时间**: 3小时  
**执行者**: Mini-Agent

#### 描述
实现LLM响应缓存，减少重复调用。

#### 验收标准
- [ ] 相同输入命中缓存
- [ ] 缓存过期机制
- [ ] 缓存命中统计
- [ ] 可配置是否缓存

#### 代码实现
```python
# app/agents/cache.py
import hashlib
import json
from typing import Optional
from app.core.redis import redis_client
from app.config import settings

class LLMCache:
    """LLM响应缓存"""
    
    PREFIX = "llm_cache:"
    DEFAULT_TTL = 7 * 24 * 3600  # 7天
    
    @staticmethod
    def _make_key(messages: list, model: str, **kwargs) -> str:
        """生成缓存key"""
        data = {
            "messages": messages,
            "model": model,
            **kwargs
        }
        content = json.dumps(data, sort_keys=True)
        hash_val = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"{LLMCache.PREFIX}{hash_val}"
    
    async def get(self, messages: list, model: str, **kwargs) -> Optional[dict]:
        """获取缓存"""
        key = self._make_key(messages, model, **kwargs)
        data = await redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    
    async def set(
        self,
        messages: list,
        model: str,
        response: dict,
        ttl: int = None,
        **kwargs
    ):
        """设置缓存"""
        key = self._make_key(messages, model, **kwargs)
        await redis_client.setex(
            key,
            ttl or self.DEFAULT_TTL,
            json.dumps(response)
        )

llm_cache = LLMCache()
```

#### 依赖
- M0-04 (Redis)

---

### M3-07: Prompt模板管理 (Opus 4.5)
**优先级**: P1  
**预估时间**: 4小时  
**执行者**: Opus 4.5

#### 描述
设计和实现Prompt模板管理系统。

#### 验收标准
- [ ] 模板版本管理
- [ ] 变量替换机制
- [ ] Few-shot示例支持
- [ ] 多语言模板

#### 输出文件
- `backend/app/agents/prompts/base.py`
- `backend/app/agents/prompts/templates/`

#### 代码实现
```python
# app/agents/prompts/base.py
from typing import Dict, Any, List
from string import Template
from pathlib import Path
import yaml

class PromptTemplate:
    """Prompt模板基类"""
    
    def __init__(
        self,
        template: str,
        input_variables: List[str],
        few_shot_examples: List[dict] = None,
    ):
        self.template = template
        self.input_variables = input_variables
        self.few_shot_examples = few_shot_examples or []
    
    def format(self, **kwargs) -> str:
        """格式化模板"""
        # 验证变量
        for var in self.input_variables:
            if var not in kwargs:
                raise ValueError(f"Missing variable: {var}")
        
        # 添加few-shot示例
        examples_text = ""
        if self.few_shot_examples:
            examples_text = "\n\n## Examples\n"
            for ex in self.few_shot_examples:
                examples_text += f"\nInput: {ex['input']}\nOutput: {ex['output']}\n"
        
        # 替换变量
        result = Template(self.template).safe_substitute(**kwargs)
        return result.replace("{{examples}}", examples_text)
    
    @classmethod
    def from_yaml(cls, path: str) -> "PromptTemplate":
        """从YAML文件加载"""
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return cls(
            template=data['template'],
            input_variables=data.get('input_variables', []),
            few_shot_examples=data.get('examples', []),
        )


class PromptManager:
    """Prompt管理器"""
    
    def __init__(self, templates_dir: str = None):
        self.templates_dir = Path(templates_dir or "app/agents/prompts/templates")
        self._cache: Dict[str, PromptTemplate] = {}
    
    def get(self, name: str, language: str = "en") -> PromptTemplate:
        """获取模板"""
        cache_key = f"{name}_{language}"
        
        if cache_key not in self._cache:
            path = self.templates_dir / language / f"{name}.yaml"
            if not path.exists():
                # 回退到英文
                path = self.templates_dir / "en" / f"{name}.yaml"
            
            self._cache[cache_key] = PromptTemplate.from_yaml(str(path))
        
        return self._cache[cache_key]


# 全局实例
prompt_manager = PromptManager()
```

#### 模板示例
```yaml
# app/agents/prompts/templates/en/tor_analysis.yaml
template: |
  You are an expert consultant analyzing Terms of Reference (TOR) documents.
  
  ## Task
  Analyze the following TOR and extract key information.
  
  ## TOR Document
  $tor_content
  
  ## Required Output
  Extract the following in JSON format:
  1. project_title
  2. objectives (array)
  3. scope_of_work (array of {task, description})
  4. deliverables (array of {name, deadline})
  5. qualifications (array)
  6. evaluation_criteria (array of {criterion, weight})
  
  {{examples}}
  
  ## Your Analysis

input_variables:
  - tor_content

examples:
  - input: "TOR for Water Supply Project..."
    output: '{"project_title": "Water Supply Improvement", ...}'
```

#### 依赖
- M3-02

---

### M3-08: LLM调用API (Mini-Agent)
**优先级**: P1  
**预估时间**: 2小时  
**执行者**: Mini-Agent

#### 描述
创建通用LLM调用API端点。

#### 验收标准
- [ ] POST /api/v1/llm/chat
- [ ] 支持流式响应
- [ ] 返回积分消费
- [ ] 请求限流

#### 依赖
- M3-05

---

### M3-09: Token统计中间件 (Mini-Agent)
**优先级**: P2  
**预估时间**: 2小时  
**执行者**: Mini-Agent

#### 描述
实现Token统计和日志记录。

#### 验收标准
- [ ] 记录每次调用详情
- [ ] 响应头包含Token信息
- [ ] 统计报表数据准备

#### 依赖
- M3-04

---

### M3-10: LLM服务测试 (Mini-Agent)
**优先级**: P1  
**预估时间**: 3小时  
**执行者**: Mini-Agent

#### 描述
编写LLM服务单元测试和集成测试。

#### 验收标准
- [ ] Mock LLM响应
- [ ] 测试计费逻辑
- [ ] 测试缓存命中
- [ ] 测试错误处理

#### 依赖
- M3-01 ~ M3-09

---

## 里程碑检查点

### 完成标准
- [ ] DeepSeek API可正常调用
- [ ] 积分计费准确
- [ ] LangChain集成可用
- [ ] Prompt模板管理完善

### 交付物
1. LLM客户端封装
2. 积分计费模块
3. Prompt模板系统
4. 测试覆盖

---

## 成本估算

### Token消耗预估（单次标书生成）
| 步骤 | 模型 | 输入Token | 输出Token | 积分 |
|------|------|-----------|-----------|------|
| TOR分析 | V3 | 20,000 | 2,000 | 6 |
| 评分标准 | R1 | 5,000 | 3,000 | 5 |
| 大纲生成 | V3 | 10,000 | 2,000 | 4 |
| 内容生成(5章) | V3 | 50,000 | 25,000 | 35 |
| 质量检查 | R1 | 30,000 | 5,000 | 16 |
| **合计** | - | 115,000 | 37,000 | **66积分** |

### 套餐建议
- 入门包(1000积分): 约15次完整生成
- 专业包(20000积分): 约300次完整生成
