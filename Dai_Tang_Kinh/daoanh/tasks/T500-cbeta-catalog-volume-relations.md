---
id: T500
title: "Quan hệ quyển cho tác phẩm: ETL từ CBETA Catalog API (work → khoảng quyển → file)"
status: done
created: 2026-10-29
updated: 2026-11-01
owner: coordinator
module: Data / Catalog / Work volumes
priority: high
depends_on: [T486]
done_when: >
  (1) Đo coverage: số cbeta_id trong dila_catalog_works (5.747) có node trong CBETA Catalog API,
      tách theo node thường, node_type='alt' và không có node. Báo cáo ghi vào
      docs/sessions/2026-10-29/cbeta-volumes/coverage.md.
  (2) Snapshot API ra data/dila_import/cbeta_catalog_api/<ngày>/ dạng JSON, kèm SHA-256 cho từng file.
      ETL chạy offline từ snapshot, không gọi mạng khi nạp.
  (3) Bảng additive work_volumes (work_id, juan_no, cbeta_node_n, source_snapshot) và volume_files
      (work_id, juan_no, file_id) được tạo sau khi Admin duyệt schema. Không sửa bảng cũ.
  (4) Mỗi work có node thường: sinh đúng juan_end - juan_start + 1 dòng cho work_volumes. Ví dụ T0220
      (đã sửa 2026-10-31 theo XML cục bộ): quyển 1–200 ở T05n0220, 201–400 ở T06n0220, 401–600 ở T07n0220.
      API trả T05n0220 cho cả 600 quyển nên sai với 201–600.
  (5) node_type='alt' KHÔNG sinh quyển giả. Lưu vào bảng quan hệ work_alias (work_id, alt_work_id,
      note) hoặc báo cáo, sau khi Admin duyệt.
  (6) Kiểm chéo: tổng quyển từ node so với dila_catalog_works.juans. Sai lệch được liệt kê vào
      danh sách lỗi, không ghi đè.
  (7) Nguồn qua cổng license trước khi nạp DB (commit b71a68b0). Ghi kết quả vào
      docs/sessions/2026-10-29/cbeta-volumes/license-gate.md.
  (8) Dry-run trước; ghi DB chỉ khi Admin --apply, có backup. Có kế hoạch revert (DROP bảng mới).
  (9) QA (daoanh-qa) kiểm số liệu trước/sau. Admin xác nhận DONE.
---

## Mô tả

Quan hệ quyển của tác phẩm hiện chưa có trong DB: chỉ có `juans` (số quyển), 36 dòng null,
không biết quyển nào nằm ở file nào. Task này lấy node từ CBETA Catalog API (catalog_entry)
gồm `work`, `juan_start`, `juan_end`, `file`, rồi nạp thành hai bảng mới additive.

## Kiến thức đã kiểm chứng (2026-10-29)

- Trường của catalog_entry: `n`, `label`, `node_type`, `work`, `category`, `creator`,
  `juan_start`, `juan_end`, `file`. `alt` là giá trị của `node_type`, không phải tên trường.
- Ví dụ T0220: node CBETA.003.001.001, label "T0220 大般若波羅蜜多經 (1~200卷)", quyển 1–200,
  file T05n0220a.
- Repo DILA-edu/cbeta-metadata: thư mục `catalog/` đã ngừng từ 2026-05-21, không dùng làm cây bộ
  loại. `special-works/` chứa tác phẩm nhiều tập. Chưa xác minh được danh sách 201–400 và 401–600
  của T0220 từ repo; cần lấy từ API.
- API là cây theo tham số q: phải duyệt đệ quy từng node, không có lệnh trả đủ mọi quyển.

## Các bước

1. **Đo coverage** (chỉ đọc DB và API): lấy danh sách cbeta_id, truy vấn từng node, đếm node thường,
   alt và không có node. Kết quả ghi coverage.md.
2. **Snapshot**: lưu từng phản hồi API vào data/dila_import/cbeta_catalog_api/<ngày>/, tạo
   SHA256SUMS.
3. **Cổng license**: kiểm điều kiện sử dụng nội dung và metadata; ghi license-gate.md. Chưa qua
   thì dừng ở bước 4.
4. **Schema**: Admin duyệt hai bảng mới work_volumes và volume_files (và work_alias nếu cần).
5. **ETL dry-run**: sinh dòng quyển từ node, kiểm chéo juans, xuất CSV lỗi.
6. **Apply** khi Admin cho phép: backup DB trước, ghi trong một transaction.
7. **QA** đếm trước/sau; kiểm các mẫu T0220 và một tác phẩm nhiều tập trong special-works.

## Ví dụ kết quả khi Done

Với T0220 (Đại Bát-nhã), DB có thêm các dòng:

| work_id | juan_no | file | node |
|---|---|---|---|
| T0220 | 1 | T05n0220a | CBETA.003.001.001 (1–200) |
| T0220 | 201 | (theo API) | node tiếp theo |

Trên trang tác phẩm, Admin thấy "Quyển 1–200 → T05n0220a" thay vì một con số "600 quyển". Các
tác phẩm có node alt được đánh dấu "trỏ sang tạng khác", không có quyển giả.

## Ràng buộc

- Chỉ ghi DB sau dry-run và Admin --apply, có backup trước.
- Không đổi cbeta_id hay authority_id.
- Không git add/commit/reset khi chưa có lệnh.
- Test bằng 127.0.0.1.

## Tiến độ 2026-10-31

Admin phê chuẩn đề xuất xử lý hai điểm mở (chi tiết: `docs/sessions/2026-10-31/cbeta-volumes/`).

