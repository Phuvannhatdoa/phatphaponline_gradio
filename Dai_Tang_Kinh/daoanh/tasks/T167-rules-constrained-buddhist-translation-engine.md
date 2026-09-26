---
id: T167
title: "Rules-Constrained Buddhist Translation Engine (spec T158 cũ -> đổi số T167 + sửa SSOT)"
module: translation
priority: high
status: in_progress
depends_on: [T95, T94, T110, T123, T126, T158-glossary-resolver]
created: 2026-09-24
updated: 2026-09-24
plan_approved_at: "2026-09-24 (Lee duyệt - đổi số T158->T167, sửa CURRENT SSOT, extend T123/rules thay vì hệ mới)"
owner: Lee
done_when: >
  Phase 0 (spec + integration audit) hoàn tất read-only; các gap đã xác nhận thực sự
  (quota_exhausted status, validator L0-L3, ruleset_id per segment) được build additively;
  T95 worker KHÔNG rebuild, translation_rules KHÔNG tạo bảng song song; mọi thay đổi revert được 1 lệnh.
---

# T167 - Rules-Constrained Buddhist Translation Engine

**Status:** in_progress (2026-09-24) - SPEC ĐÃ HIỆU CHỈNH THEO AUDIT THẬT + Phase 1 (Schema + Constitution) DONE + worker quota contract DONE + Phase 4 validator DONE (bản đầu, additive). Còn: seed tồn tại trong DB, tích hợp validator vào pipeline/UI review, benchmark, GOLD. Xem mục "BUILD PROGRESS".
**Admin decision:** Phê chuẩn hướng `CBETA passage -> small atomic unit -> Translation Constitution/Rules -> DILA context + glossary_vi + CBETA context -> Qwen3.8-27B via Groq -> deterministic validation -> Human Scholarly Review -> GOLD`. T167 KHÔNG rebuild T95 -> EXTEND/REUSE T95. **Mọi bug khi fix revert được 1 lệnh** (xem Rollback).

---

## PHÊ CHUẨN KIẾN TRÚC (ADMIN DECISION)

```
CBETA passage
→ small atomic passage/unit
→ Translation Constitution / Rules (translation_rules, T123)
→ DILA canonical context + glossary_vi + CBETA context
→ Qwen3.8-27B via Groq
→ draft
→ deterministic validation  (validator L0-L3)
→ Human Scholarly Review (T94 manual_verified)
→ GOLD (future fine-tuning dataset)
```

## CURRENT SSOT (2026-09-24 - ĐÃ SỬA so với spec T158 cũ)

| Task | Trạng thái thật | Bằng chứng |
|------|----------------|------------|
| T157 | DONE + Live QA | taskdone.md |
| T130 | **DONE** (spec cũ ghi IN_PROGRESS - SAI) | taskdone.md L5, commit `c686636` |
| T131 | **DONE** (spec cũ ghi IN_PROGRESS - SAI) | taskdone.md L5, `c686636`, frontmatter đã sync T166 |
| T132 | **DONE** (spec cũ ghi waiting T131 - SAI) | tasktodo.md, P1-P8 commits |
| T95 | DONE (file ở `tasks/backup/T95-...`) | taskdone.md L29 |
| T94 | DONE (file ở `tasks/backup/T94-...`) | alignment schema, verify route live |
| T110 | DONE | glossary pipeline, T05 closure |
| T126 | DONE/live - **là Q&A Backend (KHÔNG phải Groq/Qwen)** | `T126-qa-backend-real.md` |
| T123 | DONE - **Style Constitution = Translation Constitution hiện có** | `_t123_build_style_prompt`, `translation_rules` table |
| T158-glossary-resolver | **DONE - pre-translation DB lookup ĐÃ CÓ** | `_glossary_resolver`, GLOSSARY LOCK inject |
| T158-lineage-consensus | DONE (T158 dùng lần 2) | taskdone |

**Số task:** T158 đã dùng 2 lần (glossary-resolver + lineage-consensus) nên **KHÔNG được đặt tên T158**. Task mới = **T167** (T166 là max hiện tại). "Current next task number is T158" trong spec cũ là SAI.

