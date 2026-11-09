---
id: T241
title: "GPS Chùa Việt Nam — Tầng 0/1 (Wikidata + OpenStreetMap), cơ sở dữ liệu places_vn"
module: GIS / Places
priority: medium
status: done
depends_on: []
created: 2026-10-06
updated: 2026-10-06
done_when: "Đặc tả thiết kế cấu trúc Tầng 0/1 (Wikidata+OSM) hoàn chỉnh: schema places_vn + logic khớp + acceptance + task/docs đã đăng ký. Phần triển khai code ETL/DB bàn giao cho T242."
---

# T241 — GPS Chùa Việt Nam (Tầng 0/1 Wikidata + OSM)

> Đặc tả chi tiết: `docs/integration/Uu-Tien-1-T07-gis-buddhist-maps-vietnam-consolidated.md` (M7-VN).

> **Phạm vi task: THIẾT KẾ CẤU TRÚC + ĐĂNG KÝ TÀI LIỆU — ĐÃ DONE (2026-10-06).**
> Phần **triển khai ETL / DB / dashboard** đã bàn giao cho **T242**: `tasks/T242-vn-temple-gps-t0t1-implementation.md`.

## Mục tiêu

Thu thập **ground truth GPS** cho chùa / tổ đình / tự viện / thiền viện Việt Nam từ 2 nguồn
mở miễn phí: **Wikidata `P625` (Tầng 0)** và **OpenStreetMap Overpass `religion=buddhist` (Tầng 1)**,
đổ vào bảng RAW `places_vn` theo format mirror chuẩn DILA với ID namespace `VN`+10 số.
**Bỏ qua GPS DILA** cho phạm vi VN (DILA không phủ chùa VN hiện đại).

## Nguyên tắc

- Zero-RAM: ETL dùng generator/iterator, không nạp toàn bộ dữ liệu vào RAM.
- Code Preservation: KHÔNG ghi đè `places_dila` / `places` / `entity` hiện có.
- 3-Layer model: RAW `places_vn` → STAGING `places_vn_pending` → FINAL merge.
- Mỗi nguồn phải đăng ký vào `dataset_sources` (`origin_url`, `license`, `usage_level`).
- Mọi GPS tự động thu thập được phép **trực tiếp**; liên kết lịch sử↔hiện đại vẫn **vô hiệu** đến 200 cặp ground truth.

## Cách tiếp cận

### Tầng 0 — Wikidata (seed, chất lượng cao)
1. Tạo `scripts/vn_places_t0_wikidata.py` (generator + try-except tiếng Việt).
2. SPARQL: entity chùa VN (`P17=Q881` Việt Nam + subclass temple) kèm `P625` (tọa độ),
   `P131` (đơn vị hành chính), `P138` (tông phái, nếu có), label vi/en/zh, sitelink Wikipedia.
3. Xuất `data/vn_places_t0_wikidata.json` → đăng ký nguồn Wikidata (CC0, GREEN) → import `places_vn` (id `VN...`, `accuracy='dila_exact'`).

### Tầng 1 — OpenStreetMap Overpass (số lượng lớn)
4. Tạo `scripts/vn_places_t1_osm.py`.
5. Overpass `node/way/relation["amenity"="place_of_worship"]["religion"="buddhist"]` trong bbox VN; tính centroid cho way/relation.
6. Dedupe với Tầng 0 (khoảng cách <200 m + trùng tên) → giữ record mới.
7. Xuất `data/vn_places_t1_osm.json` → đăng ký nguồn OSM (ODbL, GREEN + attribution) → import `places_vn` (`accuracy='osm_centroid'`).

### Merge + kiểm định
8. Tạo `scripts/vn_places_merge_validate.py`: gộp T0+T1, gắn `source`/`accuracy`, validate bbox VN, chống trùng ID `PL*`.
9. Cập nhật `docs/db_schema.md` (thêm bảng `places_vn` + ghi chú 3-layer).
10. Session log `docs/sessions/2026-10-06_T241_t0t1.md` + cập nhật master `session.md`.
11. Chạy `python scripts/build_progress_data.py` → dashboard cập nhật.

## Acceptance criteria — PHẠM VI THIẾT KẾ (đã tick đủ, DONE)

- [x] File đặc tả M7-VN tồn tại (8 khối) + đăng ký trong `docs/integration/`.
- [x] Schema `places_vn` định nghĩa (17 cột, ID `VN`+10 số, bbox VN).
- [x] 3-Layer model + `dataset_sources` + logic khớp + acceptance của đặc tả.
- [x] Task T241 + docs (`tasktodo.md` / `progress.md`) đã đăng ký.
- [x] Phần triển khai ETL/DB/dashboard đã cắt sang **T242** (không thất thoát).

> ✅ Các acceptance về **dữ liệu thật** (output JSON >0, import `places_vn`, `dataset_sources` thật, rebuild dashboard) được chuyển sang **T242**.