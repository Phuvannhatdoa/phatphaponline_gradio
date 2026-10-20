# Session 2026-09-29 — T172 BUILD: Han-Việt charwise debug pipeline
**Task:** `T172-hanviet-charwise-debug` · **Loại:** code+data+docs · **Số:** T172 (số SPEC; task file mới, chưa từng tồn tại ở HEAD)

---

## Mục tiêu
Build đầy đủ theo `docs/Mimo-Flash/T172-hanviet-charwise-debug-SPEC.md` (amend T191): sidecar 3 bảng, migration backup/idempotent/revert, API attach/filter/stats, UI index+detail, tests, REPORT, commit 2-pass + pipip best-effort.

## Đã làm

### 1. Script charmap — `scripts/t172_build_charmap.py`
- `HAN_VIET_CHAR` (app.py:1294) trích bằng **AST** (không regex) → **1.478 entry**; đọc `hanviet_fallback` (8.650) + `custom_hanviet_override` (3.968) thẳng sqlite.
- Merge theo priority **override > HAN_VIET_CHAR > fallback** → `hanviet_char_map` **11.300 unique char**; phát hiện **552 đa âm** (so sánh chuẩn hoá case-insensitive); 1 violation thông tin: key đa ký tự `平定`→`Bình Định` bị skip (không phải 1 âm tiết).
- Helpers thuần (test import được): `is_ideograph` (Ext A/B + compatibility gồm U+279CC) · `compute_charwise` · `legacy_compare` (exact/normalized/differs/not_comparable — chuẩn hoá NFC/lower/whitespace; legacy còn sót ideograph → not_comparable) · `validate_status` (unknown > exception > poly&differs→needs_review > mismatch > valid) · `is_transliteration_flag` (unknown rỗng ∧ match∈{exact,normalized}).
- CLI `--stats/--export/--apply/--revert`.

### 2. Script migration — `scripts/t172_hanviet_charwise_migrate.py`
- Import build_charmap; `--apply/--dry-run/--revert/--yes/--no-copy/--person/--limit/--db-path` + env `T172_DB`.
- Backup file-level `data/backups/lineage_backup_t172_<ts>.db` (khi `--no-copy` → dump 3 cột people JSON); seed char_map + `hanviet_exception_list` (seed `蘇嚩羅`); sweep `fetchmany(2000)` generator; UPSERT `INSERT OR REPLACE` idempotent; assert `people` COUNT trước=trong=sau; counts → console + `data/t172_status_counts.json`; `--revert` DROP 3 sidecar (people/name_vi_map không đụng).
- Fix nhỏ: `cmd_apply/cmd_revert` dùng `db = args.db_path or DB_PATH`; bỏ code chết `process_person`.

### 3. Test-run trên DB copy (trước khi đụng DB thật)
- Copy lineage.db → `%LOCALAPPDATA%\Temp\opencode\t172_test.db` (env `T172_DB`) **– DB thật chưa bao giờ bị chạm trong lúc dev/test**.
- Fixture 7 rows khớp; full **47.036 rows / 1.637 non-Hán skip / ~6s**; chạy lặp 2× = idempotent; people 48.673 giữ nguyên; revert DROP sạch 2 chiều.

### 4. app.py — 3 endpoint + helper (đúng SPEC §5/§11)
- List `api_dila_persons_search` :8202: param `hv_status` (7 mức `valid/normalized/exact/exception/mismatch/unknown_char/needs_review/differs`), `hv_filter_sql`, `LEFT JOIN person_hanviet_debug d` count+rows, poll `hv_*` → object `hv{charwise,legacy,status,reason,legacy_match,han_count,syll_count}`; ttl_local rows `"hv": null`; không đổi field cũ.
- Detail `api_person_by_id` :17490: attach `hv` qua helper `_t172_load_hv()` (đặt cạnh :8403).
- Mới `GET /daoanh/api/dila/hv/stats` :8403 → `{total, by_status[5], by_legacy_match[5], is_transliteration, dict_version}`.
- `python -m py_compile app.py` OK.

