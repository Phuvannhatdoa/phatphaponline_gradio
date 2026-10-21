---
id: T435
bug_id: BUG-048
title: "Bug verify: BUG-048: Cột Claude trong namevimap.html không hiện số (done/total) như cột Gemini"
status: done
created: 2026-10-20
updated: 2026-10-21
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

## Audit lại 2026-10-20 (vòng 2) — admin vẫn báo thiếu số, root cause THỰC SỰ khác

Report vòng 1 (API + HTML span + `loadCodexColStatus`) **đã có đủ trong code hiện tại**
(verify lại bằng grep: `app.py:16318` có route, `namevimap.html:726` có
`<span id="codex-col-status">`, `namevimap.html:2518` có hàm `loadCodexColStatus`). Nhưng
mở route thật bằng browser (đã login sẵn) vẫn tái hiện đúng triệu chứng admin báo: header
CLAUDE không có số dù chờ > 10s.

**Root cause thật (xác nhận bằng network log thật, không đoán):** `switchTab()`
(`namevimap.html:1007-1052`) có 2 đường vào tab ETL:
- Lần đầu vào tab (`etlTabLoaded === false`) → gọi `_etlFullLoad()` (dòng 1040), hàm này gọi
  cả 5 hàm nặng: `loadEtlStats`, `loadEtlFlagLiveData`, `etlFlagQueueLoad`,
  `loadAiColStatus`, `loadCodexColStatus` — dùng chung 1 `AbortSignal` từ
  `_etlNewAbortSignal()`.
- Lần sau quay lại tab ETL khi `etlTabLoaded === true` (dòng 1041-1044, nhánh `else`) →
  **CHỈ gọi `loadEtlFlagLiveData(sig)`**, với `sig` MỚI từ `_etlNewAbortSignal()`. Hàm này
  (dòng 1532-1534) luôn `abort()` controller cũ trước khi tạo controller mới — nếu lần vào
  tab ETL trước đó CHƯA kịp xong `etlFlagQueueLoad`/`loadAiColStatus`/`loadCodexColStatus`,
  cả 3 request đó bị abort vĩnh viễn và KHÔNG được gọi lại (nhánh `else` không gọi chúng).
  `loadEtlFlagLiveData` thì luôn được gọi lại mỗi lần quay vào tab nên tự phục hồi — đúng lý
  do admin thấy DILA name_vi/queue vẫn đúng nhưng CLAUDE/GEMINI header + "Bulk FLAG Queue"
  trống/"Đang tải…" mãi.
- Verify network log thật: `GET /api/admin/codex-transliterate/status` và
  `GET /api/admin/namevi/flag-list?...` bị `net::ERR_ABORTED` một lần, sau đó KHÔNG có
  request thay thế trong suốt phiên; trong khi 12 request `namevi-queue/<id>` cũng bị abort
  cùng lúc nhưng có bản retry 200 OK ngay sau (do `loadEtlFlagLiveData` được gọi lại).

**Kết luận:** lỗi lớp resolver/JS state (tab re-entry không đồng bộ danh sách hàm cần tải
lại) — không phải thiếu endpoint/HTML (đã đủ từ vòng 1), không phải SQLite lock chậm (đó là
nguyên nhân phụ quan sát ở BUG-050/T437, tái hiện được cả khi backend rảnh ở đây).

**Phạm vi sửa vòng 2:** sửa nhánh `else` trong `switchTab()` (dòng 1041-1044) để gọi lại đủ
`etlFlagQueueLoad`, `loadAiColStatus`, `loadCodexColStatus` mỗi khi quay lại tab ETL — không
chỉ `loadEtlFlagLiveData`. Cân nhắc gộp dùng chung `_etlFullLoad()` cho cả 2 nhánh (đơn giản
hơn, tránh lệch danh sách hàm về sau), miễn `etlSelectStep(0)` không reset state đang xem dở
không mong muốn. Backup trước khi sửa vào `docs/sessions/2026-10-20/T435/`.

## Xác nhận DONE

Admin xác nhận DONE 2026-10-21.
