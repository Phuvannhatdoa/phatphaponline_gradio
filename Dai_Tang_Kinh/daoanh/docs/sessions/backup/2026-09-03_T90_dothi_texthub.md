# Session 2026-09-03 — T90: Đồ Thị Text-Hub + Hierarchical Layout

## Công việc đã làm

### 1. Tab Nexus → Full-Width Main Panel
- Di chuyển nội dung Tab Nexus ra `#nexus-main-panel` (full-width, tương tự Đồ Thị / Đại Tạng)
- Thêm `_hideAllMain()` helper trong tab click handler để ẩn tất cả panels
- Viết mới `renderNexusTab` + `_renderNexusMainPanel` — header (label_vi, label_zh, id), canvas dedup, empty state
- Sidebar giữ nguyên: placeholder + stats count

### 2. Bỏ LIMIT trong `api_places_graph`
- Bỏ `LIMIT 8` trên query texts, `LIMIT 6` trên nearby places, `[:6]` slice persons
- Bỏ `title_vi IS NOT NULL` filter — hiển thị text kể cả khi chỉ có title_zh

### 3. Text-Hub Edge Routing (Backbone thay đổi)
Cấu trúc cũ: `place → person` (flat, không có thứ tự thời gian)
Cấu trúc mới: `place → text_hub → person` (hub = Tục/Tống/Minh Cao Tăng Truyện)

**Map nguồn:** `_CTT_SH = {'唐高僧傳': '2060', '宋高僧傳': '2061', '明高僧傳': '2062'}`

Logic:
- `nexus_events.source_book` → lookup `_CTT_SH` → CBETA sh_number
- Nếu text hub chưa có trong `text_node_ids`: tạo mới (từ `cbeta_catalog_vn`) + edge `place → hub`
- Edge `hub → person` (label rỗng, `has_ref=True`, `ref=source_book`)
- Fallback: nếu catalog miss → edge trực tiếp `place → person`

**Kết quả verify (PL022435 — Thiếu Lâm Tự):**
- 76 nodes: 3 text hubs + 49 địa danh lân cận + 24 tăng nhân
- `text:2060` (唐高僧傳) → 11 monks
- `text:2061` (宋高僧傳) → 12 monks (incl. Thần Tú, Phổ Tịch)
- `text:2062` (明高僧傳) → 1 monk (Thích Đại Đồng)

### 4. Hierarchical Layout LR trong Đồ Thị Main Panel
**Vấn đề:** 49 địa danh lân cận làm force-directed layout lộn xộn, không thấy cấu trúc thời gian

**Giải pháp:**
- Tách `nearbyNodes` (group=place, id≠center) → chips clickable trong strip `#gmp-nearby`
- Graph vis.js chỉ render: center (level 0) → text hubs (level 1) → persons (level 2)
- Layout: `hierarchical LR, sortMethod: directed, physics: false`
- Edges: `cubicBezier forceDirection: horizontal`

## Files thay đổi
- `places.html`: Tab click handler (nexus case), renderNexusTab, _renderNexusMainPanel, _renderGraphMainPanel (hierarchical), HTML #gmp-nearby strip
- `app.py`: api_places_graph — bỏ limits, thêm _CTT_SH, text_node_ids, text-hub edge routing

## Deployed
- SCP + restart VPS `158.220.106.183` — APP STARTED OK
- `places.html` hierarchical layout: SCP OK

## Bugs fixed (post-deploy)
1. **`series` column missing on VPS** — `cbeta_catalog_vn` trên VPS không có cột `series`
   → Bỏ `AND (series='T' OR series IS NULL)` khỏi 2 query trong `api_places_graph`
2. **`nexus_events` table missing on VPS** — T16 ETL chưa chạy trên VPS
   → Wrap query trong `try/except Exception: nexus_rows = []` (graceful degradation)
   → VPS hiển thị texts (3 hub) + nearby places (49) nhưng không có persons
   → Người dùng cần chạy T16 ETL trên VPS để bật đầy đủ (confirmed local: 24 monks)

## VPS status (sau fix)
- Graph PL022435: ok=True, 52 nodes (3 text + 49 place), 0 person (nexus_events missing)
- Local: 76 nodes đầy đủ (3 text + 49 place + 24 person)