## PHASE 0 - INTEGRATION AUDIT (ĐÃ CHẠY READ-ONLY 2026-09-24)

### 1. T95 reuse map (worker ĐÃ TỒN TẠI, giữ nguyên)
- `scripts/cbeta_translate_worker.py`: `new-job` tạo translation_jobs + translation_job_items, commit per passage INSERT translation_segments, resume, retry/backoff (2/4/8s max 3), raw audit, revert-job (`--revert`). Groq call `call_groq` L111, model mặc định `qwen/qwen3.8-27b` (L61), key env GROQ_API_KEY → llm_config groq_key (không key literal). `PROMPT_VERSION='t95-batch-cbeta-v1'` (L59).

### 2. T94 reuse map (verification ĐÃ CÓ)
- Route `POST /daoanh/api/admin/translation/verify` (app.py L20087-20134): insert `passage_translation_alignment` alignment_type='manual_verified', review_status='verified'. Idempotent, rollback thủ công = xóa dòng alignment.

### 3. T110 reuse map
- `data/glossaries/vi-buddhist.json` (glossary lock gốc) + pipeline glossary_vi → `_glossary_resolver` (T158-glossary-resolver) inject db_verified terms vào GLOSSARY LOCK trước khi gọi LLM.

### 4. T126 reuse map (HIỆU CHỈNH so với spec cũ)
- T126 = Q&A Backend (wire UI), KHÔNG phải Groq/Qwen. Model contract tái sử dụng: **T95 worker** (`scripts/cbeta_translate_worker.py`) + **T123 Style Constitution** (`_t123_unified_style_prompt` app.py L16445). Mặc định provider=groq, model=qwen/qwen3.8-27b.

### 5. DB/schema thực tế
- `data/lineage.db`: translation_jobs + translation_job_items (tạo bởi `scripts/t95_schema_migrate.py`, additive, --dry-run/--apply/--verify/--revert). translation_segments đã có: passage_id, provider, source_original_hash, quality_status (default 'unreviewed'), created_by_job_id, revision_no, supersedes_translation_id, prompt_version, review_status, translation_status (default 'draft').
- translation_cache có cột **rules_version** (app.py L2660) - versioning GLOSSARY/RULES đã có 1 phần.

### 6. Code integration points thực tế
- `app.py`: routes translation (L2647 translate_context, L3059 translate_gemini_cbeta, L3568 polish_cbeta_translation, L9612 cbeta/translate_segment, L19652-20092 translation/jobs + verify, L20204 segments/translate), T123 Style Constitution builder (L16292, L16445), GLOSSARY LOCK (L16475).
- Monitor/review UI: `admin/translation_monitor.html` + `translation_rules.html` + `translation_cache.html`.

### 7-9. File đề xuất (theo spec, giữ nguyên)
- Constitution: extend `translation_rules` table (rule meta + version) - KHÔNG tạo bảng mới song song.
- Validator: `scripts/translation_validator.py` (mới, additive).
- Benchmark: `scripts/buddhist_han_vi_bench/` (mới).

### 10. Thay đổi schema additive (nếu cần, sau audit bổ sung)
- `translation_segments` thêm `ruleset_id` (TEXT, additive) nếu cần truy vết ruleset per segment. Theo quy trình `t95_schema_migrate.py`: dry-run → backup → apply → verify → revert.

### 11. Risks/conflicts
- **T158 spec cũ sai SSOT** → đã sửa (mục CURRENT SSOT).
- **T126 gán sai role** → đã hiệu chỉnh reuse map (mục 4).
- Quota hiện bị đánh thành translation failure (xem phase 3 gap).
- Lint ESM error (admin/placevn.html) + e2e:runtime EPERM là pre-existing env, không liên quan.

### 12-14. Tests / dependency / rollback
- Tests: `scripts/test_t95_18.py` hiện có + thêm validator unit tests.
- Dependencies: T130/T131 đã DONE, 0 phụ thuộc mới. Không đụng T150 (lineage audit). 
- Rollback: mọi commit `git revert --no-edit <sha>`; DB additive theo t95 migrate --revert + backup.

### 15. Recommendation: **BUILD** (theo phase, additive)

---

