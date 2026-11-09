# T500 — ETL dry-run quan hệ quyển (chỉ đọc)

- Ngày: 2026-10-29
- Script: `scripts/t500_cbeta_volumes_dryrun.py`
- Đầu vào: `data/dila_import/cbeta_catalog_api/2026-10-29/catalog_entry_raw.json` (offline, không gọi mạng)
- Không ghi DB. Schema nháp: `scripts/t500_work_volumes_schema.sql` (chưa áp dụng).

## Số liệu

| Chỉ số | Giá trị |
|---|---|
| Work trong DB | 5.747 |
| Work có node tác phẩm (`node_type = work`) | 4.899 |
| Work không có node tác phẩm | 848 (847 không có node nào, 1 chỉ có node alt tương đương) |
| Dòng quyển sinh ra (`work_volumes_dryrun.csv`) | 21.513 |
| Work có số quyển khớp DB (sau gộp union) | 4.825 |
| Work lệch số quyển | 74 (đều thuộc nhóm Y, API không trả thông tin quyển) |
| Node thiếu thông tin quyển | 150 (thuộc 75 work: 74 Y, 1 X) |
| Quyển bị gán cho nhiều file khác nhau | 0 |
| Node alt | 902 (888 không tách được mã tương đương, 14 có mã tương đương trong DB) |
| Dòng alias trong DB (`alias_dryrun.csv`) | 49 |

## Phát hiện làm thay đổi kế hoạch

1. **Plan giả định API luôn có `juan_start` và `juan_end`. Sai.** Trong 11.209 node tác phẩm, 11.173 node chỉ có `juan_start` (thường là 1), không có `juan_end`. Số quyển nằm trong nhãn, ví dụ `T0397 大方等大集經 (60卷)`. Dry-run đọc nhãn `(N卷)` khi thiếu `juan_end`, và ghi nguồn từng dòng (`api_range` hoặc `label_count`).

2. **Ví dụ T0220 trong plan sai.** Plan ghi node `CBETA.003.001.001` quyển 1–200 file `T05n0220a`. Dữ liệu thật: node `CBETA.003.001.001` là quyển 1–400, file `T05n0220`, và T0220 có tổng cộng 600 quyển.

3. **Một tác phẩm có nhiều node trùng.** T0220 có node `orig-T.005.001` ghi cả 600 quyển, cùng với các node chia nhỏ (1–400, 401–537, …, 593–600). A1057 có hai node giống hệt nhau. Cộng dồn từng node sẽ đếm trùng. Dry-run gộp theo tập số quyển (union).

4. **Nhóm Y không có thông tin quyển trong API.** 74 work có node nhưng không có `juan_start`/`juan_end`, cũng không có nhãn `(N卷)`. Các work này không sinh dòng quyển và được ghi vào lỗi để Admin xem.

## Lỗi cần Admin xem

Xem `errors_dryrun.csv`. Chưa có lỗi nào được tự sửa.

- `lệch_juans_db_vs_api` (74): DB có số quyển, API không có. Cần Admin quyết nguồn nào giữ.
- `node_thiếu_juan` (150): node không có thông tin quyển.

## Quyết định của Admin (2026-10-29)

1. **Đã thêm cột `juan_source`** vào `work_volumes` (`api_range` hoặc `label_count`) trong bản nháp schema.
2. **Nhóm Y (74 work, 75 kể cả X1123): giữ nguyên số quyển theo DB.** ETL không sinh dòng quyển từ API cho các work này. Ghi vào `errors_dryrun.csv` để theo dõi.
3. **Cách lưu quyển** (xem giải thích bên dưới). Chưa đổi schema; chờ Admin quyết khi duyệt tiếp.

## Cách lưu quyển: theo từng quyển hay theo khoảng

- **Theo từng quyển** (schema hiện tại): mỗi quyển một dòng. T0220 có 600 dòng, T0397 có 60 dòng.
- **Theo khoảng**: mỗi đoạn quyển liên tục cùng file một dòng, ví dụ T0220 gộp thành các đoạn 1–400, 401–537…

Toàn bộ 21.513 dòng theo quyển gộp lại được thành **4.829 dòng theo khoảng** (số đo trong dry-run).

## Đề xuất cần Admin quyết sau này

- Chọn một trong hai cách lưu. Theo từng quyển dễ tra cứu từng quyển, theo khoảng gọn và nhẹ hơn nhiều.

## Đã áp dụng (2026-10-30, theo lệnh Admin "ok" và cách lưu theo từng quyển)

- Sao lưu trước khi ghi: `data/backups/lineage_pre_t500_20261030_134418.db`.
- Script: `scripts/t500_apply_work_volumes.py --apply` (một transaction, rollback nếu kiểm sau ghi không khớp).
- Trước: 3 bảng chưa có. Sau: `work_volumes` 21.513 dòng, `volume_files` 21.513 dòng, `work_alias` 24 dòng.
- `dila_catalog_works` không đổi: 5.747 dòng, tổng `juans` 26.497 (trước và sau bằng nhau).
- Kiểm chéo trực tiếp trong DB: không có dòng mồ côi, không trùng khóa, mọi work đều có trong `dila_catalog_works`, số quyển của 4.825 work khớp `juans`. T0220: 600 dòng, quyển 1–600, file `T05n0220`.
- Dòng alias: dry-run ghi 49 dòng, sau khi khử trùng cặp (work, mã alt) còn 24 dòng.
- Chưa có QA độc lập bằng daoanh-qa. Kiểm trên là kiểm trực tiếp bằng truy vấn.

## Cập nhật 2026-10-31 (phê chuẩn đề xuất xử lý hai điểm mở)

- **Lỗi 1 (59 work có quyển không bắt đầu từ 1): chấp nhận.** `juan_no` là số quyển thật theo CBETA. Tiêu chí QA đổi thành: số dòng = `juans`, và mỗi quyển nằm trong `juan_start..juan_end` của node nguồn. Không sửa DB.
- **Lỗi 2 (file_id T0220): API sai, đã kiểm bằng XML cục bộ** `data/cbeta/xml-p5-full/T/`:
  - `T05/T05n0220.xml`: quyển 1–200 (marker `cb:juan` 001 → 200).
  - `T06/T06n0220.xml`: quyển 201–400.
  - `T07/T07n0220.xml`: quyển 401–600.
  - `volume_files` hiện ghi `T05n0220` cho cả 600 quyển, nên sai với 400 quyển (201–600). **Chưa sửa DB.** Đề xuất: sửa theo khoảng đã đo ở trên, sao lưu trước, một transaction, Admin duyệt.
  - Cần kiểm thêm: các work nhiều tập khác, bằng cách đối chiếu juan marker trong XML cục bộ (đọc streaming, không nạp cả file vào RAM).
- **Lỗi phụ (6 alias tự trỏ): đã xử lý.** Script bỏ cặp `work_id = alt_code`. DB xóa 6 dòng trong một transaction: `work_alias` 24 → 18. Backup: `data/backups/lineage_pre_t500_fix_20261031_153200.db`.
- Số liệu sau xử lý: `work_volumes` 21.513, `volume_files` 21.513, `work_alias` 18.
