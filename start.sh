#!/usr/bin/env bash
# ================================================================
# BidAgent V2 — 一键本地启动脚本
#
# 用法:
#   chmod +x start.sh && ./start.sh          # 启动所有服务
#   ./start.sh --stop                        # 停止所有服务
#   ./start.sh --status                      # 查看服务状态
#   ./start.sh --reset-db                    # 重置数据库
# ================================================================

set -euo pipefail

# ── 颜色定义 ─────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# ── 项目根目录 ───────────────────────────────────────────────────
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
LOG_DIR="$PROJECT_DIR/.logs"
PID_DIR="$PROJECT_DIR/.pids"

# ── 日志和 PID 目录 ──────────────────────────────────────────────
mkdir -p "$LOG_DIR" "$PID_DIR"

# ── 辅助函数 ─────────────────────────────────────────────────────
log_info()    { echo -e "${GREEN}[INFO]${NC}  $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $*"; }
log_step()    { echo -e "${CYAN}[STEP]${NC}  ${BOLD}$*${NC}"; }
log_success() { echo -e "${GREEN}[✓]${NC}    $*"; }

banner() {
    echo -e "${BLUE}"
    echo "  ╔══════════════════════════════════════════╗"
    echo "  ║        BidAgent V2 — 本地开发环境        ║"
    echo "  ╠══════════════════════════════════════════╣"
    echo "  ║  Frontend  : http://localhost:3000       ║"
    echo "  ║  Backend   : http://localhost:8000       ║"
    echo "  ║  API Docs  : http://localhost:8000/docs  ║"
    echo "  ║  PostgreSQL: localhost:5432               ║"
    echo "  ║  Redis     : localhost:6379               ║"
    echo "  ╚══════════════════════════════════════════╝"
    echo -e "${NC}"
}

# ── 启动 Docker Engine/Desktop ───────────────────────────────────
ensure_docker() {
    # 已经能用就直接返回
    if docker info >/dev/null 2>&1; then
        return 0
    fi

    log_warn "Docker 未运行，尝试自动启动..."

    # macOS — Docker Desktop
    if [[ "$(uname -s)" == "Darwin" ]]; then
        open -a Docker 2>/dev/null || true
    # Linux — 优先 systemd，其次 service
    elif command -v systemctl >/dev/null 2>&1; then
        sudo systemctl start docker 2>/dev/null || true
    elif command -v service >/dev/null 2>&1; then
        sudo service docker start 2>/dev/null || true
    fi

    # 等待 Docker 就绪（最多 30 秒）
    local retries=30
    while [[ $retries -gt 0 ]]; do
        if docker info >/dev/null 2>&1; then
            log_success "Docker 已就绪"
            return 0
        fi
        retries=$((retries - 1))
        sleep 1
    done

    log_error "Docker 启动超时。请手动启动 Docker 后重试。"
    exit 1
}

# ── 检测依赖 ─────────────────────────────────────────────────────
check_deps() {
    local missing=()

    command -v docker >/dev/null 2>&1    || missing+=("docker")
    command -v docker compose >/dev/null 2>&1 || {
        command -v docker-compose >/dev/null 2>&1 || missing+=("docker-compose")
    }
    command -v python3 >/dev/null 2>&1   || missing+=("python3")
    command -v node >/dev/null 2>&1      || missing+=("node")
    command -v npm >/dev/null 2>&1       || missing+=("npm")

    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "缺少依赖: ${missing[*]}"
        log_error "请先安装后再运行此脚本"
        exit 1
    fi
}

# docker compose 兼容
DOCKER_COMPOSE="docker compose"
command -v docker compose >/dev/null 2>&1 || DOCKER_COMPOSE="docker-compose"

# ── .env 文件 ────────────────────────────────────────────────────
ensure_env() {
    if [[ ! -f "$PROJECT_DIR/.env" ]]; then
        log_warn ".env 文件不存在，从 .env.example 复制..."
        if [[ -f "$PROJECT_DIR/.env.example" ]]; then
            cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
            log_info "已创建 .env — 请根据需要修改 API Key 等配置"
        else
            log_error "未找到 .env.example — 请手动创建 .env 文件"
            exit 1
        fi
    fi
}

