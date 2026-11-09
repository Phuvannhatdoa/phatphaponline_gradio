# Audit / Bug Fix Report — T470_PHASE2_BOSUNG

> Vòng bổ sung PHASE 2 (2026-10-26) của T470 — đã được Admin duyệt thêm theo
> prompt. Tiếp nối sau vòng 1 (12.560 ô birth/death ghi, revert 218 ô TCN).

## 1. Vị trí audit (thực tế)

| Hạng mục | File / Schema / Endpoint thực tế |
|----------|----------------------------------|
| Data source (JSON) | `daoanh/data/dila_import/extracted/A*.json` (49.487 file) |
| CSV đối chiếu đầu vào | `docs/sessions/2026-10-26/dila_json_reconcile_after_v2.csv`, `dila_id_missing_from_people.csv` (818 dòng = 817 ID + header) |
| DB | `data/lineage.db` — bảng `people` (PK `id`, không NOT NULL/UNIQUE/CHECK nào trên `name_zh/name_vi/name_en/name_ja`, không trigger chặn insert thiếu tên — đã audit bằng `.schema people` trước khi làm bất cứ gì) và `codex_person_name` (PK `dila_id`) |
| Script ghi | `scripts/t470_phase2_bosung_apply.py` (dry-run mặc định, `--apply`, `--revert`) |
| Script đối chiếu | `scripts/dila_json_reconcile_dryrun.py` (chạy lại bản sao ghi ra `dila_json_reconcile_after_v3.csv/log`) |
| API kiểm chứng | `GET /daoanh/api/person/<id>/dila_full` (`app.py:21546`) |

## 2. Root cause / quyết định (đã xác minh)

- **Lớp xử lý:** data import (DILA JSON → DB), không phải bug UI/resolver.
- **Bước 1 (bắt buộc):** `.schema people` không có ràng buộc nào chặn dòng
  thiếu tên → KHÔNG dừng, tiếp tục bước 2 theo đúng chỉ dẫn.
- 4 field (`places_of_origin`, `works_in_tripitaka`, `cbeta_citations`,
  `active_at_places`) trong JSON chỉ là **chuỗi tên**, không có ID chuẩn đi
  kèm để join an toàn vào `person_origin_link`/`dila_catalog_contributors`/
  `cbeta_person_mentions`/`nexus_events` → ghi sẽ phải merge-by-name, vi phạm
  `data-integrity.md`/`naming-and-identity.md` → **DỪNG**, không ghi, chỉ báo
  số liệu (xem `tasks/T471-dila-json-import-note.md`).
- `wikidata_qid`: không có bảng person-wikidata trong DB → chỉ báo số liệu
  (2.005 ID), không ghi (đúng yêu cầu).

## 3. Data/API contract trước → sau

| | Trước | Sau |
|--|-------|-----|
| `people` (số dòng) | 48.673 | 49.490 (+817) |
| `codex_person_name` (số dòng) | 49.335 | 49.487 (+152) |
| `people.dynasty` DB_THIEU | 659 | 0 |
| `people.bio` DB_THIEU | 817 | 0 |
| `birth_year`/`death_year` DB_THIEU | 189 | 0 |
| `codex_person_name.xml_sha256` DB_THIEU | 152 | 0 |
| `GET /daoanh/api/person/A000002/dila_full` | response giống hệt bản `A000002_dila_full_after_phase2.json` (A000002 đã đủ dữ liệu từ trước, không nằm trong 817 ID mới hoặc 189 ô birth/death còn thiếu) | **Không đổi** — xem mục 6, case đối chứng dùng `A018048` (1 trong 817 ID mới) để xác nhận route phản ánh đúng dữ liệu mới ghi |

## 4. Files changed

- `daoanh/scripts/t470_phase2_bosung_apply.py` — script mới, ghi INSERT/UPDATE
  theo đúng phạm vi (xem mục 5).
- `daoanh/docs/ROLLBACK.md` — thêm mục backup + lệnh revert cho vòng bổ sung.
- `daoanh/docs/tasktodo.md` — chưa sửa trong lượt này (theo ràng buộc, không
  đụng dashboard/task khác ngoài T470/T471; tasktodo chỉ cần cập nhật nếu
  Admin yêu cầu — để Admin tự quyết khi xác nhận).
- `daoanh/tasks/T471-dila-json-import-note.md` — task mới, `status: in_progress`.
- CSV/log mới trong `docs/sessions/2026-10-26/`: `t471_names_pending_admin.csv`,
  `dila_json_reconcile_after_v3.csv`, `dila_json_reconcile_after_v3.log`,
  `t470_phase2_bosung_apply.log`, `t470_phase2_bosung_revert_log.jsonl`,
  `A000002_dila_full_v3_after_bosung.json`, `A018048_dila_full_newperson_check.json`.

## 5. Migration / import / dry-run / rollback

