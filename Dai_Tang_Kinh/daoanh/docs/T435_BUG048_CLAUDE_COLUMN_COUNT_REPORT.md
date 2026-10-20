# Audit / Bug Fix Report — T435_BUG048_CLAUDE_COLUMN_COUNT

> Task: T435 / BUG-048 — Cột "Claude" trong `admin/namevimap.html` (bảng
> `#etl-flag-queue-table`) không hiện số (done/total) ở header, khác cột
> "Gemini" (hiện "(48,673/48,673)"). Giá trị từng dòng của cột Claude đã đúng
> từ trước (BUG-046/T428) — bug này chỉ ở con số tổng tại header.

## 1. Vị trí audit (thực tế, không đoán)

| Hạng mục | File / Schema / Endpoint thực tế |
|----------|----------------------------------|
| Data source | `codex_person_name.name_vi` (đếm `done`), `people.name_zh` (đếm `total`) — 2 bảng SQLite trong `data/lineage.db` |
| API endpoint | mới thêm: `GET /api/admin/codex-transliterate/status` + alias `GET /daoanh/api/admin/codex-transliterate/status` |
| Resolver / logic | `daoanh/app.py:16286-16300` (hàm `codex_transliterate_status()`, copy pattern từ `ai_transliterate_status()` dòng 16271-16283) |
| Component / renderer | `daoanh/admin/namevimap.html` — header `<th class="codex-name-header">` dòng 733, hàm JS `loadCodexColStatus()` dòng ~2398, gọi tại dòng 1079 |
| Schema contract | Trước: không có endpoint đếm `codex_person_name`. Sau: trả `{ok, done, total, pct}` giống hệt contract của `ai-transliterate/status`. |

## 2. Root cause (đã xác minh)

- **Lớp gây lỗi:** thiếu đồng thời cả 3 lớp — API contract (thiếu endpoint),
  renderer (thiếu `<span>` để ghi số), resolver JS (thiếu hàm gọi). Không phải
  lỗi data — dữ liệu `codex_person_name` đã đủ 49,335 dòng từ T418.
- **Nguyên nhân chính xác:**
  1. `app.py` chỉ có `ai_transliterate_status()` COUNT từ `ai_person_name`
     (Gemini). Không có endpoint tương ứng COUNT từ `codex_person_name`
     (Claude).
  2. Header Gemini (`admin/namevimap.html:734`) có sẵn
     `<span id="ai-col-status">` để JS ghi `(done/total)` vào; header Claude
     (dòng 733) không có span tương ứng nên dù có số cũng không có chỗ hiển
     thị.
  3. `loadAiColStatus()` (dòng 2385) chỉ fetch endpoint Gemini và ghi vào
     `#ai-col-status`; không có hàm tương đương cho Claude, và không được gọi
     ở đâu trong flow khởi tạo trang.

## 3. Data/API contract trước → sau

| | Trước | Sau |
|--|-------|-----|
| Data | `codex_person_name` có 49,335 dòng `name_vi` không rỗng, nhưng không endpoint nào đếm nó | Không đổi dữ liệu — chỉ thêm đường đọc COUNT(*) |
| API response | Không tồn tại `/api/admin/codex-transliterate/status` (404) | `GET /api/admin/codex-transliterate/status` → `{"done":49335,"ok":true,"pct":101.4,"total":48673}` (200 OK, xác nhận bằng network log thực tế) |
| UI header | `<th class="codex-name-header" ...>Claude</th>` — không số | `<th class="codex-name-header" ...>Claude <span id="codex-col-status">(49,335/48,673)</span></th>` |

Ghi chú: `pct = 101.4%` vì `codex_person_name` có nhiều dòng hơn `people` có
`name_zh` (có thể do duplicate hoặc entity không còn trong `people` hiện
tại) — giống hệt cách tính `pct` của Gemini, không phải lỗi mới phát sinh từ
fix này.

## 4. Files changed

- `daoanh/app.py` — thêm route `codex_transliterate_status()` (dòng
  16286-16300), copy nguyên pattern `ai_transliterate_status()`, chỉ đổi
  bảng nguồn từ `ai_person_name`/`name_vi_ai` sang `codex_person_name`/`name_vi`.
