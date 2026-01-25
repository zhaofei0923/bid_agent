# BidAgent 文档驱动开发工作流指南

> 本文档详细说明如何使用 **文档驱动开发模式**，以 Mini-Agent (CLI) 为核心执行者，
> 配合 Opus 4.5 (架构/审查) 和 Claude Code (补充编码) 进行 BidAgent 项目开发。

---

## 目录

1. [开发模式概述](#1-开发模式概述)
2. [文档驱动开发核心流程](#2-文档驱动开发核心流程)
3. [任务文档编写规范](#3-任务文档编写规范)
4. [Mini-Agent CLI 使用详解](#4-mini-agent-cli-使用详解)
5. [Opus 4.5 使用场景](#5-opus-45-使用场景)
6. [Claude Code 使用场景](#6-claude-code-使用场景)
7. [多 AI 协作工作流示例](#7-多-ai-协作工作流示例)
8. [代码审查与验收](#8-代码审查与验收)
9. [Prompt 模板库](#9-prompt-模板库)

---

## 1. 开发模式概述

### 1.1 文档驱动开发理念

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      文档驱动开发 (Doc-Driven Development)              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   核心理念: 先写文档，后写代码                                          │
│                                                                         │
│   ┌──────────────┐      ┌──────────────┐      ┌──────────────┐         │
│   │  任务规格文档 │─────▶│  Mini-Agent  │─────▶│   代码产出   │         │
│   │ (task-specs) │      │  读取并执行  │      │  (自动生成)  │         │
│   └──────────────┘      └──────────────┘      └──────────────┘         │
│          ▲                                           │                  │
│          │                                           ▼                  │
│   ┌──────────────┐                           ┌──────────────┐          │
│   │  Opus 4.5    │◀──────────────────────────│  审查迭代    │          │
│   │ (文档编写)   │                           │              │          │
│   └──────────────┘                           └──────────────┘          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 AI 角色分工

| AI 工具 | 角色定位 | 输入 | 输出 | 使用方式 |
|---------|---------|------|------|---------|
| **Mini-Agent** | 主执行者 | 任务文档路径 | 代码实现 | CLI 命令 |
| **Opus 4.5** | 架构师/文档作者 | 需求描述 | 任务文档、设计方案 | Copilot Chat |
| **Claude Code** | 补充编码助手 | 具体编码问题 | 代码片段、调试 | 独立客户端 |

### 1.3 协作模型

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         AI 协作模型                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   👨‍💻 开发者（你）                                                       │
│   ├── 需求分析与决策                                                    │
│   ├── 触发 Mini-Agent 执行任务                                         │
│   ├── 最终代码审查与验收                                                │
│   └── 部署与发布                                                        │
│                                                                         │
│   🧠 Opus 4.5（Copilot Chat - 架构师 & 文档作者）                       │
│   ├── 编写/审查任务规格文档                                             │
│   ├── 复杂架构设计                                                      │
│   ├── 技术方案评审                                                      │
│   └── 代码质量审查                                                      │
│                                                                         │
│   🤖 Mini-Agent（CLI - 主执行者）                                       │
│   ├── 读取 task-specs 文档                                             │
│   ├── 自动分解任务                                                      │
│   ├── 调度子代理执行                                                    │
│   ├── 代码生成与文件操作                                                │
│   └── 测试执行                                                          │
│                                                                         │
│   ⚡ Claude Code（独立客户端 - 补充编码）                               │
│   ├── 交互式代码修改                                                    │
│   ├── 实时调试                                                          │
│   ├── 快速原型验证                                                      │
│   └── Mini-Agent 遗漏的细节补充                                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.4 使用场景决策树

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         何时使用哪个 AI？                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  需要完成一个开发任务?                                                  │
│       │                                                                 │
│       ├── 有标准化任务文档? ──────────────▶ Mini-Agent CLI             │
│       │         │                                                       │
│       │         └── 没有 ──────────────────▶ Opus 4.5 编写文档         │
│       │                                          │                      │
│       │                                          ▼                      │
│       │                                     Mini-Agent CLI              │
│       │                                                                 │
│  需要架构设计/技术方案?                                                 │
│       │                                                                 │
│       └────────────────────────────────────▶ Opus 4.5                  │
│                                                                         │
│  需要快速调试/交互式修改?                                               │
│       │                                                                 │
│       └────────────────────────────────────▶ Claude Code               │
│                                                                         │
│  代码审查/质量检查?                                                     │
│       │                                                                 │
│       └────────────────────────────────────▶ Opus 4.5                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 文档驱动开发核心流程

### 2.1 标准开发循环

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         标准开发循环                                    │
│                                                                         │
│    ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐    │
│    │ 1.编写   │────▶│ 2.执行   │────▶│ 3.补充   │────▶│ 4.审查   │    │
│    │ 任务文档 │     │Mini-Agent│     │Claude Cd │     │ Opus4.5  │    │
│    │(Opus4.5) │     │  (CLI)   │     │ (可选)   │     │          │    │
│    └──────────┘     └──────────┘     └──────────┘     └──────────┘    │
│         │                                                   │          │
│         │              ┌──────────┐                         │          │
│         └──────────────│ 5.验收   │◀────────────────────────┘          │
│                        │  (你)    │                                    │
│                        └──────────┘                                    │
│                             │                                          │
│                             ▼                                          │
│                      通过? ─────▶ 提交代码                             │
│                        │                                               │
│                        └── 否 ──▶ 返回步骤 1/2/3                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 详细流程说明

#### Step 1: 编写任务文档 (Opus 4.5)

**在 VS Code Copilot Chat 中使用 Opus 4.5 编写任务规格：**

```
我需要为 BidAgent 项目编写一个任务规格文档。

## 任务概述
实现用户注册接口

## 请按照 docs/task-spec-template.md 的格式生成任务文档，包含：
1. YAML Front Matter 元信息
2. 描述章节
3. 输入/输出文件
4. 验收标准 (AC-N 格式)
5. 详细实现步骤
6. 代码模板

## 技术约束
- 后端: FastAPI + SQLAlchemy 2.x + Pydantic 2.x
- 参考: docs/architecture/data-model.md
```

#### Step 2: Mini-Agent 执行 (CLI)

```bash
# Mini-Agent 读取任务文档并执行
mini-agent run docs/task-specs/M1-user-system/README.md --task M1-03

# 或执行整个里程碑
mini-agent run docs/task-specs/M1-user-system/README.md --all

# 查看执行状态
mini-agent status
```

#### Step 3: Claude Code 补充 (可选)

当 Mini-Agent 完成主要实现后，使用 Claude Code 进行交互式补充：

- 修复细节问题
- 调整代码风格
- 添加遗漏的边界处理
- 实时调试

#### Step 4: Opus 4.5 审查

```
请审查 Mini-Agent 生成的代码。

## 任务规格
docs/task-specs/M1-user-system/README.md 中的 M1-03

## 生成的文件
- backend/app/schemas/auth.py
- backend/app/services/auth_service.py
- backend/app/api/v1/auth.py
- backend/tests/api/test_auth.py

## 审查要点
1. 是否满足所有验收标准
2. 代码规范符合性
3. 安全性检查
4. 性能评估
```

#### Step 5: 你的验收

- 运行测试确认通过
- 手动测试关键功能
- 确认代码质量
- 提交并推送

---

## 3. 任务文档编写规范

> 详细模板请参考 [docs/task-spec-template.md](./task-spec-template.md)

### 3.1 文档结构概览

任务文档必须包含以下结构以便 Mini-Agent 正确解析：

```markdown
---
# YAML Front Matter (必需)
id: M1-03
title: 注册接口
executor: mini-agent
priority: P0
estimated_hours: 2
task_type: coding
dependencies: [M1-01, M1-02]
outputs:
  - backend/app/schemas/auth.py
  - backend/app/services/auth_service.py
  - backend/app/api/v1/auth.py
acceptance_criteria:
  - POST /api/v1/auth/register 可用
  - 邮箱唯一性检查
  - 密码强度验证
---

## 描述
[任务描述]

## 输入
[前置条件]

## 输出文件
[文件列表]

## 验收标准
- [ ] AC-1: ...
- [ ] AC-2: ...

## 详细步骤
1. ...
2. ...

## 代码模板
```

### 3.2 关键字段说明

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `id` | string | ✅ | 任务唯一标识，格式 `M{X}-{YY}` |
| `executor` | enum | ✅ | `mini-agent` 或 `opus` |
| `priority` | enum | ✅ | `P0` (阻塞) / `P1` (重要) / `P2` (一般) |
| `task_type` | enum | ✅ | `coding` / `testing` / `documentation` / `design` / `research` |
| `dependencies` | array | ❌ | 依赖的任务 ID 列表 |
| `outputs` | array | ✅ | 输出文件路径列表 |
| `acceptance_criteria` | array | ✅ | 验收标准列表 |

### 3.3 task_type 与子代理映射

Mini-Agent 根据 `task_type` 自动路由到专业子代理：

| task_type | 子代理 | 专长 |
|-----------|--------|------|
| `coding` | Coder | 代码编写、重构 |
| `testing` | Tester | 测试设计、自动化测试 |
| `documentation` | Documenter | 技术文档编写 |
| `design` | Architect | 系统架构设计 |
| `research` | Researcher | 信息收集、技术调研 |

---

## 4. Mini-Agent CLI 使用详解

### 4.1 基础命令

```bash
# 查看帮助
mini-agent --help

# 查看版本
mini-agent --version

# 执行单个任务
mini-agent run <task-doc-path> --task <task-id>

# 执行整个文档中的所有任务
mini-agent run <task-doc-path> --all

# 仅执行 mini-agent 标记的任务
mini-agent run <task-doc-path> --executor mini-agent

# 查看任务执行状态
mini-agent status

# 查看任务依赖图
mini-agent deps <task-doc-path>
```

### 4.2 典型使用场景

#### 场景 A: 执行单个任务

```bash
# 执行 M1-03 用户注册接口任务
mini-agent run docs/task-specs/M1-user-system/README.md --task M1-03

# Mini-Agent 会：
# 1. 解析 YAML Front Matter
# 2. 检查依赖任务状态
# 3. 路由到 Coder 子代理
# 4. 按详细步骤执行
# 5. 生成输出文件
# 6. 报告执行结果
```

#### 场景 B: 批量执行里程碑任务

```bash
# 执行 M1 里程碑所有 mini-agent 任务
mini-agent run docs/task-specs/M1-user-system/README.md \
  --executor mini-agent \
  --parallel

# --parallel: 允许无依赖关系的任务并行执行
```

#### 场景 C: 增量执行（跳过已完成）

```bash
# 仅执行未完成的任务
mini-agent run docs/task-specs/M1-user-system/README.md \
  --skip-completed
```

### 4.3 执行选项

| 选项 | 说明 |
|------|------|
| `--task <id>` | 指定执行单个任务 |
| `--all` | 执行文档中所有任务 |
| `--executor <type>` | 过滤执行者类型 |
| `--parallel` | 允许并行执行 |
| `--skip-completed` | 跳过已完成任务 |
| `--dry-run` | 仅解析不执行 |
| `--verbose` | 详细日志输出 |
| `--timeout <seconds>` | 设置超时时间 |

### 4.4 执行结果处理

Mini-Agent 执行完成后会生成报告：

```
┌─────────────────────────────────────────────────────────────────┐
│                    Mini-Agent 执行报告                          │
├─────────────────────────────────────────────────────────────────┤
│  任务: M1-03 注册接口                                           │
│  状态: ✅ 成功                                                  │
│  耗时: 45s                                                      │
│                                                                 │
│  生成文件:                                                      │
│  ✅ backend/app/schemas/auth.py                                 │
│  ✅ backend/app/services/auth_service.py                        │
│  ✅ backend/app/api/v1/auth.py                                  │
│  ✅ backend/tests/api/test_auth.py                              │
│                                                                 │
│  验收标准:                                                      │
│  ✅ AC-1: POST /api/v1/auth/register 可用                       │
│  ✅ AC-2: 邮箱唯一性检查                                        │
│  ✅ AC-3: 密码强度验证                                          │
│  ⚠️ AC-4: 测试覆盖率 > 80% (当前: 75%)                          │
│                                                                 │
│  建议: 使用 Claude Code 补充测试用例                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Opus 4.5 使用场景

> Opus 4.5 通过 VS Code GitHub Copilot Chat 访问，选择 Claude Opus 4.5 模型。

### 5.1 核心使用场景

#### 场景 A: 编写任务规格文档

**什么时候用**: 开始新功能开发，需要创建 Mini-Agent 可读取的任务文档

```
我需要为 BidAgent 项目编写任务规格文档。

## 功能需求
实现标书版本历史管理功能，支持：
- 记录每次修改
- 版本对比
- 版本回滚

## 请按照 docs/task-spec-template.md 格式生成，包含：
1. YAML Front Matter
2. 完整的验收标准 (AC-N 格式)
3. 详细实现步骤
4. SQLAlchemy 模型代码模板
5. API 路由代码模板

## 技术约束
- 参考 docs/architecture/data-model.md
- 遵循 docs/coding-standards.md
```

#### 场景 B: 架构设计

**什么时候用**: 需要设计新模块架构，在编写任务文档之前

```
我需要设计 BidAgent 的 Agent 调度模块架构。

## 背景
- 技术栈: FastAPI + LangGraph + DeepSeek
- 参考: docs/architecture/agent-workflow.md

## 需求
- 管理多个 LangGraph Agent 生命周期
- 支持并发任务处理
- 任务队列和优先级调度
- 状态监控和日志

## 请提供
1. 模块目录结构
2. 核心类/接口定义
3. 数据流图
4. 与现有模块的交互方式
```

#### 场景 C: 代码审查

**什么时候用**: Mini-Agent 完成实现后，进行质量审查

```
请审查以下由 Mini-Agent 生成的代码。

## 任务信息
- 任务 ID: M1-03
- 任务文档: docs/task-specs/M1-user-system/README.md

## 生成的文件
[粘贴或列出文件内容]

## 审查要点
1. 是否满足所有验收标准
2. 安全性检查（这是认证模块）
3. 代码规范 (docs/coding-standards.md)
4. 性能评估
5. 改进建议
```

#### 场景 D: 疑难问题诊断

**什么时候用**: 遇到复杂 bug 或技术难题

```
我遇到了一个问题需要帮助诊断。

## 问题描述
用户登录后 JWT Token 验证偶尔失败

## 错误信息
```
[错误堆栈]
```

## 相关代码
```python
[代码片段]
```

## 环境信息
- Python: 3.11
- FastAPI: 0.109.0
- Ubuntu 22.04

## 已尝试
1. 检查 Token 过期时间
2. 验证密钥配置

请分析可能的原因和解决方案。
```

---

## 6. Claude Code 使用场景

> Claude Code 通过独立客户端访问，由 minimax-m2.1 模型驱动。

### 6.1 核心使用场景

#### 场景 A: 交互式代码修改

**什么时候用**: 需要实时修改代码并立即看到效果

```
Mini-Agent 生成的 auth_service.py 需要调整：

1. 添加邮箱格式验证
2. 密码强度检查需要包含特殊字符要求
3. 添加注册限流逻辑

请直接修改文件。
```

#### 场景 B: 实时调试

**什么时候用**: 代码运行出错，需要交互式调试

```
运行测试时 test_user_register 失败：

AssertionError: 期望状态码 201，实际 422

请帮我：
1. 分析失败原因
2. 修复代码
3. 重新运行测试验证
```

#### 场景 C: 补充 Mini-Agent 遗漏

**什么时候用**: Mini-Agent 完成大部分工作，需要补充细节

```
Mini-Agent 生成的注册接口缺少以下内容：

1. 邮箱验证码发送逻辑
2. 注册成功后的欢迎邮件
3. 操作日志记录

请补充这些功能。
```

#### 场景 D: 快速原型验证

**什么时候用**: 需要快速验证某个技术方案可行性

```
我想验证使用 Redis 实现 JWT Token 黑名单的方案：

1. 写一个最小验证代码
2. 运行测试
3. 评估性能
```

---

## 7. 多 AI 协作工作流示例

### 7.1 完整示例: 实现用户注册功能

#### Phase 1: Opus 4.5 编写任务文档

**你在 Copilot Chat 中:**
```
请为 BidAgent 项目编写用户注册功能的任务规格文档。

## 功能需求
- 用户通过邮箱和密码注册
- 邮箱唯一性检查
- 密码强度验证 (至少8位，包含大小写和数字)
- 注册成功返回 JWT Token

## 请按照 docs/task-spec-template.md 格式生成
## 参考 docs/architecture/data-model.md 中的 User 模型
```

**Opus 4.5 输出任务文档后，保存到 `docs/task-specs/M1-user-system/README.md`**

#### Phase 2: Mini-Agent 执行

```bash
# 执行注册接口任务
mini-agent run docs/task-specs/M1-user-system/README.md --task M1-03 --verbose

# 查看执行进度
mini-agent status

# 执行完成后查看报告
```

#### Phase 3: Claude Code 补充

**Mini-Agent 报告显示 AC-4 (测试覆盖率) 未达标**

在 Claude Code 中:
```
Mini-Agent 生成的 test_auth.py 测试覆盖率为 75%，需要达到 80%。

请补充以下测试用例：
1. 测试重复邮箱注册
2. 测试密码强度不足
3. 测试邮箱格式错误
4. 测试空字段提交

文件位置: backend/tests/api/test_auth.py
```

#### Phase 4: Opus 4.5 审查

**你在 Copilot Chat 中:**
```
请审查用户注册功能的完整实现。

## 文件列表
- backend/app/schemas/auth.py
- backend/app/services/auth_service.py
- backend/app/api/v1/auth.py
- backend/tests/api/test_auth.py

## 审查重点
1. 安全性 (密码处理、输入验证)
2. 代码规范
3. 错误处理完整性
4. 测试覆盖度
```

**Opus 4.5 审查反馈后，如有问题，返回 Phase 2 或 3 修复**

#### Phase 5: 你的验收

```bash
# 运行测试
cd backend && pytest tests/api/test_auth.py -v --cov=app.api.v1.auth

# 启动服务手动测试
uvicorn app.main:app --reload

# 使用 curl 或 Postman 测试接口
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "Test123456", "name": "Test User"}'
```

### 7.2 协作时序图

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│   你    │     │Opus 4.5 │     │Mini-Agt │     │Claude Cd│
└────┬────┘     └────┬────┘     └────┬────┘     └────┬────┘
     │               │               │               │
     │  编写任务需求  │               │               │
     │──────────────>│               │               │
     │               │               │               │
     │  任务规格文档  │               │               │
     │<──────────────│               │               │
     │               │               │               │
     │  保存文档到 task-specs        │               │
     │─────────────────────────────>│               │
     │               │               │               │
     │  mini-agent run              │               │
     │─────────────────────────────>│               │
     │               │               │               │
     │               │  执行任务     │               │
     │               │  生成代码     │               │
     │               │               │               │
     │  执行报告 (部分 AC 未通过)    │               │
     │<─────────────────────────────│               │
     │               │               │               │
     │  补充遗漏的代码              │               │
     │─────────────────────────────────────────────>│
     │               │               │               │
     │  修改完成                    │               │
     │<─────────────────────────────────────────────│
     │               │               │               │
     │  请求代码审查  │               │               │
     │──────────────>│               │               │
     │               │               │               │
     │  审查报告      │               │               │
     │<──────────────│               │               │
     │               │               │               │
     │  验收并提交    │               │               │
     │               │               │               │
```

---

## 8. 代码审查与验收

### 8.1 审查检查清单

```
┌─────────────────────────────────────────────────────────────────┐
│                    代码审查检查清单                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📋 功能验证                                                    │
│  □ 所有验收标准 (AC-N) 均已满足                                 │
│  □ 边界情况已处理                                               │
│  □ 错误处理完整                                                 │
│                                                                 │
│  📝 代码规范                                                    │
│  □ 遵循 docs/coding-standards.md                                │
│  □ 类型注解完整                                                 │
│  □ 命名清晰一致                                                 │
│  □ 无 TODO 或临时代码                                           │
│                                                                 │
│  🔒 安全性                                                       │
│  □ 输入验证完整                                                 │
│  □ 无 SQL 注入风险                                              │
│  □ 无 XSS 风险                                                  │
│  □ 敏感数据已加密                                               │
│  □ 权限检查正确                                                 │
│                                                                 │
│  ⚡ 性能                                                        │
│  □ 数据库查询已优化                                             │
│  □ 无 N+1 查询问题                                              │
│  □ 适当使用缓存                                                 │
│                                                                 │
│  🧪 测试                                                        │
│  □ 测试覆盖率 >= 80%                                            │
│  □ 所有测试通过                                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 验收流程

```bash
# 1. 运行 lint 检查
cd backend && ruff check app/

# 2. 运行类型检查
mypy app/

# 3. 运行测试
pytest -v --cov=app --cov-report=term-missing

# 4. 检查测试覆盖率
# 确保关键模块覆盖率 >= 80%

# 5. 手动功能测试
# 启动服务，测试核心功能

# 6. 提交代码
git add .
git commit -m "feat(auth): 实现用户注册接口 (M1-03)"
git push
```

---

## 9. Prompt 模板库

### 9.1 Opus 4.5 模板

#### 编写任务文档
```
请为 BidAgent 项目编写任务规格文档。

## 功能需求
[描述功能需求]

## 请按照 docs/task-spec-template.md 格式生成，包含：
1. YAML Front Matter (id, executor, priority, task_type, dependencies, outputs)
2. 描述章节
3. 输入/输出文件
4. 验收标准 (AC-N 格式)
5. 详细实现步骤
6. 代码模板

## 技术约束
- 后端: FastAPI + SQLAlchemy 2.x + Pydantic 2.x
- 前端: Next.js 15 + TypeScript + shadcn/ui
- 参考: docs/architecture/data-model.md
- 规范: docs/coding-standards.md
```

#### 架构设计
```
我需要设计 [模块名] 的架构。

## 背景
- 项目技术栈: [技术栈]
- 相关文档: [文档路径]

## 需求
[功能需求列表]

## 请提供
1. 模块目录结构
2. 核心类/接口定义
3. 数据流图
4. 与现有模块的交互
5. 技术风险和解决方案
```

#### 代码审查
```
请审查以下代码。

## 任务信息
- 任务 ID: [ID]
- 任务文档: [路径]

## 生成的文件
[文件列表或内容]

## 审查要点
1. 验收标准满足度
2. 安全性
3. 代码规范
4. 性能
5. 改进建议
```

### 9.2 Claude Code 模板

#### 补充代码
```
Mini-Agent 生成的 [文件名] 需要补充：

1. [需要补充的功能1]
2. [需要补充的功能2]

文件位置: [路径]
请直接修改文件。
```

#### 调试修复
```
运行 [测试/程序] 时出错：

[错误信息]

请帮我：
1. 分析失败原因
2. 修复代码
3. 验证修复
```

---

## 附录: 快速参考

### 常用命令

```bash
# Mini-Agent
mini-agent run <doc> --task <id>    # 执行单任务
mini-agent run <doc> --all          # 执行所有任务
mini-agent status                    # 查看状态
mini-agent deps <doc>               # 查看依赖图

# 后端开发
cd backend
uvicorn app.main:app --reload       # 启动服务
pytest -v --cov=app                 # 运行测试
ruff check app/                     # 代码检查
alembic upgrade head                # 数据库迁移

# 前端开发
cd frontend
npm run dev                         # 启动服务
npm run lint                        # 代码检查
npm run test                        # 运行测试
```

### 文档路径

| 文档 | 路径 | 用途 |
|------|------|------|
| 任务模板 | `docs/task-spec-template.md` | Mini-Agent 任务文档格式 |
| 任务规格 | `docs/task-specs/M{X}-*/` | 各里程碑任务定义 |
| AI 协作指南 | `docs/ai-collaboration-guide.md` | 多 AI 工具协作详解 |
| 编码规范 | `docs/coding-standards.md` | 代码风格要求 |
| 数据模型 | `docs/architecture/data-model.md` | 数据库设计 |
| API 契约 | `docs/api-contracts/openapi.yaml` | API 接口定义 |

---

> 📝 **文档版本**: 2.0 | **更新日期**: 2026-01-25 | **变更**: 重构为文档驱动开发模式，以 Mini-Agent 为核心执行者
