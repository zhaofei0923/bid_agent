# M6 - 积分系统任务规格书

## 概述
| 属性 | 值 |
|------|-----|
| 里程碑 | M6 - Credits System |
| 周期 | Week 9 |
| 任务总数 | 8 |
| Opus 4.5 任务 | 2 |
| Mini-Agent 任务 | 6 |

## 目标
- 实现积分余额管理
- 实现LLM调用计费
- 实现充值功能
- 创建使用统计

---

## 任务列表

### M6-01: 积分系统设计 (Opus 4.5)
**优先级**: P0  
**预估时间**: 3小时  
**执行者**: Opus 4.5

#### 描述
设计完整的积分计费体系。

#### 设计要点
1. 积分计算规则
2. 计费精度处理
3. 并发安全
4. 审计追踪

#### 计费规则设计
```python
# 积分计费规则
# 1 积分 ≈ ¥0.01 (仅内部核算)

class CreditRules:
    """积分计费规则"""
    
    # === DeepSeek 模型价格 ===
    # DeepSeek V3: Input $0.27/M, Output $1.10/M (约 ¥1.89/M, ¥7.7/M)
    # DeepSeek R1: Input $0.55/M, Output $2.19/M (约 ¥3.85/M, ¥15.33/M)
    
    # 平台加价系数 (覆盖运营成本 + 毛利)
    MARKUP_RATIO = 1.5
    
    # 积分/Token 换算 (积分数 per 1K tokens)
    CREDIT_RATES = {
        "deepseek-v3": {
            "input": 0.3,   # ≈ 0.2 * 1.5 = 0.3 积分/1K input tokens
            "output": 1.2,  # ≈ 0.8 * 1.5 = 1.2 积分/1K output tokens
        },
        "deepseek-r1": {
            "input": 0.6,   # ≈ 0.4 * 1.5 = 0.6 积分/1K input tokens
            "output": 2.4,  # ≈ 1.6 * 1.5 = 2.4 积分/1K output tokens
        },
    }
    
    # 功能固定积分消耗
    FEATURE_CREDITS = {
        "tor_analysis": 50,        # TOR分析固定消耗
        "document_embedding": 10,  # 文档向量化固定消耗
        "section_generation": 30,  # 每章节生成固定消耗
        "quality_check": 20,       # 质量检查固定消耗
        "export_pdf": 5,           # PDF导出
        "export_docx": 5,          # DOCX导出
    }
    
    @classmethod
    def calculate_llm_credits(
        cls,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> int:
        """计算LLM调用积分"""
        rates = cls.CREDIT_RATES.get(model, cls.CREDIT_RATES["deepseek-v3"])
        
        input_credits = (input_tokens / 1000) * rates["input"]
        output_credits = (output_tokens / 1000) * rates["output"]
        
        # 向上取整，最少1积分
        return max(1, int(input_credits + output_credits + 0.5))
```

#### 验收标准
- [ ] 计费规则清晰
- [ ] 价格可配置
- [ ] 防止超额消费

#### 输出文件
- `backend/app/core/credits.py`
- `docs/architecture/credits-model.md`

#### 依赖
- M0-01

---

### M6-02: 积分服务实现 (Mini-Agent)
**优先级**: P0  
**预估时间**: 4小时  
**执行者**: Mini-Agent

#### 描述
实现积分服务核心逻辑。

