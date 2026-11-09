# T500 — nhật ký phiên 2026-10-31

Task: `tasks/T500-cbeta-catalog-volume-relations.md` · Trạng thái sau phiên: **in_progress**

## Đã làm
1. Admin phê chuẩn đề xuất xử lý hai điểm mở của QA (2026-10-30).
2. Lỗi 1 (59 work không bắt đầu từ quyển 1): chấp nhận. Tiêu chí QA đổi thành số dòng = `juans`, và mỗi quyển nằm trong `juan_start..juan_end`.
3. Lỗi 2 (file_id T0220): kiểm bằng XML cục bộ `data/cbeta/xml-p5-full/T/`. Phát hiện API sai: `T05n0220` 1–200, `T06n0220` 201–400, `T07n0220` 401–600. DB vẫn ghi `T05n0220` cho cả 600 quyển. **Chưa sửa DB.** Chờ Admin duyệt.
4. Lỗi phụ (6 alias tự trỏ): sửa `scripts/t500_apply_work_volumes.py` (bỏ `work_id == alt_code`), sao lưu DB, xóa 6 dòng trong một transaction. `work_alias` 24 → 18.

## Sao lưu
- Script trước khi sửa: `docs/sessions/2026-10-31/cbeta-volumes/t500_apply_work_volumes.py.before-t500-fix`
- Task trước khi sửa: `docs/sessions/2026-10-31/cbeta-volumes/T500-cbeta-catalog-volume-relations.md.before-fix`
- DB: `data/backups/lineage_pre_t500_fix_20261031_153200.db`

## Trạng thái
- `work_volumes` 21.513 · `volume_files` 21.513 · `work_alias` 18 · `dila_catalog_works` không đổi.
- Chưa commit. Chưa ghi DONE.

## Việc tiếp theo
1. Admin duyệt sửa `volume_files` cho T0220 theo XML (201–400 → `T06n0220`, 401–600 → `T07n0220`), có backup và một transaction.
2. Kiểm các work nhiều tập khác bằng XML cục bộ (streaming).
3. daoanh-qa kiểm lại; Admin xác nhận DONE.

## QA lại (daoanh-qa, 2026-10-31)
- Mục 1, 2, 3, 5 PASS: alias 18 không tự trỏ, số dòng và khóa không đổi, số quyển khớp `juans`, script compile.
- Mục 4 FAIL: 61 work lệch `file_id` so với XML cục bộ (2.120 dòng), gồm T0220 (400 dòng) và 60 work khác (1.720 dòng). Nguyên nhân chung: mọi work nhiều tập đều lấy file của tập đầu từ trường `file` của API.
- 3 work (X0714, L1557, GA0037) có cùng số quyển ở hai file XML, cần quy tắc chọn file.
- Hướng sửa: lấy file theo mốc `<cb:juan>` trong XML cục bộ. Sao lưu, ghi trong một transaction. Chờ Admin duyệt. Chưa ghi DONE.

## Admin duyệt (2026-10-31): "1) ok, 2) giải thích"
- Mục 1 đã thực hiện: sửa `volume_files` theo mốc `<cb:juan>` XML cục bộ cho 2.054 dòng / 58 work (gồm T0220). Backup `data/backups/lineage_pre_t500_volfiles_20261031_162355.db`. Kiểm sau ghi: 2.054/2.054 khớp đề xuất; `volume_files` và `work_volumes` đều 21.513; T0220 = T05n0220 ×200, T06n0220 ×200, T07n0220 ×200.
- Mục 2 (3 work X0714, L1557, GA0037): giữ nguyên, chờ Admin chọn quy tắc.
- Script: `scripts/t500_fix_volume_files_dryrun.py`, `scripts/t500_apply_volume_files_fix.py`.
- Còn lại: 103 dòng ở các work không có mốc trong XML cục bộ, giữ nguyên.

## Admin phê chuẩn đề xuất A (2026-10-31)
- 3 work X0714, L1557, GA0037 giữ file mà danh mục CBETA (API) đang ghi: X39n0714, L130n1557, GA036n0037. Đã kiểm trong DB: đúng như vậy, không cần ghi DB.
- Bản trùng ở file khác (X40n0714, L131–133n1557, GA037n0037, và các bản trùng khác) được ghi nhận là bản khác, không dùng trong DB.
- Còn lại: 103 dòng không có mốc quyển trong XML cục bộ, giữ nguyên.

## QA cuối (daoanh-qa, 2026-10-31): ĐẠT
- Số dòng, khóa, mồ côi: PASS (volume_files 21.513, work_volumes 21.513, work_alias 18).
- file_id so với XML cục bộ: PASS. 2.054 dòng đã sửa khớp 100%. 0 dòng lệch ngoài 3 work phương án A. 103 dòng không có mốc XML, ghi riêng.
- T0220: PASS (T05n0220 ×200, T06n0220 ×200, T07n0220 ×200).
- Số quyển: PASS (4.825 work khớp juans, 0 dòng ngoài khoảng node).
- Đủ điều kiện để Admin xác nhận DONE. Trạng thái vẫn in_progress cho đến khi Admin xác nhận.

## Admin chọn W1 phương án 2 (2026-10-31)
- Sửa 64 dòng `volume_files` không trùng theo XML cho X0714, L1557, GA0037. Giữ 5 quyển trùng theo API.
- Backup `data/backups/lineage_pre_t500_w1_20261031_215527.db`. Kiểm: 64/64 khớp XML, volume_files 21.513, work_volumes 21.513.
- Chưa đánh DONE. Chờ tester chạy lại và Admin xác nhận DONE.
