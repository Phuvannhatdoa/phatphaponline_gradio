# T485 — Kế hoạch tích hợp Dila ID Person và Place vào tab Catalog

- Ngày: 2026-10-29
- Task: `tasks/T485-catalog-dila-person-place-integration.md`
- Trạng thái: đã được Admin phê chuẩn đề xuất, chưa triển khai

## 1. Bối cảnh

Dila ID Person và Place đã được import vào `data/lineage.db`:

- `dila_catalog_contributors`: 5.589 dòng, 4.321 tác phẩm, 2.221 person ID, 7 dòng person_id null.
- `dila_catalog_places`: 765 dòng, 723 tác phẩm, 112 place ID.

Đối chiếu với store đang dùng:

| Đối tượng | Store Pass | Khớp |
|---|---|---|
| Person | `name_vi_map` (approved_by = 'admin') | 1.871 / 2.221 ID có dòng; 350 chưa có |
| Person | `entity` / `ai_person_name` | 2.218 / 2.221; 3 ID không có |
| Place | `namevi_map_places` | 112 / 112 |

Tên Việt trong `dila_catalog_contributors` là ZQLOCAL (5.579) và cloud_session (10). So với
`name_vi_map`, 4.222 trùng, 409 lệch, 951 không có dòng map.

## 2. Mục tiêu

Một lần Pass ở bất kỳ tab nào (Catalog, ETL/Person, Place) phải được mọi tab thấy. Tên
người và địa danh liên quan đến tác phẩm được hiển thị ngay trong tab Catalog.

## 3. Các bước triển khai

### Bước 1 — Đối soát chỉ đọc
Viết script đếm lại các số liệu ở mục 1 bằng so khớp tập ID trong Python (tránh `EXISTS`
trên bảng lớn; truy vấn kiểu đó đã chạy quá 120 giây). Ghi kết quả vào
`docs/sessions/2026-10-29/catalog-dila-link/`. Không ghi DB.

### Bước 2 — API đọc
Mở rộng `api_admin_catalog_works` (routes_places.py):

- Thêm khóa `contributors`: danh sách `{seq, person_id, name_zh, name_vi, name_vi_src,
  role_vi, name_vi_map, pass_status}`.
- Thêm khóa `places`: danh sách `{seq, place_id, name_zh, name_vi, pass_status, lat, long}`.
- Tên Việt người: ưu tiên `name_vi_map`; nếu không có thì dùng ZQLOCAL và đánh dấu nguồn.

### Bước 3 — Pass người
Route mới `POST /daoanh/api/admin/catalog-contributors/<cbeta_id>/<seq>/pass`:

- Kiểm X-Session-Token; sai thì 403.
- Ghi `name_vi_map` theo dila_id: `approved_by='admin'`, `approved_at=now`.
- Không đổi schema. Ghi audit theo cách `_persist_canonical_decision` nếu phù hợp.

### Bước 4 — Pass địa danh
Dùng `/daoanh/api/places/vi-map/<id>/approve` đã có. Không tạo route mới.

### Bước 5 — Giao diện
Trong `admin/namevimap.html`, tab Catalog: mỗi tác phẩm mở ra danh sách người và địa danh,
có nút Pass và badge nguồn. Giữ nguyên cột và thứ tự đã đổi (Hán tự, HVDic, Gemini, Claude,
Lexicon, Nguyễn Minh Tiến, Đã Pass).

### Bước 6 — Kiểm chứng
- `python -X utf8 -m py_compile routes_places.py`.
- Kiểm JS inline của `admin/namevimap.html` bằng `node --check` trên bản sao trong scratchpad.
- Browser thật tại 127.0.0.1:8080, đăng nhập bởi Admin: screenshot trước/sau, network log.
- Pass thử chỉ làm khi Admin đồng ý, và revert sau khi test để không tạo phê duyệt giả
  (như T482 đã làm).

## 4. Quyết định đã chốt

1. 409 tên lệch: Admin Pass từng dòng; hệ thống không tự chọn.
2. 350 person chưa có tên: hiển thị "chưa có"; Gemini chỉ dịch khi Admin yêu cầu riêng.
3. Pass từ Catalog ghi thẳng vào `name_vi_map` và `namevi_map_places` qua cơ chế đang chạy.

## 5. Rủi ro

- `name_vi_map` có 46.726 dòng, nhiều dòng cho cùng một dila_id. Phải chọn đúng dòng mà code
  đang đọc, không lấy bừa dòng đầu.
- Pass ghi đè tên dùng chung: ảnh hưởng tab ETL và tab Person. Cần kiểm trước khi bật.
- 3 person ID không có entity: nếu hiển thị sai nhãn sẽ gây hiểu nhầm; phải hiện rõ "không có entity".

## 6. Rollback

- Code: `git revert` theo commit khi Admin cho phép commit.
- Dữ liệu: Pass chỉ thêm/sửa `name_vi_map.approved_by/approved_at` và `namevi_map_places`.
  Trước khi chạy Pass thật, sao lưu các dòng liên quan vào `docs/sessions/2026-10-29/catalog-dila-link/`.
