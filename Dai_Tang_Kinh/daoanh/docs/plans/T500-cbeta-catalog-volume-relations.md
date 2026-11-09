# T500 — Quan hệ quyển từ CBETA Catalog API

- Ngày: 2026-10-29
- Task: `tasks/T500-cbeta-catalog-volume-relations.md`
- Trạng thái: pending, chờ Admin duyệt schema và cổng license

## 1. Mục tiêu

Biết mỗi tác phẩm gồm những quyển nào và quyển nào nằm trong file nào, dựa trên nguồn CBETA
Catalog API. Thay cho con số `juans` đơn lẻ.

## 2. Nguồn

- CBETA Catalog API, endpoint catalog_entry (duyệt theo tham số q).
- Các trường dùng: `work`, `juan_start`, `juan_end`, `file`, `node_type`, `label`.
- Repo `DILA-edu/cbeta-metadata`: dùng `special-works/` và `work-info/`. Không dùng `catalog/`
  (đã ngừng từ 2026-05-21).

## 3. Thiết kế dữ liệu (đề xuất, chờ duyệt)

| Bảng | Khóa | Cột chính | Ghi chú |
|---|---|---|---|
| work_volumes | (work_id, juan_no) | cbeta_node_n, source_snapshot | additive, mới |
| volume_files | (work_id, juan_no) | file_id | additive, mới |
| work_alias | (work_id, alt_work_id) | note | additive, cho node_type='alt' |

Không thêm cột vào `dila_catalog_works`. Không sửa khóa cũ.

## 4. Quy tắc ETL

1. Với mỗi node thường có `juan_start` và `juan_end`: sinh một dòng cho từng quyển trong khoảng.
2. Node `node_type='alt'`: không sinh quyển, ghi vào work_alias.
3. Node không có `juan_start`: ghi vào danh sách lỗi, không đoán.
4. Kiểm chéo: tổng quyển của các node cùng work so với `dila_catalog_works.juans`. Lệch thì ghi
   vào danh sách lỗi.

## 5. Các bước

1. Đo coverage (chỉ đọc). Ghi coverage.md.
2. Snapshot API vào `data/dila_import/cbeta_catalog_api/<ngày>/` kèm SHA256SUMS.
3. Qua cổng license. Ghi license-gate.md.
4. Admin duyệt schema (ba bảng ở mục 3).
5. ETL dry-run, xuất CSV lỗi và báo cáo.
6. Apply khi Admin cho phép, có backup, trong một transaction.
7. QA đối chiếu mẫu T0220 và một tác phẩm trong special-works.

## 6. Rủi ro

- Một phần DILA không nằm trong CBETA: coverage thấp, phải báo rõ.
- API có thể đổi cấu trúc hoặc giới hạn tốc độ: snapshot để tránh phụ thuộc mạng.
- Lệch giữa juans trong DB và tổng quyển từ API: không tự sửa, báo Admin.

## 7. Rollback

- Bảng mới: `DROP TABLE work_volumes, volume_files, work_alias` (không ảnh hưởng dữ liệu cũ).
- Snapshot và backup DB giữ trong `docs/sessions/2026-10-29/cbeta-volumes/`.

## 8. Liên quan

- T486: quan hệ dữ liệu tác phẩm.
- Kiểm chứng ngày 2026-10-29: xem phần "Kiến thức đã kiểm chứng" trong task.
