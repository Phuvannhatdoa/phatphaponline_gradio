# T172-REPORT — Debug Pipeline Phiên Âm Hán-Việt Theo Từng Hán Tự (Charwise)

**Task:** T172 · **Loại:** code (sidecar + migration + API + UI) · **Trạng thái:** BUILD DONE (2026-09-29)
**SPEC:** `docs/Mimo-Flash/T172-hanviet-charwise-debug-SPEC.md` (đã amend T191 line-refs) · **Cờ:** dữ liệu kiểm tra kỹ thuật, `valid` ≠ verified.

---

## 1. File sửa / tạo

| File | Việc |
|---|---|
| `scripts/t172_build_charmap.py` | **Mới.** AST-extract `HAN_VIET_CHAR` (app.py:1294, **1.478** entry) + đọc `hanviet_fallback`(8.650) + `custom_hanviet_override`(3.968) → merge **`hanviet_char_map` 11.300 unique char** (priority override > HAN_VIET_CHAR > fallback); `is_ideograph()` (Ext A/B+, compatibility gồm U+279CC); `compute_charwise`; `legacy_compare` (exact/normalized/differs/not_comparable); `validate_status` (rule **unknown > exception > (poly & differs → needs_review) > mismatch > valid**); `is_transliteration_flag`; CLI `--stats/--export/--apply/--revert`. |
| `scripts/t172_hanviet_charwise_migrate.py` | **Mới.** Import từ build_charmap. `--apply/--dry-run/--revert/--yes/--no-copy/--person/--limit/--db-path` + env `T172_DB`; backup file-level `data/backups/lineage_backup_t172_<ts>.db` (hoặc dump 3 cột JSON khi `--no-copy`); seed `hanviet_char_map` + `hanviet_exception_list` (seed **`蘇嚩羅`**); full sweep `fetchmany(2000)` → UPSERT `person_hanviet_debug`; assert `people` immutability; counts → console + `data/t172_status_counts.json`; `--revert` DROP 3 sidecar (không đụng people). |
| `app.py` | **+~100 dòng.** (1) `api_dila_persons_search` (:8202) — param `hv_status`, `hv_filter_sql` map, `LEFT JOIN person_hanviet_debug d` ở count + rows, SELECT d.*, cleanup object `hv{charwise,legacy,status,reason,legacy_match,han_count,syll_count}` (không đổi field cũ); (2) `api_person_by_id` (:17490) — attach `hv` qua helper `_t172_load_hv()`; (3) helper `_t172_load_hv()` (cạnh :8403); (4) **mới** `GET /daoanh/api/dila/hv/stats` (:8403) → `{total, by_status, by_legacy_match, is_transliteration, dict_version}`. `python -m py_compile` OK. |
| `admin/dila_person_index.html` | Icon cột **HV** + `hvCell(r)` (⚠ amber #d97706 24px khi `status ∈{mismatch,unknown_char,exception,needs_review}` hoặc `legacy_match='differs'`; ✓ khi valid; `·` khi hv null) + tooltip 5 dòng + filter `<select#hvSelect>` 7 mức → `hv_status` trong buildQuery + badges stats từ `/dila/hv/stats`. |
| `admin/person.html` | Khối read-only **"Kiểm tra phiên âm Hán-Việt"** (`#card-hv` sau `#meta`, `#hv-badge` + `#hv-body`) + `renderHv(h)`; ẩn khi `hv` null; hiện raw/legacy/charwise/count/unknown/status/reason/legacy_match/is_transliteration. |
| `tests/fixtures/t172_hanviet_cases.json` | **Mới.** char_map + polyphonic + 7 case C1–C7 (đúng SPEC §8). |
| `tests/test_t172_charwise.py` | **Mới.** **64 PASS / 0 FAIL** (không cần DB thật; worst-case bypass cho immutability path). |
| `scripts/lint-check.ps1` | **Sửa bug pre-existing (Batch 4 đã hứa ở ROLLBACK §5):** (a) pattern `<script...>` giờ nuốt `>` (trước `$m.Length` = 7, cắt nhầm `>` đầu block ⇒ mọi file FAIL); (b) node v24 `--check` cần đuôi `.js` (GetTempFileName() `.tmp` → ERR_UNKNOWN_FILE_EXTENSION); (c) JSX (placevn.html) skip không fail; (d) `$ErrorActionPreference=Stop` gây dừng giữa chừng → Continue + `$LASTEXITCODE`; (e) thêm `dila_person_index.html` + `person.html` vào danh sách check. **Nay lint check 7 block thật trên 5 file — PASS.** |
| `docs/Mimo-Flash/T172-hanviet-charwise-debug-REPORT.md` | File này (bàn giao, SPEC §9 phase 7). |

## 2. Migration — DB thật

Chạy lần lượt (Nguyễn: `python scripts/t172_hanviet_charwise_migrate.py` từ `daoanh/`):

```text
[--apply --person fixture 7 id] → 7 rows, backup lineage_backup_t172_20260929_114458.db
[--apply full]                 → 47,036 debug rows · 1,637 skipped (không phải tên Hán) · 7.1s
                                 backup lineage_backup_t172_20260929_114540.db
[immutable] people COUNT(*) 48,673 → 48,673 ✓ (KHÔNG bao giờ ghi people)
```

**Status counts (full, idempotent — chạy lặp 2× kết quả y hệt):**

| status | count | legacy_match | count |
|---|---|---|---|
| valid | 40.575 | exact | 38.912 |
| mismatch | 920 | normalized | 1.661 |
| unknown_char | 534 | differs | 5.930 |
| exception | 1 | not_comparable | 533 |
| needs_review | 5.006 | NULL | 0 |

`is_transliteration = 1`: **40.573** · dict_version `t172-20260928-3dict`.

**Spot-check fixture (đúng SPEC + directive):**
- `A000006 一山国師` (legacy 17 âm metadata) → `Nhất Sơn Quốc Sư` (charwise) · mismatch · differs.
- `A000008 一行` → `Nhất Hành` charwise · **needs_review** (đa âm 行 hàng/hành, khác legacy) · differs · `is_transliteration=0`.
- `A000016/A023828 一行…` → needs_review (đa âm) như T191 L2 (4 person `一行` search).
- `A000026 了貞` `Liễu Trinh` → valid · exact · translit=1.
- `A000044 蘇嚩羅` `Tô Phược La` → **exception** (seed) · exact · translit=1.
- `A000047 于頔` `Vu 頔` → **unknown_char** (頔 không có reading → `[?頔]`) · not_comparable.

## 3. API (sau restart server mới hiệu lực)

1. `GET /daoanh/api/dila/persons?hv_status=<s>` với `s ∈ {valid, mismatch, unknown_char, exception, needs_review, normalized, differs}` (7 mức).
2. `GET /daoanh/api/persons/<id>` → thêm `hv` object (null nếu chưa migrate/không row).
3. `GET /daoanh/api/dila/hv/stats` → `{ok, total:47036, by_status:[5], by_legacy_match:[5], is_transliteration:40573, dict_version}`.

## 4. Test

- `python tests/test_t172_charwise.py` → **64 PASS / 0 FAIL** (_standalone; npm run test là placeholder repo — convention chạy trực tiếp_).
- `npm run guard` PASS (SSOT repo-root, no nested .git) · `npm run lint` PASS (7 block — sau fix lint-check.ps1) · `npm run test` PASS · `npm run e2e` PASS (13 page, 0 fail). `npm run pipeline` PASS trừ `e2e:runtime` EPERM pre-existing (env).

## 5. Rủi ro / lưu ý

- **Dữ liệu kiểm tra, không tự verified** — `needs_review` 5.006 person (đa âm khác legacy) + `mismatch` 920 + `unknown_char` 534 là **hàng đợi review cho T171/HITL**, không tự sửa `people.name_vi` (SPEC §1 cấm; cấu trúc "record-not-block").
- **Phase 1 (re-verify UI live 7 ví dụ) chưa chạy** — cần restart app.py trên máy chạy server rồi mở `admin/dila_person_index.html` + `person.html`; đã verify ở mức DB + js `node --check` + SQL real. Nhập vào acceptance nợ.
- **Revert:** code `git revert --no-edit <sha_pass1>` + DB `python -X utf8 scripts/t172_hanviet_charwise_migrate.py --revert` (DROP 3 sidecar, people nguyên vẹn) hoặc restore `data/backups/lineage_backup_t172_20260929_114540.db`.
- **Lint fix đi kèm** (`scripts/lint-check.ps1`) là bug env pre-existing (đã hứa "Batch 4" ở ROLLBACK §5) — tách theo dõi, nếu muốn revert riêng thì `git revert` commit đó chỉ chạm 1 file.
- Sidecar 47.036 row chỉ cho person có tên Hán; 1.637 row non-Hán (romanized) không debug — đúng SPEC.