## PHASE 1 - TRANSLATION CONSTITUTION (extend T123, KHÔNG tạo mới)

- Sử dụng bảng `translation_rules` (rule_code, rule_type, rule_text, priority, status active/pending) sẵn có.
- Seed 15 canonical rules dưới đây additively (RULE-001..015) kèm `ruleset_version` meta.
- Prompt nhận `ruleset_id + ruleset_version` (đã có rules_version trong translation_cache; thêm ruleset_id vào translation_segments nếu cần).
- **KHÔNG hard-code toàn bộ constitution trong Python.**

Canonical rules:
RULE-001 No Addition · RULE-002 No Omission · RULE-003 Terminology Consistency · RULE-004 Canonical Person Name · RULE-005 Canonical Place Name · RULE-006 Buddhist Terminology Preservation · RULE-007 Subject/Object Preservation · RULE-008 Ambiguity Preservation · RULE-009 Verse/Kệ Preservation · RULE-010 No External Doctrinal Inference · RULE-011 Unknown Term → REVIEW · RULE-012 Unknown Proper Name → REVIEW · RULE-013 Low Confidence → REVIEW · RULE-014 No Automatic Canonical Promotion · RULE-015 Provenance Required

## PHASE 2 - CONTEXT CONTRACT
- Minimal packet: source passage + surrounding context + glossary_vi hits + DILA canonical person/place hits + CBETA metadata + source provenance. Không dump toàn DB, không bịa context.

## PHASE 3 - MODEL CONTRACT
- Reuse Groq worker (`cbeta_translate_worker.py`). Default provider=groq, model=qwen/qwen3.8-27b (L61).
- Giữ: batch, resume, retry/backoff, per-passage commit, raw audit, revert-job, quota-safe resume.
- **GAP THỰC SỰ cần build:** worker hiện có error_type 'rate_limit' (L136) nhưng hết retry → item 'failed' + job last_error → **quota bị đánh là translation failure**. Cần nhánh `status='quota_exhausted'` (+ job paused/resumable), KHÔNG tính là failed.

## PHASE 4 - VALIDATOR (mới, additive)
- Deterministic layers: A schema/JSON · B provenance · C omission/addition gate · D terminology consistency · E canonical person/place · F source/target sanity · G ruleset compliance.
- Trả: PASS / REVIEW / FAIL. **KHÔNG silently rewrite.** FAIL phải auditable (giữ raw).

## PHASE 5 - QUALITY LEVELS
- L0 machine draft · L1 rules-constrained draft · L2 evidence-aware scholarly draft · L3 human-approved GOLD. Chỉ L3 vào GOLD. Map lên translation_status/quality_status có sẵn (draft/unreviewed/reviewed...), không tạo hệ trùng.

## PHASE 6 - HUMAN REVIEW
- Reuse T94 manual_verified (alignment_type='manual_verified', review_status='verified'). Persist: source text, AI draft, final reviewed text, model, provider, ruleset version, prompt version, source version, review status, reviewer, review timestamp, provenance. Không tạo hệ verify thứ 2.

## PHASE 7 - BENCHMARK (BUDDHIST-HAN-VI-BENCH)
- 500 real CBETA passages. Categories: ordinary Classical Chinese, Buddhist terminology, person names, place names, titles, long syntax, repetitive canonical structures, polysemy, verse, context-dependent.
- Metrics: Semantic Fidelity, Terminology Accuracy, Canonical Person/Place Accuracy, Doctrinal Fidelity, Context Consistency, Omission/Addition/Hallucination Rate, Human Scholarly Acceptance. **Không bịa benchmark.**

## PHASE 8 - GOLD DATASET
- Export training-ready: source, final translation, provenance, ruleset version, review metadata. Separable from drafts. **Chỉ cho future fine-tune task, KHÔNG fine-tune trong T167.**

## NON-GOALS
- KHÔNG rebuild T95, KHÔNG tạo second worker, KHÔNG thay DILA bằng LLM-generated names, KHÔNG thay glossary_vi bằng model guesses, KHÔNG auto-publish AI translation, KHÔNG bịa scholarly translation, KHÔNG bịa benchmark score, KHÔNG activate external sources tự động, KHÔNG sửa canonical ID, KHÔNG redesign unrelated lineage tasks, KHÔNG đụng T130/T131/T157, KHÔNG tạo fake data, KHÔNG reset --hard, KHÔNG destructive DB migration.

