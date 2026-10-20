---
id: T250
title: "M7 — Attribution badges (DILA/GeoNames/WHG) + Gate VN + chạy acceptance full"
module: GIS / Places
priority: medium
status: pending
depends_on: [T243, T244, T245, T246, T247, T248, T249]
created: 2026-10-06
updated: 2026-10-06
done_when: "Badge attribution hiện trong chi tiết địa danh; auto-linking VN vô hiệu (gate 200 cặp); toàn bộ acceptance M7 pass."
---

# T250 — M7 · Attribution + Gate VN + Acceptance run

> Nguồn đặc tả (Single Source): `docs/integration/Uu-Tien-1-T07-gis-buddhist-maps-consolidated.md` (M7 toàn cầu).

## 📎 Liên kết các phần khác — MỞ TRƯỚC KHI DEV
| Phần | Đường dẫn | Dùng để |
|---|---|---|
| Đặc tả M7 | `docs/integration/Uu-Tien-1-T07-gis-buddhist-maps-consolidated.md` | §Acceptance 8 tiêu chí |
| T243–T249 | `tasks/T243-...m7-...` → `tasks/T249-m7-maps-main.md` | Tổng hợp hoàn tất |
| Docs | `docs/db_schema.md`, `docs/progress.md` | Cập nhật sau khi xong |

## Mục tiêu
Nhóm các việc bọc ngoài của M7: **attribution badges** (DILA/GeoNames/WHG) trong chi tiết địa danh,
**gate vô hiệu auto-linking Việt Nam** (đến 200 cặp ground truth), và **chạy tổng acceptance** của M7.

## Cách tiếp cận
1. Attribution: hiện badge/text nguồn DILA, GeoNames, WHG trong panel chi tiết địa danh (từ `geo_cross_ref`).
2. Gate VN: **tự động linking cho dữ liệu Việt Nam vô hiệu** đến khi có ground truth ≥200 cặp minh chứng.
3. Chạy kiểm tra toàn bộ **8 acceptance criteria** của M7, ghi kết quả.
4. Cập nhật `docs/db_schema.md` (nếu có bảng mới), `docs/progress.md`, session log, rebuild dashboard.

## Ràng buộc
- Code Preservation; không tự link VN; ghi đủ nguồn + license; không để liên kết vượt 25 km.

## Acceptance criteria
- [ ] Badge/text attribution DILA/GeoNames/WHG trong chi tiết địa danh.
- [ ] Auto-linking VN vô hiệu (gate 200 cặp) — không hoàn tác khi chưa có gate.
- [ ] 8/8 acceptance M7 pass (làm bảng 8 tiêu chí + kết quả).
- [ ] Session log + rebuild dashboard hoàn tất.