# ── 停止所有服务 ─────────────────────────────────────────────────
stop_all() {
    log_step "停止所有服务..."

    # 停止前端
    if [[ -f "$PID_DIR/frontend.pid" ]]; then
        local fpid
        fpid=$(cat "$PID_DIR/frontend.pid")
        if kill -0 "$fpid" 2>/dev/null; then
            kill "$fpid" 2>/dev/null || true
            # 同时杀掉 node 子进程
            pkill -P "$fpid" 2>/dev/null || true
            log_info "前端已停止 (PID $fpid)"
        fi
        rm -f "$PID_DIR/frontend.pid"
    fi

    # 停止后端
    if [[ -f "$PID_DIR/backend.pid" ]]; then
        local bpid
        bpid=$(cat "$PID_DIR/backend.pid")
        if kill -0 "$bpid" 2>/dev/null; then
            kill "$bpid" 2>/dev/null || true
            pkill -P "$bpid" 2>/dev/null || true
            log_info "后端已停止 (PID $bpid)"
        fi
        rm -f "$PID_DIR/backend.pid"
    fi

    # 停止 Celery
    if [[ -f "$PID_DIR/celery.pid" ]]; then
        local cpid
        cpid=$(cat "$PID_DIR/celery.pid")
        if kill -0 "$cpid" 2>/dev/null; then
            kill "$cpid" 2>/dev/null || true
            pkill -P "$cpid" 2>/dev/null || true
            log_info "Celery 已停止 (PID $cpid)"
        fi
        rm -f "$PID_DIR/celery.pid"
    fi

    # 额外清理：杀掉可能残留的进程
    pkill -f "uvicorn app.main:app" 2>/dev/null || true
    pkill -f "next dev" 2>/dev/null || true
    pkill -f "celery.*app.tasks" 2>/dev/null || true

    # 关闭浏览器标签
    close_browser_tab 2>/dev/null || true

    # 停止 Docker 容器 (postgres + redis)
    cd "$PROJECT_DIR"
    $DOCKER_COMPOSE stop postgres redis 2>/dev/null || true
    log_success "所有服务已停止"
}

# ── 查看状态 ─────────────────────────────────────────────────────
show_status() {
    echo -e "${BOLD}=== BidAgent 服务状态 ===${NC}"
    echo ""

    # PostgreSQL
    if $DOCKER_COMPOSE ps postgres 2>/dev/null | grep -qi "up"; then
        echo -e "  PostgreSQL : ${GREEN}● 运行中${NC}  (localhost:5432)"
    else
        echo -e "  PostgreSQL : ${RED}○ 未运行${NC}"
    fi

    # Redis
    if $DOCKER_COMPOSE ps redis 2>/dev/null | grep -qi "up"; then
        echo -e "  Redis      : ${GREEN}● 运行中${NC}  (localhost:6379)"
    else
        echo -e "  Redis      : ${RED}○ 未运行${NC}"
    fi

    # Backend
    if [[ -f "$PID_DIR/backend.pid" ]] && kill -0 "$(cat "$PID_DIR/backend.pid")" 2>/dev/null; then
        echo -e "  Backend    : ${GREEN}● 运行中${NC}  (http://localhost:8000)"
    else
        echo -e "  Backend    : ${RED}○ 未运行${NC}"
    fi

    # Celery
    if [[ -f "$PID_DIR/celery.pid" ]] && kill -0 "$(cat "$PID_DIR/celery.pid")" 2>/dev/null; then
        echo -e "  Celery     : ${GREEN}● 运行中${NC}"
    else
        echo -e "  Celery     : ${YELLOW}○ 未运行${NC}  (可选)"
    fi

    # Frontend
    if [[ -f "$PID_DIR/frontend.pid" ]] && kill -0 "$(cat "$PID_DIR/frontend.pid")" 2>/dev/null; then
        echo -e "  Frontend   : ${GREEN}● 运行中${NC}  (http://localhost:3000)"
    else
        echo -e "  Frontend   : ${RED}○ 未运行${NC}"
    fi

    echo ""
    echo -e "  日志目录: ${CYAN}$LOG_DIR/${NC}"
    echo -e "  查看日志: ${CYAN}tail -f $LOG_DIR/backend.log${NC}"
}

# ── 重置数据库 ───────────────────────────────────────────────────
reset_db() {
    log_step "重置数据库..."
    cd "$PROJECT_DIR"

    # 确保 postgres 运行
    $DOCKER_COMPOSE up -d postgres
    sleep 3

    # 删除并重建数据库（必须连接到 postgres 库，不能连接到被删除的库本身）
    docker exec bidagent-postgres psql -U bidagent -d postgres -c "DROP DATABASE IF EXISTS bidagent;" 2>/dev/null || true
    docker exec bidagent-postgres psql -U bidagent -d postgres -c "CREATE DATABASE bidagent;" 2>/dev/null || true

    # 重建 pgvector 扩展
    docker exec bidagent-postgres psql -U bidagent -d bidagent \
        -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null || true

    # 运行 Alembic 迁移
    cd "$BACKEND_DIR"
    if [[ -d "alembic" ]]; then
        source venv/bin/activate
        export PYTHONPATH="$BACKEND_DIR:${PYTHONPATH:-}"
        log_info "运行数据库迁移..."
        python3 -m alembic upgrade head 2>&1 || {
            log_warn "Alembic 迁移失败 — 请手动检查: cd backend && python3 -m alembic upgrade head"
        }
        deactivate
    fi

    log_success "数据库已重置"
}

