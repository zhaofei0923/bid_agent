#!/usr/bin/env bash
# sync_all.sh — Full tender sync: ADB (local → server) + WB (on server).
#
# WHY TWO STRATEGIES:
#   ADB — Cloudflare WAF blocks all cloud datacenter IPs (CN & SG).
#         Must be fetched locally (home/office IP), then uploaded to server.
#   WB  — World Bank API is accessible directly from the server.
#         Fetched inside the Docker container, no local step required.
#
# USAGE:
#   ./sync_all.sh                    # ADB (local→server) + WB (server)
#   ./sync_all.sh --adb-only         # skip WB step
#   ./sync_all.sh --wb-only          # skip ADB step (server WB refresh only)
#   ./sync_all.sh --clear            # clear old records per-source before import
#   ./sync_all.sh --wb-pages 30      # custom WB page limit (default: 50)
#   ./sync_all.sh --adb-pages 1      # ADB RSS is single-page; default=1 is enough
#
# PREREQUISITES (local machine):
#   pip install -r backend/requirements.txt  # in virtualenv
#   SSH key must have access to SERVER_IP

set -euo pipefail

# ╔══════════════════════════════════════════════════════════════════╗
# ║  SERVER CONFIG — edit these or export the env vars before run   ║
# ╚══════════════════════════════════════════════════════════════════╝
SERVER_IP="${SERVER_IP:-152.136.160.173}"
SSH_USER="${SSH_USER:-ubuntu}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_rsa}"
BACKEND_DIR="${BACKEND_DIR:-$(cd "$(dirname "$0")/backend" && pwd)}"
REMOTE_CONTAINER="${REMOTE_CONTAINER:-bidagent-backend}"

# ── Defaults ──────────────────────────────────────────────────────
ADB_PAGES=1          # ADB RSS has no pagination; all active items come in 1 page
WB_PAGES=50          # WB self-stops when all items are expired — safety cap
CLEAR_FLAG=""
RUN_ADB=true
RUN_WB=true
LOCAL_TMP="/tmp/adb_export.json"
REMOTE_TMP="/tmp/adb_export.json"
_LOG_TMP="$(mktemp /tmp/sync_step.XXXXXX)"
trap 'rm -f "$_LOG_TMP"' EXIT

# ── Arg parsing ───────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case $1 in
    --adb-only)   RUN_WB=false;  shift ;;
    --wb-only)    RUN_ADB=false; shift ;;
    --clear|-c)   CLEAR_FLAG="--clear"; shift ;;
    --adb-pages)  ADB_PAGES="$2"; shift 2 ;;
    --wb-pages)   WB_PAGES="$2";  shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

SSH_CMD="ssh -i $SSH_KEY -o StrictHostKeyChecking=no ${SSH_USER}@${SERVER_IP}"

# ── Helper: extract last occurrence of "key=N" from captured log ──
_parse_stat() {
  local log="$1" key="$2"
  grep -oE "${key}=[0-9]+" "$log" | tail -1 | grep -oE '[0-9]+' || echo "0"
}

# ── Summary state ─────────────────────────────────────────────────
ADB_FETCHED="-"; ADB_CREATED="-"; ADB_UPDATED="-"; ADB_SKIPPED="-"
WB_CREATED="-";  WB_UPDATED="-";  WB_SKIPPED="-"

# ── Banner ────────────────────────────────────────────────────────
echo "╔══════════════════════════════════════════════════════════╗"
echo "║              Bid Agent — Full Tender Sync                ║"
echo "╠══════════════════════════════════════════════════════════╣"
printf "║  %-54s║\n" "Server     : ${SSH_USER}@${SERVER_IP}"
printf "║  %-54s║\n" "Container  : ${REMOTE_CONTAINER}"
printf "║  %-54s║\n" "ADB sync   : ${RUN_ADB}  (pages=${ADB_PAGES})"
printf "║  %-54s║\n" "WB  sync   : ${RUN_WB}  (pages=${WB_PAGES})"
printf "║  %-54s║\n" "Clear first: ${CLEAR_FLAG:-no}"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

START_TIME=$(date +%s)

# ══════════════════════════════════════════════════════════════════
# PART A — ADB  (local fetch → SCP → docker import)
# ══════════════════════════════════════════════════════════════════
if $RUN_ADB; then
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  ADB  [1/3] Fetching locally (max_pages=${ADB_PAGES}) …"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  > "$_LOG_TMP"
  (
    cd "$BACKEND_DIR"
    python3 -m scripts.export_adb \
      --output "$LOCAL_TMP" \
      --max-pages "$ADB_PAGES"
  ) 2>&1 | tee "$_LOG_TMP"
  # "Fetched N ADB tenders"
  ADB_FETCHED=$(grep -oE 'Fetched [0-9]+' "$_LOG_TMP" | tail -1 | grep -oE '[0-9]+' || echo "0")
  echo ""

  echo "  ADB  [2/3] Uploading JSON to ${SERVER_IP}:${REMOTE_TMP} …"
  scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
      "$LOCAL_TMP" "${SSH_USER}@${SERVER_IP}:${REMOTE_TMP}"
  echo ""

  echo "  ADB  [3/3] Importing into database on server …"
  > "$_LOG_TMP"
  $SSH_CMD \
    "docker cp ${REMOTE_TMP} ${REMOTE_CONTAINER}:${REMOTE_TMP} && \
     docker exec ${REMOTE_CONTAINER} python -m scripts.import_tenders \
       ${REMOTE_TMP} ${CLEAR_FLAG}" \
    2>&1 | tee "$_LOG_TMP"
  # "Import complete: created=N, updated=N, skipped=N"
  ADB_CREATED=$(_parse_stat "$_LOG_TMP" "created")
  ADB_UPDATED=$(_parse_stat "$_LOG_TMP" "updated")
  ADB_SKIPPED=$(_parse_stat "$_LOG_TMP" "skipped")
  echo ""
fi

# ══════════════════════════════════════════════════════════════════
# PART B — World Bank  (fetch directly on server)
# ══════════════════════════════════════════════════════════════════
if $RUN_WB; then
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  WB   Fetching on server (max_pages=${WB_PAGES}) …"
  echo "       (Stops automatically when all open-type items are expired)"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  > "$_LOG_TMP"
  $SSH_CMD \
    "docker exec ${REMOTE_CONTAINER} python -m scripts.run_fetcher \
       --source wb \
       --max-pages ${WB_PAGES} \
       ${CLEAR_FLAG}" \
    2>&1 | tee "$_LOG_TMP"
  # "DB upsert: created=N, updated=N, skipped=N"
  WB_CREATED=$(_parse_stat "$_LOG_TMP" "created")
  WB_UPDATED=$(_parse_stat "$_LOG_TMP" "updated")
  WB_SKIPPED=$(_parse_stat "$_LOG_TMP" "skipped")
  echo ""
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
  printf "║  %-54s║\n" "ADB  入库: 新增 ${ADB_CREATED}  更新 ${ADB_UPDATED}  跳过 ${ADB_SKIPPED}"
fi
if $RUN_ADB && $RUN_WB; then
  echo "╠══════════════════════════════════════════════════════════╣"
fi
if $RUN_WB; then
  printf "║  %-54s║\n" "WB   入库: 新增 ${WB_CREATED}  更新 ${WB_UPDATED}  跳过 ${WB_SKIPPED}"
fi
echo "╠══════════════════════════════════════════════════════════╣"
printf "║  %-54s║\n" "耗时: ${ELAPSED_FMT}"
echo "╚══════════════════════════════════════════════════════════╝"
