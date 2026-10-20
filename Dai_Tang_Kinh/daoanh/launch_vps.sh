#!/usr/bin/env bash
# launch_vps.sh — Khởi động DaoAnh trên VPS Linux
# Tương đương launch.bat nhưng dùng cho Linux
# Cách chạy: bash launch_vps.sh
# ──────────────────────────────────────────────────────────────

set -e
DAOANH_DIR="/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh"
LOG_DIR="$DAOANH_DIR/logs"
PYTHON="python3"

cd "$DAOANH_DIR"
mkdir -p "$LOG_DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  DaoAnh VPS Restart — $(date '+%Y-%m-%d %H:%M:%S')"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── [0/3] Kill tiến trình cũ ──────────────────────────────────
echo "[0/3] Tắt tiến trình cũ (app.py / server.py)..."
pkill -f "python.*app\.py"    2>/dev/null || true
pkill -f "python3.*app\.py"   2>/dev/null || true
pkill -f "python.*server\.py" 2>/dev/null || true
pkill -f "python3.*server\.py" 2>/dev/null || true
sleep 2

# ── [1/3] Auth Gateway (server.py) — port 5001 ───────────────
echo "[1/3] Auth Gateway   port 5001..."
nohup $PYTHON server.py \
    > "$LOG_DIR/auth-5001.log" \
    2> "$LOG_DIR/auth-5001-err.log" &
AUTH_PID=$!
sleep 3

# ── [2/3] App chính (app.py) — port 5000 ─────────────────────
echo "[2/3] App chính      port 5000..."
nohup $PYTHON app.py \
    > "$LOG_DIR/app-5000.log" \
    2> "$LOG_DIR/app-5000-err.log" &
APP_PID=$!
echo "       PID app.py = $APP_PID"

# Chờ Flask khởi động xong (load lexicon ~10 giây)
echo "       Đợi Flask khởi động..."
sleep 12

# ── [3/3] Verify API ──────────────────────────────────────────
echo "[3/3] Kiểm tra API..."

# Test places/search
RESULT=$(curl -sf "http://localhost:5000/daoanh/api/places/search?q=&limit=5" \
    | $PYTHON -c "import sys,json; d=json.load(sys.stdin); print('places/search OK:', len(d.get('items',[])), 'items')" 2>/dev/null \
    || echo "FAIL: places/search không phản hồi")
echo "       $RESULT"

# Test auth gateway
AUTH_OK=$(curl -sf "http://localhost:5001/api/health" 2>/dev/null \
    | $PYTHON -c "import sys,json; d=json.load(sys.stdin); print('auth OK')" 2>/dev/null \
    || echo "auth: cần kiểm tra thủ công")
echo "       $AUTH_OK"

# Whitelist admin
curl -sf -X POST http://localhost:5001/api/admin/emails/add \
    -H "Content-Type: application/json" \
    -d '{"email":"namthien@gmail.com"}' > /dev/null 2>&1 \
    && echo "       Whitelist namthien@gmail.com: OK" \
    || echo "       Whitelist: skip (auth chưa sẵn sàng)"

# ── Log tail ──────────────────────────────────────────────────
echo ""
echo "── Log app-5000 (5 dòng cuối) ─────────────"
tail -5 "$LOG_DIR/app-5000.log" 2>/dev/null || echo "(chưa có log)"

echo ""
echo "── Trạng thái port ─────────────────────────"
ss -tlnp 2>/dev/null | grep -E "5000|5001" || netstat -tlnp 2>/dev/null | grep -E "5000|5001" || echo "(dùng: ss -tlnp | grep 500)"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  XONG. App: http://phatphaponline.org/daoanh/"
echo "  Logs: $LOG_DIR/"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
