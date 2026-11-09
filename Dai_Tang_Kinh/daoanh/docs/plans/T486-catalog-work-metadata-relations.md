# T486 — Quan hệ dữ liệu tác phẩm (Catalog + work metadata)

- Ngày: 2026-10-29
- Task: `tasks/T486-catalog-work-metadata-relations.md`
- Trạng thái: pending, chờ Admin chọn nguồn chuẩn và duyệt schema nếu cần

## 1. Nguồn dữ liệu

| Nguồn | Đường dẫn | Nội dung |
|---|---|---|
| DILA authority catalog (gốc) | `data/dila_import/authority_catalog.2026-10/json/*.json` | 5.747 bản ghi, 26 nhóm |
| Bản Việt (AI + bảng) | `data/dila_import/authority_catalog.2026-10/vn_dila_authority_catalog/*.vi.json` | 5.747 bản ghi, 32 file, trạng thái unreviewed |
| DB | `data/lineage.db`: `dila_catalog_works`, `dila_catalog_contributors`, `dila_catalog_places` | Đã nạp 2026-10-22 |
| Mục Lục NMT | `cbeta_catalog_vn` (3.122 dòng) | Không có khóa CBETA |
| Canon | `canon_catalog` (3.122 dòng) | cbeta_id NULL trong mẫu |
| Kanripo | `kanripo_catalog` (101 dòng) | dila_ref, cbeta_ref |

## 2. Khóa

- `cbeta_id` (T0785, X0989): khóa chính của tác phẩm trong DB.
- `authority_id` (CA0000745): mã DILA, điền 100%.
- `vol` (T17, C056..C057): tập; 68 dải.
- `dila_catalog_contributors.person_id` (A000903…): mã người DILA.
- `dila_catalog_places.place_id` (PL000000042393…): mã địa danh DILA.

## 3. Chênh lệch DB và file vi.json

| Trường | Khớp | Lệch | Ghi chú |
|---|---|---|---|
| dynasty_vi | 5.747 | 0 | khớp hoàn toàn |
| category_vi | 5.747 | 0 | khớp hoàn toàn |
| title_vi | 5.623 | 124 | chủ yếu chữ hoa và dấu |
| byline_vi | 4.185 | 1.562 | có cả khác nội dung và chữ Hán sót |
| contributor name_vi | 3.712 | 1.870 | ví dụ A004850, A016340 khác hẳn |

Chữ Hán sót trong DB: title_vi 13 dòng, byline_vi 33 dòng.

## 4. Quan hệ quyển

- DB chỉ có `juans` (số quyển), 36 dòng null.
- File gốc không có danh sách quyển.
- Có 68 dải vol. Cần xác định dải có phải là nhiều tập liên tiếp không.

## 5. Các bước

1. **Phân loại lệch** (chỉ đọc): so từng trường, chia loại (chữ hoa/dấu, chữ Hán sót, khác nội dung).
   Xuất CSV vào `docs/sessions/2026-10-29/work-metadata/`.
2. **Quyết định nguồn chuẩn** (Admin).
3. **Dry-run cập nhật** từ file vi.json sang DB theo nguồn đã chọn, có backup, giữ trạng thái unreviewed.
4. **Danh sách chữ Hán sót** gửi Admin xác nhận âm Việt.
5. **Liên kết tên Hán** với cbeta_catalog_vn và canon_catalog: chuẩn hoá tên (bỏ phần trong ngoặc), đếm
   khớp một-một, nhiều-một, không khớp. Ghi bảng đề xuất.
6. **Quan hệ quyển**: phân tích vol; nếu thiếu nguồn, đề xuất bảng additive (chờ duyệt).
7. **QA** đếm lại trước/sau.

## 6. Rủi ro

- Ghi đè bản Việt đã được Admin soạn tay (nếu có) khi áp file vi.json.
- Liên kết theo tên Hán có thể nhầm giữa các bản trùng tên (ví dụ bản khác dịch giả).
- Quan hệ quyển có thể không có nguồn; không được bịa danh sách quyển.

## 7. Rollback

- Backup bảng trước khi ghi vào `docs/sessions/2026-10-29/work-metadata/`.
- Cập nhật chỉ thay title_vi, byline_vi, contributor name_vi và vi_json; có thể khôi phục từ backup.
