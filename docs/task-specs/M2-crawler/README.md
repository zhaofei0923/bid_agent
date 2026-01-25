# M2 - 爬虫模块任务规格书

## 概述
| 属性 | 值 |
|------|-----|
| 里程碑 | M2 - Crawler |
| 周期 | Week 3 |
| 任务总数 | 8 |
| Opus 4.5 任务 | 2 |
| Mini-Agent 任务 | 6 |

## 目标
- 实现ADB招标信息自动爬取
- 数据清洗与结构化存储
- 定时调度任务

---

## 任务列表

### M2-01: ADB网站分析与爬虫设计 (Opus 4.5)
**优先级**: P0  
**预估时间**: 4小时  
**执行者**: Opus 4.5

#### 描述
分析ADB招标网站结构，设计爬虫架构。

#### 分析目标
1. **ADB CMS Portal**: https://www.adb.org/projects/tenders/group/goods-works-and-services
2. **数据结构**: 项目名称、截止日期、国家、行业、预算等
3. **反爬策略**: 请求频率限制、验证码检测

#### 验收标准
- [ ] 完成网站结构分析文档
- [ ] 确定数据提取策略
- [ ] 设计爬虫架构图
- [ ] 定义数据模型映射

#### 输出文件
- `docs/crawler-design.md`
- `backend/app/crawler/adb/README.md`

#### 架构设计
```
┌─────────────────────────────────────────────────────────────┐
│                      Crawler Service                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │  Scheduler  │───▶│   Fetcher   │───▶│   Parser    │    │
│  │  (Celery)   │    │  (httpx)    │    │ (BeautifulSoup)│ │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
│         │                  │                  │             │
│         ▼                  ▼                  ▼             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                     Data Pipeline                    │   │
│  │  ┌─────────┐    ┌─────────┐    ┌─────────┐         │   │
│  │  │ Cleaner │───▶│Validator│───▶│ Storage │         │   │
│  │  └─────────┘    └─────────┘    └─────────┘         │   │
│  └─────────────────────────────────────────────────────┘   │
│                            │                                │
│                            ▼                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    PostgreSQL                        │   │
│  │              (bid_opportunities table)               │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

#### ADB数据字段映射
| ADB字段 | 数据库字段 | 说明 |
|---------|-----------|------|
| Project Number | external_id | 项目编号 |
| Title | title | 项目名称 |
| Country | country | 国家 |
| Sector | sector | 行业 |
| Closing Date | deadline | 截止日期 |
| Notice Type | procurement_type | 采购类型 |
| Description | description | 描述 |

#### 依赖
- M0-04

---

### M2-02: 招标机会数据模型 (Mini-Agent)
**优先级**: P0  
**预估时间**: 2小时  
**执行者**: Mini-Agent

#### 描述
创建招标机会相关数据模型。

#### 验收标准
- [ ] BidOpportunity模型定义
- [ ] 全文搜索配置
- [ ] 迁移脚本执行成功
- [ ] 索引创建完成

#### 输出文件
- `backend/app/models/opportunity.py`
- `backend/alembic/versions/002_create_opportunities.py`

#### 模型代码
```python
# app/models/opportunity.py
from sqlalchemy import Column, String, Text, DateTime, Numeric, Index, event
from sqlalchemy.dialects.postgresql import UUID, JSONB, TSVECTOR
from sqlalchemy.sql import func
from app.db.base import Base
import uuid

class BidOpportunity(Base):
    __tablename__ = "bid_opportunities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 来源标识
    source = Column(String(20), nullable=False)  # adb, wb, un
    external_id = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    
    # 基本信息
    title = Column(String(500), nullable=False)
    description = Column(Text)
    organization = Column(String(200))
    
    # 时间与金额
    published_at = Column(DateTime(timezone=True))
    deadline = Column(DateTime(timezone=True))
    budget_min = Column(Numeric(15, 2))
    budget_max = Column(Numeric(15, 2))
    currency = Column(String(10), default="USD")
    
    # 分类信息
    location = Column(String(200))
    country = Column(String(100))
    sector = Column(String(100))
    procurement_type = Column(String(50))
    
    # 状态
    status = Column(String(20), nullable=False, default="open")
    
    # 原始数据
    raw_data = Column(JSONB)
    
    # 全文搜索
    search_vector = Column(TSVECTOR)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_opp_source_external', 'source', 'external_id', unique=True),
        Index('idx_opp_status_deadline', 'status', 'deadline'),
        Index('idx_opp_search', 'search_vector', postgresql_using='gin'),
    )