#### 代码实现
```python
# app/services/credit_service.py
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.exc import IntegrityError

from app.models import User, CreditTransaction, LLMUsage, RechargeOrder
from app.core.credits import CreditRules
from app.core.config import settings
from app.exceptions import InsufficientCreditsError

class CreditService:
    """积分服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_balance(self, user_id: str) -> int:
        """获取用户积分余额"""
        result = await self.db.execute(
            select(User.credits_balance).where(User.id == user_id)
        )
        balance = result.scalar_one_or_none()
        return balance or 0
    
    async def check_credits(self, user_id: str, required: int) -> bool:
        """检查积分是否足够"""
        balance = await self.get_balance(user_id)
        return balance >= required
    
    async def deduct_credits(
        self,
        user_id: str,
        amount: int,
        transaction_type: str,
        description: str,
        reference_id: Optional[str] = None,
    ) -> CreditTransaction:
        """扣减积分 (带事务)"""
        
        # 1. 乐观锁更新余额
        stmt = (
            update(User)
            .where(User.id == user_id, User.credits_balance >= amount)
            .values(credits_balance=User.credits_balance - amount)
            .returning(User.credits_balance)
        )
        result = await self.db.execute(stmt)
        new_balance = result.scalar_one_or_none()
        
        if new_balance is None:
            # 余额不足
            raise InsufficientCreditsError(
                message="积分余额不足",
                required=amount,
                available=await self.get_balance(user_id)
            )
        
        # 2. 创建交易记录
        transaction = CreditTransaction(
            user_id=user_id,
            amount=-amount,
            balance_after=new_balance,
            transaction_type=transaction_type,
            description=description,
            reference_id=reference_id,
        )
        self.db.add(transaction)
        await self.db.commit()
        
        return transaction
    
    async def add_credits(
        self,
        user_id: str,
        amount: int,
        transaction_type: str,
        description: str,
        reference_id: Optional[str] = None,
    ) -> CreditTransaction:
        """增加积分"""
        
        # 1. 更新余额
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(credits_balance=User.credits_balance + amount)
            .returning(User.credits_balance)
        )
        result = await self.db.execute(stmt)
        new_balance = result.scalar_one()
        
        # 2. 创建交易记录
        transaction = CreditTransaction(
            user_id=user_id,
            amount=amount,
            balance_after=new_balance,
            transaction_type=transaction_type,
            description=description,
            reference_id=reference_id,
        )
        self.db.add(transaction)
        await self.db.commit()
        
        return transaction
    
    async def record_llm_usage(
        self,
        user_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        project_id: Optional[str] = None,
        feature: Optional[str] = None,
    ) -> LLMUsage:
        """记录LLM使用并扣费"""
        
        # 计算积分
        credits = CreditRules.calculate_llm_credits(model, input_tokens, output_tokens)
        
        # 扣费
        await self.deduct_credits(
            user_id=user_id,
            amount=credits,
            transaction_type="llm_usage",
            description=f"LLM调用 {model}: {input_tokens}+{output_tokens} tokens",
            reference_id=project_id,
        )
        
        # 记录使用详情
        usage = LLMUsage(
            user_id=user_id,
            project_id=project_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            credits_consumed=credits,
            feature=feature,
        )
        self.db.add(usage)
        await self.db.commit()
        
        return usage
    
    async def get_usage_stats(
        self,
        user_id: str,
        days: int = 30,
    ) -> Dict:
        """获取使用统计"""
        since = datetime.utcnow() - timedelta(days=days)
        
        # 按模型统计
        model_stats = await self.db.execute(
            select(
                LLMUsage.model,
                func.sum(LLMUsage.input_tokens).label("total_input"),
                func.sum(LLMUsage.output_tokens).label("total_output"),
                func.sum(LLMUsage.credits_consumed).label("total_credits"),
                func.count(LLMUsage.id).label("call_count"),
            )
            .where(LLMUsage.user_id == user_id, LLMUsage.created_at >= since)
            .group_by(LLMUsage.model)
        )
        
        # 按日期统计
        daily_stats = await self.db.execute(
            select(
                func.date(LLMUsage.created_at).label("date"),
                func.sum(LLMUsage.credits_consumed).label("credits"),
            )
            .where(LLMUsage.user_id == user_id, LLMUsage.created_at >= since)
            .group_by(func.date(LLMUsage.created_at))
        )
        
        return {
            "by_model": [dict(r) for r in model_stats.fetchall()],
            "by_date": [dict(r) for r in daily_stats.fetchall()],
        }
    
    async def get_transactions(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[CreditTransaction]:
        """获取交易记录"""
        result = await self.db.execute(
            select(CreditTransaction)
            .where(CreditTransaction.user_id == user_id)
            .order_by(CreditTransaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()


# 依赖注入
async def get_credit_service(db: AsyncSession) -> CreditService:
    return CreditService(db)
```

#### 验收标准
- [ ] 余额查询正确
- [ ] 扣费原子操作
- [ ] 防止负余额
- [ ] 交易记录完整

#### 依赖
- M6-01, M0-06

---

### M6-03: 充值流程设计 (Opus 4.5)
**优先级**: P1  
**预估时间**: 3小时  
**执行者**: Opus 4.5

#### 描述
设计安全的充值流程。

#### 充值方案
```
MVP阶段采用简化方案:
1. 用户提交充值请求
2. 生成支付订单
3. 用户线下转账
4. 管理员手动确认
5. 系统到账

未来可集成:
- 支付宝
- 微信支付
- Stripe (国际)
```

#### 验收标准
- [ ] 订单状态机设计
- [ ] 防重复充值
- [ ] 管理员操作审计

#### 依赖
- M6-02

---

### M6-04: 充值API实现 (Mini-Agent)
**优先级**: P1  
**预估时间**: 3小时  
**执行者**: Mini-Agent

