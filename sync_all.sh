#!/usr/bin/env bash
# sync_all.sh — Full tender sync: local fetch → server import.
#
# WHY LOCAL FETCH:
#   ADB can be blocked from cloud datacenter IPs by Cloudflare. To keep behavior
#   consistent and auditable, ADB and WB are both fetched locally, exported to
#   JSON, uploaded, and then imported on the server. The server never performs
#   upstream tender fetching in this script.
#
# USAGE:
#   ./sync_all.sh                    # ADB + WB local fetch → server import
#   ./sync_all.sh --adb-only         # skip WB step
#   ./sync_all.sh --wb-only          # skip ADB step (server WB refresh only)
#   ./sync_all.sh --clear            # clear old records per-source before import
#   ./sync_all.sh --wb-pages 30      # custom WB page limit (default: 50)
#   ./sync_all.sh --adb-pages 1      # ADB current page is parsed; default=1
#   ./sync_all.sh --all-procurement  # include non-goods procurement categories
#
# PREREQUISITES (local machine):
#   Local deps are installed automatically from backend/requirements-sync.txt
#   SSH key must have access to SERVER_IP

set -euo pipefail

# ╔══════════════════════════════════════════════════════════════════╗
# ║  SERVER CONFIG — edit these or export the env vars before run   ║
# ╚══════════════════════════════════════════════════════════════════╝
SERVER_IP="${SERVER_IP:-152.136.160.173}"
SSH_USER="${SSH_USER:-ubuntu}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_ed25519}"
BACKEND_DIR="${BACKEND_DIR:-$(cd "$(dirname "$0")/backend" && pwd)}"
REMOTE_CONTAINER="${REMOTE_CONTAINER:-bidagent-backend}"

# ── Defaults ──────────────────────────────────────────────────────
ADB_PAGES=1          # ADB current-page reader returns the latest active page
WB_PAGES=50          # WB local API fetch; stops when no more valid notices
CLEAR_FLAG=""
RUN_ADB=true
RUN_WB=true
GOODS_ONLY=true
WB_PROCUREMENT_GROUPS="${WB_PROCUREMENT_GROUPS:-GO}"
WB_NOTICE_TYPES="${WB_NOTICE_TYPES:-Invitation for Bids,Invitation for Prequalification}"
REMOTE_IMPORTER="/tmp/import_tenders.py"
_LOG_TMP="$(mktemp /tmp/sync_step.XXXXXX)"
trap 'rm -f "$_LOG_TMP"' EXIT

# ── Python: ensure local deps are available ───────────────────────
# Uses --system-site-packages --without-pip to bypass ensurepip restrictions
# on Ubuntu 24+, then installs via python3 -m pip (inherits user pip).
VENV_DIR="${BACKEND_DIR}/.venv"
if [[ ! -f "${VENV_DIR}/bin/python3" ]]; then
  echo "▶ 首次运行：初始化本地 Python 环境并安装依赖 …"
  python3 -m venv "${VENV_DIR}" --system-site-packages --without-pip
  "${VENV_DIR}/bin/python3" -m pip install --quiet \
    -r "${BACKEND_DIR}/requirements-sync.txt"
  echo "  ✓ 依赖安装完成"; echo ""
fi
PYTHON="${VENV_DIR}/bin/python3"

# ── Arg parsing ───────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case $1 in
    --adb-only)   RUN_WB=false;  shift ;;
    --wb-only)    RUN_ADB=false; shift ;;
    --clear|-c)   CLEAR_FLAG="--clear"; shift ;;
    --adb-pages)  ADB_PAGES="$2"; shift 2 ;;
    --wb-pages)   WB_PAGES="$2";  shift 2 ;;
    --all-procurement) GOODS_ONLY=false; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

SSH_OPTS=(-i "$SSH_KEY" -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=10)
SSH_CMD=(ssh "${SSH_OPTS[@]}" "${SSH_USER}@${SERVER_IP}")