## DB POLICY
- Additive only. No destructive migration. No canonical ID changes. Schema change chỉ khi audit chứng minh cần; phải có: bảng/column chính xác + indexes + migration script + backup + rollback trước BUILD.

---

## BUILD PROGRESS (2026-09-24, commit `9179d75`)

### Phase 1 — Schema + Constitution ✅ (DB additive, revert storable)
- **Migration:** `scripts/t167_schema_migrate.py` (--dry-run/--apply/--verify/--revert) tạo additive:
  - Bảng `translation_rulesets` (ruleset_id PK, ruleset_version UNIQUE, description, is_canonical, created_by, created_at, updated_at)
  - Bảng `translation_ruleset_rules` (PK ruleset_id+rule_code, priority, is_active) + index
  - Cột `translation_segments.ruleset_id` TEXT DEFAULT ''
  - Cột `translation_rules.ruleset_id` / `.ruleset_version` / `.is_canonical`
  - Backup: `data/lineage.db.backup_t167_20260924_181908` (1375 MB). Verify PASS (SQLite 3.50.4 — DROP COLUMN OK).
  - Revert DB: `python -X utf8 scripts/t167_schema_migrate.py --revert` hoặc restore backup.
- **Seed Constitution:** `scripts/seed_t167_constitution.py` (--dry-run/--verify/apply) upsert:
  - Ruleset **`t167-constitution-v1`** (is_canonical=1)
  - 15 canonical rules **RULE-001..015** vào `translation_rules` (additive, có `is_active=1`, `priority`)
  - Map 23 rules (15 RULE-* + 8 T123 style: PERSONA_BAN_DICH, EXPRESSION_PRINCIPLE, NO_ADDITION, GLOSSARY_LOCK_STABLE, CANONICAL_NAMES, TONE_OVERALL, LITERARY_PURITY, HONORIFIC_PRONOUN) vào `translation_ruleset_rules`
  - Cập nhật `translation_rules.ruleset_id/ruleset_version/is_canonical=1`
  - Verify PASS (23 rules linked, 15 rules present).

### Phase 3 — Worker quota contract ✅ (code, chưa test chạy thật)
- `scripts/cbeta_translate_worker.py`:
  - Thêm `QUOTA_EXHAUSTED = 'quota_exhausted'` + `DEFAULT_RULESET_ID = 't167-constitution-v1'`
  - `commit_translation(..., ruleset_id=DEFAULT_RULESET_ID)` → INSERT có cột ruleset_id
  - Branch `if not parsed and err_type == 'rate_limit'` (sau retry/backoff) → set item `status='quota_exhausted'`, `error_message`, print cảnh báo + `break` (KHÔNG đánh failed)
  - Finalize: nếu có item quota_exhausted → `final_status = QUOTA_EXHAUSTED` (job paused/resumable), remaining count bao gồm quota_exhausted, log `quota_exhausted {n}`.
  - Syntactic check `py_compile` PASS. Bản dịch code cũ (ruleset_id rỗng) KHÔNG bị sửa — validator gắn cờ REVIEW/FAIL.

### Phase 4 — Validator ✅ (bản đầu, additive)
- `scripts/translation_validator.py` (mới): deterministic layers A–G → PASS/REVIEW/FAIL, KHÔNG silently rewrite, FAIL auditable (giữ raw).
  - A schema/JSON · B provenance (ruleset_id tồn tại, prompt_version model provider source_hash) · C omission/addition gate (echo check, ratio 0.6–8.0, alignment) · D terminology (glossary lock, cấm Anh ngữ thay Hán-Việt) · E canonical person/place (flag [REVIEW:]) · F source/target sanity (tỷ lệ ký tự Việt, câu) · G ruleset compliance (active rules của ruleset).
  - Usage: `python scripts/translation_validator.py <translation_id> | --job <job_id> | --work <work_id> --status unreviewed`.
  - Test thật: `cbeta:T50n2060:t001947:r001` → FAIL (ruleset_id rỗng, đúng — bản cũ trước T167), layers khác PASS → validator hoạt động đúng.

