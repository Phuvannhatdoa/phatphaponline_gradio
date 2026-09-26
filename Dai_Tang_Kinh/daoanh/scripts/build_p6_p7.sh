#!/bin/bash
# Build script for Phật Tổ Đạo Ảnh - P6-P7
# Logs output to file

# Check for log file to resume
LOG_RESUME=""
if [ $# -gt 0 ] && [ "$1" == "--resume" ] && [ -n "$2" ]; then
    LOG_RESUME="$2"
    echo "📜 Resuming from log: $LOG_RESUME"
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/logs"
mkdir -p "$LOG_DIR"

LOG_FILE="$LOG_DIR/build_${TIMESTAMP}.log"
exec > >(tee -a "$LOG_FILE") 2>&1

PROJECT_DIR="/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh"
cd "$PROJECT_DIR"

echo "========================================"
echo "BUILD STARTED: $(date)"
echo "Log file: $LOG_FILE"
echo "========================================"

# ========== P2.1: Download DILA Authority Place ==========
echo ""
echo "=== STEP P2.1: Download DILA Authority Place ==="
DILA_DIR="$PROJECT_DIR/data/dila_temp"
mkdir -p "$DILA_DIR"
cd "$DILA_DIR"

if [ -f "authority_place.zip" ] || [ -f "Buddhist_Studies_Place_Authority.xml" ]; then
    echo "DILA already exists, skipping download..."
    ls -la
else
    echo "Downloading DILA Authority Place (public)..."
    curl -L -o authority_place.zip "https://authority.dila.edu.tw/authority_place.zip" --max-time 300 2>&1 || \
    echo "WARNING: Download failed"
    ls -la
fi

# ========== P2.3: Generate TTL from DILA ==========
echo ""
echo "=== STEP P2.3: Generate TTL from DILA ==="
cd "$PROJECT_DIR"
if [ -f "src/python/etl/generate_ttl.py" ]; then
    python src/python/etl/generate_ttl.py
else
    echo "WARNING: generate_ttl.py not found"
fi

# ========== Export places.json from TTL ==========
echo ""
echo "=== STEP Export: places.json from TTL ==="
if [ -f "src/python/export/export_from_ttl.py" ]; then
    python src/python/export/export_from_ttl.py
else
    echo "WARNING: export_from_ttl.py not found"
fi

# ========== P5: Re-map with full DILA ==========
echo ""
echo "=== STEP P5: Re-map places with DILA ==="
cd "$PROJECT_DIR"
if [ -f "src/python/mapping/map_places.py" ]; then
    python src/python/mapping/map_places.py
else
    echo "WARNING: map_places.py not found"
fi

# ========== P6: Enrich with pyvi (Han-Viet) ==========
echo ""
echo "=== STEP P6: Enrich - translate Han-Viet with pyvi ==="
if [ -f "src/python/translation/enrich_places.py" ]; then
    python src/python/translation/enrich_places.py
else
    echo "WARNING: enrich_places.py not found, using DILA names directly"
fi

# ========== P7: Geocoding Vietnam places ==========
echo ""
echo "=== STEP P7: Geocoding Vietnam places (OSM) ==="
if [ -f "src/python/geocoding/geocode_vietnam.py" ]; then
    python src/python/geocoding/geocode_vietnam.py
else
    echo "WARNING: geocode_vietnam.py not found"
fi

# ========== P8: Export Review CSV ==========
echo ""
echo "=== STEP P8: Export Review CSV ==="
if [ -f "src/python/export/export_review.py" ]; then
    python src/python/export/export_review.py
else
    echo "WARNING: export_review.py not found"
fi

echo ""
echo "========================================"
echo "BUILD DONE: $(date)"
echo "========================================"

# ========================================
# NEW MODULES ROADMAP (Next Phase)
# ========================================
# Module 1: Spiritual Geocoder
# - Quét <place> trong dữ liệu kinh văn
# - Tạo mapping table ancient→GPS
# 
# Module 2: Timeline-Path Engine
# - Filter theo nhân vật (Person)
# - Filter theo thời gian (thế kỷ)
# - Vẽ đường đi Thầy-Trò
#
# Module 3: Map Interface
# - Icon: Bánh xe Pháp luân (Phật thuyết)
# - Icon: Bảo tháp (Tổ sư trụ trì)
# - Icon: Dấu chân (hành trình)
#
# Module 4: Sutra-to-Map Sync
# - Click Marker → Deepsearch API
# - Hiện đoạn kinh liên quan
# - "Mục lục địa lý" Đại Tạng Kinh
