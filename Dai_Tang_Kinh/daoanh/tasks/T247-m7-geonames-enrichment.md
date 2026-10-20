---
id: T247
title: "M7 — GeoNames Enrichment: admin centroid + CC BY + hạn credit"
module: GIS / Places
priority: medium
status: pending
depends_on: [T245]
created: 2026-10-06
updated: 2026-10-06
done_when: "Gắn tâm hành chính từ GeoNames (CC BY, có link nguồn), tôn trọng 10.000 credit/ngày; không nâng độ chính xác tâm thành điểm chùa."
---

# T247 — M7 · GeoNames Enrichment

> Nguồn đặc tả (Single Source): `docs/integration/Uu-Tien-1-T07-gis-buddhist-maps-consolidated.md` (M7 toàn cầu).

## 📎 Liên kết các phần khác — MỞ TRƯỚC KHI DEV
| Phần | Đường dẫn | Dùng để |
|---|---|---|
| Đặc tả M7 | `docs/integration/Uu-Tien-1-T07-gis-buddhist-maps-consolidated.md` | §Data GeoNames (tâm xã/huyện) |
| T245 | `tasks/T245-m7-reference-linkage-geo-cross-ref.md` | Ghi link `admin_centroid` |
| Script dir | `scripts/` | Enrichment GeoNames |

## Mục tiêu
Bổ sung **tâm xã/huyện hiện đại** từ GeoNames làm tham chiếu hành chính, ghi nguồn có link (CC BY),
tôn trọng hạn **10.000 credit/ngày** cho registered users.

## Cách tiếp cận
1. Truy vấn GeoNames tọa độ tâm hành chính; lưu kèm link nguồn (CC BY).
2. Gắn vào `geo_cross_ref` dạng `admin_centroid` (bổ sung, không thay GPS điểm chùa).
3. Giới hạn 10.000 credit/ngày; chờ/backoff nếu vượt.
4. Không nâng độ chính xác tâm huyện thành điểm của chùa.

## Ràng buộc
- Zero-RAM, ghi nguồn + license, tham chiếu không phải nguồn chính.

## Acceptance criteria
- [ ] GeoNames tâm hành chính gắn đúng dạng `admin_centroid` + link CC BY.
- [ ] Không vượt 10.000 credit/ngày.
- [ ] Không nâng tâm huyện thành điểm chùa (không gán GPS chùa = tâm hành chính).