# ── Helper: extract last occurrence of "key=N" from captured log ──
_parse_stat() {
  local log="$1" key="$2"
  grep -oE "${key}=[0-9]+" "$log" | tail -1 | grep -oE '[0-9]+' || echo "0"
}

# ── Summary state ─────────────────────────────────────────────────
ADB_FETCHED="-"; ADB_CREATED="-"; ADB_UPDATED="-"; ADB_SKIPPED="-"; ADB_DELETED="-"
WB_FETCHED="-";  WB_CREATED="-";  WB_UPDATED="-";  WB_SKIPPED="-";  WB_DELETED="-"

# ── Banner ────────────────────────────────────────────────────────
echo "╔══════════════════════════════════════════════════════════╗"
echo "║              Bid Agent — Full Tender Sync                ║"
echo "╠══════════════════════════════════════════════════════════╣"
printf "║  %-54s║\n" "Server     : ${SSH_USER}@${SERVER_IP}"
printf "║  %-54s║\n" "Container  : ${REMOTE_CONTAINER}"
printf "║  %-54s║\n" "ADB sync   : ${RUN_ADB}  (pages=${ADB_PAGES})"
printf "║  %-54s║\n" "WB  sync   : ${RUN_WB}  (pages=${WB_PAGES})"
printf "║  %-54s║\n" "Goods only : ${GOODS_ONLY}"
printf "║  %-54s║\n" "Clear first: ${CLEAR_FLAG:-no}"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

START_TIME=$(date +%s)

if [[ ! -r "$SSH_KEY" ]]; then
  echo "✗ SSH key not readable: $SSH_KEY" >&2
  exit 1
fi

echo "▶ Preflight: checking SSH and remote container …"
"${SSH_CMD[@]}" \
  "docker ps --format '{{.Names}}' | grep -qx '${REMOTE_CONTAINER}'" \
  || { echo "✗ Cannot reach ${SSH_USER}@${SERVER_IP} or container ${REMOTE_CONTAINER} is not running" >&2; exit 1; }
echo "  ✓ Remote container reachable"; echo ""

echo "▶ Preflight: syncing latest importer into container …"
scp "${SSH_OPTS[@]}" \
    "${BACKEND_DIR}/scripts/import_tenders.py" \
    "${SSH_USER}@${SERVER_IP}:${REMOTE_IMPORTER}"
"${SSH_CMD[@]}" \
  "docker cp ${REMOTE_IMPORTER} ${REMOTE_CONTAINER}:/app/scripts/import_tenders.py"
echo "  ✓ Importer synced"; echo ""