```

#### 依赖
- M0-06

---

### M2-03: ADB列表页爬虫 (Mini-Agent)
**优先级**: P0  
**预估时间**: 4小时  
**执行者**: Mini-Agent

#### 描述
实现ADB招标列表页爬取。

#### 验收标准
- [ ] 获取所有活跃招标列表
- [ ] 分页处理正确
- [ ] 错误重试机制
- [ ] 请求频率控制

#### 输出文件
- `backend/app/crawler/adb/list_crawler.py`
- `backend/app/crawler/base.py`

#### 代码实现
```python
# app/crawler/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import httpx
import asyncio
from app.core.logging import logger

class BaseCrawler(ABC):
    """爬虫基类"""
    
    def __init__(self, rate_limit: float = 1.0):
        self.rate_limit = rate_limit  # 请求间隔(秒)
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
    
    @abstractmethod
    async def fetch_list(self, page: int = 1) -> List[Dict[str, Any]]:
        """获取列表页数据"""
        pass
    
    @abstractmethod
    async def fetch_detail(self, url: str) -> Dict[str, Any]:
        """获取详情页数据"""
        pass
    
    async def request(self, url: str, method: str = "GET", **kwargs) -> httpx.Response:
        """带频率限制的请求"""
        await asyncio.sleep(self.rate_limit)
        
        for attempt in range(3):
            try:
                response = await self.client.request(method, url, **kwargs)
                response.raise_for_status()
                return response
            except httpx.HTTPError as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt == 2:
                    raise
                await asyncio.sleep(2 ** attempt)
        
        raise Exception("Max retries exceeded")
    
    async def close(self):
        await self.client.aclose()


# app/crawler/adb/list_crawler.py
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from app.crawler.base import BaseCrawler
from datetime import datetime

class ADBListCrawler(BaseCrawler):
    """ADB招标列表爬虫"""
    
    BASE_URL = "https://www.adb.org/projects/tenders/group/goods-works-and-services"
    
    async def fetch_list(self, page: int = 1) -> List[Dict[str, Any]]:
        """获取招标列表"""
        url = f"{self.BASE_URL}?page={page}"
        response = await self.request(url)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        items = []
        
        # 解析列表项
        for row in soup.select('.view-content .views-row'):
            item = self._parse_list_item(row)
            if item:
                items.append(item)
        
        return items
    
    def _parse_list_item(self, row) -> Dict[str, Any] | None:
        """解析单个列表项"""
        try:
            title_elem = row.select_one('.views-field-title a')
            if not title_elem:
                return None
            
            return {
                'title': title_elem.text.strip(),
                'url': f"https://www.adb.org{title_elem['href']}",
                'external_id': self._extract_project_id(title_elem['href']),
                'country': row.select_one('.views-field-field-countries')?.text.strip(),
                'sector': row.select_one('.views-field-field-sectors')?.text.strip(),
                'deadline': self._parse_date(row.select_one('.views-field-field-closing-date')?.text),
                'procurement_type': row.select_one('.views-field-field-notice-type')?.text.strip(),
            }
        except Exception as e:
            logger.error(f"Failed to parse list item: {e}")
            return None
    
    def _extract_project_id(self, url: str) -> str:
        """从URL提取项目ID"""
        # /projects/12345-project-name -> 12345
        import re
        match = re.search(r'/projects/(\d+)', url)
        return match.group(1) if match else ""
    
    def _parse_date(self, date_str: str | None) -> datetime | None:
        """解析日期字符串"""
        if not date_str:
            return None
        try:
            # ADB日期格式: "15 Jan 2026"
            return datetime.strptime(date_str.strip(), "%d %b %Y")
        except ValueError:
            return None
    
    async def fetch_detail(self, url: str) -> Dict[str, Any]:
        """获取详情页（后续实现）"""
        pass
    
    async def fetch_all_pages(self, max_pages: int = 10) -> List[Dict[str, Any]]:
        """获取所有页面数据"""
        all_items = []
        
        for page in range(1, max_pages + 1):
            items = await self.fetch_list(page)
            if not items:
                break
            all_items.extend(items)
            logger.info(f"Fetched page {page}, got {len(items)} items")
        
        return all_items