# ── 启动基础设施 (PostgreSQL + Redis) ────────────────────────────
start_infra() {
    log_step "1/5 启动 PostgreSQL & Redis..."
    cd "$PROJECT_DIR"

    $DOCKER_COMPOSE up -d postgres redis

    # 等待 PostgreSQL 就绪
    local retries=30
    while [[ $retries -gt 0 ]]; do
        if docker exec bidagent-postgres pg_isready -U bidagent >/dev/null 2>&1; then
            break
        fi
        retries=$((retries - 1))
        sleep 1
    done

    if [[ $retries -eq 0 ]]; then
        log_error "PostgreSQL 启动超时"
        exit 1
    fi

    # 等待 Redis 就绪
    retries=15
    while [[ $retries -gt 0 ]]; do
        if docker exec bidagent-redis redis-cli ping >/dev/null 2>&1; then
            break
        fi
        retries=$((retries - 1))
        sleep 1
    done

    log_success "PostgreSQL & Redis 已就绪"
}

# ── 安装后端依赖 & 运行迁移 ──────────────────────────────────────
setup_backend() {
    log_step "2/5 安装后端依赖 & 初始化数据库..."
    cd "$BACKEND_DIR"

    # 创建虚拟环境（如不存在）
    if [[ ! -d "venv" ]]; then
        python3 -m venv venv
        log_info "已创建 Python 虚拟环境"
    fi

    # 激活虚拟环境
    source venv/bin/activate

    # 安装依赖
    pip install -q --upgrade pip
    pip install -q -r requirements.txt 2>&1 | tail -5

    # 确保 backend/.env 指向项目根 .env
    if [[ ! -e "$BACKEND_DIR/.env" ]]; then
        ln -sf "$PROJECT_DIR/.env" "$BACKEND_DIR/.env"
        log_info "已创建 backend/.env -> ../.env 符号链接"
    fi

    # 设置 PYTHONPATH
    export PYTHONPATH="$BACKEND_DIR:${PYTHONPATH:-}"

    # 运行 Alembic 迁移
    if [[ -d "alembic/versions" ]]; then
        log_info "运行数据库迁移..."
        python3 -m alembic upgrade head 2>&1 || {
            log_warn "Alembic 迁移失败 — 数据库可能已是最新"
        }
    fi

    # 确保 pgvector 扩展存在
    docker exec bidagent-postgres psql -U bidagent -d bidagent \
        -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null || true

    deactivate
    log_success "后端依赖已安装，数据库已初始化"
}

# ── 安装前端依赖 ─────────────────────────────────────────────────
setup_frontend() {
    log_step "3/5 安装前端依赖..."
    cd "$FRONTEND_DIR"

    if [[ ! -d "node_modules" ]]; then
        npm install --silent 2>&1 | tail -3
        log_success "前端依赖已安装"
    else
        log_info "前端依赖已存在，跳过安装 (如需更新请运行 npm install)"
    fi
}

# ── 启动后端 ─────────────────────────────────────────────────────
start_backend() {
    log_step "4/5 启动后端 (FastAPI + Celery)..."
    cd "$BACKEND_DIR"

    # 激活虚拟环境
    source venv/bin/activate
    export PYTHONPATH="$BACKEND_DIR:${PYTHONPATH:-}"

    # 使用 venv 内的绝对路径，避免 deactivate 后找不到命令
    local VENV_PYTHON="$BACKEND_DIR/venv/bin/python3"
    local VENV_CELERY="$BACKEND_DIR/venv/bin/celery"

    # 启动 FastAPI
    nohup "$VENV_PYTHON" -m uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --reload \
        --reload-dir app \
        > "$LOG_DIR/backend.log" 2>&1 &
    echo $! > "$PID_DIR/backend.pid"
    log_info "FastAPI 已启动 (PID $(cat "$PID_DIR/backend.pid"))"

    # 启动 Celery Worker（后台，可选失败）
    nohup "$VENV_CELERY" -A app.tasks:celery_app worker \
        --loglevel=info \
        --concurrency=2 \
        > "$LOG_DIR/celery.log" 2>&1 &
    echo $! > "$PID_DIR/celery.pid"
    log_info "Celery Worker 已启动 (PID $(cat "$PID_DIR/celery.pid"))"

    deactivate
}