- Dry-run: `python -X utf8 scripts/t470_phase2_bosung_apply.py` (không `--apply`)
  → in số liệu, không ghi gì.
- Backup: `data/lineage.db.bak_T470round2_20261026_140704`
  (1.677.467.648 B, SHA-256 `fad8071276e6653e800d675e964b571e15d39ed04ba5679aa214945fa5347f62`).
- Apply: `python -X utf8 scripts/t470_phase2_bosung_apply.py --apply`.
- Revert chọn lọc: `python -X utf8 scripts/t470_phase2_bosung_apply.py --revert`.
- Revert toàn bộ: copy backup trên đè `data/lineage.db` (khi server dừng).
- Chi tiết: `docs/ROLLBACK.md` mục 2026-10-26 "T470 Phase 2 vòng BỔ SUNG".

## 6. Test cases & kết quả

| Case | Input | Expected | Actual | PASS/FAIL |
|------|-------|----------|--------|-----------|
| 817 ID mới tạo | `A018048` (đại diện) | Dòng `people` mới, tên NULL, dynasty/bio/birth/death theo JSON nếu có | `('A018048', '印度', None, None, None, None, 'DILA')` — dynasty có, birth/death None (JSON không có năm), tên None | ✅ |
| Đối chiếu v3 toàn bộ 49.487 file | Chạy lại `dila_json_reconcile_dryrun.py` | DB_THIEU=0 cho `dynasty/concise_bio/birth_death_dates/xml_sha256` | Đúng — 0/0/0/0 (xem `dila_json_reconcile_after_v3.log`) | ✅ |
| Fallback — field không có ID an toàn | `places_of_origin`, `works_in_tripitaka`, `cbeta_citations`, `active_at_places` | KHÔNG ghi, chỉ báo số liệu | Không có UPDATE/INSERT nào chạm 4 field này (script không có code path ghi) | ✅ |
| Fallback — JSON trống | ID trong 817 không có `dynasty`/`birth_death_dates` | Để NULL, không bịa | Đã kiểm — ví dụ `A018048` không có birth/death → giữ NULL | ✅ |
| API kiểm chứng | `GET /daoanh/api/person/A000002/dila_full` (127.0.0.1:5000) | Phản ánh thay đổi nếu có | A000002 không nằm trong phạm vi ghi vòng này (đã đủ dữ liệu từ vòng trước) → response không đổi, đúng dự kiến (không phải bug) | ✅ |
| `python -m py_compile` | `scripts/t470_phase2_bosung_apply.py` | OK | `COMPILE_OK` | ✅ |

## 7b. Sửa theo QA vòng 2 (2026-10-26)

QA báo CHƯA ĐẠT với 3 vấn đề. Đã sửa cả 3:

**Vấn đề 1 — 218 ô TCN bị ghi lại thành số âm (vi phạm quyết định round 1)**

- Root cause: round 1 đã revert 218 ô birth/death TCN về NULL (chờ Admin
  quyết convention số âm), ghi lại trong
  `docs/sessions/2026-10-26/t470_bce_years_pending_admin_decision.csv`. Vòng
  bổ sung coi các ô NULL đó là `DB_THIEU` và điền lại từ JSON — JSON vẫn trả
  giá trị âm cho TCN → ghi đè lại đúng 218 ô đó thành số âm, đi ngược quyết
  định round 1.
- Đối chiếu: file CSV có 218 dòng = 153 dila_id phân biệt, 83 ô `birth_year`
  + 135 ô `death_year` = 218 — khớp đúng số QA báo (153 người / 218 ô).
- Verify trước revert: SELECT 218 ô theo đúng `dila_id` trong CSV — cả 218
  ô đều đang bằng đúng giá trị âm (`bce_year_signed`) đã bị ghi lại ở vòng bổ
  sung (không có ô nào đã NULL sẵn, không có ô nào lệch giá trị khác).
- Backup trước khi revert: `data/lineage.db.bak_T470round2qa_20261026_142825`
  (1.677.709.312 B, SHA-256 `0b7165b8a1ba7c8f0a4cbd2a2fd7253704c7c8e7876a878204677151b2d7757c`).
- Hành động: UPDATE `people SET {birth_year|death_year}=NULL WHERE id=? AND
  {col}=?` (điều kiện giá trị khớp — chỉ revert đúng ô đang bằng giá trị âm
  đã ghi, không revert mù).
- Kết quả: **218/218 ô đã về NULL**, verify lại sau revert: 218 ô NULL, 0 ô
  còn giá trị cũ; `SELECT COUNT(*) FROM people WHERE birth_year<0 OR
  death_year<0` = **0** trên toàn DB (không còn số âm nào sót lại ngoài 218
  ô này). Log revert riêng:
  `docs/sessions/2026-10-26/t470_phase2_bosung_tcn_revert_log.jsonl` (218
  entries, mỗi entry có `before`/`after`/`source_csv`). Các ô này vẫn ở
  trạng thái NULL chờ Admin quyết convention — KHÔNG tự quyết.