```

#### 依赖
- M2-01

---

### M2-04: ADB详情页爬虫 (Mini-Agent)
**优先级**: P0  
**预估时间**: 3小时  
**执行者**: Mini-Agent

#### 描述
实现ADB招标详情页爬取，获取完整信息。

#### 验收标准
- [ ] 获取完整项目描述
- [ ] 获取预算信息
- [ ] 获取文档下载链接
- [ ] 处理不同页面结构

#### 输出文件
- `backend/app/crawler/adb/detail_crawler.py`

#### 依赖
- M2-03

---

### M2-05: 数据清洗与存储 (Mini-Agent)
**优先级**: P0  
**预估时间**: 3小时  
**执行者**: Mini-Agent

#### 描述
实现数据清洗和数据库存储逻辑。

#### 验收标准
- [ ] 数据去重（基于external_id）
- [ ] 字段标准化
- [ ] 增量更新逻辑
- [ ] 事务处理正确

#### 输出文件
- `backend/app/crawler/pipeline.py`
- `backend/app/services/opportunity_service.py`

#### 代码实现
```python
# app/crawler/pipeline.py
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from app.models.opportunity import BidOpportunity
from app.core.logging import logger

class DataPipeline:
    """数据处理管道"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def process(self, items: List[Dict[str, Any]], source: str) -> int:
        """处理并存储数据"""
        cleaned = [self._clean(item, source) for item in items if item]
        
        # 使用upsert避免重复
        stmt = insert(BidOpportunity).values(cleaned)
        stmt = stmt.on_conflict_do_update(
            index_elements=['source', 'external_id'],
            set_={
                'title': stmt.excluded.title,
                'description': stmt.excluded.description,
                'deadline': stmt.excluded.deadline,
                'status': stmt.excluded.status,
                'raw_data': stmt.excluded.raw_data,
                'updated_at': func.now(),
            }
        )
        
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        logger.info(f"Processed {len(cleaned)} items")
        return result.rowcount
    
    def _clean(self, item: Dict[str, Any], source: str) -> Dict[str, Any]:
        """清洗单条数据"""
        return {
            'source': source,
            'external_id': item['external_id'],
            'url': item['url'],
            'title': item['title'][:500] if item.get('title') else '',
            'description': item.get('description'),
            'organization': item.get('organization'),
            'published_at': item.get('published_at'),
            'deadline': item.get('deadline'),
            'budget_min': item.get('budget_min'),
            'budget_max': item.get('budget_max'),
            'currency': item.get('currency', 'USD'),
            'location': item.get('location'),
            'country': item.get('country'),
            'sector': item.get('sector'),
            'procurement_type': item.get('procurement_type'),
            'status': self._determine_status(item),
            'raw_data': item,
        }
    
    def _determine_status(self, item: Dict[str, Any]) -> str:
        """判断状态"""
        from datetime import datetime
        deadline = item.get('deadline')
        if deadline and deadline < datetime.now():
            return 'closed'
        return 'open'
```

#### 依赖
- M2-02, M2-03

---

### M2-06: 定时调度任务 (Opus 4.5)
**优先级**: P1  
**预估时间**: 3小时  
**执行者**: Opus 4.5

#### 描述
配置Celery定时任务，实现自动爬取。

#### 验收标准
- [ ] Celery Worker正常启动
- [ ] 定时任务按计划执行
- [ ] 任务失败重试
- [ ] 任务执行日志

#### 输出文件
- `backend/app/celery_app.py`
- `backend/app/tasks/crawler_tasks.py`

#### 代码实现
```python
# app/celery_app.py
from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "bidagent",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1小时超时
)

# 定时任务配置
celery_app.conf.beat_schedule = {
    'crawl-adb-daily': {
        'task': 'app.tasks.crawler_tasks.crawl_adb',
        'schedule': crontab(hour=6, minute=0),  # 每天6点
    },
    'update-opportunity-status': {
        'task': 'app.tasks.crawler_tasks.update_status',
        'schedule': crontab(hour='*/4'),  # 每4小时
    },
}


# app/tasks/crawler_tasks.py
from app.celery_app import celery_app
from app.crawler.adb.list_crawler import ADBListCrawler
from app.crawler.pipeline import DataPipeline
from app.db.session import async_session
from app.core.logging import logger

@celery_app.task(bind=True, max_retries=3)
def crawl_adb(self):
    """爬取ADB招标信息"""
    import asyncio
    asyncio.run(_crawl_adb_async())

async def _crawl_adb_async():
    crawler = ADBListCrawler(rate_limit=2.0)
    
    try:
        items = await crawler.fetch_all_pages(max_pages=20)
        logger.info(f"Fetched {len(items)} items from ADB")
        
        async with async_session() as db:
            pipeline = DataPipeline(db)
            count = await pipeline.process(items, source='adb')
            logger.info(f"Stored {count} items")
    
    finally:
        await crawler.close()

@celery_app.task
def update_status():
    """更新过期机会状态"""
    import asyncio
    asyncio.run(_update_status_async())

async def _update_status_async():
    from sqlalchemy import update
    from datetime import datetime
    from app.models.opportunity import BidOpportunity
    
    async with async_session() as db:
        stmt = update(BidOpportunity).where(
            BidOpportunity.deadline < datetime.now(),
            BidOpportunity.status == 'open'
        ).values(status='closed')
        
        result = await db.execute(stmt)
        await db.commit()
        logger.info(f"Updated {result.rowcount} opportunities to closed")
```

#### 依赖
- M2-05, M0-04 (Redis)

---

### M2-07: 招标机会API (Mini-Agent)
**优先级**: P1  
**预估时间**: 3小时  
**执行者**: Mini-Agent

#### 描述
实现招标机会列表和详情API。

#### 验收标准
- [ ] GET /api/v1/opportunities 列表接口
- [ ] GET /api/v1/opportunities/{id} 详情接口
- [ ] 分页、排序、筛选功能
- [ ] 全文搜索功能

#### API实现
```python
# app/api/v1/opportunities.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from app.models.opportunity import BidOpportunity
from app.schemas.opportunity import OpportunityList, OpportunityDetail
from app.api.deps import get_db, get_current_user

router = APIRouter()

@router.get("", response_model=OpportunityList)
async def list_opportunities(
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user),
    source: Optional[str] = None,
    status: str = "open",
    sector: Optional[str] = None,
    country: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """获取招标机会列表"""
    query = select(BidOpportunity)
    
    # 筛选条件
    if source:
        query = query.where(BidOpportunity.source == source)
    if status:
        query = query.where(BidOpportunity.status == status)
    if sector:
        query = query.where(BidOpportunity.sector == sector)
    if country:
        query = query.where(BidOpportunity.country == country)
    
    # 全文搜索
    if search:
        query = query.where(
            BidOpportunity.search_vector.match(search)
        )
    
    # 总数
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    
    # 分页
    query = query.order_by(BidOpportunity.deadline.asc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }
```

#### 依赖
- M2-02, M1-02

---

### M2-08: 爬虫监控与告警 (Mini-Agent)
**优先级**: P2  
**预估时间**: 2小时  
**执行者**: Mini-Agent

#### 描述
实现爬虫执行监控和告警。

#### 验收标准
- [ ] 任务执行日志记录
- [ ] 失败告警通知
- [ ] 执行统计报表
- [ ] 健康检查端点

#### 依赖
- M2-06

---

## 里程碑检查点

### 完成标准
- [ ] ADB数据可自动入库
- [ ] 定时任务正常运行
- [ ] API可查询招标机会
- [ ] 监控告警可用

### 交付物
1. 完整的ADB爬虫
2. 数据处理管道
3. 定时调度任务
4. 招标机会API

---

## 风险与注意事项

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| 网站结构变更 | 中 | 高 | 监控告警，快速响应 |
| IP被封 | 低 | 高 | 控制频率，使用代理池 |
| 数据格式异常 | 中 | 中 | 容错处理，日志记录 |

### 法律合规
- 遵守robots.txt
- 控制爬取频率
- 仅爬取公开数据
