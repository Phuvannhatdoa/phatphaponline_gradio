# 2026-08-16 — Fix Timeout Đạo Ảnh (places_search FTS prefix + threaded servers)

## Module
- Admin / Đạo Ảnh mapping (`admin/placevn.html` + `app.py /daoanh/api/admin/places_search`)
- Hạ tầng servers (`app.py:5000`, `local_gateway.py:8080`)

## Task
Fix "Máy chủ phản hồi chậm (Timeout)!" tái diễn trên `http://localhost:8080/daoanh/admin/placevn.html` khi gõ/tìm địa danh (VD "Thiếu Lâm Tự").

## Root cause
1. **places_search gõ dở rơi về LIKE full-scan ~15.8s:** FTS5 chỉ khớp token đầy đủ; gõ "thi"/"thieu"/"tla" → Phase 0 miss → Phase 1-3 quét `LIKE '%q%'` trên `places_pending` (176K) + `hanviet_fallback` (toàn bộ) → 1 request chậm 15.8s.
2. **Server single-threaded:** cả `app.py` (`app.run(...)` không `threaded=True`) lẫn `local_gateway.py` — 1 request chậm chặn MỌI request khác → toàn bộ `safeFetch` (timeout 20s, placevn.html:301) của frontend bị abort → timeout tràn lan.
3. **places_pending_fts nhân đôi docs:** `--force` dùng `'delete-all'` trên bảng FTS thường (lưu nội dung) → lỗi im lặng → 236,590 docs (2×118,295). Chỉ bảng external content mới được dùng `'delete-all'`; bảng thường phải `DELETE FROM`.
4. **Threshold sai:** `ensure_places_search_fts` so `places_search_fts_idx` (1,067 token segments) < src//100 (1,182) → cứ tưởng index rỗng → re-populate lặp. Đúng phải so `places_search_fts_docsize` (118,304 docs).
5. (Đã fix trước trong phiên này) `places_pending` initial-load join không sargable → 11.7s → thay bằng `_build_cate_ids_map()` cache + `id IN (json_each)` → 17-270ms.

## Giải pháp
1. **Phase 0 FTS prefix (app.py `places_search`):** thử lần lượt `"q"` (phrase) → `q` (token AND) → `<t1>* <t2>* …` (prefix AND, token sanitize, tối đa 6 token) trên **cả** `places_search_fts` + `places_pending_fts`; union id + dedupe raw/long form; cate filter; LIMIT 20. **FTS đã chạy mà không khớp → trả `[]` ngay (`mode=fts_none`)**, bỏ hẳn chuỗi LIKE 15.8s. Phase 1-3 giữ code làm fallback chỉ khi FTS chưa sẵn sàng.
2. **`threaded=True`** cho `app.py` (`app.run(...)` line cuối) và `local_gateway.py`; `get_db_connection()` thêm `timeout=10`.
3. **Rebuild sạch FTS:** `scripts/build_places_search_fts.py` — external table `places_search_fts` dùng `delete-all`, bảng thường `places_pending_fts` dùng `DELETE FROM`; `--force` rebuild sạch; ngưỡng = `_docsize`.
4. **`dashboard/restart_servers.ps1`** mới — kill 5000/8080, start 2 server có log timestamp, chờ port listening (log: `dashboard/server_restart.log`, `app_restart.{out,err}.log`, `gateway_restart.{out,err}.log`).

## Files changed
- `app.py` — Phase 0 FTS prefix + `fts_none` guard (places_search); `threaded=True`; `sqlite3.connect(timeout=10)`.
- `local_gateway.py` — `threaded=True`.
- `scripts/build_places_search_fts.py` — threshold `_docsize`, `delete-all` đúng loại bảng, `--force` rebuild sạch.
- `dashboard/restart_servers.ps1` — mới (script restart 2 server + log).

## Test
- `python -m py_compile app.py` + build script → OK.
- FTS query: `thieu*` / `thieu* lam* tu*` → 25ms → PL000000023255; `tla*` → 0.5ms → 0 (không rơi vào LIKE).
- `python scripts/build_places_search_fts.py --force` → search idx sạch (docsize=118,296), pending docs=118,295 (hết trùng).
- Qua :8080: `places_pending?cate=admin_place` init → **177ms** (cũ 11.7s); `places_search` có dấu/không dấu/ID → 20-40ms; burst 4 request (ai_judge+cbdb+passages+cbeta) → 2.3s nhưng không chặn trang (threaded).
- `node tests/run-tests.js` → PASS; `npm run e2e` → PASS (3 trang).
- Windows quirk: `npm run lint` cần bash/WSL chưa cài → lint tương đương cho `places.html` (extract JS + `node --check`) → PASS.

## Result
- Gõ dở/không dấu/ID trong ô search placevn.html trả kết quả tức thì (<100ms), không còn LIKE full-scan 15.8s.
- 1 request chậm không còn chặn các request khác (threaded) → hết "Máy chủ phản hồi chậm (Timeout)!" do hàng đợi.
