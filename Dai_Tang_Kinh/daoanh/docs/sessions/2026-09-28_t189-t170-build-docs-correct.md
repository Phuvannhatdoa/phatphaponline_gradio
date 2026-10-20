# T189 — T170 build-docs correction (docs-only + 1 comment) — Session log 2026-09-28

## Bối cảnh

Admin phê chuẩn đề xuất: rà 2 file `docs/Mimo-Flash/T170-dila-place-person-v41-verify-SPEC.md` + `-verify.md`
POST-BUILD, đối chiếu hiện trạng repo/DB thật, sửa các điểm chưa đúng logic. Task mới **T189**.
0 code logic mới (chỉ đổi 1 comment trong `scripts/verify_dila_places_groq.py:419`), 0 DB.

## Audit đã làm (read-only, trước khi sửa)

- `git log`: `66d758c` (T170 feat) → `ebf4d2a` (T170 hash-fill) → T187/T74 chain → HEAD `4ae580b`.
- DB thật `data/lineage.db` (read-only via sqlite3):
  - `person_groq_audit` = **21 cột** đúng SPEC §4 + `idx_gpa_review`/`idx_gpa_diff` (+ sqlite_autoindex). Rows = **0** (chỉ schema; data chờ VPS — consistent với build closure).
  - `places_dila.id` / `people.id` / `places_pending.id` = **TEXT** (`PL000000000001…` / `A000001…` / …) → tiền đề bug "id INTEGER" trong SPEC §12/pointer = **SAI so DB thật**.
  - `journal_mode=wal` · `busy_timeout=5000`.
- Code: `t170_classify.py:26,36,56` (fold_cjk/split_brackets) · `verify_dila_places_groq.py:106-107` (`busy_timeout=10000`,`synchronous=NORMAL`, bỏ WAL) · `:73` `MAX_TOKENS=2048` · `:65` import t170_classify · `t169_classify.py:22` `'行'` + `:121` self-match `殿` fix ✓.
- Tests (đếm trực tiếp đọc file): `test_t170_person_classify.py` **17** check · `test_t170_verify_pipeline.py` **15** check · `test_t169_classify_diff.py` **11** check. `package.json` `test:t170` nằm trong `test:translation`. ✓
- Không tồn tại: `test_dila_verifier_v3.py` / `test_dila_person_verifier.py` / `test_t170_redteam.py` (tên draft SPEC §6/§8).

## Kết luận audit (đã trình Admin, được phê chuẩn)

- **ĐÚNG**: migrate DB thật, R2–R7, fix `殿`, 22 tests mới, chaining, enum/API place không cần sửa, person defer.
- **CHƯA ĐÚNG (C1–C4)**:
  - C1 frontmatter `ready-for-dev` nhưng build đã xong → `built`.
  - C2 tiền đề bug cursor "id INTEGER" sai (id TEXT); bug chỉ tái hiện ở test-harness INTEGER giả.
  - C3 §6 + gate ① trỏ 3 test file không tồn tại.
  - C4 done_when ghi "pilot 25/entity" như điều kiện đóng nhưng acceptance chưa chạy (0 rows) → tách PENDING.

## Thay đổi

1. **SPEC** `T170-dila-place-person-v41-verify-SPEC.md`: status→built · done_when tách acceptance + note [T189] ·
   §6 bảng test thật + note thay tên draft · §8 gate ① 3 file thật · §12 bug (1) đính chính id TEXT (
   `PL000000000001…`, bug chỉ test-harness INTEGER giả, giữ cursor='0').
2. **Pointer** `T170-dila-place-person-v41-verify.md`: status→built · bullet 🚀 sửa tiền đề + thêm "acceptance §8 ②–④ còn NỢ".
3. **tasks/T170-dila-place-person-v41-verify.md**: bug #1 viết lại đúng tiền đề.
4. **scripts/verify_dila_places_groq.py:419**: comment → "cursor='0' an toàn mọi entity (id THẬT là TEXT 'PL…'; bug ''~0 rows chỉ ở test-harness INTEGER) [T189]".
   ⚠️ Script = **WIP uncommitted** (HEAD không có dòng comment/cursor này) → KHÔNG đưa script vào commit T189; comment giữ trên disk.
5. **tasks/T189-t170-build-docs-correct.md** (mới) + **docs/sessions/2026-09-28_t189-t170-build-docs-correct.md** (này).
6. **docs/tasktodo.md**: top entry T189 (hunk-granular: commit blob = HEAD + T189, giữ WIP khác unstaged).
7. **docs/ROLLBACK.md**: row T189 (placeholder → hash-fill 2-pass).
8. **data/progress_data.json**: regen `python -X utf8 scripts/build_progress_data.py` (107 tasks · done=83).

## Verify

- DB-independent tests: `npm run test:t170` (17/17 + 15/15) + `python -X utf8 tests/test_t169_classify_diff.py` (11/11) → PASS (docs-only).
- `npm run guard` + `npm run test` PASS · `npm run pipeline` → PASS trừ `e2e:runtime` EPERM pre-existing.
- Dashboard JSON chứa T189 done + các file T170 không còn `ready-for-dev`.

## Commit (2-pass, toplevel `visjs-app`, temp index, byte-write refs)

- Pass 1: `docs: T189 t170 build-docs correction (status built + id TEXT + test files thật + acceptance pending) + docs`
  — SPEC + pointer (bản BUILD-docs mới nhất, LF-normalize) + task T170-verify (new) + task T189 + session + tasktodo (HEAD+T189) + ROLLBACK (HEAD+T189) + progress_data.json regen. KHÔNG gồm script (WIP).
- Pass 2: hash-fill `2548c4fcc87db76e582465b746c7015e2c8c0b94` vào ROLLBACK/task/tasktodo.
- Revert: `git revert --no-edit 2548c4fcc87db76e582465b746c7015e2c8c0b94` (0 DB).