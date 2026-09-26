# Session 2026-09-24 - T167 Rules-Constrained Buddhist Translation Engine (SPEC + INTEGRATION AUDIT)

**Ngày:** 2026-09-24
**Mode:** build (user "phê chuẩn đề xuất... tạo task mới Txx cho kế hoạch chi tiết... update /docs + dashboard... lưu logs, gitcommit, revert tiện lợi")
**SSOT repo-root:** `visjs-app` (git toplevel) - mọi commit từ đây.

## Mục tiêu
1. Đối chiếu spec **T158 "Rules-Constrained Buddhist Translation Engine"** với repo thật (read-only).
2. Chỉ ra các điểm sai logic + đề xuất giải pháp → Lee phê chuẩn.
3. Tạo task mới **T167** (vì số T158 đã dùng 2 lần), cập nhật tasktodo/ROLLBACK/dashboard/session, commit.

## Nguyên tắc áp dụng
- Additive, docs-first. T167 phiên này = 0 code/0 DB/0 API (chỉ SPEC + AUDIT).
- Commit từ git toplevel (SSOT rule T155).
- Không đụng file dirty pre-existing.
- Mọi fix revert được tiện lợi: `git revert --no-edit <sha>`.
- ROLLBACK hash-fill 2-pass theo chuẩn T146 (placeholder `<sha>` → hash thật ở commit 2).

---

## 1. Audit (read-only) — phát hiện 6 lỗi logic spec T158

| # | Spec T158 cũ nói | Thực tế (đã xác minh bằng repo) | Kết luận |
|---|------------------|----------------------------------|----------|
| 1 | "Current next task number is T158" | `tasks/T158-glossary-resolver-pre-translation-lookup.md` (DONE) + `tasks/T158-lineage-consensus.md` (DONE); max hiện có T166 | **SAI** → task mới = **T167** |
| 2 | T130 IN_PROGRESS, T131 IN_PROGRESS, T132 waiting T131 | taskdone.md: T130+T131 DONE (commit `c686636`); tasktodo: T132 DONE (6cdc2e9+7832f26) | **SAI** → all DONE |
| 3 | "T126 Groq/Qwen implementation" | T126 = "Q&A Backend thật + Wire UI" (title đã đọc) | **GÁN SAI** → Groq/Qwen = T95 worker + T123 |
| 4 | Phase 1 tạo "Translation Constitution" mới | Đã có **T123 Style Constitution**: `translation_rules` table (rule_code/type/text/priority, status active/pending) + `rules_version` trên translation_cache + `PROMPT_VERSION='t95-batch-cbeta-v1'` | **MỘT NỬA CÓ SẴN** → extend, không tạo hệ song song |
| 5 | (áp dụng) GLOSSARY LOCK inject trước LLM | Đã có **T158-glossary-resolver** `_glossary_resolver(conn, source_text)` + `_save_suggested_rules` chặn AI proposal trùng DB | **ĐÃ CÓ** → reuse |
| 6 | Phase 0 đọc `tasks/T95-...`, `tasks/T94-...` | Cả 2 nằm ở `tasks/backup/` (T95 status in_progress trong backup, T94 done) | **SAI PATH** → đọc từ backup |
| 7 | (quota) `status=quota_exhausted`, không coi là fail | Worker có `error_type='rate_limit'` (L136-137 HTTP 429) nhưng hết retry (2/4/8s max 3) → item `failed` + job last_error | **GAP THẬT** → cần build additive |

## 2. Xác minh thêm (đọc file thật)

