---
id: T249
title: "M7 — Maps Main (/daoanh/maps/main) + chấm liền/đứt + filter + dark mode"
module: GIS / Places
priority: high
status: pending
depends_on: [T243, T245]
created: 2026-10-06
updated: 2026-10-06
done_when: "Trang bản đồ hiển thị địa điểm DILA, phân biệt chấm nét liền/nét đứt, tooltip, filter nguồn+độ chính xác, không vỡ dark mode; các hàm getMapStatus/filterSitesBySource/getAccuracyColor hoạt động."
---

# T249 — M7 · Maps Main

> Nguồn đặc tả (Single Source): `docs/integration/Uu-Tien-1-T07-gis-buddhist-maps-consolidated.md` (M7 toàn cầu).

## 📎 Liên kết các phần khác — MỞ TRƯỚC KHI DEV
| Phần | Đường dẫn | Dùng để |
|---|---|---|
| Đặc tả M7 | `docs/integration/Uu-Tien-1-T07-gis-buddhist-maps-consolidated.md` | §UI/UX maps/main + §Implementation (getMapStatus, filterSitesBySource, getAccuracyColor) |
| T243 | `tasks/T243-m7-data-normalize-places.md` | Khóa chuẩn địa điểm |
| T245 | `tasks/T245-m7-reference-linkage-geo-cross-ref.md` | Nguồn/độ chính xác cho tooltip |
| UI D3/Leaflet có sẵn | `places.html` / `app.py` route | Copy pattern map hiện có |

## Mục tiêu
Trang **`/daoanh/maps/main`**: hiển thị tất cả địa điểm DILA, phân biệt **chấm nét liền** (DILA xác thực)
và **chấm nét đứt** (tâm hành chính/đối chiếu), tooltip, bộ lọc, không vỡ dark mode.

## Cách tiếp cận
1. Vẽ toàn bộ địa điểm DILA + biểu tượng chùa.
2. Chấm: nét liền = DILA chính xác; nét đứt = admin centroid/đối chiếu.
3. Tooltip hover: tên, nguồn, độ chính xác, phiên bản dữ liệu.
4. Bộ lọc nguồn (DILA/GeoNames/WHG/BGIS) + độ chính xác (tất cả/chỉ DILA/chỉ BGIS) → `filterSitesBySource(source)`.
5. `getMapStatus()` (trạng thái bản đồ) + `getAccuracyColor(accuracy)` (màu theo độ chính xác).
6. Kiểm tra dark mode không vỡ.

## Ràng buộc
- Code Preservation, Zero-RAM (chỉ lấy metadata + tọa độ cần vẽ).

## Acceptance criteria
- [ ] Phân biệt chấm nét liền/nét đứt (không vỡ dark mode).
- [ ] Tooltip đủ tên/nguồn/độ chính xác/phiên bản.
- [ ] `getMapStatus`, `filterSitesBySource`, `getAccuracyColor` hoạt động.