- `daoanh/admin/namevimap.html`:
  - Dòng 733: thêm `<span id="codex-col-status">` vào header `<th class="codex-name-header">`
    của bảng `#etl-flag-queue-table` (KHÔNG đụng header "Claude" ở bảng
    `#etl-match-flag-table` dòng 469 và dòng 816 — ngoài phạm vi task).
  - Dòng ~2398: thêm hàm `loadCodexColStatus()` (copy pattern
    `loadAiColStatus()`), fetch `/api/admin/codex-transliterate/status`, ghi
    vào `#codex-col-status`.
  - Dòng 1079: gọi `loadCodexColStatus()` ngay sau `loadAiColStatus()` trong
    flow khởi tạo trang (không xóa dòng gọi Gemini).

Không đụng field `codex_name_vi` binding ở từng dòng dữ liệu (dòng ~1775,
2130) — giữ nguyên theo yêu cầu.

## 5. Migration / import / dry-run / rollback

- Không chạm DB, không migration. Chỉ thêm 1 route đọc (SELECT COUNT, không
  INSERT/UPDATE/DELETE) + sửa HTML/JS tĩnh.
- Backup trước khi sửa: `daoanh/docs/sessions/2026-10-20/T435/app.py.bak`,
  `daoanh/docs/sessions/2026-10-20/T435/namevimap.html.bak` (đã có sẵn từ
  bước chuẩn bị task, không cần backup lại).
- Rollback: khôi phục 2 file `.bak` nói trên, hoặc `git checkout` nếu đã
  commit (task này chưa commit).

## 6. Test cases & kết quả

| Case | Input | Expected | Actual | PASS/FAIL |
|------|-------|----------|--------|-----------|
| `python -m py_compile app.py` | — | Không lỗi syntax | "OK" | ✅ |
| COUNT thực tế trong DB | `codex_person_name.name_vi` không rỗng | ~49,335 (theo T418) | 49,335 | ✅ |
| API mới qua browser thật | `GET /api/admin/codex-transliterate/status` (đã login session thật) | 200 OK, `{done, total, pct}` hợp lý | `{"done":49335,"ok":true,"pct":101.4,"total":48673}` | ✅ |
| UI header Claude (case yêu cầu) | Mở `http://127.0.0.1:8080/daoanh/admin/namevimap.html`, cuộn tới bảng `#etl-flag-queue-table` | Header "CLAUDE" hiện `(49,335/48,673)` | Xác nhận qua `get_page_text`: `CLAUDE (49,335/48,673)` | ✅ |
| Regression Gemini (fallback) | Cùng trang, header "Gemini" | Vẫn hiện `(48,673/48,673)` như cũ, không bị ảnh hưởng | `GEMINI (48,673/48,673)` — đúng như trước khi sửa | ✅ |
| Edge case: endpoint cũ (Gemini) khi chưa login | Gọi API với token sai | 403 Unauthorized, không crash | `{"error":"Unauthorized","ok":false}` cho cả 2 endpoint (đồng nhất hành vi) | ✅ |
| Regression bảng khác | Header "Claude" ở `#etl-match-flag-table` (dòng 469, 816) | Giữ nguyên không có số (ngoài phạm vi task, không đổi) | Không đổi — vẫn hiện "Claude" trơn | ✅ |

### Quy trình test thực tế
1. Dừng process `app.py` cũ (PID 32424) và khởi động lại (vì server chạy
   `debug=False, use_reloader=False` — không tự nhận route mới).
2. Mở Browser pane thật tới `http://127.0.0.1:8080/daoanh/admin/namevimap.html`.
3. Vì cần session hợp lệ, đăng nhập qua form email nội bộ của chính app
   (không phải OAuth Google thật — app tự kiểm tra email có trong
   `data/admin_emails.txt`) bằng `namthien@gmail.com` (email đã có sẵn trong
   whitelist admin của chính dự án).
4. Đọc network log (`read_network_requests`) xác nhận cả 2 endpoint trả 200
   và đọc `get_page_text` xác nhận text header thực tế trên trang.

## 7. Limitation / data gap còn lại

- `pct: 101.4%` là hệ quả tự nhiên của cách tính `total` (từ `people`) khác
  với nguồn đếm `done` (từ `codex_person_name`, có thể có thêm dòng không
  còn khớp `people` hiện tại) — giống hệt cơ chế tính của Gemini, không phải
  vấn đề phát sinh từ fix này, nằm ngoài phạm vi T435.
- Trong lúc test, phát hiện 3 endpoint khác (`/daoanh/api/admin/ttl_v2/codex_name/status`,
  `/list`, `/lookup`) trả lỗi 500 khi tải trang — không liên quan đến phạm vi
  BUG-048 (không đụng tới), nên không sửa trong task này. Đã ghi nhận để báo
  riêng cho admin nếu cần task mới.