#### 描述
实现充值订单相关API。

#### 代码实现
```python
# app/api/v1/credits.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user, get_admin_user
from app.services.credit_service import CreditService
from app.schemas.credits import (
    CreditBalance,
    RechargeRequest,
    RechargeResponse,
    TransactionList,
    UsageStats,
)

router = APIRouter()

@router.get("/balance")
async def get_balance(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
) -> CreditBalance:
    """获取积分余额"""
    service = CreditService(db)
    balance = await service.get_balance(str(current_user.id))
    
    return CreditBalance(
        user_id=str(current_user.id),
        balance=balance,
    )


@router.get("/transactions")
async def get_transactions(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
) -> TransactionList:
    """获取交易记录"""
    service = CreditService(db)
    transactions = await service.get_transactions(
        str(current_user.id), limit, offset
    )
    
    return TransactionList(
        items=[t.to_dict() for t in transactions],
        total=len(transactions),
    )


@router.get("/usage")
async def get_usage_stats(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
) -> UsageStats:
    """获取使用统计"""
    service = CreditService(db)
    stats = await service.get_usage_stats(str(current_user.id), days)
    return stats


@router.post("/recharge")
async def create_recharge_order(
    request: RechargeRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
) -> RechargeResponse:
    """创建充值订单"""
    from app.models import RechargeOrder
    import uuid
    
    order = RechargeOrder(
        id=uuid.uuid4(),
        user_id=current_user.id,
        amount_cny=request.amount,
        credits_amount=request.amount * 100,  # ¥1 = 100积分
        status="pending",
    )
    db.add(order)
    await db.commit()
    
    return RechargeResponse(
        order_id=str(order.id),
        amount_cny=order.amount_cny,
        credits_amount=order.credits_amount,
        status=order.status,
        payment_info={
            "bank": "招商银行",
            "account": "xxxx xxxx xxxx 1234",
            "name": "xxx科技有限公司",
            "note": f"充值订单 {order.id}",
        }
    )


@router.post("/recharge/{order_id}/confirm")
async def confirm_recharge(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_admin_user),
):
    """管理员确认充值 (MVP阶段手动)"""
    from sqlalchemy import select
    from app.models import RechargeOrder
    
    result = await db.execute(
        select(RechargeOrder).where(RechargeOrder.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(404, "订单不存在")
    
    if order.status != "pending":
        raise HTTPException(400, "订单状态不正确")
    
    # 更新订单状态
    order.status = "completed"
    order.confirmed_by = admin.id
    order.confirmed_at = datetime.utcnow()
    
    # 增加积分
    service = CreditService(db)
    await service.add_credits(
        user_id=str(order.user_id),
        amount=order.credits_amount,
        transaction_type="recharge",
        description=f"充值 ¥{order.amount_cny}",
        reference_id=str(order.id),
    )
    
    return {"status": "success", "credits_added": order.credits_amount}
```

#### 验收标准
- [ ] 余额查询API
- [ ] 交易记录API
- [ ] 充值订单API
- [ ] 管理员确认API

#### 依赖
- M6-02, M6-03

---

### M6-05: 积分计费中间件 (Mini-Agent)
**优先级**: P0  
**预估时间**: 2小时  
**执行者**: Mini-Agent

#### 描述
实现LLM调用前的积分检查中间件。

#### 代码实现
```python
# app/agents/middlewares/credit_check.py
from functools import wraps
from typing import Callable
from app.services.credit_service import CreditService
from app.core.credits import CreditRules
from app.exceptions import InsufficientCreditsError

def require_credits(estimated_credits: int = 50):
    """
    装饰器: 检查积分是否足够
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(state, *args, **kwargs):
            user_id = state.get("user_id")
            if not user_id:
                raise ValueError("state中未找到user_id")
            
            # 检查积分
            from app.database import async_session
            async with async_session() as db:
                service = CreditService(db)
                balance = await service.get_balance(user_id)
                
                if balance < estimated_credits:
                    raise InsufficientCreditsError(
                        message="积分不足，请充值后继续",
                        required=estimated_credits,
                        available=balance
                    )
            
            # 执行原函数
            result = await func(state, *args, **kwargs)
            return result
        
        return wrapper
    return decorator


# 使用示例
@require_credits(estimated_credits=100)
async def analyze_tor(state):
    ...
```

#### 验收标准
- [ ] 调用前检查
- [ ] 预估消耗准确
- [ ] 异常处理友好

#### 依赖
- M6-02

---