- `scripts/cbeta_translate_worker.py` tồn tại: GROQ_URL, DEFAULT_MODEL=`qwen/qwen3.8-27b`, `llm_key_model()`, `call_groq()` (L111), commit-per-passage, retry/backoff, revert-job, raw audit. ✓
- `scripts/t95_schema_migrate.py`: additive (dry-run/apply/verify/revert) — tạo translation_jobs + translation_job_items, thêm cột translation_segments (passage_id/provider/source_original_hash/quality_status 'unreviewed'/created_by_job_id/revision_no/supersedes_translation_id). **Thiếu cột ruleset_id** → gap. ✓
- app.py routes translation: translate_context L2647, translate_gemini_cbeta L3059, polish_cbeta_translation L3568, cbeta/translate_segment L9612, translation/jobs L19652-20092 (resume/cancel/verify/raw), segments/translate L20204. T123 builder `_t123_unified_style_prompt` L16445, GLOSSARY LOCK L16475. ✓
- T94 verify route live: POST `/daoanh/api/admin/translation/verify` (alignment_type='manual_verified', review_status='verified', idempotent). ✓
- Monitor UI: `admin/translation_monitor.html` + `translation_rules.html` + `translation_cache.html` ✓
- git toplevel = `visjs-app` ✓ guard PASS.

## 3. Quyết định + tạo task T167

- Lee phê chuẩn: đổi số **T158→T167**, sửa CURRENT SSOT (T130/T131/T132 = DONE), extend **T123/translation_rules** thay vì tạo hệ mới, reuse **T95 worker** (không rebuild) + **T94 verify** + **T110 glossary** + **T158-glossary-resolver**.
- Tạo `tasks/T167-rules-constrained-buddhist-translation-engine.md` (full corrected spec: Phase 0 audit results, Phase 1..8, NON-GOALS, DB POLICY, ROLLBACK).
- gap thật được đưa vào done_when: quota_exhausted status, validator L0-L3, ruleset_id/segment.

## 4. Files thay đổi phiên này

- `tasks/T167-rules-constrained-buddhist-translation-engine.md` (mới)
- `docs/tasktodo.md` (row T167 đầu ACTIVE)
- `docs/ROLLBACK.md` (row T167, placeholder `<sha_T167>` → hash-fill commit 2)
- `docs/sessions/2026-09-24_t167-rules-constrained-translation-engine.md` (file này)
- `data/progress_data.json` (regen `python -X utf8 scripts/build_progress_data.py`)

## 5. Verify
- `npm run guard` PASS.
- `npm run test` PASS.
- `data/progress_data.json`: chứa T167 `in_progress`, n_tasks 89→90, last_date 2026-09-24.

## 6. Rollback
- Docs-only phiên này: `git revert --no-edit <sha_T167>` (khôi phục tasktodo/ROLLBACK/session/progress_data.json). 0 DB, 0 code.

---

# Session 2026-09-24 (tiếp) — T167 BUILD Phase 1/3/4 (schema + constitution + quota + validator)

## 1. Mục tiêu
- Build các gap thực sự đã xác định ở Phase 0 audit — additive, revert được 1 lệnh + DB revert.

## 2. Đã làm

### Phase 1a — Schema migration (`scripts/t167_schema_migrate.py`, mới)
- Tạo (additive, --dry-run/--apply/--verify/--revert):
  - Bảng `translation_rulesets`, `translation_ruleset_rules` (+ index)
  - Cột `translation_segments.ruleset_id` TEXT DEFAULT ''
  - Cột `translation_rules.ruleset_id` / `.ruleset_version` / `.is_canonical`
- Backup `data/lineage.db.backup_t167_20260924_181908` (1375 MB). Verify PASS (SQLite 3.50.4 DROP COLUMN OK).

### Phase 1b — Seed Constitution (`scripts/seed_t167_constitution.py`, mới)
- Ruleset `t167-constitution-v1` (canonical), 15 rules RULE-001..015 INSERT vào `translation_rules`, map 23 rules (15 RULE + 8 T123 style) vào `translation_ruleset_rules`, set ruleset_meta. Verify PASS.

### Phase 3 — Worker quota contract (`scripts/cbeta_translate_worker.py`, sửa)
- Thêm `QUOTA_EXHAUSTED='quota_exhausted'`, `DEFAULT_RULESET_ID='t167-constitution-v1'`, `commit_translation(ruleset_id=...)`, branch rate_limit sau retry → `quota_exhausted` + break, finalize job `final_status=QUOTA_EXHAUSTED`. `py_compile` PASS.

### Phase 4 — Validator (`scripts/translation_validator.py`, mới)
- Layers A–G → PASS/REVIEW/FAIL, không silently rewrite. Test thật `cbeta:T50n2060:t001947:r001` → FAIL đúng (ruleset_id rỗng, bản cũ).