- **Lỗi 1 (59 work không bắt đầu từ quyển 1): chấp nhận.** `juan_no` là số quyển thật theo CBETA; `juans` là
  số quyển đang giữ, không phải chỉ số lớn nhất. Tiêu chí QA đã đổi: số dòng = `juans`, và mỗi quyển nằm trong
  `juan_start..juan_end` của node nguồn. Không đổi DB.
- **Lỗi 2 (file_id T0220): đã kiểm bằng XML cục bộ** `data/cbeta/xml-p5-full/T/`. Quyển 1–200 ở `T05n0220`
  (398 marker `cb:juan`, từ 001 đến 200), quyển 201–400 ở `T06n0220` (201–400), quyển 401–600 ở `T07n0220`
  (401–600). `volume_files` hiện ghi `T05n0220` cho 600 quyển, nên **sai với 400 quyển**. Chưa sửa DB: đang
  chờ Admin duyệt sửa theo file XML (đề xuất trong `etl_dryrun_report.md`).
- **Lỗi phụ (6 alias tự trỏ): đã xử lý.** Script `t500_apply_work_volumes.py` bỏ cặp `work_id = alt_code`.
  DB: xóa 6 dòng trong `work_alias` (JA123, JB005, JB125, JB134, JB214, JB277), 24 → 18, trong một transaction.
  Backup: `data/backups/lineage_pre_t500_fix_20261031_153200.db`.

QA lại 2026-10-31 (daoanh-qa): mục 1, 2, 3, 5 PASS. Mục 4 FAIL: ngoài T0220, **60 work khác** (1.720 dòng)
có `file_id` lệch với XML cục bộ, vì mọi work nhiều tập đều lấy file của tập đầu từ trường `file` của API.
3 work (X0714, L1557, GA0037) có cùng số quyển ở hai file XML: Admin phê chuẩn **phương án A**, giữ file
mà danh mục CBETA (API) đang ghi (X39n0714, L130n1557, GA036n0037). Không đổi DB cho 3 work này. Hướng sửa: lấy file theo
mốc `<cb:juan>` trong XML cục bộ, sao lưu và ghi trong một transaction. Chưa ghi DONE.

**Đã áp dụng (2026-10-31):** sửa `volume_files` theo mốc `<cb:juan>` XML cục bộ cho **2.054 dòng / 58 work**
(gồm T0220: 1–200→T05n0220, 201–400→T06n0220, 401–600→T07n0220). Backup
`data/backups/lineage_pre_t500_volfiles_20261031_162355.db`. Script: `scripts/t500_fix_volume_files_dryrun.py`,
`scripts/t500_apply_volume_files_fix.py`. Kiểm sau ghi: 2.054/2.054 khớp đề xuất; `volume_files` và
`work_volumes` đều 21.513.

**Admin phê chuẩn phương án A cho 3 work còn lại (2026-10-31):** X0714, L1557, GA0037 giữ file mà danh mục
CBETA (API) đang ghi (X39n0714, L130n1557, GA036n0037) — đã kiểm trong DB, đúng như vậy, không cần ghi DB.
Bản trùng ở file khác (X40n0714, L131–133n1557, GA037n0037) ghi nhận là bản khác, không dùng trong DB.
103 dòng không có mốc quyển trong XML cục bộ: giữ nguyên.

**QA cuối (daoanh-qa, 2026-10-31): ĐẠT.** Số dòng/khóa/mồ côi PASS (volume_files 21.513, work_volumes 21.513,
work_alias 18). file_id so với XML cục bộ PASS (2.054 dòng đã sửa khớp 100%, 0 dòng lệch ngoài 3 work
phương án A, 103 dòng không có mốc XML ghi riêng). T0220 PASS. Số quyển khớp `juans` PASS (4.825 work,
0 dòng ngoài khoảng node). Đủ điều kiện để Admin xác nhận DONE.

**Tester (QA-2026-10-31-T500.md): EVIDENCE_INCOMPLETE.** Hai điểm tester nêu: (1) thiếu DEV-REPORT — đã bổ
sung `docs/sessions/2026-10-31/T500-DEV-REPORT.md`; (2) **W1** — tester đề nghị Admin xác nhận rõ: phương án A
(2026-10-31) áp dụng cho **toàn bộ 64 dòng** của 3 work X0714/L1557/GA0037 (giữ file tập đầu theo API cho mọi
quyển của 3 work này), không chỉ 5 quyển trùng giữa 2 file XML (`volume_files_conflicts.csv`). Script hiện tại
loại cả 3 work khỏi vòng sửa XML (biến `HOLD_WORKS`), nên toàn bộ 64 dòng giữ nguyên theo API — đúng với lời
phê chuẩn phương án A, nhưng cần Admin xác nhận đã hiểu đúng phạm vi áp dụng trước khi đánh DONE.

Việc còn lại: **Admin xác nhận W1** (phạm vi áp dụng phương án A cho 64 dòng của 3 work) và **xác nhận DONE**
cho T500. Không tự đánh DONE, không đổi `done_when`.

**2026-11-01: Admin xác nhận DONE.** Bằng chứng: QA đạt (2026-10-31), tester PASS_WITH_WARNINGS, W1 phương
án A áp dụng cho cả 64 dòng (Admin chọn).

## Liên quan

- T486: quan hệ dữ liệu tác phẩm (nguồn chuẩn tên Việt, xác minh tác giả).
- Kế hoạch chi tiết: docs/plans/T500-cbeta-catalog-volume-relations.md.
