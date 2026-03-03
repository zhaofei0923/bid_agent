#!/usr/bin/env bash
# sync_adb.sh — Fetch ADB tenders locally and sync to the remote server DB.
#
# Prerequisites (local machine):
#   cd backend && python -m pip install -r requirements.txt
#   The backend virtualenv (or container) must be able to reach adb.org.
#
# Usage:
#   chmod +x sync_adb.sh
#   ./sync_adb.sh                          # default 5 pages (~100 tenders)
#   ./sync_adb.sh --pages 10
#   ./sync_adb.sh --pages 3 --clear       # clear ADB rows on server first
#
# Required env vars (or edit the CONFIG block below):
#   SERVER_IP   — remote server IP / hostname   (default: 152.136.160.173)
#   SSH_USER    — SSH username                  (default: ubuntu)
#   SSH_KEY     — path to SSH private key       (default: ~/.ssh/id_rsa)
#   BACKEND_DIR — local path to backend/        (default: ./backend)

set -euo pipefail

# ── CONFIG ──────────────────────────────────────────────────────────────────
SERVER_IP="${SERVER_IP:-152.136.160.173}"
SSH_USER="${SSH_USER:-ubuntu}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_rsa}"
BACKEND_DIR="${BACKEND_DIR:-$(cd "$(dirname "$0")/backend" && pwd)}"
REMOTE_CONTAINER="bidagent-backend"
REMOTE_TMP="/tmp/adb_export.json"
LOCAL_TMP="/tmp/adb_export.json"
MAX_PAGES=5
CLEAR_FLAG=""

# ── ARGUMENT PARSING ─────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case $1 in
    --pages|-p)
      MAX_PAGES="$2"; shift 2 ;;
    --clear|-c)
      CLEAR_FLAG="--clear"; shift ;;
    *)
      echo "Unknown option: $1"; exit 1 ;;
  esac
done

SSH_CMD="ssh -i $SSH_KEY -o StrictHostKeyChecking=no ${SSH_USER}@${SERVER_IP}"

echo "═══════════════════════════════════════════════════════"
echo " ADB Local → Server Sync"
echo " Pages       : $MAX_PAGES"
echo " Clear first : ${CLEAR_FLAG:-no}"
echo " Server      : ${SSH_USER}@${SERVER_IP}"
echo "═══════════════════════════════════════════════════════"

# ── STEP 1: Run export locally ───────────────────────────────────────────────
echo ""
echo "▶ [1/3] Fetching ADB data locally (≤ ${MAX_PAGES} pages) …"
(
  cd "$BACKEND_DIR"
  python -m scripts.export_adb \
    --output "$LOCAL_TMP" \
    --max-pages "$MAX_PAGES"
)
echo "   Export saved to: $LOCAL_TMP"

# ── STEP 2: SCP the file to the server ──────────────────────────────────────
echo ""
echo "▶ [2/3] Uploading JSON to ${SERVER_IP}:${REMOTE_TMP} …"
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
    "$LOCAL_TMP" "${SSH_USER}@${SERVER_IP}:${REMOTE_TMP}"
echo "   Upload complete."

# ── STEP 3: Import inside Docker on the server ───────────────────────────────
echo ""
echo "▶ [3/3] Importing into database on server …"
$SSH_CMD "docker cp ${REMOTE_TMP} ${REMOTE_CONTAINER}:${REMOTE_TMP} && \
          docker exec ${REMOTE_CONTAINER} python -m scripts.import_tenders \
            ${REMOTE_TMP} ${CLEAR_FLAG}"

# ── DONE ─────────────────────────────────────────────────────────────────────
echo ""
echo "✓ Sync complete."
