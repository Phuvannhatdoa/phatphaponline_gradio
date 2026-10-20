---
id: T427-2
title: "T427-2: Fix tab ETL load hang (edge-case after AbortController)"
status: pending
created: 2026-10-20
owner: null
depends_on: [T427, BUG-050, T437]
---

# T427-2 — Tab ETL kẹt "Đang tải…" (edge-case sau AbortController)

## Nguồn gốc

Tách ra từ T427 (xem `tasks/T427-namevimap-place-verification-tab.md`, mục "QA ROUND 3
FOLLOW-UP — VÒNG SỬA TIẾP" và "MERGE OPTION B"). Khi sửa lỗi 2 (tab ETL load 24-43s do
hàng đợi request nặng) bằng AbortController (`_etlAbortCtrl` trong `admin/namevimap.html`),
đã xuất hiện 1 edge-case còn tồn: nếu Admin rời tab ETL giữa lúc request đang bị `abort()`
rồi quay lại tab ETL ngay sau đó, UI có thể kẹt ở trạng thái "Đang tải…" (biến
`etlTabLoaded` / cờ loading không được reset đúng khi request bị huỷ giữa chừng, khác với
luồng "load xong bình thường" hoặc "load thất bại vì lỗi mạng thật").

Liên quan BUG-050 (namevimap stuck loading — xem
`daoanh/docs/BUG050_NAMEVIMAP_STUCK_LOADING_REPORT.md` và `tasks/T437-bug050-namevimap-stuck-loading.md`)
đã xử lý 1 dạng kẹt loading khác (timer 45s) — cần đối chiếu để không tạo 2 cơ chế
chống-kẹt chồng chéo/nhau đè nhau.

## Mục tiêu

Tab ETL không kẹt "Đang tải…" khi Admin quay lại tab sau khi request bị abort (do chuyển
tab nhanh). Phối hợp đúng với:
- BUG-050 timer 45s (timeout an toàn hiện có).
- Logic full-load của ETL (`_etlFullLoad()`, `_etlAbortCtrl`, `_etlNewAbortSignal()` —
  thêm trong T427 round 3 follow-up vòng sửa tiếp, namevimap.html ~dòng 1531-1550).

## done_when

- Tab ETL không kẹt "Đang tải…" khi quay lại sau abort; phối với BUG-050 timer 45s + ETL
  full-load logic.
- Test thật bằng browser: rời tab ETL giữa lúc request bị abort (không đợi hết 800ms /
  không đợi request xong) → quay lại tab ETL → kiểm UI hiển thị đúng dữ liệu (không kẹt
  loading vô hạn), có ảnh/network log làm bằng chứng.
- Không regression: Case A (rời trước 800ms) và Case B (ở lại đủ lâu) của T427 vẫn đúng
  như đã verify.
- `python -m py_compile app.py` OK nếu có đổi app.py; `node --check` cho nội dung
  `<script>` trong namevimap.html nếu có đổi JS.
- daoanh-qa kiểm độc lập trước khi báo Admin xác nhận DONE.

## Phạm vi

Dự kiến chỉ sửa `admin/namevimap.html` (logic `etlTabLoaded` / `_etlFullLoad()` /
`_etlAbortCtrl`). Không đổi schema DB. Backup trước khi sửa vào `docs/sessions/<ngày>/`.
