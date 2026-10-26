---
id: T435
bug_id: BUG-048
title: "Bug verify: BUG-048: Cột Claude trong namevimap.html không hiện số (done/total) như cột Gemini"
status: in_progress
created: 2026-10-20
updated: 2026-10-20
owner: null
module: Admin / namevimap.html
priority: low
depends_on: [T418, T428]
done_when: >
  Header cột "Claude" trên http://127.0.0.1:8080/daoanh/admin/namevimap.html
  hiện số dạng (done/total) giống header cột "Gemini" (hiện "(48,673/48,673)").
  Số lấy từ COUNT(*) thật trong bảng codex_person_name (WHERE name_vi IS NOT NULL
  AND name_vi != ''), không hard-code. Admin xác nhận DONE sau khi xem screenshot
  before/after + network log API trả đúng field.
---

# T435 / BUG-048 — Cột Claude namevimap.html không show number

## Triệu chứng (Admin báo)

Route: `http://127.0.0.1:8080/daoanh/admin/namevimap.html`

Cột "Claude" trong bảng (ETL FLAG queue, `#etl-flag-queue-table`) hiển thị trống,
không có số như cột Gemini ("Gemini 48,673/48,673"). Cột TTL name_vi, DILA name_vi
hiển thị bình thường (đây là nói về SỐ ĐẾM ở header, không phải giá trị từng dòng
— giá trị từng dòng đã đúng từ BUG-046/T428).

## Root cause đã xác minh (audit trước khi sửa)

1. **HTML thiếu element**: header Gemini (`admin/namevimap.html` dòng 734) có
   `<span id="ai-col-status">` để JS ghi `(done/total)` vào. Header Claude
   (dòng 733, `<th class="codex-name-header">`) KHÔNG có span tương ứng
   → không có nơi để JS ghi số vào, dù JS có chạy cũng không hiện được.
2. **JS không gọi API cho Claude**: hàm `loadAiColStatus()` (dòng 2385-2396)
   chỉ fetch `/api/admin/ai-transliterate/status` (đếm bảng `ai_person_name` —
   Gemini) và ghi vào `#ai-col-status`. Không có hàm tương ứng cho Claude
   (`codex_person_name`).
3. **API thiếu endpoint**: `app.py` chỉ có `ai_transliterate_status()`
   (dòng 16269-16283, COUNT từ `ai_person_name`). Không có endpoint đếm
   `codex_person_name` (ví dụ `/api/admin/codex-transliterate/status`).

→ Đây là bug thiếu cả 3 lớp (API + HTML + JS binding), không phải data sai.
Dữ liệu `codex_person_name` đã có đủ 49,335 dòng (xác nhận qua T418), chỉ là
UI chưa có đường ống hiển thị con số này ở header.

## Phạm vi sửa

1. `app.py`: thêm route GET `/api/admin/codex-transliterate/status` (+ alias
   `/daoanh/api/admin/codex-transliterate/status`) — COUNT(*) FROM
   `codex_person_name` WHERE name_vi IS NOT NULL AND name_vi != '' làm `done`,
   tổng `people` có name_zh làm `total` (giống logic Gemini).
2. `admin/namevimap.html`:
   - Dòng 733: thêm `<span id="codex-col-status">` trong header Claude.
   - Thêm hàm `loadCodexColStatus()` tương tự `loadAiColStatus()`, gọi vào
     cùng chỗ với `loadAiColStatus()` (dòng ~1078).
3. Không đổi field `codex_name_vi` ở từng dòng (đã đúng, không đụng).
4. Backup 2 file trước khi sửa vào `docs/sessions/2026-10-20/T435/`.

## Test bắt buộc

- Mở browser thật tới route trên, screenshot trước (header Claude trống).
- Sau fix: screenshot header Claude hiện "(N/total)", network log xác nhận
  API mới trả 200 + đúng field done/total.
- Edge case: API lỗi (DB lock) → header giữ rỗng, không crash JS khác
  (ví dụ Gemini vẫn hiện số bình thường — không regression).

**Admin xác nhận DONE (2026-10-26).** Báo cáo: docs/T435_BUG048_FINAL_REPORT.md (BUG-048). Trạng thái DONE đã ghi trong docs/bugs.md (commit b1832c7f).
