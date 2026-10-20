---
id: T406
title: "Lỗi 'Invalid LatLng object: (NaN, NaN)' khi chọn địa danh không có toạ độ"
status: pending
created: 2026-10-15
updated: 2026-10-15
owner: unassigned
parent: T404
module: GIS / Places
priority: medium
depends_on: []
done_when: >
  (1) Xác định rõ route tái hiện: /daoanh/places, chọn một địa danh không có gps_lat/gps_long
  (kể cả khi gợi ý tự động truyền lat=null sau T404) → không còn lỗi console
  "Invalid LatLng object: (NaN, NaN)" khi gọi map.flyTo.
  (2) Kiểm cả hai nguồn gọi flyTo: chọn trực tiếp trên bản đồ và chọn từ ô Search/autocomplete.
  (3) Hành vi khi thiếu toạ độ: không crash, có fallback rõ ràng (giữ view hiện tại hoặc thông báo
  "địa danh chưa có toạ độ") — không tự suy toạ độ từ nơi khác.
  (4) Bằng chứng: console log trước/sau trên trình duyệt thật.
  (5) daoanh-qa kiểm độc lập; Admin xác nhận DONE.
---

# T406 — Lỗi flyTo NaN khi địa danh thiếu toạ độ

## Nguồn phát hiện

Ghi nhận ngoài phạm vi khi làm T404 (places.html autocomplete): `tasks/T404-places-search-autocomplete-jank.md`
mục "Phát hiện ngoài phạm vi" #2. Lỗi có sẵn từ trước T404, nhưng T404 làm lỗi dễ gặp hơn vì gợi ý
autocomplete giờ có thể truyền `lat=null`.

## Nghi vấn vị trí

`places.html` ~L1496: `map.flyTo([d.gps_lat, d.gps_long])` — chỉ kiểm truthy, không kiểm `Number.isFinite`,
nên `gps_lat`/`gps_long` là `null`/`undefined`/`NaN` vẫn lọt qua và gọi flyTo với toạ độ không hợp lệ.

## Phạm vi

Chỉ sửa chỗ gọi `flyTo` trong `places.html` (thêm kiểm `Number.isFinite` trước khi bay bản đồ) và đường
dẫn dữ liệu đưa toạ độ vào đó. Không sửa raw DILA/Marcus để vá toạ độ thiếu — nếu DB thật sự thiếu
gps_lat/gps_long cho một địa danh, đó là vấn đề data khác (xem T407 nếu liên quan A033811), không fix tại đây.

## Các bước

- [ ] Tái hiện: tìm 1 địa danh không có gps_lat/gps_long trong DB, chọn trên UI, xem console
- [ ] Backup places.html → docs/sessions/<ngày>/T406/places.html.bak-before-T406
- [ ] Sửa: thêm kiểm `Number.isFinite(lat) && Number.isFinite(lng)` trước khi gọi flyTo, fallback khi thiếu
- [ ] Kiểm trình duyệt thật: console trước/sau + ảnh chụp
- [ ] daoanh-qa kiểm độc lập
- [ ] Admin xác nhận DONE