## 3. Verify
- `python -X utf8 scripts/t167_schema_migrate.py --verify` → ĐẦY ĐỦ ✅
- `python -X utf8 scripts/seed_t167_constitution.py --verify` → 23 rules linked, 15 rules present ✅
- `py_compile` worker + validator OK.
- `npm run guard` + `npm run test` (đang chạy trước khi commit).

## 4. Rollback (build)
- Code: `git revert --no-edit <sha_T167b>` (4 file additive).
- DB: `python -X utf8 scripts/t167_schema_migrate.py --revert` hoặc restore backup `lineage.db.backup_t167_20260924_181908`.
- Docs: trong cùng commit (task/tasktodo/ROLLBACK/session/progress_data.json).

---

# Session 2026-09-25 — T167 BUILD 2 (validator INTEGRATED vào pipeline + UI + validate-job CLI)

## 1. Mục tiêu
- Hoàn tất T167 Phase 4: validator không chỉ là CLI mà **tự chạy sau mỗi commit translation**; hiển thị kết quả trong monitor UI. Giữ additive, revert được.

## 2. Đã làm

### Schema (additive)
- `t167_schema_migrate.py` mở rộng 3 cột `translation_segments.validation_status / validation_report / validated_at` + index `idx_ts_validation`.
- Apply: backup `data/lineage.db.backup_t167_20260925_073742` (1375 MB), verify PASS (10 cột/bảng T167 đầy đủ).

### Worker (`scripts/cbeta_translate_worker.py`)
- Hàm `_validator()`: load `translation_validator` qua `importlib.util.spec_from_file_location` (đường dẫn tuyệt đối) — hoạt động được cả CLI lẫn khi app.py import worker qua importlib.
- Sau `commit_translation` (status committed): chạy `validate_translation(tid, con)` → UPDATE validation_status/report/validated_at. Crash → FAIL + JSON error (không chặn commit).
- CLI mới **`validate-job --job <id>`**: validate toàn bộ segment committed của job cũ → cập nhật cột. Test real pilot `job-T50n2060-20260905_132951584532`: 9/9 FAIL (ruleset_id rỗng, bản cũ trước T167 — đúng provenance).

### API + UI
- app.py `api_t95_job_detail`: subquery thêm `validation_status` per item.
- translation_monitor.html: chip `validator PASS/REVIEW/FAIL` cạnh nút Duyệt chuẩn.

### Verify
- `py_compile` worker + app PASS; node JS-check monitor OK.
- `npm run guard` + `npm run test` + `npm run e2e` PASS (lint ESM pre-existing).
- `scripts/test_t95_18.py` 18/18 PASS (chạy trên bản SAO DB tempfile; worker + validator tích hợp; mock tạo REVIEW đúng; KHÔNG đụng data thật — verify 0 mock-text segment còn lại).
- DB thật sạch: 66 segments (65 active, 1 superseded r002 thật), 0 mock-text.

## 3. Rollback (build 2)
- Code: `git revert --no-edit 3cabea8` (4 file: worker + t167_schema_migrate + app.py + translation_monitor.html).
- DB: `python -X utf8 scripts/t167_schema_migrate.py --revert` (DROP 3 cột validation) hoặc restore backup `lineage.db.backup_t167_20260925_073742`.
- Lưu ý: bản dịch cũ đã validate-job có validation_status=FAIL (provenance) — revert phase 2 xóa cột nhưng raw audit/alignment vẫn còn.---

# Session 2026-09-25 (tiếp) — T167 BUILD 3 (Phase 7 BUDDHIST-HAN-VI-BENCH: 500 real passages + metric deterministic)

## 1. Mục tiêu
- Xây benchmark chuẩn cho bản dịch Hán→Việt: 500 passage THẬT từ CBETA T50n2060 (9316 passage trong DB), 10 category khó (verse, repetitive, titles, context_dependent, long_syntax, person, place, terminology, polysemy, ordinary), score deterministic từ validator (reuse) + glossary + places — KHÔNG bịa passage, KHÔNG bịa score.