## BUILD PROGRESS 2 (2026-09-25, commit `3cabea8`) — Validator INTEGRATED vào pipeline + UI

### Phase 3+4 — Worker tự validate sau mỗi commit ✅ (additive cột, revert được)
- **Schema mở rộng (t167_schema_migrate.py, additive):** `translation_segments.validation_status` / `.validation_report` / `.validated_at` + index `idx_ts_validation`. Backup mới `data/lineage.db.backup_t167_20260925_073742`. Verify PASS (3 cột mới).
- **Worker `cbeta_translate_worker.py`:** sau `commit_translation` chạy ngay `_validator().validate_translation(tid, con)` (load `translation_validator` qua importlib từ đường dẫn tuyệt đối — an toàn cả CLI lẫn trong app.py) → cập nhật `validation_status/report/validated_at`. Lỗi validator crash → `FAIL` + JSON error (auditable, KHÔNG rewrite, KHÔNG chặn commit). Thêm CLI **`validate-job --job <id>`** validate toàn bộ segment committed của 1 job cũ (bản trước T167 ruleset rỗng → FAIL provenance, đúng).
- **app.py job detail** (`/daoanh/api/translation/jobs/<id>`): subquery trả `validation_status` per item.
- **translation_monitor.html:** chip `validator PASS/REVIEW/FAIL` (xanh/vàng/đỏ) cạnh nút Duyệt chuẩn.
- **Tests:** `npm run test` placeholder (PASS), `scripts/test_t95_18.py` 18/18 PASS (chạy trên bản SAO DB — worker + validator tích hợp, mock tạo REVIEW đúng, KHÔNG đụng data thật: verify 0 mock-text segment còn lại), `py_compile` worker+app PASS, node JS check monitor OK, guard + e2e PASS.

## BUILD PROGRESS 3 (2026-09-25, commit `22a5cf7`) — Phase 7 benchmark ✅ (deterministic, KHÔNG bịa score)

### Phase 7 — BUDDHIST-HAN-VI-BENCH (500 real CBETA passages + metric)
- **Package `scripts/buddhist_han_vi_bench/`** (mới):
  - `__init__.py` — constants: 10 CATEGORIES, METRICS, AUTO_METRICS (terminology_accuracy, canonical_names_accuracy, context_consistency, omission_addition), HUMAN_METRICS (semantic_fidelity, doctrinal_fidelity, human_acceptance), paths `data/benchmark/buddhist_han_vi_bench{,_scored,_human}.json`.
  - `select.py` — **select deterministic**: đọc 9316 passage thật T50n2060 từ DB, detector admin bằng glossary + places.json + cấu trúc Hán văn (regex), gán KHÔNG-trùng-lặp mỗi passage → đúng 1 category theo thứ tự ưu tiên (verse → repetitive → titles → context_dependent → long_syntax → person → place → terminology → polysemy → ordinary). Output 500 items, đủ 10 category × 50, passage độc nhất.
  - `score.py` — **score deterministic**: load benchmark, với mỗi item lấy bản dịch hiện hành từ translation_segments (revision cao nhất), chạy lại `validate_translation` (reuse validator qua importlib — layer A–G thật); tính terminology_accuracy (glossary hit), canonical_names_accuracy (place Hán trong passage ∧ trong bản dịch), alignment_count đọc từ passage_translation_alignment. **Metric CẦN NGƯỜI (semantic_fidelity/doctrinal_fidelity/human_acceptance) đặt `None` + `human_required=true` — KHÔNG bịa số.**
  - `__main__.py` — CLI `select | score | report | human | show` (human ghi 1–5 mới vào `..._human.json`, reviewer + timestamp).
