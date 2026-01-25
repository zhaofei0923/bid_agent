# Ubuntu 开发环境搭建指南

> 本指南帮助你在 **原生 Ubuntu 系统** 上搭建 BidAgent 项目的完整开发环境。

---

## 目录

1. [前置要求](#1-前置要求)
2. [安装基础工具](#2-安装基础工具)
3. [安装 Docker](#3-安装-docker)
4. [安装开发工具链](#4-安装开发工具链)
5. [安装 Mini-Agent CLI](#5-安装-mini-agent-cli)
6. [配置 VS Code](#6-配置-vs-code)
7. [克隆和启动项目](#7-克隆和启动项目)
8. [常见问题解答](#8-常见问题解答)

---

## 1. 前置要求

### 系统要求

- Ubuntu 22.04 LTS 或更高版本
- 至少 8GB 内存 (推荐 16GB+)
- 至少 50GB 可用磁盘空间

### 检查系统版本

```bash
cat /etc/os-release
uname -a
```

---

## 2. 安装基础工具

### 2.1 更新系统

```bash
sudo apt update && sudo apt upgrade -y
```

### 2.2 安装基础依赖

```bash
sudo apt install -y build-essential git curl wget unzip \
    software-properties-common apt-transport-https ca-certificates \
    gnupg lsb-release
```

---

## 3. 安装 Docker

### 3.1 安装 Docker Engine

```bash
# 添加 Docker 官方 GPG 密钥
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# 添加 Docker 仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### 3.2 配置 Docker 免 sudo

```bash
# 添加当前用户到 docker 组
sudo usermod -aG docker $USER

# 重新登录或执行以下命令使组生效
newgrp docker
```

### 3.3 验证安装

```bash
docker --version
docker compose version
docker run hello-world
```

---

## 4. 安装开发工具链

### 4.1 安装 Node.js (使用 nvm)

```bash
# 安装 nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# 重新加载 shell 配置
source ~/.bashrc

# 安装 Node.js 20.x
nvm install 20
nvm use 20
nvm alias default 20

# 验证
node --version  # 应显示 v20.x.x
npm --version
```

### 4.2 安装 Python (使用 pyenv)

```bash
# 安装 pyenv 依赖
sudo apt install -y build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
    libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \
    libffi-dev liblzma-dev

# 安装 pyenv
curl https://pyenv.run | bash

# 添加到 ~/.bashrc
cat >> ~/.bashrc << 'EOF'

# Pyenv configuration
export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
EOF

# 重新加载配置
source ~/.bashrc

# 安装 Python 3.11
pyenv install 3.11
pyenv global 3.11

# 验证
python --version  # 应显示 Python 3.11.x
pip --version
```

### 4.3 安装 PostgreSQL 客户端 (可选)

```bash
sudo apt install -y postgresql-client
```

---

## 5. 安装 Mini-Agent CLI

Mini-Agent 是本项目的核心开发工具，用于读取任务文档并自动分解执行开发任务。

### 5.1 安装依赖

```bash
# 确保 Python 虚拟环境激活或使用全局 Python
pip install psutil aiofiles httpx
```

### 5.2 安装 Mini-Agent

```bash
# 根据你的 Mini-Agent 安装方式执行
# 示例：从 pip 安装
pip install mini-agent

# 或从源码安装
# git clone <mini-agent-repo> ~/tools/mini-agent
# cd ~/tools/mini-agent && pip install -e .
```

### 5.3 验证安装

```bash
mini-agent --version
mini-agent --help
```

### 5.4 配置 Mini-Agent

创建配置文件 `~/.mini-agent/config.yaml`：

```yaml
# Mini-Agent 配置
orchestration:
  executor:
    default_mode: "auto"
    async_concurrency: 200
    thread_pool_size: 16
    timeout: 300

  router:
    strategy: "hybrid"
    keyword_threshold: 0.7

# 默认工作空间
workspace:
  default: ~/projects/bid_agent

# LLM 配置 (适配项目 DeepSeek 模型)
llm:
  provider: "deepseek"
  model: "deepseek-v3"
  temperature: 0.3
```

---

## 6. 配置 VS Code

### 6.1 安装 VS Code

```bash
# 下载并安装
wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
sudo install -D -o root -g root -m 644 packages.microsoft.gpg /etc/apt/keyrings/packages.microsoft.gpg
sudo sh -c 'echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list'
sudo apt update
sudo apt install -y code
```

### 6.2 推荐扩展

在 VS Code 中安装以下扩展：

```
ms-python.python                # Python 支持
ms-python.vscode-pylance        # Python 智能提示
charliermarsh.ruff              # Python Linter/Formatter
dbaeumer.vscode-eslint          # ESLint
esbenp.prettier-vscode          # Prettier
bradlc.vscode-tailwindcss       # Tailwind CSS
ms-azuretools.vscode-docker     # Docker 支持
github.copilot                  # GitHub Copilot
github.copilot-chat             # GitHub Copilot Chat (Opus 4.5)
```

### 6.3 配置 GitHub Copilot

1. 安装 `github.copilot` 和 `github.copilot-chat` 扩展
2. 登录 GitHub 账号
3. 在 Copilot Chat 中选择 **Claude Opus 4.5** 模型用于架构设计和代码审查

---

## 7. 克隆和启动项目

### 7.1 克隆项目

```bash
mkdir -p ~/projects
cd ~/projects
git clone <repo-url> bid_agent
cd bid_agent
```

### 7.2 启动基础服务

```bash
# 启动 PostgreSQL、Redis、MinIO
docker compose up -d postgres redis minio

# 检查服务状态
docker compose ps

# 查看日志
docker compose logs -f postgres
```

### 7.3 启动后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7.4 启动前端

打开新终端：

```bash
cd ~/projects/bid_agent/frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 7.5 服务访问地址

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:3000 |
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |
| MinIO Console | http://localhost:9001 |

---

## 8. 常见问题解答

### Q1: Docker 命令需要 sudo？

```bash
# 将当前用户添加到 docker 组
sudo usermod -aG docker $USER

# 重新登录或执行
newgrp docker
```

### Q2: 端口被占用？

```bash
# 检查端口占用
sudo lsof -i :8000
sudo lsof -i :3000

# 终止占用进程
sudo kill -9 <PID>
```

### Q3: 数据库连接失败？

```bash
# 检查 PostgreSQL 容器状态
docker compose ps postgres

# 查看日志
docker compose logs postgres

# 测试连接
psql -h localhost -U bidagent -d bidagent
# 密码: bidagent123
```

### Q4: Mini-Agent 无法识别任务文档？

确保任务文档符合标准化模板格式（参考 `docs/task-spec-template.md`），包含：
- YAML Front Matter 元信息
- 固定章节顺序
- AC-N 格式的验收标准

### Q5: pyenv 安装 Python 失败？

```bash
# 安装额外依赖
sudo apt install -y libssl-dev libbz2-dev libncurses5-dev \
    libncursesw5-dev libreadline-dev libsqlite3-dev libffi-dev

# 重试安装
pyenv install 3.11
```

---

## 快速参考

### 常用路径

| 描述 | 路径 |
|------|------|
| 项目根目录 | `~/projects/bid_agent` |
| 后端代码 | `~/projects/bid_agent/backend` |
| 前端代码 | `~/projects/bid_agent/frontend` |
| 任务规格文档 | `~/projects/bid_agent/docs/task-specs/` |
| Mini-Agent 配置 | `~/.mini-agent/config.yaml` |

### 常用命令

```bash
# 启动/停止 Docker 服务
docker compose up -d
docker compose down

# 激活 Python 虚拟环境
source ~/projects/bid_agent/backend/venv/bin/activate

# 启动后端
cd ~/projects/bid_agent/backend && uvicorn app.main:app --reload

# 启动前端
cd ~/projects/bid_agent/frontend && npm run dev

# 用 VS Code 打开项目
cd ~/projects/bid_agent && code .

# Mini-Agent 读取任务文档执行
mini-agent run docs/task-specs/M1-user-system/README.md
```

---

> 📝 **提示**: 环境搭建完成后，请阅读 [AI 协作指南](./ai-collaboration-guide.md) 了解如何使用 Mini-Agent + Opus 4.5 + Claude Code 进行开发。