## 2. Build
### Package mới `scripts/buddhist_han_vi_bench/` (4 file)
- `__init__.py`: constants — CATEGORIES (10), METRICS (7), AUTO_METRICS (4), HUMAN_METRICS (3), paths `data/benchmark/buddhist_han_vi_bench{,_scored,_human}.json`.
- `select.py`: select() deterministic (seed 20260925). Đọc 9316 passage thật, detect rules: VERSE_TRIG (偈/頌), REP_TRIG (爾時/如是我聞/一時...), TITLE_RE (皇帝/太子...), person (PERSON_SUFFIX/PERSON_LIST), place (places.json nameChinese), terminology (glossary), polysemy (≥3/13 từ), long_syntax (≥70 tự), context_dependent (chỉ từ + ko kết thúc 。), ordinary = không khớp gì. Gán KHÔNG-trùng 1 category theo thứ tự ưu tiên hiếm trước → output 500 item (mỗi category 50, passage độc nhất).
- `score.py`: score_all() — với mỗi item lấy translation_segments revision cao nhất (nếu có), chạy lại validator (importlib) → layer A–G thật; terminology_accuracy (glossary hit), canonical_names_accuracy (place Hán trong Hán và trong bản dịch), alignment_count (passage_translation_alignment), omission_addition (layer C). Human metrics (semantic/doctrinal fidelity, human_acceptance) = **None** + human_required=true. NOTE: `context_consistency` để None (cần human) — ghi source context thô.
- `__main__.py`: CLI select/score/report/human/show. `human <passage_id> --sf --df --cf --te --cp --hs --reviewer` ghi `..._human.json`.

### Chạy thật
- `select` → 500 items, phân bố đều (mỗi category 50); pools: verse 75, repetitive 401, titles 291, context 152, long_syntax 95, person 1080, place 987, terminology 964, polysemy 918, ordinary 4353.
- `score` → 500 items, **2/500 có bản dịch pilot** (t000001 polysemy + t000002 ordinary) → validator chạy đúng (A/B/G FAIL vì ruleset_id rỗng — bản cũ trước T167, expected). Còn lại chờ worker/job translate.

## 3. Verify
- `tests/test_t167_benchmark.py` **15/15 PASS**: determinism seed (2 lần select → cùng tập passage), 500/500 item thật T50n2060, 10 category đủ, passage độc nhất, features đầy đủ (10 key), meta total=9316 khớp DB, round-trip load_set, scored 500 items, human metrics luôn None (không bịa), item có bản dịch → validator_overall hiện.
- `py_compile` 4 file package PASS. `npm run guard` + `npm run test` + `npm run e2e` PASS. `scripts/test_t95_18.py` 18/18 PASS (regression — không đụng worker pipeline).
- `build_progress_data.py` regen OK (73%, 91 tasks, 479 commits).

## 4. Ghi chú kỹ thuật
- Detector long_syntax: line đầu dùng ≥90 → pool 1 (quá khắt) → chỉnh ≥70 (=108 passage) → pool 95 OK.
- Exclusive-priority assignment: mỗi passage đúng 1 category (category hiếm đi trước) để tránh passage bị nhiều category nuốt → phân bố 50×10 đều, không cần random.
- score.py có dead line `segd = dict(seg) if seg else None` đã xóa.
- Test human CLI đã chạy rồi **xóa** `buddhist_han_vi_bench_human.json` (không ship fake human score).

## 5. Rollback (build 3)
- ⚠️ Do agent khác commit đồng thời: file Phase 7 nằm TRONG commit hỗn hợp `22a5cf7` (cùng T5 `app.py`/`places.html`). 
- Revert file Phase 7 RIÊNG: `git checkout 7325830 -- scripts/buddhist_han_vi_bench tests/test_t167_benchmark.py` (từ toplevel, đường dẫn đầy đủ) + bỏ 2 file `data/benchmark/*.json` đang track force-added (hoặc `git rm --cached` + xóa).
- **0 DB revert** (Phase 7 không đổi schema). Backup Phase 6 `lineage.db.backup_t167_20260925_073742` vẫn hợp lệ.
