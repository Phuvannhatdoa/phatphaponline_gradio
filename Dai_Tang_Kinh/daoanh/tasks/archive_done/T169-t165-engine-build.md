---
id: T169
title: "T165 engine BUILD Phase 3 — Rules-Constrained Translation Engine implementation (SPEC v2 §14.3 checklist)"
module: app · scripts · docs · DB (additive 5 cột + backfill match_scope)
priority: high
status: done
created: 2026-09-25
updated: 2026-09-25
depends_on: [T165 (SPEC, id quản lý số task riêng), T167 (seed RULE-001..015), T168 (SPEC v2 review-accepted)]
owner: claudecode
spec: docs/Mimo-Flash/T165-rules-constrained-translation-engine-SPEC.md
done_when: SPEC §14.3 BUILD PHASE 3 checklist (6 mục) toàn bộ PASS; migration additive 5 cột (match_scope/match_terms + constitution_hash/selected_rule_codes/glossary_hash) + backfill match_scope chạy trên DB thật với backup; style_constitution.py SSOT + tests PASS; app.py _t73_* wrap dual-key (lookup source_type/status='edited' guard, write constitution/selected/glossary_hash, invalidate upsert/approve, _t73_call_gemini log usage) + Phase 3b 8 call site truyền source_text; t50 refactor import; admin UI match fields + invalidated_cache_count; prompt_tokens HIT+MISS đo được; guard + npm pipeline + e2e:runtime PASS; tasktodo/ROLLBACK/session log/db_schema.md cập nhật; dashboard regen; commit 2-pass hash-fill qua scripts/t83_force_commit.py.
---

# T169 — T165 engine BUILD Phase 3 (Rules-Constrained Translation Engine)

**Status:** DONE (2026-09-25) — Build toàn bộ Phase 1-8 hoàn thành. Xem `docs/Mimo-Flash/T165-rules-constrained-translation-engine-SPEC.md` §14.3.
**Kết quả:** Phase 1 migration `--apply` ĐÃ CHẠY (backup `data/backups/lineage_t165_20260925_135855.db`; +5 cột; backfill `match_scope` always=41/terms=71; cache 3 hash cột NULL). Phase 2 SSOT `style_constitution.py` + tests **10/10 PASS** (thêm `test_pre_migration_guards_16`). Phase 3 wrap `_t73_style_lock`/`_t73_build_style_prompt`/`_t73_call_gemini` (metrics) + Phase 3b 5 write site dual-key + 8 call site source_text + upsert/approve invalidate + `_t165_extract_match_terms` auto-backfill. Phase 4 `t50_passage_vi_backfill.py` delegate SSOT. Phase 5 `admin/translation_rules.html` match fields + scope badge + invalidated_cache_count. Phase 6/7 `npm run guard` + `npm run pipeline` PASS + e2e:runtime 2/2 + admin API live (rules=112/active=111/rv=572e8566/terms-scope=71). Phase 8 docs (ROLBACK/tasktodo/db_schema/session) + commit 2-pass.
**Phạm vi:** `style_constitution.py` (mới, cùng cấp app.py — SSOT) · `scripts/t165_rules_engine_migrate.py` (mới) · `app.py` (wrap `_t73_*` + Phase 3b 8 call site + upsert/approve invalidate + `_t73_call_gemini` log) · `scripts/t50_passage_vi_backfill.py` (refactor import) · `admin/translation_rules.html` (match fields + invalidated_cache_count) · `tests/test_t165_style_constitution.py` (mới) · DB additive 5 cột + backfill `match_scope` · `docs/db_schema.md`, `docs/tasktodo.md`, `docs/ROLLBACK.md`, `docs/sessions/2026-09-25_t169-t165-engine-build.md` · `data/progress_data.json` (regen).

## Bối cảnh

T165 SPEC v2 đã được review-accept (T168). SPEC §14.3 = BUILD PHASE 3 CHECKLIST quy 6 mục bắt buộc để hiện thực Rules-Constrained Translation Engine:

1. §4.4 lookup cache kèm `source_type` + `status!='invalidated'` + nhánh ưu tiên `status='edited'` (#1#2#3).
2. Bỏ DELETE `selected_rule_codes IS NULL` (#4) — chỉ DELETE theo `instr(','||codes||',', ','||code||',')`.
3. Công thức hash post-resolver (FULL rule_text + filtered glossary + exemplar + PROMPT_FORMAT_VERSION + t166 fingerprint) + `label`/`json_mode` (#5) + Phase 3b bắt buộc (#7).
4. §5.1 wrappers: `_build_dila_card_prompt`, `_t126_build_qa_prompt`, `_t73_call_gemini` (#6#8) + READ sites ~22 (#9).
5. extract match_terms ≥2 chars + forced-always khi fail (#10) + coverage dry-run trên 1762 cache (#11) + fingerprint mass-miss cảnh báo (#12).
6. Selector chốt `status='active' AND is_active=1` (#13) + Bảng thật 112/1762/rv15 (đã apply SPEC hôm nay).

## Các bước (Build)

1. **Task file T169** (file này) + tasktodo/ROLLBACK rows.
2. **Phase 1 — Migration:** `scripts/t165_rules_engine_migrate.py`:
   - `--stats` (đọc schema hiện tại, đếm row, in n always/terms dự kiến) · `--dry-run` (in SQL + backup path, 0 apply) · `--apply` (backup `data/backups/lineage_t165_<ts>.db` qua sqlite backup API; ADD 5 cột idempotent; backfill match_scope/match_terms theo quy tắc §4.2; backfill 3 cột hash cache = NULL) · `--revert` (DROP 5 cột).
   - Update `docs/db_schema.md`.
3. **Phase 2 — SSOT `style_constitution.py`** (cùng cấp app.py):
   - `PROMPT_FORMAT_VERSION='t165-v1'` · `source_hash` · `extract_match_terms` (regex + lọc ≥2 chars, fail→[]) · `select_rules` (selector `status='active' AND is_active=1`, filter match_scope!='terms' OR any term substring, keys DB: rule_code/rule_type/rule_text) · `constitution_hash` (sha256[:16], FULL rule_text + filtered glossary "zh→vi" + exemplar "zh:vi" + version + fingerprint) · `glossary_hash` · `filter_glossary_for_text` · `style_lock` (chạy resolver động nếu có, hash post-merge) · `log_prompt_metrics` (usage → logger, không hard-fail) · `build_style_prompt` (dán Y `_t73_build_style_prompt`, chỉ đổi nguồn rule_block/glossary_block) · `invalidate_cache_for_rule` (DELETE theo §3 — bỏ NULL) · `invalidate_cache_all_semantic`. KHÔNG import app.py (chống circular).
   - Tests `tests/test_t165_style_constitution.py` (extract/select/hash/invalidate/dedup/db thật khớp).
4. **Phase 3 — Wrap app.py `_t73_*`** (giữ tên hàm — code preservation):
   - `_t73_get_active_rules` → chốt selector `status='active' AND is_active=1` (#13), thêm cột match_scope/match_terms (best-effort nếu có).
   - `_t73_style_lock(conn, source_text=None, ...)` → delegate `style_lock`; callers cũ không truyền text → all-active (hành vi = hôm nay).
   - `_t73_build_style_prompt` / `_t73_source_hash` → delegate.
   - Dual-key lookup helper `_t165_lookup_cache` (constitution_hash trước, legacy rules_version sau, source_type luôn kèm, ưu tiên edited, rules_outdated badge).
   - Write helper `_t165_write_cache` (ghi constitution_hash + selected_rule_codes + glossary_hash + rules_version; edited-row không bao giờ REPLACE).
   - 5 write sites (6380-6401 relation_evidence · 16723-16736 person_bio · 17157-17249 dila_card · 17300-17313 bio_vi edited · 17759-17772 place_note) → chuyển lookup+write dual-key; dila_card bắt buộc hash post-resolver.
   - Upsert/approve → `invalidate_cache_for_rule` sau khi sửa rule_text/is_active/approve; response thêm `invalidated_cache_count`.
   - `_t73_call_gemini` → gọi `log_prompt_metrics` với `usage` từ response.
   - `_glossary_resolver` docstring "12" → "14" (#14).
5. **Phase 3b — Enumerate 8 call site và truyền source_text:**
   1. app.py 2659 (`/api/translate`? `text`) 
   2. 6379 (relation evidence excerpt)
   3. 16724 (person bio bio_zh)
   4. 17173 dila_card (source_data JSON join)
   5. 17759 (place note note_zh)
   6. 17907 (preview/passage — cần đọc)
   7. 18081 (passage preview)
   8. 20772 (_t126_build_qa_prompt — question/evidence; KHÔNG ghi cache → all-active hoặc evidence text, ghi rõ trong session).
6. **Phase 4 — Refactor `scripts/t50_passage_vi_backfill.py`:** body `_style_lock_blocks`/`build_prompt` → import `style_constitution` (sys.path), xoá query rule cục bộ.
7. **Phase 5 — Admin UI `admin/translation_rules.html`:** form create/edit Match scope + Match terms (1 Hán từ/dòng → JSON), chip `ALWAYS`/`TERMS: 法嗣`, body gửi thêm match_scope/match_terms, message hiện `invalidated_cache_count`.
8. **Phase 6 — Apply:** `python -X utf8 scripts/t165_rules_engine_migrate.py --apply` trên DB thật (backup tự tạo) + verify stats.
9. **Phase 7 — Verify:** `npm run guard` · `npm run pipeline` · e2e:runtime (`--output=.pw-tmp`) · coverage dry-run (rule/match trên 1762 source_text, liệt kê rule chưa match lần nào) · đo prompt_tokens 1 HIT + 1 MISS (target ↓, không fail) · `docs/db_schema.md` · session log · tasktodo ⏳ → ✅ · ROLLBACK row (code + schema path) · dashboard regen.
10. **Phase 8 — Commit 2-pass hash-fill:** pass 1 content qua `t83_force_commit.py` (chỉ stage path T169), pass 2 docs thay sha thật + status done + dashboard.

## Verify

- DB thật: 5 cột mới tồn tại; backfill match_scope đúng (n terms / n always / n fail→always); cache 3 cột hash NULL (1762).
- `style_constitution` tests PASS; `npm run pipeline` PASS; e2e:runtime 2/2.
- lookup HIT: `constitution_hash` khớp; fallback legacy: rules_version; rules_outdated badge đúng khi rv lệch.
- Upsert rule sửa rule_text → cache row chứa rule bị xoá (instr), không đụng row NULL.
- prompt_tokens đo được HIT + MISS, ghi session (baseline <150-250?).
- Revert: code → `git revert --no-edit <sha>`; schema → `t165_rules_engine_migrate.py --revert` + backup path.

## Files

- `style_constitution.py` (mới — SSOT, cùng cấp app.py)
- `scripts/t165_rules_engine_migrate.py` (mới)
- `app.py` (wrap `_t73_*` + Phase 3b + upsert/approve invalidate + `_t73_call_gemini` log + `_glossary_resolver` docstring 14)
- `scripts/t50_passage_vi_backfill.py` (refactor)
- `admin/translation_rules.html` (match fields + invalidated_cache_count)
- `tests/test_t165_style_constitution.py` (mới)
- `docs/db_schema.md` · `docs/tasktodo.md` · `docs/ROLLBACK.md` · `docs/sessions/2026-09-25_t169-t165-engine-build.md`
- `data/progress_data.json` (regen)

## Rollback

- Code/docs: `git revert --no-edit <sha>` (2-pass: sha thật ghi sau).
- Schema: `python -X utf8 scripts/t165_rules_engine_migrate.py --revert` (DROP 5 cột) + restore backup `data/backups/lineage_t165_*.db` nếu cần.
- Cache sai sau deploy: `invalidate_cache_all_semantic(conn)` hoặc bump `PROMPT_FORMAT_VERSION` → miss dần (chọn 1, ghi session).
- Data rule: UPDATE rule ngược + invalidate lại.