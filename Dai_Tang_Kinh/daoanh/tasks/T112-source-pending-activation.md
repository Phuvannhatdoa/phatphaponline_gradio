---
id: T112
title: "Source Pending Activation — 8 nguồn implemented=0"
module: Data Governance / Source Registry
priority: low
status: done
depends_on: [T108, T70, T34]
created: 2026-09-08
updated: 2026-09-10
done_when: >
  Đánh giá 8 nguồn implemented=0 (SAT, CHGIS, BDRC, FoJin, Kanripo, TGAZ,
  SuttaCentral, 84000): mỗi nguồn có quyết định rõ (activate với data đã có sẵn /
  defer / block legal) ghi vào docs/SOURCE_REGISTRY.md + source_authority.
  KHÔNG tìm nguồn mới; chỉ kích hoạt khi dữ liệu đã tồn tại trong repo.
---

# T112 — Source Pending Activation

## Mục tiêu (đặc tả "25 nguồn" → sửa thành thực trạng 13/5/8)
8 nguồn `implemented=0` trong `source_authority`: SAT, CHGIS, BDRC, FoJin, Kanripo,
TGAZ, SuttaCentral, 84000. Tinh thần lộ trình: **"Chuẩn hóa & Tái cấu trúc, không
tìm data mới"** → chỉ kích hoạt nguồn khi dữ liệu đã có sẵn, không đẩy chi phí ingest.

## Phạm vi
- Audit từng nguồn (dữ liệu sẵn có trong repo? legal đã rõ? T70/T34 kết quả?).
- Ghi quyết định vào `docs/SOURCE_REGISTRY.md` + cập nhật `source_authority`.
- Chỉ chạy ETL khi thực sự kích hoạt (additive + backup).

## Tiến độ (2026-09-09)
- ✅ Đã audit 8 nguồn + soạn bảng quyết định **draft** vào `docs/SOURCE_REGISTRY.md` §5:
  **5 BLOCK** (BDRC/SAT/CHGIS/FoJin/TGAZ — legal chưa rõ) · **3 DEFER** (Kanripo/SuttaCentral/84000 —
  CC BY-NC-SA cần chốt phạm vi) · **1 REFERENCE_ONLY** (Wikidata). 0 kích hoạt, 0 ETL.
- ⏳ Chờ **Lee Tổng duyệt** để chốt `source_authority.integration_mode` (không đụng bảng base) → đóng T112.

## Acceptance
- 1 quyết định rõ ràng cho cả 8 nguồn (activate/defer/block), có lý do & người duyệt.
- Không phát sinh nguồn mới ngoài registry.

## D-Feedback (ráspec5 2026-09-09 — từ đặc tả nhầm "T118 Knowledge Base Management")
Đặc tả "Feedback Loop" yêu cầu: mỗi lần Tăng Ni truy vấn **không có kết quả** → hệ thống tự ghi
"Yêu cầu bổ sung dữ liệu" → Admin biết thiếu phần nào → ưu tiên nguồn cần kích hoạt. Đây là
**đầu vào ưu tiên trực tiếp cho T112** (8 nguồn pending) → gắn vào task này:

### D1 — Bảng `data_gap_requests` (additive, Zero-RAM)
- Cột: `id` · `query_vi TEXT` · `query_norm TEXT` (bỏ dấu để group) · `entity_type` ·
  `endpoint` · `user_level` · `created_at`. 0 ALTER bảng base; chỉ INSERT.
- Ghi khi retrieval handler trả **no-result** (`NOT INDEXED` checkbox hiện tại, T100 honest
  "Chưa có dữ liệu…") — một dòng INSERT đơn giản, không cần login/rate-limit kín đáo.

### D2 — Admin report
- `GET /daoanh/api/admin/data-gaps?top=50` — group theo `query_norm` (count DESC + created_at mới
  nhất + endpoint); UI: tab nhỏ trong dashboard → Lee thấy "Tăng Ni đang thiếu phần nào".

### D3 — Ánh xạ gap → nguồn
- Bảng ánh xạ additive `gap_source_hint` hoặc field `hint_source` trong `data_gap_requests` (gợi ý
  1 trong 8 nguồn: SAT/CHGIS/BDRC/FoJin/Kanripo/TGAZ/SuttaCentral/84000) → giúp Lee ưu tiên kích hoạt.
- Báo cáo tổng hợp vào `docs/SOURCE_REGISTRY.md` §5 mỗi đợt review.

### Cam kết
- Additive, read-only hệ kia, Zero-RAM (LIMIT), trung thực (không bịa kết quả khi thiếu dữ liệu),
  không gom nội dung query nhạy cảm; revert = `git revert`.
## Note r?spec6 (2026-09-09, DEPLOYMENT_SPEC)
- "query_log" trong ??c t? Deployment = **?? ph? D-Feedback** (`data_gap_requests`) ? KH?NG
t?o b?ng tr?ng; m?t b?ng duy nh?t cho c? Live Monitoring + Content Request List.
- Feedback of T?ng Ni "b?o l?i hi?n th?/sai/thi?u" = **T119 Gap 5** (`user_feedback`), t?ch kh?i gap n?y.

## X?y d?ng Batch B (2026-09-10) ? D-Feedback IMPLEMENTED
- B?ng additive `data_gap_requests` (id, entity_type, entity_id, entity_name, gap_type,
  note_plain, source_hint, status new|ack|closed, created_at; UNIQUE(entity_type,entity_id,gap_type)).
- Auto-gi?t: `_t112_record_gap` ? `/daoanh/api/entity/<id>/web-enrich` (thieu_nguon khi kh?ng
  index ???c Wikipedia) + `/daoanh/api/places/<id>` (thieu_noidung khi thi?u m? t?).
- `GET /daoanh/api/admin/data-gaps?status=&page=` (by_type t?ng h?p) + `POST .../data-gap/<id>/status`.
- `query_log` (DEPLOYMENT_SPEC) KH?NG t?o b?ng ri?ng ? ?? ph?. (xem note r?spec6 ph?a d??i)
- Tr?ng th?i: **done — Lee Tổng duyệt 2026-09-10 (phê chuẩn §5 8 nguồn: 5 BLOCK/3 DEFER/1 REFERENCE_ONLY).**
