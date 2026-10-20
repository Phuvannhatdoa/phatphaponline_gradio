---
id: T277
title: "Lưu trữ tài liệu tích hợp không dùng (230 file → _archive) và tích hợp dần các file còn giá trị"
module: Data Governance / Docs
priority: medium
status: in_progress
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: 00_PLAN_OVERVIEW
plan_approved_at: "2026-10-10 (Admin đồng ý chuyển nhóm bỏ/hoãn vào _archive, giữ file tích hợp được, gom thành 1 task lớn để làm dần)"
done_when: >
  (1) Nhóm bỏ/hoãn nằm trong docs/integration/_archive/ với MANIFEST.tsv, hoàn tác được bằng --restore. ĐÃ XONG.
  (2) Mỗi file còn giá trị có một dòng trong bảng Phase bên dưới, kèm module đích và điều kiện trước khi tích hợp.
  (3) Trước khi tích hợp file nào: viết lại theo cấu trúc chuẩn, bỏ số liệu không nguồn, đánh lại số module nếu trùng, qua cổng M1 nếu dùng dữ liệu ngoài.
  (4) Mỗi phase có lệnh kiểm chứng và Admin xác nhận DONE. KHÔNG tự đánh DONE.
revert: >
  Chuyển file: python -X utf8 scripts/t277_archive_integration.py --restore (đưa mọi file trong manifest về chỗ cũ).
  Không có thay đổi code hay DB.
outcome: >
  2026-10-10: đã chuyển 230 file (111 M-series, 119 Uu-Tien). Còn 18 file + thư mục Cline/ ở docs/integration/.
---

# T277 — Lưu trữ và tích hợp dần tài liệu

## 1. Đã làm

- Chuyển 230 file bỏ/hoãn vào `docs/integration/_archive/` bằng `scripts/t277_archive_integration.py --apply`. Manifest: `_archive/MANIFEST.tsv` (230 dòng + tiêu đề).
- Giữ tại chỗ (đang dùng hoặc đầu vào task khác): `00_PLAN_OVERVIEW`, `REALITY_CHECK`, `M0`–`M5` (kế hoạch), `M17`, `M136`, `M137`, `T189`–`T200`, `T255`, thư mục `Cline/`.
- Viết `_archive/README.md` giải thích nhóm và cách hoàn tác.

## 2. Việc cần làm dần

Không tích hợp nguyên văn. Mọi file phải được viết lại theo: không có số liệu không nguồn; đánh lại số module nếu trùng; có điều kiện pháp lý (M1) nếu dùng dữ liệu bên ngoài.

| Phase | File trong `_archive/` | Module đích / nối với | Điều kiện trước khi làm | Trạng thái |
|---|---|---|---|---|
| A — dữ liệu & dòng truyền | `M-series/M7-gis-buddhist-maps.md` | M3 (GPS cross-ref) | Dùng sau khi M3 có hàng đợi duyệt | ⏳ Chờ M3 |
| A | `M-series/M98-automated-lineage-preservation.md` | T275 (neo số đời TTL) | Bỏ phần blockchain và số liệu 100 năm / 90%; chỉ giữ phần đối soát dòng truyền | ✅ **ĐÃ REVISED** → `M98-automated-lineage-preservation_REVISED.md` |
| A | `M-series/M27-connection-monk-disciple.md` | Quan hệ thầy–đệ (DILA/TTL) | Bỏ số liệu "10.000+ practitioners"; sửa lỗi mã hóa; cần quyết định về dữ liệu người dùng | ✅ **ĐÃ REVISED** → `M27-connection-monk-disciple_REVISED.md` |
| A | `M-series/M51-advanced-knowledge-graph.md`, `M-series/M97-living-dharma-knowledge-graphs.md`, `M-series/M12-knowledge-graph-expansion.md` | Knowledge graph hiện có | Gộp ba file thành một spec; chỉ giữ phần đọc số liệu thật | ✅ **ĐÃ CONSOLIDATED** → `KG_CONSOLIDATED_REVISED.md` |
| A | `M-series/M70-analytics-dashboard.md`, `M-series/M99-integrated-dharma-dashboard.md` | Dashboard hiện có | Gộp thành một spec dashboard; chỉ giữ phần đọc số liệu thật | ✅ **ĐÃ CONSOLIDATED** → `DASH_CONSOLIDATED_REVISED.md` |
| B — dịch & xác minh | `M-series/M44-translation-quality.md`, `M-series/M85-ai-dharma-teachings-verification.md`, `M-series/M94-cross-cultural-dharma-translation.md` | T170 (xác minh tên), T269 (quy tắc dịch) | Sau khi T170 có kết quả pilot; tuân thủ cổng AI dịch | ⏳ Chờ T170 pilot |
| C — API & tìm kiếm | `M-series/M16-api-ecosystem.md` | API hiện có (313 route) | Liệt kê route thật trước; không mở API công khai khi chưa có license | ⏳ Chờ liệt kê route |
| D — đã đánh số lại | `M-series/T278-…` … `M-series/T282-…` (từ M1–M5 consolidated) | Chỉ tham khảo, chưa tích hợp | Viết lại theo format task khi làm tới | ⏳ Chờ khi làm tới |
| E — bỏ hẳn sau xác nhận | `M-series/M53-test.md` (rỗng) | — | Admin xác nhận xóa; hiện giữ trong archive | ⏳ Chờ Admin |

Các file còn lại trong `_archive/` (khoảng 200 file tính năng tiêu dùng, blockchain, lượng tử, BCI, haptic, và bản Uu-Tien) **không có kế hoạch tích hợp**. Giữ để tra cứu.

## 3. Các bước

- [x] **Bước 1 — Chuyển nhóm bỏ/hoãn vào `_archive/` (230 file), có manifest và lệnh hoàn tác.**
- [x] **Bước 2 — Viết `_archive/README.md` và cập nhật danh sách giữ tại chỗ.**
- [x] **Bước 3 — Đánh lại số module cho nhóm M1–M5 trùng (Phase D) thành T278–T282 (format task).**
- [ ] **Bước 4 — Phase A: viết lại M98, M27 theo quy tắc trong bảng (bỏ số liệu không nguồn).**
- [ ] **Bước 5 — Phase A: gộp M12/M51/M97 thành một spec; gộp M70/M99 thành một spec dashboard.**
- [ ] **Bước 6 — Phase A: nối M7 vào M3 sau khi M3 có hàng đợi duyệt.**
- [ ] **Bước 7 — Phase B: M44/M85/M94 sau khi T170 có kết quả pilot.**
- [ ] **Bước 8 — Phase C: M16 sau khi liệt kê route API thật.**
- [ ] **Bước 9 — Admin xác nhận DONE cho từng phase.**

## 4. Ràng buộc

- Không xóa file trong `_archive/` khi chưa có xác nhận của Admin.
- Không git commit/push nếu không có lệnh rõ ràng.
- Không đổi code hay DB trong task này trừ khi có task riêng.

## 5. Liên quan

- [00_PLAN_OVERVIEW](../docs/integration/00_PLAN_OVERVIEW.md) (kế hoạch M0–M5)
- T231 (nối LicenseGate), T275 (neo số đời TTL), T170 (xác minh tên), T269 (quy tắc dịch)
