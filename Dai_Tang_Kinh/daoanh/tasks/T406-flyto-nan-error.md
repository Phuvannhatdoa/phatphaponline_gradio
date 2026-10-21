---
id: T406
title: "Lỗi 'Invalid LatLng object: (NaN, NaN)' khi chọn địa danh không có toạ độ"
status: done
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

- [x] Tái hiện: tìm 1 địa danh không có gps_lat/gps_long trong DB, chọn trên UI, xem console
- [x] Backup places.html → docs/sessions/2026-10-21/T406/places.html.bak-before-T406
- [x] Sửa: thêm kiểm `Number.isFinite(lat) && Number.isFinite(lng)` trước khi gọi flyTo, fallback khi thiếu
- [x] Kiểm trình duyệt thật: console trước/sau + ảnh chụp
- [ ] daoanh-qa kiểm độc lập
- [ ] Admin xác nhận DONE

## Kết quả thực hiện (2026-10-21)

### Audit DB
`data/lineage.db` bảng `places`: 59.161 bản ghi, 685 thiếu `gps_lat`/`gps_long`. Kiểm hết các
bản ghi này (truy vấn SELECT, không ghi) thì thấy 2 trạng thái duy nhất khi đi qua UI:
1. Record có trong `entity_hub`/`entity` → `/daoanh/api/entity/<id>/unified` trả `ok:true`,
   UI dùng nhánh T26 UNIFIED PATH (đã có `isFinite` guard sẵn, dòng ~1334-1339) → an toàn.
2. Record không match cả `entity_hub`/`entity` lẫn `places.id`/`namevi_map_places.dila_id`
   (do lệch định dạng id ngắn `PL000123` vs id dài `PL000000000123` dùng trong search/autocomplete)
   → cả unified lẫn legacy `/daoanh/api/places/<id>` đều 404 → `loadPlaceDetail` return sớm ở
   `if (!json.ok || !json.data) return;`, không chạm tới dòng flyTo — không crash nhưng panel
   kẹt "Đang tải...".

Không tìm thấy bản ghi nào hiện có trong DB mà `gps_lat`/`gps_long` vừa truthy vừa không phải
số hữu hạn (dữ liệu hiện tại sạch). Tức là với dữ liệu DB NGAY BÂY GIỜ, không có đường thực tế
nào trên UI chạm được dòng lỗi bằng dữ liệu sẵn có trong DB — lỗi là một lỗ hổng phòng thủ
(defensive gap) có thể bị kích hoạt bất cứ lúc nào dữ liệu lệch dạng (API khác, nhập liệu sau
này, hoặc path autocomplete khác truyền `lat`/`lng` không hợp lệ), đúng như mô tả gốc của T404.

### Xác nhận root cause bằng mock có kiểm soát (trước khi sửa)
Dùng `javascript_tool` (chỉ debug, không phải "fix giả") tạm chặn `window.fetch` để: (a) ép
`/daoanh/api/entity/<id>/unified` trả 404 (buộc code đi vào LEGACY FALLBACK PATH), (b) ép
`/daoanh/api/places/<id>` trả `{ok:true, data:{gps_lat:"NaN", gps_long:"NaN", ...}}` — đúng
hình dạng dữ liệu "truthy nhưng không phải số hữu hạn" nghi vấn trong task. Gọi
`window.selectItem('T406MOCK', null, null)` qua console và bắt được chính xác:

```
loadPlaceDetail error: Error: Invalid LatLng object: (NaN, NaN)
    at new v (leaflet.js:5:7245)
    ...
    at selectItem (http://127.0.0.1:8080/daoanh/places:1517:29)
```

→ xác nhận 100% root cause đúng dòng 1516-1517 (cũ) như nghi vấn trong task, không phải chỗ khác.
Đã restore `window.fetch` ngay sau bước debug, không để lại patch nào trong page.

### Thay đổi code
`places.html` dòng ~1516-1521 (cũ), thay truthy-check `if (d.gps_lat && d.gps_long)` bằng
`parseFloat` + `Number.isFinite` guard, cùng pattern với các chỗ gọi `flyTo` khác trong file
(dòng 1264, 1336, 1716, 1871, 11602 — tất cả đã có guard này từ trước, chỉ riêng nhánh
LEGACY FALLBACK PATH trong `loadPlaceDetail` là thiếu). Khi thiếu toạ độ hợp lệ: không gọi
`flyTo` (giữ nguyên view bản đồ hiện tại), `_currentGps = null`, log `console.info` thay vì để
Leaflet throw lỗi. Không thêm toast UI mới (chưa có cơ chế toast sẵn trong file, giữ thay đổi
tối thiểu theo đúng phạm vi task). Không sửa DB, không suy toạ độ từ nguồn khác.

### Kiểm lại sau khi sửa
- Lặp lại đúng mock ở trên (fetch unified→404, legacy→`gps_lat/gps_long:"NaN"`) → không còn
  "Invalid LatLng", console in `"T406: địa danh chưa có toạ độ hợp lệ, giữ nguyên view bản đồ: T406MOCK"`.
- Regression trên trình duyệt thật, KHÔNG mock, với "Thiếu Lâm Tự" (PL000000023255, có gps hợp
  lệ 34.507018/112.935331):
  - (a) click marker trên bản đồ → không có lỗi "Invalid LatLng" (chỉ có 503 rate-limit của
    endpoint khác, không liên quan T406, có sẵn từ trước).
  - (b) gõ "少林寺" vào ô Search, click gợi ý autocomplete đầu tiên → chọn đúng entity, map
    không lỗi, console sạch.
- `node --check` trên cả 3 khối `<script>` inline của `places.html` (trích xuất qua Python
  regex) → pass cả 3.
- `node scripts/lint-check.js` (từ `daoanh/`) → pass (script này hiện không liệt kê
  `places.html` trong danh sách file kiểm, không áp dụng cho file này, nhưng không có lỗi nào
  phát sinh do thay đổi).

### Bằng chứng
- Backup trước sửa: `docs/sessions/2026-10-21/T406/places.html.bak-before-T406`
- Console log before (mock, dòng gây lỗi): xem trích dẫn stack trace ở trên, trỏ đúng
  `places:1517:29` (bản cũ trước khi sửa).
- Console log after (mock): `T406: địa danh chưa có toạ độ hợp lệ, giữ nguyên view bản đồ: T406MOCK`.
- Regression real-UI: console sạch (chỉ warning dev-build + 503 không liên quan) khi chọn
  Thiếu Lâm Tự qua marker bản đồ và qua autocomplete.

### Còn lại cho daoanh-qa
- Kiểm lại diff trong `places.html` (đúng 1 chỗ, dòng ~1516-1525).
- Nếu muốn tái hiện lỗi gốc (trước sửa) bằng dữ liệu DB thật (không mock), cần một bản ghi có
  `gps_lat`/`gps_long` truthy nhưng không phải số hữu hạn — DB hiện tại không có bản ghi nào
  như vậy, nên QA có thể dùng lại kỹ thuật mock `window.fetch` ở trên trên bản `.bak-before-T406`
  nếu cần so sánh trực tiếp.
- Chưa thêm toast UI "địa danh chưa có toạ độ" — nếu Admin muốn có thông báo hiển thị cho người
  dùng (không chỉ console.info), cần task riêng vì phải thêm cơ chế toast mới vào `places.html`.
