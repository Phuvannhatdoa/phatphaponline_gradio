# 2026-08-15 — Fix lỗi 500 trang Đạo Ảnh (places_search charmap cp1252)

## Module
- Admin / Đạo Ảnh mapping (`admin/placevn.html`)
- Hạ tầng (encoding console app.py)

## Task
Fix: `GET /daoanh/api/admin/places_search` trả 500 khi tìm địa danh tiếng Việt có dấu (VD "Thiếu Lâm", "Thiếu Lâm Tự").

## Root cause
- `app.py:4293` có `print(f'[places_search] q={q!r} cate={cate!r}', flush=True)`.
- Console Windows chạy cp1252 → không encode được ký tự `ế` → `UnicodeEncodeError` → rơi vào `except` (app.py:4440) → trả **500** kèm JSON lỗi.
- `q='tla'` (không dấu) chạy OK; `q='Thiếu'` / `'Thiếu Lâm Tự'` → 500. Reproduce bằng Flask test client: `err = "'charmap' codec can't encode character '\\u1ebf'..."`.

## Giải pháp (Code Preservation — không đổi logic)
1. **Encoding toàn app:** đầu `app.py` (sau khối import hanviet, ~dòng 21) thêm:
   ```python
   _sys.stdout.reconfigure(encoding='utf-8', errors='replace')
   _sys.stderr.reconfigure(encoding='utf-8', errors='replace')
   ```
   (viết dạng vòng lặp an toàn, try/except) → chữa mọi `print(...)` tiếng Việt (13 chỗ) khỏi lỗi cp1252, không đổi logic.
2. **Subprocess UTF-8:** `api_progress_dashboard` (app.py:6139) `subprocess.run(..., text=True, timeout=60)` → thêm `encoding='utf-8', errors='replace'` → dừng `UnicodeDecodeError` ở reader thread khi chạy `?regenerate=1` (script build_progress_data.py xuất UTF-8).

## Files changed
- `app.py` — 2 khối sửa trên.

## Test
- `python -m py_compile app.py` → OK.
- Flask test client: `'Thiếu Lâm'`(admin_place) → **200, 1 place**; `'Thiếu Lâm Tự'`(temple_site) → **200, 2 places**; `'tla'` → 200.
- `GET /daoanh/api/progress/dashboard?regenerate=1` → **200** (12 modules), log sạch.
- Qua gateway :8080: `places_search?q=Thiếu Lâm Tự` → **200**; `dashboard/stats` → **200**.
- `npm run e2e` → PASS. `node tests/run-tests.js` → PASS. `npx playwright test tests/e2e-runtime.spec.js` → **2/2 PASS** (đã cài playwright chromium lần đầu).
- Lưu ý môi trường Windows: `npm run lint` cần bash/WSL (chưa cài); các file `admin/*.html` chứa `<script type="text/babel">` (JSX) không qua được `node --check` — sẵn có, không liên quan fix này.

## Result
- Đạo Ảnh mapping search tiếng Việt có dấu hoạt động 200, có kết quả.
- Log server hết traceback charmap/UnicodeDecodeError.
