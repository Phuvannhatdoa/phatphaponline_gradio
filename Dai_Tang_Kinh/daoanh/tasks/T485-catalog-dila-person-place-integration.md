---
id: T485
title: "Tích hợp Dila ID Person và Place vào tab Catalog (đồng bộ Pass với tab ETL và tab Place)"
status: pending
created: 2026-10-29
updated: 2026-10-29
owner: coordinator
module: Admin UI / Catalog / Identity
priority: medium
depends_on: [T482, T484]
done_when: >
  (1) GET /daoanh/api/admin/catalog-works trả thêm contributors (person_id, tên Việt,
      trạng thái Pass) và places (place_id, tên Việt, trạng thái Pass) cho từng tác phẩm,
      lấy từ dila_catalog_contributors và dila_catalog_places (chỉ đọc, không ghi DB).
  (2) Tên Việt của người lấy từ name_vi_map khi đã có dòng; tên ZQLOCAL trong
      dila_catalog_contributors chỉ là dự phòng, có badge nguồn đúng quy tắc ZQLOCAL=5.
  (3) Pass người từ tab Catalog ghi vào name_vi_map (approved_by='admin'); Pass địa danh
      ghi qua đúng route /daoanh/api/places/vi-map/<id>/approve có sẵn. Tab ETL/Person và tab
      Place thấy cùng trạng thái ngay sau khi Pass (đồng bộ theo dila_id).
  (4) Mỗi tác phẩm mở ra thấy người và địa danh liên quan, có trạng thái đã Pass hay chưa.
  (5) Số liệu đối chiếu sau tích hợp khớp báo cáo: 2.221 person ID (1.871 có name_vi_map,
      350 chưa có), 112 place ID (đều có trong namevi_map_places), 7 dòng person_id null và
      3 ID không có entity được báo rõ, không bị ẩn.
  (6) 409 tên lệch giữa Catalog và name_vi_map KHÔNG tự chọn: đưa ra danh sách để Admin
      Pass từng dòng.
  (7) python -X utf8 -m py_compile routes_places.py đạt; node --check trên script inline của
      admin/namevimap.html đạt; QA (daoanh-qa) kiểm chứng bằng browser thật tại 127.0.0.1,
      screenshot before/after, network log.
  (8) Admin xác nhận DONE.
---

## Mô tả

Import Dila ID Person và Place đã nằm trong DB: `dila_catalog_contributors` (5.589 dòng,
4.321 tác phẩm, 2.221 person ID) và `dila_catalog_places` (765 dòng, 723 tác phẩm, 112 place
ID). Task này nối hai bảng đó vào tab Catalog và bảo đảm Pass của cùng một thực thể được
ghi vào đúng store dùng chung, để mọi tab thấy cùng trạng thái.

## Kiểm tra đã làm (chỉ đọc, 2026-10-29)

| Mục | Số liệu |
|---|---|
| Person ID trong `name_vi_map` | 1.871 / 2.221 (350 chưa có) |
| Person ID trong `entity` | 2.218 / 2.221 (3 không có) |
| Place ID trong `namevi_map_places` | 112 / 112 |
| Tên Catalog trùng `name_vi_map` | 4.222 trùng, 409 lệch, 951 không có dòng map |
| `name_vi_src` của contributors | ZQLOCAL 5.579, cloud_session 10 |

Số "lệch" lấy dòng `name_vi_map` đầu tiên của mỗi ID nên là ước lượng; khi làm task phải
đếm lại theo đúng `name_vi_final` hoặc `name_vi` như code đang đọc.

## Thiết kế

1. **API (chỉ đọc).** Mở rộng `api_admin_catalog_works` trong routes_places.py: join
   `dila_catalog_contributors` và `dila_catalog_places` theo cbeta_id; với person thì join
   `name_vi_map` theo dila_id, với place thì join `namevi_map_places` theo dila_id.
2. **Pass người.** Route mới `POST /daoanh/api/admin/catalog-contributors/<cbeta_id>/<seq>/pass`
   (cần X-Session-Token): ghi `name_vi_map` theo dila_id, `approved_by='admin'`,
   `approved_at=now`. Không tạo bảng mới, không đổi schema.
3. **Pass địa danh.** Dùng nguyên route `/daoanh/api/places/vi-map/<id>/approve` đã có.
4. **Giao diện.** Mở rộng dòng tác phẩm trong `admin/namevimap.html` (tab Catalog) để liệt
   kê người và địa danh, mỗi mục có nút Pass và badge nguồn.
5. **Đối soát.** Script chỉ đọc đếm lại các số ở mục "Kiểm tra đã làm" trước và sau.

## Quyết định đã chốt (đề xuất mặc định, Admin phê chuẩn 2026-10-29)

- 409 tên lệch: Admin xem từng dòng rồi Pass. Hệ thống không tự chọn tên.
- 350 person ID chưa có `name_vi_map`: hiển thị "chưa có", không tự dịch hàng loạt. Dịch
  Gemini cho nhóm này chỉ làm khi Admin yêu cầu riêng, vì hạn mức free rất thấp.
- Pass từ Catalog ghi thẳng vào `name_vi_map` và `namevi_map_places`, dùng cùng cơ chế
  approve đang chạy ở tab ETL và tab Place.

## Ràng buộc

- Không ghi DB ngoài luồng Pass do Admin bấm. Không chạy script có `--apply` khi chưa có lệnh.
- Backup trước khi sửa code: `docs/sessions/2026-10-29/catalog-gemini/`.
- Không git add/commit/reset khi chưa có lệnh rõ ràng.
- Test bằng `127.0.0.1`, không dùng `localhost`.
- Quy tắc nguồn: DILA=1 (tên Hán), ZQLOCAL=5 (tên Việt), badge rõ nguồn trên giao diện.

## Liên quan

- T482: tab Catalog và bảng `place_catalog`.
- T484: tab Catalog cho tên Kinh (dila_catalog_works), HVDic, Gemini Free.
- Kế hoạch chi tiết: `docs/plans/T485-catalog-dila-person-place-integration.md`.
