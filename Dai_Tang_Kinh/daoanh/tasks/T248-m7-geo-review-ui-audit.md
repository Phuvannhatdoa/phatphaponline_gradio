---
id: T248
title: "M7 — Geo Review UI (/daoanh/admin/geo_review.html) + audit log"
module: GIS / Places
priority: high
status: pending
depends_on: [T245, T246, T247]
created: 2026-10-06
updated: 2026-10-06
done_when: "Trang duyệt hiện 2 ứng viên cạnh nhau + Accept/Reject/Later + mini-map theo độ chính xác + audit log cho mỗi hành động."
---

# T248 — M7 · Geo Review UI + Audit

> Nguồn đặc tả (Single Source): `docs/integration/Uu-Tien-1-T07-gis-buddhist-maps-consolidated.md` (M7 toàn cầu).

## 📎 Liên kết các phần khác — MỞ TRƯỚC KHI DEV
| Phần | Đường dẫn | Dùng để |
|---|---|---|
| Đặc tả M7 | `docs/integration/Uu-Tien-1-T07-gis-buddhist-maps-consolidated.md` | §UI/UX geo_review + §Acceptance (audit log) |
| T245 | `tasks/T245-m7-reference-linkage-geo-cross-ref.md` | Nguồn link cần duyệt |
| UI admin mẫu | `/daoanh/admin/*.html` (thư mục admin/) | Copy pattern UI hiện có |
| Schema | `docs/db_schema.md` | Bảng audit (en_audit_log...) |

## Mục tiêu
Trang **`/daoanh/admin/geo_review.html`**: hàng đợi duyệt ứng viên địa lý 2 bên cạnh nhau,
cho phép **Accept / Reject / Later**, mini-map theo độ chính xác, và **audit log** cho mọi hành động.

## Cách tiếp cận
1. Hàng đợi: mỗi dòng 2 ứng viên (tên Hán, tên Việt, nguồn, tọa độ, độ chính xác) + điểm khớp + khoảng cách.
2. Nút Accept / Reject / Later; mỗi hành động ghi **audit log** (ai, khi nào, quyết định, dữ liệu trước/sau).
3. **Mini-map** mỗi ứng viên: vẽ 2 điểm + đường nối, màu theo độ chính xác (xanh/andng/đỏ).
4. Audit tool detail khi hover ứng viên.

## Ràng buộc
- Mọi action có audit log (bắt buộc acceptance M7), Code Preservation UI hiện có.

## Acceptance criteria
- [ ] Hiển thị 2 ứng viên + điểm khớp + khoảng cách.
- [ ] Accept/Reject/Later hoạt động; mỗi hành động có 1 dòng audit log.
- [ ] Mini-map đổi màu theo độ chính xác (xanh/vàng/đỏ).