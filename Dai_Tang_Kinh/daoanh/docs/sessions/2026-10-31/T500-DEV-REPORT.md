# T500 — DEV-REPORT (2026-10-31)

Task: `tasks/T500-cbeta-catalog-volume-relations.md`. Trạng thái: **in_progress** (chưa DONE).

Nguồn số liệu dùng trong báo cáo này: `docs/sessions/2026-10-31/T500-cbeta-volumes-session-log.md`
(nhật ký phiên dev) và `docs/qa_reports/QA-2026-10-31-T500.md` (báo cáo tester, kết luận
EVIDENCE_INCOMPLETE). Không dùng số liệu nào ngoài hai file này. Mỗi dòng dưới đây ghi rõ nguồn.

## 1. Việc đã làm trong phiên 2026-10-31

1. Admin phê chuẩn đề xuất xử lý hai điểm mở của QA 2026-10-30.
   (Nguồn: session-log mục "Đã làm" #1.)
2. Lỗi 1 (59 work không bắt đầu từ quyển 1): chấp nhận, đổi tiêu chí QA thành "số dòng = `juans`, mỗi
   quyển nằm trong `juan_start..juan_end`". Không đổi DB.
   (Nguồn: session-log mục "Đã làm" #2.)
3. Lỗi 2 (file_id T0220): kiểm bằng XML cục bộ `data/cbeta/xml-p5-full/T/`. API ghi `T05n0220` cho cả 600
   quyển; XML cho thấy 1–200→T05n0220, 201–400→T06n0220, 401–600→T07n0220.
   (Nguồn: session-log mục "Đã làm" #3.)
4. Lỗi phụ (6 alias tự trỏ): sửa `scripts/t500_apply_work_volumes.py` (bỏ điều kiện `work_id == alt_code`),
   xóa 6 dòng `work_alias` (JA123, JB005, JB125, JB134, JB214, JB277) trong một transaction, có backup
   trước. `work_alias`: 24 → 18.
   (Nguồn: session-log mục "Đã làm" #4; số liệu work_alias=18 cũng được QA-2026-10-31-T500.md xác nhận.)
5. QA vòng giữa (daoanh-qa): mục 1, 2, 3, 5 PASS; mục 4 (file_id) FAIL — 61 work lệch XML cục bộ (2.120
   dòng), gồm T0220 (400 dòng) + 60 work khác (1.720 dòng); 3 work X0714, L1557, GA0037 có cùng số quyển
   ở hai file XML, cần quy tắc chọn file.
   (Nguồn: session-log mục "QA lại (daoanh-qa, 2026-10-31)".)
6. Admin duyệt: "1) ok, 2) giải thích" — áp dụng sửa `volume_files` theo mốc `<cb:juan>` XML cục bộ cho
   **2.054 dòng / 58 work** (gồm T0220). Backup `data/backups/lineage_pre_t500_volfiles_20261031_162355.db`.
   Kiểm sau ghi: 2.054/2.054 khớp đề xuất; `volume_files` và `work_volumes` đều 21.513; T0220 =
   T05n0220×200, T06n0220×200, T07n0220×200. Script: `scripts/t500_fix_volume_files_dryrun.py`,
   `scripts/t500_apply_volume_files_fix.py`. Mục 2 (3 work X0714/L1557/GA0037) giữ nguyên, chờ Admin chọn
   quy tắc. Còn 103 dòng ở các work không có mốc trong XML cục bộ, giữ nguyên.
   (Nguồn: session-log mục "Admin duyệt (2026-10-31)".)
7. Admin phê chuẩn đề xuất **phương án A**: 3 work X0714, L1557, GA0037 giữ file mà danh mục CBETA (API)
   đang ghi (X39n0714, L130n1557, GA036n0037) — đã kiểm trong DB đúng như vậy, không cần ghi DB. Bản
   trùng ở file khác (X40n0714, L131–133n1557, GA037n0037, và các bản trùng khác) ghi nhận là bản khác,
   không dùng trong DB. 103 dòng không có mốc quyển trong XML cục bộ: giữ nguyên.
   (Nguồn: session-log mục "Admin phê duyệt đề xuất A (2026-10-31)".)
8. QA cuối (daoanh-qa, 2026-10-31): số dòng/khóa/mồ côi PASS (volume_files 21.513, work_volumes 21.513,
   work_alias 18); file_id so XML cục bộ PASS (2.054 dòng đã sửa khớp 100%, 0 dòng lệch ngoài 3 work
   phương án A, 103 dòng không có mốc XML ghi riêng); T0220 PASS; số quyển khớp `juans` PASS (4.825 work,
   0 dòng ngoài khoảng node). Kết luận: đủ điều kiện để Admin xác nhận DONE, trạng thái vẫn in_progress
   cho đến khi Admin xác nhận.
   (Nguồn: session-log mục "QA cuối (daoanh-qa, 2026-10-31): ĐẠT".)

## 2. Trạng thái DB (nguồn: session-log mục "Trạng thái")

- `work_volumes`: 21.513 dòng.
- `volume_files`: 21.513 dòng.
- `work_alias`: 18 dòng.
- `dila_catalog_works`: không đổi.
- Chưa commit. Chưa ghi DONE.

## 3. Phạm vi file (chỉ file thật sự tạo/sửa cho T500, tách khỏi file M của session khác)

Nguồn: `QA-2026-10-31-T500.md` mục `task_scope` và `files_changed (T500)`.

- `scripts/t500_apply_volume_files_fix.py` (mới)
- `scripts/t500_apply_work_volumes.py` (sửa — bỏ điều kiện `work_id == alt_code`)
- `scripts/t500_cbeta_volumes_dryrun.py` (mới)
- `scripts/t500_fix_volume_files_dryrun.py` (mới)
- `scripts/t500_work_volumes_schema.sql` (mới)
- `tasks/T500-cbeta-catalog-volume-relations.md` (sửa — mục "Tiến độ 2026-10-31")
- `docs/plans/T500-cbeta-catalog-volume-relations.md`
- `docs/sessions/2026-10-29/cbeta-volumes/` (toàn thư mục — coverage.md, license-gate.md, snapshot)
- `docs/sessions/2026-10-31/` (nhật ký, backup script/task trước sửa)
- `docs/tasktodo.md` (sửa — block T500)
- DB: 3 bảng mới additive `work_volumes`, `volume_files`, `work_alias` trong `data/lineage.db`
- `data/dila_import/cbeta_catalog_api/2026-10-29/` (snapshot API, có SHA256SUMS)

Tester ghi rõ: các file `M` khác trong `git diff --name-only HEAD` (`app.py`, `sync_cbeta_refs.py`,
`tests/test_t23x...`) **thuộc session khác, không xác định được là do T500** — không đưa vào phạm vi T500.
(Nguồn: QA-2026-10-31-T500.md dòng `files_changed (T500)`.)

## 4. Việc còn lại / cần Admin quyết (nguyên văn từ QA-2026-10-31-T500.md)

- **W1**: `volume_files_fix_proposal.csv` có 64 dòng của 3 work giữ lại (L1557: 61 dòng đề xuất
  L131/L132/L133n1557; GA0037 juan 3–4 → GA037n0037; X0714 juan 4 → X40n0714). Ngoài ra còn 5 quyển trùng
  giữa 2 file XML (`volume_files_conflicts.csv`, không nằm trong 64 dòng này). Script loại cả 3 work
  (`HOLD_WORKS`), nên cả 64 dòng không mơ hồ vẫn giữ file tập đầu theo API. Đúng với câu "Không đổi DB cho
  3 work này" của phương án A, nhưng **Admin cần xác nhận đã hiểu phương án A áp cho cả work chứ không chỉ
  5 quyển trùng**.
- **W2**: 103 dòng không có mốc XML, giữ nguyên, chưa kiểm được.
- **W3**: thiếu DEV-REPORT — đã khắc phục bằng file này.
- **W4**: tasktodo có 2 block T500 trùng marker; block mới nhất chưa phản ánh phương án A và QA cuối — đã
  gộp thành một block duy nhất trong `docs/tasktodo.md`.

## 5. Kết luận tester (nguyên văn, nguồn QA-2026-10-31-T500.md)

- `production_mutation_detected`: false (tester chỉ SELECT ở mode=ro; DB ghi trước đó là do dev, có backup
  và Admin cho phép theo session log).
- `blockers`: thiếu DEV-REPORT; chưa có Admin xác nhận DONE; W1 cần Admin xác nhận.
- `final_status`: EVIDENCE_INCOMPLETE (thiếu DEV-REPORT); các kiểm tra kỹ thuật độc lập đều đạt, có cảnh báo.
- Kết luận tester: "T500 chưa xong. Số liệu DB đúng với mô tả, nhưng còn thiếu DEV-REPORT, chưa có Admin
  xác nhận DONE, và 64 dòng của 3 work giữ file khác với XML cục bộ cần Admin xác nhận."

## 6. Việc KHÔNG làm trong lần xử lý này (theo đúng phạm vi được giao)

- Không ghi DB, không chạy script có `--apply`.
- Không sửa 64 dòng `volume_files` của L1557, GA0037, X0714 — đây là quyết định **W1** của Admin.
- Không đánh DONE, không đổi `status` trong frontmatter task, không đổi `done_when`.
- Không chạy `git add/commit/reset`.

## Cập nhật sau quyết định W1 (2026-10-31)
- Các mục trên nói 64 dòng của X0714, L1557, GA0037 chưa được sửa. Mô tả đó nay đã lỗi thời.
- Admin chọn phương án 2. Đã chạy `scripts/t500_apply_w1_volume_files.py --apply`: sửa 64/64 dòng khớp XML, giữ 5 quyển trùng theo API.
- Sao lưu: `data/backups/lineage_pre_t500_w1_20261031_215527.db`. Kiểm sau ghi: volume_files 21.513, work_volumes 21.513.
- Chi tiết hoàn tác: `docs/ROLLBACK.md`, mục T500 W1.
