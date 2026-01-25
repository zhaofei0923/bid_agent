# BidAgent 学习计划

## 学习目标

在开始开发 BidAgent 之前，需要掌握以下技术栈。本学习计划以**视频教程**为主，辅以官方文档和实践项目。

---

## 技术栈概览

| 技术 | 用途 | 优先级 | 预计学习时间 |
|------|------|--------|-------------|
| Next.js 15 | 前端框架 | P0 | 3天 |
| FastAPI | 后端框架 | P0 | 2天 |
| LangChain + LangGraph | LLM编排 | P0 | 4天 |
| PostgreSQL + pgvector | 数据库 | P1 | 2天 |
| Docker | 容器化 | P1 | 1天 |
| Tailwind + shadcn/ui | UI组件 | P1 | 1天 |
| Celery | 任务队列 | P2 | 1天 |

**总计**: 约 2 周（14天）

---

## Week 1: 核心框架

### Day 1-2: FastAPI 基础

**视频教程**

| 平台 | 课程 | 时长 | 语言 |
|------|------|------|------|
| YouTube | [FastAPI Full Course - Amigoscode](https://www.youtube.com/watch?v=GN6ICac3OXY) | 5h | EN |
| YouTube | [FastAPI 完整教程 - 码农高天](https://www.youtube.com/watch?v=XnYYwcOfcn8) | 3h | 中文 |
| B站 | [FastAPI从入门到实战](https://www.bilibili.com/video/BV1iN411X72b) | 8h | 中文 |

**学习重点**
- [ ] 路由和路径参数
- [ ] Pydantic数据验证
- [ ] 依赖注入 (Depends)
- [ ] 异步处理 (async/await)
- [ ] 中间件和错误处理
- [ ] OAuth2 JWT认证

**实践任务**
```python
# 完成一个简单的 Todo API
# - POST /todos - 创建待办
# - GET /todos - 获取列表
# - PUT /todos/{id} - 更新
# - DELETE /todos/{id} - 删除
# - 使用 Pydantic 模型
# - 实现 JWT 认证
```

---

### Day 3-5: Next.js 15 App Router

**视频教程**

| 平台 | 课程 | 时长 | 语言 |
|------|------|------|------|
| YouTube | [Next.js 14/15 Full Course - JavaScript Mastery](https://www.youtube.com/watch?v=wm5gMKuwSYk) | 5h | EN |
| YouTube | [Next.js App Router - Traversy Media](https://www.youtube.com/watch?v=ZjAqacIC_3c) | 1h | EN |
| B站 | [Next.js 14完整教程](https://www.bilibili.com/video/BV1Lg4y1w7fC) | 6h | 中文 |

**学习重点**
- [ ] App Router 目录结构
- [ ] Server Components vs Client Components
- [ ] 数据获取 (fetch, Server Actions)
- [ ] 路由和导航
- [ ] 布局和模板
- [ ] 中间件
- [ ] API Routes

**实践任务**
```typescript
// 创建一个简单的博客应用
// - 文章列表页 (SSR)
// - 文章详情页 (动态路由)
// - 登录页面 (Client Component)
// - 使用 Server Actions 创建文章
```

---

### Day 6-7: Tailwind CSS + shadcn/ui

**视频教程**

| 平台 | 课程 | 时长 | 语言 |
|------|------|------|------|
| YouTube | [Tailwind CSS Full Course - Dave Gray](https://www.youtube.com/watch?v=lCxcTsOHrjo) | 4h | EN |
| YouTube | [shadcn/ui Tutorial - Web Dev Simplified](https://www.youtube.com/watch?v=7MKEOfSP2s4) | 30m | EN |
| B站 | [Tailwind CSS速成](https://www.bilibili.com/video/BV1Zf4y1P7Dq) | 2h | 中文 |

**学习重点**
- [ ] Tailwind 工具类
- [ ] 响应式设计
- [ ] 暗色模式
- [ ] shadcn/ui 安装配置
- [ ] 常用组件使用

**实践任务**
```bash
# 使用 shadcn/ui 构建一个仪表盘布局
# - 侧边栏
# - 顶部导航
# - 卡片组件
# - 表格组件
# - 表单组件
```

---

## Week 2: LLM 和数据库

### Day 8-10: LangChain + LangGraph

**视频教程**

| 平台 | 课程 | 时长 | 语言 |
|------|------|------|------|
| YouTube | [LangChain Full Course - FreeCodeCamp](https://www.youtube.com/watch?v=HSZ_uaif57o) | 4h | EN |
| YouTube | [LangGraph Tutorial - Sam Witteveen](https://www.youtube.com/watch?v=R8KB-Zcynxc) | 1h | EN |
| YouTube | [LangGraph Agents Deep Dive](https://www.youtube.com/watch?v=bq1Plo2RhYI) | 2h | EN |
| B站 | [LangChain中文教程](https://www.bilibili.com/video/BV1zu4y1Z7mc) | 5h | 中文 |

**官方资源**
- [LangChain 文档](https://python.langchain.com/docs/)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [LangChain Cookbook](https://github.com/langchain-ai/langchain/tree/master/cookbook)

**学习重点**
- [ ] LangChain 基本概念 (LLM, Chain, Agent)
- [ ] Prompt Templates
- [ ] Output Parsers
- [ ] Document Loaders
- [ ] Text Splitters
- [ ] Embeddings 和 Vector Stores
- [ ] LangGraph 状态机
- [ ] LangGraph 节点和边
- [ ] 人机交互 (Human-in-the-loop)

**实践任务**
```python
# 构建一个简单的 RAG 应用
# 1. 加载 PDF 文档
# 2. 分割文本
# 3. 创建向量存储
# 4. 实现问答功能

# 构建一个 LangGraph 工作流
# 1. 定义状态
# 2. 创建节点
# 3. 添加条件边
# 4. 实现多步骤任务
```

---

### Day 11-12: PostgreSQL + pgvector

**视频教程**

| 平台 | 课程 | 时长 | 语言 |
|------|------|------|------|
| YouTube | [PostgreSQL Tutorial - Programming with Mosh](https://www.youtube.com/watch?v=qw--VYLpxG4) | 4h | EN |
| YouTube | [pgvector Tutorial - Supabase](https://www.youtube.com/watch?v=ibzlEQmgPPY) | 30m | EN |
| B站 | [PostgreSQL入门到精通](https://www.bilibili.com/video/BV1av411s7Ry) | 6h | 中文 |

**学习重点**
- [ ] SQL 基础复习
- [ ] PostgreSQL 特性
- [ ] 索引和性能优化
- [ ] pgvector 安装
- [ ] 向量相似度搜索
- [ ] SQLAlchemy 2.x 异步

**实践任务**
```sql
-- 创建带向量列的表
CREATE EXTENSION vector;

CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    content TEXT,
    embedding vector(1536)
);

-- 创建索引
CREATE INDEX ON documents 
USING ivfflat (embedding vector_cosine_ops);

-- 相似度查询
SELECT content 
FROM documents 
ORDER BY embedding <=> $1 
LIMIT 5;
```

---

### Day 13: Docker 基础

**视频教程**

| 平台 | 课程 | 时长 | 语言 |
|------|------|------|------|
| YouTube | [Docker Crash Course - Traversy Media](https://www.youtube.com/watch?v=Kyx2PsuwomE) | 1h | EN |
| YouTube | [Docker Compose Tutorial](https://www.youtube.com/watch?v=HG6yIjZapSA) | 2h | EN |
| B站 | [Docker从入门到实践](https://www.bilibili.com/video/BV1og4y1q7M4) | 3h | 中文 |

**学习重点**
- [ ] Docker 基本概念
- [ ] Dockerfile 编写
- [ ] Docker Compose
- [ ] 多容器编排
- [ ] 数据卷和网络

**实践任务**
```yaml
# docker-compose.yml
# 编排以下服务:
# - PostgreSQL
# - Redis
# - FastAPI 后端
# - Next.js 前端
```

---

### Day 14: Celery + Redis

**视频教程**

| 平台 | 课程 | 时长 | 语言 |
|------|------|------|------|
| YouTube | [Celery with FastAPI - Very Academy](https://www.youtube.com/watch?v=Nal6KCkwKLc) | 1h | EN |
| B站 | [Celery分布式任务队列](https://www.bilibili.com/video/BV1nE411L7jP) | 2h | 中文 |

**学习重点**
- [ ] Celery 基本概念
- [ ] Task 定义
- [ ] 定时任务 (Beat)
- [ ] 与 FastAPI 集成
- [ ] 任务监控

**实践任务**
```python
# 实现一个异步任务
# 1. 配置 Celery
# 2. 创建后台任务
# 3. 在 FastAPI 中触发
# 4. 查询任务状态
```

---

## 补充学习资源

### 官方文档

| 技术 | 文档链接 |
|------|----------|
| Next.js | https://nextjs.org/docs |
| FastAPI | https://fastapi.tiangolo.com/ |
| LangChain | https://python.langchain.com/docs/ |
| LangGraph | https://langchain-ai.github.io/langgraph/ |
| Tailwind CSS | https://tailwindcss.com/docs |
| shadcn/ui | https://ui.shadcn.com/docs |
| PostgreSQL | https://www.postgresql.org/docs/ |
| Celery | https://docs.celeryq.dev/ |

### 推荐 YouTube 频道

| 频道 | 内容方向 |
|------|----------|
| [Fireship](https://www.youtube.com/@Fireship) | 快速技术概览 |
| [Traversy Media](https://www.youtube.com/@TraversyMedia) | Web开发教程 |
| [Web Dev Simplified](https://www.youtube.com/@WebDevSimplified) | 前端深入 |
| [Sam Witteveen](https://www.youtube.com/@samwitteveenai) | LLM/AI应用 |
| [码农高天](https://www.youtube.com/@benny-gg) | Python中文 |

### 推荐 B站 UP主

| UP主 | 内容方向 |
|------|----------|
| [技术胖](https://space.bilibili.com/165659472) | 全栈教程 |
| [峰华前端工程师](https://space.bilibili.com/302954484) | 前端技术 |
| [Python小甲鱼](https://space.bilibili.com/314076440) | Python基础 |

---

## 学习检查清单

### Week 1 完成标准

- [ ] 能独立创建 FastAPI 项目并实现 CRUD API
- [ ] 理解 FastAPI 依赖注入和 JWT 认证
- [ ] 能使用 Next.js App Router 创建页面
- [ ] 理解 Server/Client Components 区别
- [ ] 能使用 Tailwind 构建响应式布局
- [ ] 能使用 shadcn/ui 组件

### Week 2 完成标准

- [ ] 理解 LangChain 核心概念
- [ ] 能实现简单的 RAG 应用
- [ ] 理解 LangGraph 状态机工作原理
- [ ] 能设计并实现多步骤 Agent 工作流
- [ ] 能使用 pgvector 进行向量搜索
- [ ] 能编写 Docker Compose 文件
- [ ] 能配置 Celery 异步任务

---

## 学习建议

### 1. 视频 + 实践结合

```
观看视频 (30%) → 跟着敲代码 (40%) → 独立实践 (30%)
```

### 2. 建立知识连接

学习新技术时，思考如何在 BidAgent 中应用：
- FastAPI → 用户认证、积分扣费 API
- Next.js → 前端页面和表单
- LangChain → TOR 分析、内容生成
- PostgreSQL → 数据存储
- Celery → 爬虫定时任务

### 3. 记录学习笔记

使用 Notion 或 Obsidian 记录：
- 核心概念
- 常见问题
- 代码片段
- 踩坑经验

### 4. 不要过度追求完美

MVP 阶段，够用即可：
- 不需要掌握所有 API
- 先理解核心概念
- 实际开发中再深入

---

## 进阶学习 (开发后期)

### 性能优化
- [ ] Next.js 性能优化 (ISR, 缓存)
- [ ] FastAPI 性能优化 (连接池, 缓存)
- [ ] PostgreSQL 查询优化

### 测试
- [ ] pytest 单元测试
- [ ] Playwright E2E 测试
- [ ] React Testing Library

### 部署运维
- [ ] GitHub Actions CI/CD
- [ ] Docker 生产配置
- [ ] 监控告警 (Prometheus/Grafana)

---

## 时间安排模板

```
每日学习计划 (4-6小时)
├── 上午 (2-3h)
│   ├── 观看视频教程
│   └── 跟着敲代码
├── 下午 (2-3h)
│   ├── 独立实践任务
│   └── 查阅文档解决问题
└── 晚上 (可选)
    └── 整理笔记/复习
```

祝学习顺利！🚀