- Các ô birth/death khác (phần còn lại của 153 người không nằm trong 218 ô
  TCN, và 36 ô birth/death hợp lệ trong 817 ID mới) — không đụng tới, đã
  kiểm bằng cách chỉ UPDATE theo đúng `(id, col)` lấy từ CSV 218 dòng.

**Vấn đề 2 — dry-run ghi REVERT_LOG gây trùng lặp**

- Root cause: dòng ~305-307 (cũ) ghi `REVERT_LOG` vô điều kiện, không kiểm
  `args.apply` → mỗi lần dry-run (không `--apply`) cũng ghi log y hệt log
  khi `--apply` thật, nhân đôi log (2.374 dòng thay vì 1.187 thực).
- Fix: bọc đoạn ghi `REVERT_LOG` trong `if args.apply:`; nhánh dry-run chỉ in
  ra số lượng entries *sẽ* ghi nếu chạy `--apply`, không ghi file.
- Dọn log cũ: đã backup bản gốc
  (`docs/sessions/2026-10-26/t470_phase2_bosung_revert_log.jsonl.bak_before_dedupe`,
  2.374 dòng) rồi dedupe giữ thứ tự xuất hiện đầu tiên — còn
  **1.187 dòng** (khớp đúng số entries thực tế phát sinh từ 1 lần `--apply`
  duy nhất; đã verify 2.374 dòng = 1.187 dòng unique × 2, tức mỗi dòng bị
  nhân đôi chính xác một lần do 1 lần dry-run trước đó).
- `--revert` không bị ảnh hưởng về tính đúng: trước fix, dù log trùng, UPDATE
  revert có điều kiện so khớp giá trị hiện tại = `after` nên chạy 2 lần vẫn
  idempotent; INSERT revert gọi DELETE 2 lần trên cùng id vô hại (lần 2
  không còn dòng để xoá). Dedupe chỉ để log sạch, không phải sửa lỗi dữ liệu.

**Vấn đề 3 — `--revert` xoá dòng `people` dù Admin đã điền tên sau đó**

- Root cause: dòng ~349-353 (cũ) `DELETE FROM people WHERE id=?` cho mọi
  entry `op=insert` của bảng `people`, không kiểm điều kiện nào — nếu Admin
  đã điền `name_zh`/`name_vi` cho 1 trong 817 dòng mới (đúng mục đích T471)
  rồi ai đó chạy `--revert`, dữ liệu tên sẽ mất theo dòng bị xoá.
- Fix: trước khi DELETE một dòng `people` có `op=insert`, SELECT
  `name_zh, name_vi, name_en, name_ja` — nếu còn **NULL/rỗng cả 4 cột** mới
  cho xoá; nếu đã có ít nhất 1 cột có giá trị thì **bỏ qua, không xoá**, ghi
  cảnh báo ra stdout (liệt kê các id bị bỏ qua) thay vì crash toàn bộ.
- Test: seed 2 dòng test (`TEST_NONAME` chưa có tên, `TEST_HASNAME` đã có
  `name_zh='測試'`) trên **bản copy DB** (không đụng DB thật), chạy
  `do_revert()` với `REVERT_LOG` giả trỏ 2 entry insert cho 2 id này.
  Kết quả: `TEST_NONAME` bị xoá đúng, `TEST_HASNAME` **được giữ lại** và in
  cảnh báo `"ID bo qua vi da co ten: TEST_HASNAME"`. Không chạy `--revert`
  thật trên DB sản xuất trong lượt sửa này (chỉ test cô lập), vì T470/T471
  vẫn `in_progress` và không ai yêu cầu revert toàn bộ 817 dòng.

`python -m py_compile scripts/t470_phase2_bosung_apply.py` → `COMPILE_OK`
sau khi sửa cả 3.

## 7. Limitation / data gap còn lại

- 817 dòng `people` mới **chưa có tên** (`name_zh`/`name_vi`) — cần Admin điền
  tay, danh sách tại `docs/sessions/2026-10-26/t471_names_pending_admin.csv`.
- 4 field (`places_of_origin`, `works_in_tripitaka`, `cbeta_citations`,
  `active_at_places`) chưa ghi — cần Admin quyết có mở resolver tên→ID an
  toàn hay không (xem `tasks/T471-dila-json-import-note.md`).
- `wikidata_qid`: không có bảng lưu trong DB, chưa có hạ tầng để ghi.
- 20 ID có `concise_bio` KHAC_GIA_TRI (khác giá trị, không phải DB_THIEU) —
  chưa xử lý, để Admin quyết riêng (không tự ghi đè theo đúng ràng buộc).