### M6-06: 前端积分组件 (Mini-Agent)
**优先级**: P1  
**预估时间**: 3小时  
**执行者**: Mini-Agent

#### 描述
实现前端积分显示和管理组件。

#### 组件实现
```typescript
// src/components/credits/CreditBalance.tsx
"use client"

import { useCredits } from "@/hooks/useCredits"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Coins, TrendingDown, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"

export function CreditBalance() {
  const t = useTranslations("credits")
  const router = useRouter()
  const { balance, isLoading, refetch } = useCredits()
  
  const getBalanceStatus = (balance: number) => {
    if (balance >= 1000) return { status: "healthy", color: "bg-green-500" }
    if (balance >= 100) return { status: "low", color: "bg-yellow-500" }
    return { status: "critical", color: "bg-red-500" }
  }
  
  const { status, color } = getBalanceStatus(balance || 0)
  
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">
          <Coins className="w-4 h-4 inline mr-2" />
          {t("balance")}
        </CardTitle>
        <Button 
          variant="ghost" 
          size="icon"
          onClick={() => refetch()}
          disabled={isLoading}
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
        </Button>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <div className="text-2xl font-bold">
            {isLoading ? "..." : balance?.toLocaleString()}
          </div>
          <Badge className={color}>
            {t(`status.${status}`)}
          </Badge>
        </div>
        
        {status === "critical" && (
          <div className="mt-2 text-sm text-red-600 flex items-center">
            <TrendingDown className="w-4 h-4 mr-1" />
            {t("lowBalanceWarning")}
          </div>
        )}
        
        <Button 
          className="w-full mt-4"
          onClick={() => router.push("/dashboard/credits/recharge")}
        >
          {t("recharge")}
        </Button>
      </CardContent>
    </Card>
  )
}


// src/components/credits/UsageChart.tsx
"use client"

import { useMemo } from "react"
import { useCreditsUsage } from "@/hooks/useCredits"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer 
} from "recharts"
import { useTranslations } from "next-intl"

export function UsageChart() {
  const t = useTranslations("credits")
  const { data: usage, isLoading } = useCreditsUsage(30)
  
  const chartData = useMemo(() => {
    if (!usage?.by_date) return []
    return usage.by_date.map((item: any) => ({
      date: new Date(item.date).toLocaleDateString(),
      credits: item.credits,
    }))
  }, [usage])
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("usageChart")}</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="h-[200px] flex items-center justify-center">
            Loading...
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData}>
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Line 
                type="monotone" 
                dataKey="credits" 
                stroke="#8884d8"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}
```

#### 验收标准
- [ ] 余额实时显示
- [ ] 低余额警告
- [ ] 使用统计图表
- [ ] 充值入口

#### 依赖
- M6-04, M7-02

---

### M6-07: 交易明细页面 (Mini-Agent)
**优先级**: P2  
**预估时间**: 2小时  
**执行者**: Mini-Agent

#### 描述
实现积分交易明细页面。

#### 验收标准
- [ ] 交易列表展示
- [ ] 分页加载
- [ ] 筛选功能
- [ ] 导出功能

#### 依赖
- M6-06

---

### M6-08: 积分告警 (Mini-Agent)
**优先级**: P2  
**预估时间**: 2小时  
**执行者**: Mini-Agent

#### 描述
实现低积分告警通知。

#### 代码实现
```python
# app/services/notification_service.py
from typing import Optional
from app.core.config import settings

async def check_and_notify_low_balance(
    user_id: str,
    current_balance: int,
    threshold: int = 100,
):
    """检查并发送低余额通知"""
    if current_balance < threshold:
        # 发送通知 (暂时仅记录日志，后续可接入邮件/WebSocket)
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"User {user_id} has low credit balance: {current_balance}")
        
        # TODO: 发送邮件通知
        # TODO: 发送WebSocket实时通知
```

#### 验收标准
- [ ] 余额低于阈值触发
- [ ] 避免重复通知
- [ ] 通知记录保存

#### 依赖
- M6-02

---

## 里程碑检查点

### 完成标准
- [ ] 积分扣费正确
- [ ] 不会出现负余额
- [ ] 交易记录完整
- [ ] 充值流程可用
- [ ] 前端显示正确

### 交付物
1. 积分服务模块
2. 充值流程
3. 前端积分组件
4. 使用统计功能

---

## 安全考虑

| 风险 | 缓解措施 |
|------|----------|
| 并发扣费 | 乐观锁 + 数据库事务 |
| 负余额 | 扣费前检查 + 数据库约束 |
| 重复充值 | 订单幂等性 |
| 审计缺失 | 所有操作记录日志 |
