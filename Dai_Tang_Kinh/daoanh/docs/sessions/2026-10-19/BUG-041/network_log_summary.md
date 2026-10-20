# BUG-041 — Network log evidence (2026-10-19)

## Route
`http://127.0.0.1:8080/daoanh/places?mode=lineage&focus=A007928&lm=tree` → tab Truyền Thừa

## API xác minh root cause (trước khi sửa)

```
GET /daoanh/api/monk/search?q=Thiên+Nhiên      -> {"count":0,"results":[]}
GET /daoanh/api/monk/search?q=Thien+Nhien      -> {"count":0,"results":[]}
GET /daoanh/api/monk/A007928                   -> {"ok":false,"error":"Monk not found"}
GET /daoanh/api/monk/A007928/ancestor-path?root=A001719
  -> {"ok":true,"found":false,"depth":0,"path":[{id:"A007928", name_vi:"Thiên Nhiên", ...}]}
```

Kết luận: `/api/monk/search` dùng bảng `monk_dict`/`monk_name_index` (dataset khác, KHÔNG chứa
A007928). Bảng dữ liệu thật cho cây pháp hệ là `people` (DILA, id dạng "A...") — đọc qua
`_t86_person_info()` trong app.py (dòng 5953). `/api/monk/search` vì vậy không dùng được cho
tính năng search-to-navigate trong tab Truyền Thừa.

Endpoint đã tồn tại sẵn và search đúng trên bảng `people`:

```
GET /daoanh/api/persons/browse?q=Thiên+Nhiên&limit=20   -> total=16, gồm A007928
GET /daoanh/api/admin/search_all?q=Thiên+Nhiên          -> 16 person match (cate_internal='person'),
                                                             gồm A007928 và A009460 (Đan Hà Thiên Nhiên)
```//đây chính là API `_fetchLineageSearchResults()` dùng để fix.

## Request khi gõ "Thiên Nhiên" — TRƯỚC KHI SỬA

Không có request XHR/fetch nào được gọi. `#lineage-search` input handler cũ chỉ chạy
`_renderLineageSidebarHighlight(q)` — lọc DOM các `<button>` đã có sẵn trong `#lineage-quicklist`
(chuỗi ancestor-path của node đang xem, tối đa ~8-40 node). Không fetch, không navigate.
Xem code cũ (trước fix) tại `places.html.bak` trong thư mục này, dòng ~8654-8658.

## Request khi gõ "Thiên Nhiên" — SAU KHI SỬA

```
[35432.140] GET /daoanh/api/admin/search_all?q=Thiên%20Nhiên → 200 OK
[35432.317] GET /daoanh/api/admin/search_all?q=Thiên%20Nhiên → 200 OK   (debounce lần 2, do gõ lại)
[35432.519] GET /daoanh/api/admin/search_all?q=Thiên%20Nhiên → 200 OK
[35432.667] GET /daoanh/api/admin/search_all?q=Hoài%20Nhượng → [ERR_ABORTED]  (abort do debounce — đúng hành vi AbortController khi gõ tiếp)
[35432.668] GET /daoanh/api/admin/search_all?q=Hoài%20NhượngHuệ → 200 OK
```

Không có lỗi 4xx/5xx thật nào (ERR_ABORTED chỉ là abort chủ động khi debounce huỷ request cũ,
đúng thiết kế — không phải lỗi server).

## Kết quả render

- Dropdown `#lineage-search-results` hiện 16 kết quả khớp "Thiên Nhiên" (nhiều người trùng tên,
  gồm A007928 chính node đang xem và các vị khác như A009460 — Đan Hà Thiên Nhiên 丹霞天然).
- Click 1 kết quả (A009460) → `centerLineageOn('A009460')` → URL đổi sang
  `focus=A009460&lm=tree&chain=...` → cây pháp hệ đầy đủ Huệ Năng → Hành Tư → Hi Thiên → Thiên Nhiên
  render đúng, quicklist/inspector cập nhật theo node mới. Xem ảnh 03.
- Regression A001719 (Huệ Năng, có cạnh): tree vẫn render đầy đủ như cũ sau khi thêm tính năng
  search (ảnh 04), input search cũng fetch đúng (search_all trả 200).