# ── 启动前端 ─────────────────────────────────────────────────────
start_frontend() {
    log_step "5/5 启动前端 (Next.js)..."
    cd "$FRONTEND_DIR"

    # 设置 API 代理地址
    export NEXT_PUBLIC_API_URL=http://localhost:8000/v1

    nohup npx next dev --port 3000 \
        > "$LOG_DIR/frontend.log" 2>&1 &
    echo $! > "$PID_DIR/frontend.pid"
    log_info "Next.js 已启动 (PID $(cat "$PID_DIR/frontend.pid"))"
}

# ── 等待服务就绪 ─────────────────────────────────────────────────
wait_ready() {
    echo ""
    log_info "等待服务就绪..."

    # 等待后端
    local retries=30
    while [[ $retries -gt 0 ]]; do
        if curl -s http://localhost:8000/v1/health >/dev/null 2>&1; then
            break
        fi
        retries=$((retries - 1))
        sleep 1
    done

    if [[ $retries -eq 0 ]]; then
        log_warn "后端未响应 health check — 请检查日志: tail -f $LOG_DIR/backend.log"
    else
        log_success "后端已就绪 ✓"
    fi

    # 等待前端
    retries=30
    while [[ $retries -gt 0 ]]; do
        if curl -s http://localhost:3000 >/dev/null 2>&1; then
            break
        fi
        retries=$((retries - 1))
        sleep 1
    done

    if [[ $retries -eq 0 ]]; then
        log_warn "前端未响应 — 请检查日志: tail -f $LOG_DIR/frontend.log"
    else
        log_success "前端已就绪 ✓"
    fi
}

# ── 打开浏览器 ───────────────────────────────────────────────────
open_browser() {
    local url="http://localhost:3000"
    if command -v xdg-open >/dev/null 2>&1; then
        xdg-open "$url" >/dev/null 2>&1 &
    elif command -v open >/dev/null 2>&1; then
        open "$url" >/dev/null 2>&1 &
    elif command -v wslview >/dev/null 2>&1; then
        wslview "$url" >/dev/null 2>&1 &
    else
        log_warn "无法自动打开浏览器，请手动访问: $url"
        return
    fi
    log_success "已打开浏览器: $url"
}

# ── 关闭浏览器标签（尽力而为）────────────────────────────────────
close_browser_tab() {
    # 尝试通过 wmctrl 关闭包含 BidAgent 的浏览器窗口
    if command -v wmctrl >/dev/null 2>&1; then
        wmctrl -c "localhost:3000" 2>/dev/null || true
        wmctrl -c "BidAgent" 2>/dev/null || true
    fi
    # 尝试通过 xdotool 关闭
    if command -v xdotool >/dev/null 2>&1; then
        local wids
        wids=$(xdotool search --name "localhost:3000" 2>/dev/null || true)
        for wid in $wids; do
            xdotool windowactivate "$wid" 2>/dev/null && xdotool key --window "$wid" ctrl+w 2>/dev/null || true
        done
        wids=$(xdotool search --name "BidAgent" 2>/dev/null || true)
        for wid in $wids; do
            xdotool windowactivate "$wid" 2>/dev/null && xdotool key --window "$wid" ctrl+w 2>/dev/null || true
        done
    fi
}

# ── 主流程 ───────────────────────────────────────────────────────
main() {
    cd "$PROJECT_DIR"

    case "${1:-}" in
        --stop|-s)
            stop_all
            exit 0
            ;;
        --status)
            show_status
            exit 0
            ;;
        --reset-db)
            reset_db
            exit 0
            ;;
        --help|-h)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  (无参数)     启动所有服务"
            echo "  --stop, -s   停止所有服务"
            echo "  --status     查看服务运行状态"
            echo "  --reset-db   重置数据库"
            echo "  --help, -h   显示帮助"
            exit 0
            ;;
    esac

    echo ""
    echo -e "${BOLD}🚀 BidAgent V2 — 启动本地开发环境${NC}"
    echo ""

    # 前置检查
    ensure_docker
    check_deps
    ensure_env

    # 先停掉旧进程
    stop_all 2>/dev/null || true
    echo ""

    # 按顺序启动
    start_infra
    setup_backend
    setup_frontend
    start_backend
    start_frontend
    wait_ready

    # 打开浏览器
    open_browser

    # 显示信息
    banner

    echo -e "${BOLD}日志查看:${NC}"
    echo -e "  后端:  ${CYAN}tail -f $LOG_DIR/backend.log${NC}"
    echo -e "  前端:  ${CYAN}tail -f $LOG_DIR/frontend.log${NC}"
    echo -e "  Celery: ${CYAN}tail -f $LOG_DIR/celery.log${NC}"
    echo ""
    echo -e "${BOLD}停止服务:${NC}  ${CYAN}./start.sh --stop${NC}"
    echo -e "${BOLD}查看状态:${NC}  ${CYAN}./start.sh --status${NC}"
    echo ""
}

main "$@"