- **Chọn 500 passage:** seed cố định `20260925`, re-run trùng tập passage (deterministic). Phân bố chính xác: mỗi category 50 (verse/repetitive kẹp theo pool: verse pool 75, repetitive 401, titles 291, context 152, long_syntax 95 ≥ len70, person 1080, place 987, terminology 964, polysemy 918, ordinary 4353).
- **Score 500 item:** 2/500 có bản dịch pilot (t000001/t000002 polysemy+ordinary) → validator layers đúng (A/B/G FAIL vì ruleset_id rỗng — bản cũ trước T167, expected), còn lại chờ worker/job translate. Báo `with_translation: 2`.
- **Tests:** `tests/test_t167_benchmark.py` 15/15 PASS (determinism seed, 500 item thật, 10 category, passage độc nhất, meta=9316, round-trip JSON, scored đủ 500, human metrics luôn None, validator chạy trên item có bản dịch). `py_compile` 4 file package PASS. `guard` + `npm run test` + `npm run e2e` PASS. `scripts/test_t95_18.py` 18/18 PASS (regression worker/validator không đổi). Regen `data/progress_data.json` OK (73%, 91 tasks, 479 commits).
- **KHÔNG đổi DB schema Phase 7** — output là data files + scripts (additive, revert = git revert). Backup Phase 6 `data/lineage.db.backup_t167_20260925_073742` vẫn hợp lệ.

### Chạy lại
```bash
python -X utf8 -m scripts.buddhist_han_vi_bench select   # → data/benchmark/buddhist_han_vi_bench.json
python -X utf8 -m scripts.buddhist_han_vi_bench score    # → ..._scored.json
python -X utf8 -m scripts.buddhist_han_vi_bench report   # tổng hợp theo category
python -X utf8 -m scripts.buddhist_han_vi_bench human <passage_id> --sf 4 --df 5 ...
```

### Còn lại (chưa build)
- Seeding các bản dịch cũ ruleset_id mặc định (KHÔNG tự động — để human review quyết, tránh giả ràng buộc).
- Điền human scores thật cho benchmark (chờ admin/giáo thọ duyệt per item) → Phase 8 GOLD export từ scored/human.
- Phase 8 GOLD export: `buddhist_han_vi_bench_human.json` + translation_segments → training-ready dataset (JSONL), KHÔNG fine-tune trong T167.
- Hiển thị validation trong reader (places.html badge) — nếu admin muốn.

## Files
- `tasks/T167-rules-constrained-buddhist-translation-engine.md` (mới - file này)
- `docs/tasktodo.md` (row T167 đầu ACTIVE)
- `docs/ROLLBACK.md` (row T167, hash-fill 2-pass)
- `docs/sessions/2026-09-24_t167-rules-constrained-translation-engine.md` (session log)
- `data/progress_data.json` (regen `python -X utf8 scripts/build_progress_data.py`)

## Rollback
- Docs-only (commit spec/audit `795fa20`): `git revert --no-edit 795fa20` - khôi phục tasktodo/ROLLBACK/session/progress_data.json. 0 DB, 0 code.
- Build phase (`9179d75`): **code revert `git revert --no-edit 9179d75`** (3 scripts: worker + t167_schema_migrate + seed_t167_constitution + translation_validator — additive, không đụng file khác). Kèm **DB revert**: `python -X utf8 scripts/t167_schema_migrate.py --revert` (xóa 2 bảng + 5 cột additive) hoặc restore `data/lineage.db.backup_t167_20260924_181908`. Dữ liệu rules seed nằm trong translation_rules (bảng cũ) — revert script sẽ xóa rows RULE-001..015 + unlink ruleset meta nếu muốn; mặc định giữ (additive, vô hại).
- Build phase 2 (`3cabea8`): **code revert `git revert --no-edit 3cabea8`** (4 file: worker + t167_schema_migrate + app.py + translation_monitor.html — additive; undo xóa 3 cột validation_status/report/validated_at khỏi translation_segments). **DB revert**: `python -X utf8 scripts/t167_schema_migrate.py --revert` đã xóa luôn 3 cột (DROP COLUMN); hoặc restore backup `data/lineage.db.backup_t167_20260925_073742` (sau build 2). Lưu ý: bản dịch cũ được validate-job đã có validation_status=FAIL (provenance ruleset rỗng) — revert phase 2 xóa cột, dữ liệu đó mất khỏi segment nhưng raw audit + alignment vẫn còn.
- Phase sau: mỗi commit riêng `git revert --no-edit <sha>`; DB theo migrate + backup.