### 5. UI
- `admin/dila_person_index.html`: `<th>HV</th>`; `hvCell(r)` (⚠ amber #d97706 24px khi status ∈{mismatch,unknown_char,exception,needs_review} || legacy_match='differs'; ✓ khi valid; `·` khi null) + tooltip 5 dòng; `#hvSelect` 7 mức → `hv_status`; badges stats từ `/dila/hv/stats`.
- `admin/person.html`: `#card-hv` read-only sau `#meta` (badge + body: raw/legacy/charwise/han_count/syll_count/unknown/status/reason/legacy_match/is_transliteration) + `renderHv(h)`; ẩn khi null; gọi trong `load()`.
- Edit tool bị `FileSystem.writeFile` flaky 2 lần → re-read rồi retry được.

### 6. Lint bug pre-existing (Batch 4 — ROLLBACK §5 đã hứa) — sửa `scripts/lint-check.ps1`
- Nguyên nhân gốc khiến `npm run lint` "PASS" giả trước đây: (a) regex `<script(?!...)` không nuốt `>` → `$m.Length=7`, jsCode mở đầu bằng `>` → mọi block mà có bị cắt nhầm → Node 24 báo lỗi; (b) `GetTempFileName()` cho đuôi `.tmp` → node v24 `ERR_UNKNOWN_FILE_EXTENSION`; (c) placevn.html chứa **JSX** (React) `node --check` không hiểu → cần skip; (d) `$ErrorActionPreference=Stop` + `2>&1` → trình chết giữa chừng.
- Sửa: regex nuốt `>` · temp file đuôi `.js` (guid) · JSX skip · Continue + `$LASTEXITCODE` · thêm `dila_person_index.html` + `person.html` vào scope. → **7 script block / 5 file PASS** (xác nhận 2 file T172 `node --check` OK trực tiếp bằng python harness).
- **Không phải lỗi T172** — file mới đã sạch; đây là nợ môi trường nhập theo, fix chủ động.

### 7. Migrate DB THẬT
- Fixture: `--apply --person A000006,...` 7 id → backup `lineage_backup_t172_20260929_114458.db`.
- Full: `--apply` → backup `lineage_backup_t172_20260929_114540.db` · **47.036 rows · 1.637 skip · 7.1s · people 48,673 → 48,673 ✓**.
- Database lint khả thi: `npm run guard` PASS · `npm run lint` PASS · `npm run test` PASS · `npm run e2e` PASS · `npm run pipeline` PASS trừ `e2e:runtime` EPERM pre-existing.

### 8. Docs + commit
- REPORT `docs/Mimo-Flash/T172-...-REPORT.md` + task `tasks/T172-hanviet-charwise-debug.md` + session này + tasktodo row + ROLLBACK row + dashboard regen + commit 2-pass hash-fill + pipip best-effort (offline).

## Verify
- Status full: valid 40.575 · mismatch 920 · unknown_char 534 · exception 1 · needs_review 5.006 · legacy exact 38.912/normalized 1.661/differs 5.930/not_comparable 533 · translit=1 40.573.
- Fixture: A000006 mismatch·differs · A000008 needs_review `Nhất Hành` · A000016/A023828 needs_review · A000026 valid·exact·translit 1 · A000044 exception · A000047 unknown_char `[?頔]` not_comparable.
- SQL thật: needs_review A000008/A000025/A000078 · differs total 5.930 · by_status 5 key.

## Trạng thái
- **Task todo**: 9 items — 8 DONE, item 9 (docs/commit/pipip) DONE tại commit này.
- **Nợ acceptance**: Phase 1 re-verify UI live (7 ví dụ) sau restart server (VPS/HITL).

## Revert
- `git revert --no-edit 032fb516b348676b9a678ed745ec76ab23c6406d` + `python -X utf8 scripts/t172_hanviet_charwise_migrate.py --revert` (DB DROP 3 sidecar).