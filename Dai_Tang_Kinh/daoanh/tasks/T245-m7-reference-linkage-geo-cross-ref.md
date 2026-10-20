---
id: T245
title: "M7 — Reference Linkage: geo_cross_ref (schema + 33 BGIS T31 + Wikidata P625)"
module: GIS / Places
priority: high
status: pending
depends_on: [T244]
created: 2026-10-06
updated: 2026-10-06
done_when: "'geo_cross_ref' có đủ nguồn/phiên bản/độ chính xác/độ tin cậy; 33 liên kết BGIS từ T31 giữ nguyên kèm admin_centroid; Wikidata P625 chỉ là tham chiếu thứ ba."
---

# T245 — M7 · Reference Linkage (geo_cross_ref)

> Nguồn đặc tả (Single Source): `docs/integration/Uu-Tien-1-T07-gis-buddhist-maps-consolidated.md` (M7 toàn cầu).

## 📎 Liên kết các phần khác — MỞ TRƯỚC KHI DEV
| Phần | Đường dẫn | Dùng để |
|---|---|---|
| Đặc tả M7 | `docs/integration/Uu-Tien-1-T07-gis-buddhist-maps-consolidated.md` | §Acceptance (liên kết geo_cross_ref), §Data (BGIS/Wikidata) |
| Schema DB | `docs/db_schema.md` | Bảng `geo_cross_ref`, `places_dila` |
| T244 | `tasks/T244-m7-matching-engine.md` | Đầu ra khớp để ghi link |

## Mục tiêu
Lưu từng liên kết đối chiếu có **nguồn, phiên bản, độ chính xác, độ tin cậy**;
**giữ nguyên 33 liên kết BGIS** từ T31 (gắn `admin_centroid`); **Wikidata P625** chỉ là tham chiếu thứ ba,
không dùng cho logic khớp.

## Cách tiếp cận
1. Đảm bảo/lập schema `geo_cross_ref` đủ cột: nguồn, phiên bản, độ chính xác, độ tin cậy.
2. **33 liên kết BGIS từ T31**: giữ nguyên, gắn `admin_centroid`.
3. Wikidata `P625`: chỉ ghi tham chiếu thứ ba (tag `REFERENCE_ONLY`), không tham gia tính điểm khớp.
4. Không dùng BGIS để suy ra năm lập; không nâng độ chính xác tâm hành chính.

## Ràng buộc
- Code Preservation (không phá 33 link T31), Zero-RAM, đăng ký nguồn đối chiếu.

## Acceptance criteria
- [ ] Mỗi link `geo_cross_ref` có đủ nguồn/phiên bản/độ chính xác/độ tin cậy.
- [ ] 33 link BGIS T31 giữ nguyên + `admin_centroid`.
- [ ] Wikidata P625 chỉ là tham chiếu thứ ba (không vào logic khớp).