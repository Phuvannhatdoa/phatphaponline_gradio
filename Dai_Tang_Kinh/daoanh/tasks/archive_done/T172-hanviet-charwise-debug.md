---
id: T172-hanviet-charwise-debug
title: "T172 — Debug pipeline phiên âm Hán-Việt theo từng Hán tự (charwise sidecar + migration + API + UI)"
module: Editorial / Person Identity
priority: high
status: done
owner: claudecode
depends_on: [T166-canonical-identity-guard, T171-person-name-standard]
created: 2026-09-25
updated: 2026-09-29
done_at: "2026-09-29 (BUILD DONE — guard/lint/test/e2e PASS trừ e2e:runtime EPERM pre-existing; migrate full 47.036 rows DB thật; commit 2-pass hash-fill 032fb516b348676b9a678ed745ec76ab23c6406d)"
plan_approved_at: "2026-09-25 (Admin chốt 3 mặc định: đa âm = reading + needs_review + candidates; gộp addendum vào T171 person_name_alias; sidecar person_hanviet_debug; legacy giữ display)"
done_when: |
  P1: charmap script trích AST HAN_VIET_CHAR (1.478 entry) + merge 3 dict → hanviet_char_map 11.300 unique
      + assert 1 âm tiết + đa âm 552 + exception seed 蘇嚩羅 (CLI --stats/--export/--apply/--revert).
  P2: migrate script --apply DB THẬT (backup data/backups/lineage_backup_t172_20260929_114540.db;
      person_hanviet_debug 47.036 rows, 1.637 non-Hán skip, idempotent, people COUNT giữ 48.673,
      counts → data/t172_status_counts.json; --revert DROP 3 sidecar verify 2 chiều).
  P3: API attach/filter/stats — list?hv_status (7 mức), detail hv object, GET /daoanh/api/dila/hv/stats.
  P4: UI index (cột HV ⚠ + tooltip 5 dòng + filter) + detail (khối read-only "Kiểm tra phiên âm Hán-Việt").
  P5: tests+fixture 64 PASS · npm run guard/lint/test/e2e PASS (lint fix pre-existing kèm, Batch 4 ROLLBACK §5).
  P6: REPORT docs/Mimo-Flash/T172-...-REPORT.md + task/session/tasktodo/ROLLBACK/dashboard + commit 2-pass.
  P7 (NỢ acceptance): Phase 1 re-verify UI live 7 ví dụ sau restart server — cần HITL/VPS.
  Revert: git revert --no-edit 032fb516b348676b9a678ed745ec76ab23c6406d (code/docs) + python -X utf8 scripts/t172_hanviet_charwise_migrate.py --revert (DB).
---

# T172-hanviet-charwise-debug — Debug pipeline phiên âm Hán-Việt theo từng Hán tự (Charwise)

## Bối cảnh

`people.name_vi` hiện là chuỗi trộn 5 nguồn từ `name_vi_map`; quy trình phiên âm trước (`bulk_transliterate.py` root,
lexicon khớp cả chuỗi, `_han_viet()` app.py:1849 chỉ cho place) không để lại **dấu vết kiểm tra từng chữ** → không
phân biệt được `valid`, `mismatch`, `unknown_char`, `needs_review` (đa âm), exception. T172 build **sidecar kiểm tra
kỹ thuật** (không sửa `people`, không LLM, không auto-verified) để T171/alias + admin review có dữ liệu đối chiếu.

SPEC: `docs/Mimo-Flash/T172-hanviet-charwise-debug-SPEC.md` (amend T191 line-refs `_han_viet`=1849 · `HAN_VIET_CHAR`=1294 ·
`|` sidecar 13 field · `is_transliteration` định nghĩa).

## Thay đổi (BUILD)