_sync_source() {
  local source="$1" pages="$2" label="$3"
  local local_tmp="/tmp/${source}_export.json"
  local remote_tmp="/tmp/${source}_export.json"
  local fetched created updated skipped deleted_invalid deleted_expired deleted_non_goods deleted_missing deleted

  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  ${label}  [1/3] Fetching locally (max_pages=${pages}) …"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  > "$_LOG_TMP"
  (
    cd "$BACKEND_DIR"
    EXPORT_ARGS=(--source "$source" --output "$local_tmp" --max-pages "$pages")
    if [[ "$GOODS_ONLY" == true ]]; then
      EXPORT_ARGS+=(--goods-only)
    fi
    ADB_GOODS_ONLY="$([[ "$GOODS_ONLY" == true ]] && echo 1 || echo 0)" \
    WB_PROCUREMENT_GROUPS="$WB_PROCUREMENT_GROUPS" \
    WB_NOTICE_TYPES="$WB_NOTICE_TYPES" \
    $PYTHON -m scripts.export_tenders "${EXPORT_ARGS[@]}"
  ) 2>&1 | tee "$_LOG_TMP"
  fetched=$(grep -oE 'Fetched [0-9]+' "$_LOG_TMP" | tail -1 | grep -oE '[0-9]+' || echo "0")
  echo ""

  echo "  ${label}  [2/3] Uploading JSON to ${SERVER_IP}:${remote_tmp} …"
  scp "${SSH_OPTS[@]}" \
      "$local_tmp" "${SSH_USER}@${SERVER_IP}:${remote_tmp}"
  echo ""

  echo "  ${label}  [3/3] Importing into database and deleting expired records …"
  > "$_LOG_TMP"
  "${SSH_CMD[@]}" \
    "docker cp ${remote_tmp} ${REMOTE_CONTAINER}:${remote_tmp} && \
     docker exec ${REMOTE_CONTAINER} python -m scripts.import_tenders \
       ${remote_tmp} ${CLEAR_FLAG}" \
    2>&1 | tee "$_LOG_TMP"
  created=$(_parse_stat "$_LOG_TMP" "created")
  updated=$(_parse_stat "$_LOG_TMP" "updated")
  skipped=$(_parse_stat "$_LOG_TMP" "skipped")
  deleted_invalid=$(_parse_stat "$_LOG_TMP" "deleted_invalid")
  deleted_expired=$(_parse_stat "$_LOG_TMP" "deleted_expired")
  deleted_non_goods=$(_parse_stat "$_LOG_TMP" "deleted_non_goods")
  deleted_missing=$(_parse_stat "$_LOG_TMP" "deleted_missing")
  deleted=$(( deleted_invalid + deleted_expired + deleted_non_goods + deleted_missing ))
  echo ""

  case "$source" in
    adb)
      ADB_FETCHED="$fetched"; ADB_CREATED="$created"; ADB_UPDATED="$updated"
      ADB_SKIPPED="$skipped"; ADB_DELETED="$deleted"
      ;;
    wb)
      WB_FETCHED="$fetched"; WB_CREATED="$created"; WB_UPDATED="$updated"
      WB_SKIPPED="$skipped"; WB_DELETED="$deleted"
      ;;
  esac
}

# ══════════════════════════════════════════════════════════════════
# PART A — ADB  (local fetch → SCP → docker import)
# ══════════════════════════════════════════════════════════════════
if $RUN_ADB; then
  _sync_source "adb" "$ADB_PAGES" "ADB "
fi

# ══════════════════════════════════════════════════════════════════
# PART B — World Bank  (local fetch → SCP → docker import)
# ══════════════════════════════════════════════════════════════════
if $RUN_WB; then
  _sync_source "wb" "$WB_PAGES" "WB  "
fi

# ── Elapsed time ──────────────────────────────────────────────────
END_TIME=$(date +%s)
ELAPSED=$(( END_TIME - START_TIME ))
ELAPSED_FMT="$(( ELAPSED / 60 ))m $(( ELAPSED % 60 ))s"

# ── Summary box ───────────────────────────────────────────────────
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                    同步结果汇总                          ║"
echo "╠══════════════════════════════════════════════════════════╣"
if $RUN_ADB; then
  printf "║  %-54s║\n" "ADB  抓取: ${ADB_FETCHED} 条"
  printf "║  %-54s║\n" "ADB  入库: 新增 ${ADB_CREATED}  更新 ${ADB_UPDATED}  跳过 ${ADB_SKIPPED}  删除失效 ${ADB_DELETED}"
fi
if $RUN_ADB && $RUN_WB; then
  echo "╠══════════════════════════════════════════════════════════╣"
fi
if $RUN_WB; then
  printf "║  %-54s║\n" "WB   抓取: ${WB_FETCHED} 条"
  printf "║  %-54s║\n" "WB   入库: 新增 ${WB_CREATED}  更新 ${WB_UPDATED}  跳过 ${WB_SKIPPED}  删除失效 ${WB_DELETED}"
fi
echo "╠══════════════════════════════════════════════════════════╣"
printf "║  %-54s║\n" "耗时: ${ELAPSED_FMT}"
echo "╚══════════════════════════════════════════════════════════╝"
