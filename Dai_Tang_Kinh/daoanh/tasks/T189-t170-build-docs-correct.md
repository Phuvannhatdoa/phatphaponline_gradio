---
id: T189-t170-build-docs-correct
title: "T189 — T170 build-docs correction (C1–C4, docs-only + 1 comment code): status built + tiền đề id TEXT + test files thật + acceptance pending"
module: Editorial / LLM Translation
priority: high
status: done
owner: claudecode
depends_on: [T170-dila-place-person-v41-verify]
created: 2026-09-28
updated: 2026-09-28
done_at: "2026-09-28 (docs-only + 1 comment; pipeline PASS; commit 2-pass hash-fill)"
plan_approved_at: "2026-09-28 (Admin: Đồng ý build — phê chuẩn đề xuất check 2 file T170 POST-BUILD)"
done_when: |
  C1: frontmatter status SPEC+pointer `ready-for-dev → built` (build closure §12 đã ghi, acceptance còn nợ).
  C2: tiền đề "id INTEGER" trong SPEC §12 + pointer bullet + tasks/T170-verify + comment `cursor` sửa thành id TEXT
      (`PL000000000001…`/`A000001…`); bug chỉ tái hiện ở test-harness INTEGER giả; giữ cursor='0' an toàn.
  C3: SPEC §6 + §8 gate ① trỏ đúng 3 file test thật (person_classify 17 + verify_pipeline 15 + t169_classify_diff 11),
      bỏ tên draft không tồn tại (test_dila_verifier_v3/test_dila_person_verifier/test_t170_redteam).
  C4: done_when tách acceptance (validate-only + pilot 25/entity) → PENDING chờ GROQ key/VPS; code-build = DONE.
  Docs: task + session + tasktodo + ROLLBACK + dashboard regen; commit 2-pass hash-fill.
  Verify: test:t170 17/17 + 15/15 · test:t169 11/11 · npm run pipeline PASS trừ e2e:runtime EPERM pre-existing.
  Revert: git revert --no-edit 2548c4fcc87db76e582465b746c7015e2c8c0b94 (docs + 1 comment, 0 DB).
---

# T189-t170-build-docs-correct — T170 build-docs correction

## Bối cảnh

Sau T170-BUILD (SPEC §12 BUILD CLOSURE + pointer 🚀 BUILD DONE, commits `66d758c`/`ebf4d2a`), Admin yêu cầu
rà 2 file `docs/Mimo-Flash/T170-dila-place-person-v41-verify-SPEC.md` + `-verify.md` xem logic còn khớp
hiện trạng repo/DB thật không. Audit read-only đối chiếu DB (`data/lineage.db`) + code + tests:

- **Xác nhận đúng**: `person_groq_audit` 21 cột + idx_gpa_review/idx_gpa_diff (0 rows — chỉ schema, data chờ VPS);
  backup `lineage_t170_20260928_150114.db`; R2/R3/R4/R5/R6/R7 trong code (`t170_classify.py:26,36,56`,
  `verify_dila_places_groq.py:106-107,73,65`); tests 17/17 + 15/15 đếm trực tiếp; `test:t170` chained `test:translation`.
- **Phát hiện 4 điểm chưa đúng logic** → C1–C4 (bên dưới) đã sửa tại chỗ sau khi Admin phê chuẩn.

## Thay đổi (C1–C4)

| # | File | Sửa |
|---|------|-----|
| C1 | `docs/Mimo-Flash/T170-dila-place-person-v41-verify-SPEC.md` + `-verify.md` | frontmatter `status: ready-for-dev → built` (build đã xong; acceptance §8 ②–④ còn nợ) |
| C2 | SPEC §12 · pointer bullet 🚀 · `tasks/T170-dila-place-person-v41-verify.md` bug #1 · `scripts/verify_dila_places_groq.py:419` comment | đính chính tiền đề: `places_dila.id`/`people.id` = **TEXT** (`PL000000000001…`/`A000001…`, DB thật), KHÔNG INTEGER; bug cursor `''→0 rows` chỉ tái hiện ở test-harness schema INTEGER giả; giữ `cursor='0'` an toàn mọi entity |
| C3 | SPEC §6 + §8 gate ① | thay tên draft `test_dila_verifier_v3.py`/`test_dila_person_verifier.py`/`test_t170_redteam.py` (không tồn tại) → file thật `test_t170_person_classify.py` (17) + `test_t170_verify_pipeline.py` (15) + `test_t169_classify_diff.py` (11) |
| C4 | SPEC `done_when` | tách "validate-only + pilot 25/entity" thành **acceptance PENDING** (chờ GROQ key VPS); code-build = DONE |

## Việc đã làm

1. **SPEC**: status→built · done_when (tách acceptance + note T189) · §6 bảng test thật + note thay tên draft ·
   §8 gate ① 3 file thật · §12 bug (1) đính chính id TEXT.
2. **Pointer**: status→built · bullet 🚀 sửa "INTEGER cursor" → "id THẬT TEXT, bug chỉ test-harness INTEGER" + thêm
   "acceptance §8 ②–④ còn NỢ (chờ GROQ key VPS)".
3. **tasks/T170-dila-place-person-v41-verify.md**: bug #1 viết lại theo tiền đề đúng.
4. **scripts/verify_dila_places_groq.py:419**: comment `cursor` → "an toàn mọi entity (id TEXT; bug ''~0 rows chỉ test-harness INTEGER) [T189]".
   ⚠️ Script đang là **WIP uncommitted** (bản đầy đủ T170 chưa về HEAD) → commit T189 **KHÔNG gồm** script; comment giữ trên disk, đi theo commit script của T170.
5. **Docs**: task `tasks/T189...md` · session `docs/sessions/2026-09-28_t189-t170-build-docs-correct.md` ·
   tasktodo top entry · ROLLBACK row.
6. **Dashboard**: regen `scripts/build_progress_data.py` → `data/progress_data.json` (107 tasks · done=83).

## Verify

- `npm run test:t170` (17/17 + 15/15) · `python -X utf8 tests/test_t169_classify_diff.py` (11/11) · `npm run guard` PASS — docs-only.
- `npm run pipeline` PASS trừ `e2e:runtime` EPERM pre-existing.
- DB read-only (đã chạy lúc audit): id TEXT · person_groq_audit 21 cột.

## Revert

- `git revert --no-edit 2548c4fcc87db76e582465b746c7015e2c8c0b94` — khôi phục SPEC/pointer/task/tasktodo/ROLLBACK/session cũ (0 DB, 0 code).
- Lưu ý hunk-granular: commit đưa SPEC/pointer = bản BUILD-docs mới nhất (amend + §12 + edit T189) tại path HEAD; bản rename `X-` + WIP khác của agent song song để nguyên trong worktree.

## Còn lại (thủ công, chờ GROQ key trên VPS)

- Acceptance §8 ③④: `--validate-only` + `--pilot 25 --entity {place,person}` → admin duyệt → full run
  `scripts/verify_dila_places_groq.py --entity person` (~1.947 batch).