| # | File | Nội dung |
|---|------|----------|
| P1 | `scripts/t172_build_charmap.py` (mới) | AST-extract `HAN_VIET_CHAR` app.py:1294 (1.478) + merge `hanviet_fallback`/`custom_hanviet_override` → `hanviet_char_map` 11.300 unique char; poly 552 (case-insensitive); 1 violation info (key đa ký tự `平定` → skip); `is_ideograph` gồm U+279CC; algorithm helpers (pure, test import được). |
| P2 | `scripts/t172_hanviet_charwise_migrate.py` (mới) | `--apply/--dry-run/--revert/--yes/--no-copy/--person/--limit/--db-path` + `T172_DB`; backup `data/backups/lineage_backup_t172_<ts>.db`; seed char_map + exception `蘇嚩羅`; sweep fetchmany(2000) → UPSERT `person_hanviet_debug`; people immutability assert; log counts → `data/t172_status_counts.json`; revert DROP 3 sidecar. |
| P3 | `app.py` | list :8202 (`hv_status` 7 mức + LEFT JOIN + object `hv` không đổi field cũ) · detail :17490 (`hv` qua `_t172_load_hv()`) · helper `_t172_load_hv()` · mới `GET /daoanh/api/dila/hv/stats` :8403. py_compile OK. |
| P4 | `admin/dila_person_index.html` + `admin/person.html` | Cột HV ⚠ 24px + tooltip 5 dòng + `#hvSelect` filter + badges stats; khối read-only #card-hv (6 trường), ẩn khi hv null. |
| P5 | `tests/fixtures/t172_hanviet_cases.json` + `tests/test_t172_charwise.py` | 64 PASS / 0 FAIL (no real DB); fixture 7 case C1–C7 + ideograph/order/legacy-NFC/idempotent/immutability/exception. |
| infra | `scripts/lint-check.ps1` | Fix bug pre-existing (Batch 4 ROLLBACK §5): `>`-offset regex · node v24 `.js` temp · JSX skip · ErrorActionPreference Stop→Continue · +2 file T172 vào scope. Nay lint 7 block/5 file PASS. |
| docs | `REPORT` + task + session + tasktodo + ROLLBACK + dashboard | Bàn giao §SPEC9. |

## Verify

- `python -X utf8 scripts/t172_hanviet_charwise_migrate.py --apply` DB thật → **47.036 rows · 1.637 skip · 7.1s · idempotent · people 48.673 giữ nguyên**.
- Status: valid 40.575 · mismatch 920 · unknown_char 534 · exception 1 · needs_review 5.006 · legacy exact 38.912/normalized 1.661/differs 5.930/not_comparable 533 · translit=1 40.573.
- Fixture: A000006 mismatch·differs · A000008 needs_review (poly 行) · A000026 valid·exact·translit 1 · A000044 exception · A000047 unknown_char `[?頔]`·not_comparable.
- SQL thật: needs_review sample A000008/A000025/A000078 · differs total 5.930 · A000008 `Nhất Hành` · by_status 5 key.
- `python -m py_compile app.py` OK · `node --check` 2 file HTML PASS · `npm run guard`/`lint`/`test`/`e2e` PASS · pipeline PASS trừ `e2e:runtime` EPERM pre-existing.

## Nợ / acceptance PENDING

- **Phase 1 re-verify UI live 7 ví dụ** (SPEC §9 P1) — cần `scripts/restart_server.ps1` + mở index/detail lấy hv; xác minh KNOWN: 6/7 ví dụ directive lệch DB cũ (đã nằm SPEC §2); sau khi có server chạy app.py mới sẽ vào acceptance. Ngoài phạm vi: seed alias (T171 song song), HITL review 5.006+920+534 rows, đa âm candidates UI.

## Revert

- Code/docs: `git revert --no-edit 032fb516b348676b9a678ed745ec76ab23c6406d` — khôi phục worktree T172 (scripts/tests/docs + app.py data-diff hunk + lint-check.ps1 + UI 2 file).
- DB: `python -X utf8 scripts/t172_hanviet_charwise_migrate.py --revert` (DROP `person_hanviet_debug` + `hanviet_char_map` + `hanviet_exception_list`; `people`/`name_vi_map` nguyên vẹn) hoặc restore `data/backups/lineage_backup_t172_20260929_114540.db`.