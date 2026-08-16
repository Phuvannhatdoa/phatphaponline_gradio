# 2026-08-16 — Fix Autocomplete GIS Places (/daoanh/places)

## Module
- GIS Places (`places.html`, `app.py /daoanh/api/places/search`)

## Task
Fix ô search `/daoanh/places`: gõ chữ "Thiếu Lâm Tự" autocomplete không chạy; sau khi chọn gợi ý, ô search không hiện tên đã chọn (VD "Thiếu Lâm Tự"), dù thanh kết quả trái vẫn trả đúng.

## Root cause
1. **`/daoanh/api/places/search` nhạy dấu + LIKE full-scan:** `LIKE '%q%'` trên `places` + `namevi_map_places` (118K) — gõ **không dấu** `thieu lam` → **count=0**; gõ có dấu → 300-860ms/lần; gõ dở → mỗi lần 1 full-scan. (Đo thực tế: `thieu lam` = 0 kết quả, `thi` = 670ms, `Thiếu Lâm Tự` = 599ms.)
2. **Không có dropdown gợi ý:** ô search chỉ vẽ marker trên bản đồ khi tìm đủ tên — không có list "autocomplete".
3. **`selectResult()` không set `searchInput.value`:** khi click gợi ý chỉ chạy marker + flyTo + `selectItem` (panel trái đúng) nhưng ô search giữ nguyên text user đang gõ → "ô search không hiện tên".

## Giải pháp (Code Preservation)
1. **Rewrite `/daoanh/api/places/search` (app.py) với FTS fast path:**
   - `len(q)>=2`: MATCH thử `"q"` → `q` → `<t1>* <t2>* …` trên `places_pending_fts` + `places_search_fts` (union id, dedupe raw/long form).
   - Khớp: có dấu, **không dấu**, gõ dở, ID, Hán. FTS miss → trả `[]` nhanh (không LIKE full-scan).
   - Build kết quả đúng contract cũ `{id, name_zh, name_vi, lat, lng, type, confidence, source}` — GPS từ `places` (JOIN name_zh) + curated name_vi từ `namevi_map_places`.
   - Giữ nguyên nhánh `q=` rỗng (initial load `scope=temple`, batch offset) + lọc `dynasty` + `_ensure_vietnamese`.
2. **Dropdown autocomplete (places.html):**
   - `<ul id="autocompleteList">` dưới ô search (absolute, style theo trang).
   - `input` → debounce 150ms → fetch `/daoanh/api/places/search?q=…&limit=10` → render `name_vi` + `name_zh` + id.
   - Click item (`mousedown` + `preventDefault` để không bị blur nuốt) → `selectResult(r)`.
   - Enter → `doSearch` + ẩn dropdown; Escape/blur → ẩn dropdown.
3. **`selectResult()` set `searchInput.value = r.name_vi || r.name_zh || r.id`** — ô search hiện đúng tên đã chọn; set `.value` không kích hoạt `input` nên không re-search.

## Files changed
- `app.py` — rewrite `api_places_search` (nhánh `len(q)>=2`) dùng FTS + fallback LIKE khi FTS chưa sẵn sàng.
- `places.html` — dropdown `<ul id="autocompleteList">`, hàm `escapeHtml/hideAutocomplete/selectResult/runAutocomplete`, listeners input/keydown/blur.

## Test
- `python -m py_compile app.py` → OK.
- Qua :8080 `/daoanh/api/places/search`:
  - `thieu lam` (không dấu) → **4 kết quả gồm Thiếu Lâm Tự** (trước: 0).
  - `thieu lam tu` → 2; `thi` → 8; `Thiếu Lâm Tự` → 2; `PL000000000049` → 1; `少林寺` → Thiếu Lâm Tự.
  - Phản hồi 280ms-1s (FTS ensure lần đầu), không còn 0 kết quả do dấu.
- Page qua :8080: chứa `autocompleteList` + `searchInput.value = r.name_vi` (fix đã deploy qua gateway static, không cần restart).
- Lint tương đương places.html (extract JS + `node --check`) → PASS; `node tests/run-tests.js` → PASS; `npm run e2e` → PASS.

## Result
- Gõ bất kỳ (có dấu/không dấu/gõ dở/ID/Hán) → dropdown gợi ý hiện; click "Thiếu Lâm Tự" → ô search hiện đúng "Thiếu Lâm Tự" + marker bay + panel trái mở chi tiết.
- Browser cần **Ctrl+F5** để nạp `places.html` mới.
