---
id: T168
title: "Rule Resolver + Context Compiler + Cache Correctness (absorb T158-DEBUG-001 directive) — REVIEW + PLAN"
module: Editorial / LLM Translation
priority: high
status: pending
owner: claudecode
depends_on: [T165, T166]
created: 2026-09-25
updated: 2026-09-25
spec: docs/Mimo-Flash/T168-rule-resolver-context-compiler-PLAN.md
designed_by: opencode (mimo-v2.6) — review directive [T158-DEBUG-001]
handoff_to: Claude Code Agent
plan_approved_at: "2026-09-25 (Admin: gộp REVIEW+PLAN 1 file T168 · sau đó đồng ý build = G1 → Phase 0 audit + Phase 1 resolver build xong, xem B0 + docs/sessions/2026-09-25_t165-build-phase0-1-2.md)"
absorbed_into: [T165, T166]
source_directive: "[T158-DEBUG-001] Rules-Constrained Translation Engine Optimization — Groq/Qwen Rule Resolver + Context Compiler + Cache Correctness"
done_when: |
  Review (PART A) + Plan (PART B) ghi 1 file này; T165 SPEC §16 + T166 §21
  trỏ về đây; tasktodo + ADMIN_REVIEW item 19 + session + ROLLBACK + dashboard
  regen; npm run pipeline PASS. Khi build: Phase 0–8 theo §B, gate deterministic
  test PASS mới pilot Groq ≤5; helper dùng style_constitution.py (KHÔNG _t158_*/
  _t168_build_prompt); cache key = constitution_hash additive, KHÔNG đổi
  source_hash; lifecycle tái dùng pending→active/dismissed.
---

# T168 — Rule Resolver + Context Compiler + Cache Correctness

> **Directive gốc:** `[T158-DEBUG-001]` (Admin gửi 2026-09-25) — yêu cầu check logic trước.
> **Kết luận review:** đúng hướng, nhưng **4 P0 + 8 P1** phải sửa; **absorb vào T165/T166**,
> không xây parallel engine. **Task ID thật = T168** (T158 đã dùng ×2).
> **Trạng thái:** PLAN ONLY — Admin chưa duyệt chạy Phase 0 audit.

---

# PART A — REVIEW (check logic ↔ repo/DB thật)

Audit read-only: `data/lineage.db` (mode=ro) · `app.py` (21.054 dòng) ·
`admin/app.py` (18.865 dòng) · `scripts/cbeta_translate_worker.py` · `tests/`.

## A0. Kết luận

| Mục | Kết luận |
|-----|----------|
| Tổng thể | **Đúng** — đây là "Rule Resolver + Context Compiler", không phải tối ưu token thuần; §1/§6 tự cấm builder & rule-system thứ 2 = đúng nguyên tắc repo |
| Có thể nhận nguyên trạng? | **KHÔNG** — 4 P0 (ID trùng, ID rule bịa, cache key xung đột schema, rủi ro parallel builder) |
| Cách nhận | **Absorb vào T165** (resolver/compiler/cache) + **T166** (canonical safety) → task trung giao **T168** (file này) |
| Số liệu nhận thêm | Deterministic test mới (A–I) · benchmark `prompt_tokens` · observability 11 field · validator audit · pilot ≤5 |

## A1. Số đo / schema THẬT (không bịa)

| Hạng mục | Sự thật | Nguồn |
|----------|---------|-------|
| `translation_rules` cols | `id, rule_code, rule_type, description, rule_text, is_active, priority, created_by, created_at, updated_at, status, suggested_by` | `PRAGMA table_info` |
| `rule_type` | chỉ **4 giá trị**: terminology 86 · style 8 · forbidden 2 · grammar 1 | `GROUP BY rule_type` |
| lifecycle thật | **`pending`** (AI suggestion — `_save_suggested_rules` app.py:16804, 17164) → **`active`+`is_active=1`** (approve app.py:17520) → **`dismissed`**; hiện 96 active + 1 dismissed, 0 pending | code + DB |
| `translation_glossary` | `id, term_zh, term_vi, source_label, is_locked, created_at` · 79 locked · **14 term 1-char** | PRAGMA + count |
| `translation_cache` | `source_hash, source_type, entity_id, source_text, translated_text, model_id, rules_version, status, report_count, approved_by…` · **`UNIQUE(source_hash, source_type)`** · 1.761 row (auto 1.752 · **edited 6** · draft 2 · invalidated 1) · **39 chỗ `FROM translation_cache`** | PRAGMA + count + grep |
| Hash hiện tại | `_t73_source_hash` = `sha256(text)[:24]` (16272) · `_t73_rules_version` = `sha256(join rule_text)[:16]` (16266) — glossary/exemplar KHÔNG tham gia | app.py |
| Glossary tables có thật | `glossary_term` (`term, language, definition, full_text…`) · `glossary_vi` (`term, term_vi, match_type, vi_confidence…`) · `translation_glossary` · `term_glossaries` | sqlite_master |
| Entity/term resolver đã có | **`_glossary_resolver`** app.py:16330 — n-gram 2–5 char, 14 bảng authority ưu tiên P1 `translation_glossary` locked → … trả `db_verified`/`db_ambiguous` | app.py |
| T95 / T94 | `scripts/cbeta_translate_worker.py` (26.586 B) · `translation_jobs`/`translation_job_items` có thật (`provider, model_name, attempt_count`) · validator thật = `validate_unit(zh,vi)` **dòng 188** + JSON extract **dòng 168** · T94 `manual_verified` admin/app.py:18193 | file + schema |
| Tests hiện có | `tests/` chỉ 4 file: `test_b25_authority_contract` · `test_license_firewall` · `test_real_data_license` · `test_t158_consensus` → **KHÔNG có test T123/T95/cache** | `ls tests/` |
| Prompt đo được | đầy đủ ≈ **14.874 chars ≈ 4.000–5.000 token** (rule_block 12.287 + glossary 1.373 + exemplar 606) · static 11 rule = **2.700 chars** · static+XML ≈ 3.400 chars ≈ **750–950 token** · không có tokenizer lib | đo 2026-09-25 |
| Groq | `_t73_call_gemini` (16482): **bỏ `data['usage']`** (16510-16513) · 0 retry/backoff · `role='user'` đơn · model `qwen/qwen3.8-27b` · log 0 byte → **429 chưa từng xảy ra** | app.py + log |

## A2. Directive nói ĐÚNG (giữ)

| § | Khớp repo |
|---|-----------|
| §1/§6 không builder/rule-system thứ 2 | `_t73_style_lock` 16291 + `_t73_build_style_prompt` 16444 là SSOT · `t50 build_prompt` mirror |
| §4 bắt buộc `match_terms`, cấm regex-scan nội dung rule | = T165 §14.2 #10 (regex `{1,8}` vs term ≥2 chars) |
| §20 thêm 500–1000 rule không sửa code | = mục tiêu T165 `_select_rules` |
| §10/§11 canonical safety, unknown→REVIEW | = **T166** (layer trên T165) |
| §13 semantic invalidation (rule liên quan đổi → MISS, rule lạ → HIT) | = Test Case 2 / T165 D8 |
| §7 XML là organizational, không tự đảm bảo compliance | = quyết Admin: XML = Phase 8 T165 |
| §16 không test nào được weaken để PASS | chuẩn repo (pipeline PASS thật) |
| §22 thứ tự phase + §23 pilot ≤5 + §24 `git revert` (cấm reset --hard) | chuẩn repo |

## A3. P0 — sai, sửa trước khi nhận

| # | Directive nói | Thực tế (bằng chứng) | Sửa thành |
|---|---------------|------------------------|-----------|
| **P0-1** | `tasks/T158-<canonical-name>.md` · helper `_t158_*` · "không tạo T158 trùng" | **T158 đã dùng ×2**: `tasks/T158-glossary-resolver-pre-translation-lookup.md` + `tasks/T158-lineage-consensus.md` + `tests/test_t158_consensus.py` → lệnh này **tự mâu thuẫn** | Task **T168**, file `docs/Mimo-Flash/T168-…-PLAN.md` (quy ước đánh số Admin 2026-09-25); helper = module **`style_constitution.py`** (T165 §5) — không `_t158_*`, không `_t168_build_prompt` |
| **P0-2** | §11 `RULE-011…RULE-015` phải được enforce | `SELECT count(*) … WHERE rule_code LIKE 'RULE-%'` = **0 row**; T165 SPEC §74 đã ghi "ID bịa, 0 match" | Ánh xạ sang cơ chế thật: suggestion = `status='pending'` · approve = `active` · unknown/entity = `_glossary_resolver` unresolved + **T166 post-assert** · **không** tạo code `RULE-0xx` |
| **P0-3** | §8 cache key = `TEXT+STATIC+MATCHED+CONTEXT` (thay key tra cứu) | `translation_cache` có **`UNIQUE(source_hash, source_type)`** + **39 reader** theo `source_hash`/`rules_version` → đổi ý nghĩa `source_hash` = phá mọi reader + UNIQUE | Composite key = cột additive **`constitution_hash`** (đã là T165 §4) = hash **phần thật đã inject**, tính **sau** `finalize_lock`; `static/matched/context hash` chỉ **log/observability** (hoặc cột additive), KHÔNG thay key tra; migration dùng `scripts/t165_rules_engine_migrate.py` (không script thứ 2) |
| **P0-4** | Task mới `_t158_resolve_translation_rules()` + `_t158_compile_translation_context()` | Vi phạm chính §1 của nó nếu tách rời T165 (đang có SPEC + absorb plan T167) → ra builder/registry thứ 2 | **Absorb**: resolver = `_select_rules` always∪terms (T165 §5) **⊕ compose** `_glossary_resolver` sẵn có (16330) · compiler = `build_style_prompt` mở rộng + `finalize_lock` · không nhân bản `known_pending`/GLOSSARY LOCK |

## A4. P1 — lệch, ảnh hưởng nghiệm thu

| # | Vấn đề | Bằng chứng | Sửa |
|---|--------|------------|-----|
| 1 | Lifecycle tên bịa: `DRAFT/APPROVED/ACTIVE`, `CANDIDATE/PENDING_REVIEW` | code thật `pending`/`active`/`dismissed` + cột `is_active` | **REUSE tên thật** (§20 chính directive cũng cho phép) |
| 2 | Taxonomy `persona/output format/no-omission` như thể là `rule_type` | `rule_type` chỉ 4 giá trị; `PERSONA_BAN_DICH`, `OUTPUT_FORMAT`, `NO_ADDITION` là **rule_code** trong style/forbidden/grammar | static = `rule_type IN (style,forbidden,grammar)` → **11 rule / 2.700 chars**; dynamic term = terminology (85 active) theo `match_terms`; không thêm cột `rule_type` |
| 3 | DYNAMIC_ENTITY lấy từ `translation_rules` | thật = `_glossary_resolver` (14 bảng P1–P14) + `name_vi_map`/authority; canonical do **T166** | compose, **không reimplement**; entity nào không có verified vi → REVIEW |
| 4 | §16 "T123 tests / T95 tests / cache tests PASS" | `tests/` chỉ 4 file, **không có 3 nhóm này** | đổi thành **"viết mới test"** (pytest đã cài 2026-09-25 do env gap) |
| 5 | §12 target `<350 input tokens` | đo: static+XML ≈ **750–950**; prompt đầy đủ ≈ 4–5k; `_t73_call_gemini` **bỏ `usage`** (16510) | log `usage.prompt_tokens` trước (T165 D3a) → 350 chỉ là **target tương đối**, không hard-gate |
| 6 | §9 test E/F (context đổi → MISS) | `style_lock` tính hash **trước** khi append resolver (app.py:17070–17090) | hash **sau** `finalize_lock` (T165 §14.2 #5a) |
| 7 | §9 test C bỏ sót | 6 row `status='edited'` lookup không được REPLACE (T165 #3) | test phải phủ nhánh `edited` → trả row + `rules_outdated` |
| 8 | `match_terms` 1-char | 14 term 1-char trong glossary locked + regex `{1,8}` (T165 #10) | lọc **≥2 chars**; rỗng → `match_scope='always'`; in stats |

## A5. P2 (giữ, không cần sửa)

XML chỉ organizational (Phase 8) · pilot ≤5 + không gọi Groq trước khi deterministic PASS · `validate_unit` (worker:188) là validator sẵn — **audit mở rộng, không viết mới** · frontend chỉ chạy `npm test/e2e` khi đụng `admin/translation_rules.html` · §25 "update SSOT theo convention" = quy ước Mimo-Flash đánh số.

## A6. Bảng ánh xạ §directive → chủ sở hữu

| Directive § | Chủ sở hữu | Việc cụ thể |
|-------------|-----------|-------------|
| §3 taxonomy · §4 match_terms · §5 resolver · §6 static · §19 perf · §20 admin lifecycle | **T165** | `_select_rules` + `match_scope/match_terms` UI + migration `t165_rules_engine_migrate.py` |
| §7 XML boundary | **T165 Phase 8** | optional, sau Admin QA |
| §8 key · §9 regression A–I · §12 benchmark · §13 second cache test · §18 observability | **T165** (§16 mới) + **T168 plan phase 4/6** | `constitution_hash` additive + test mới |
| §10 canonical · §11 unknown→REVIEW · §15 GOLD policy | **T166** (§21 mới) | post-assert + write-deny, P-PARTIAL |
| §14 validator · §17 5 case data thật · §23 pilot ≤5 | **T168 phase 0/5/6/7** | audit `validate_unit` + test mới + pilot |
| §1/§2/§6 (cấm trùng lặp) · §22 thứ tự · §24 revert · §25 deliverable | **T168** (file này) | gate + revert path |

**Out of scope:** đổi `source_hash` · DROP/ALTER bảng nền · tạo builder/rule-system thứ 2 ·
auto-promote GOLD/ACTIVE · sửa API T95/T123 · pilot >5 passage · hard-gate 350 token.

---

# PART B — PLAN (chưa chạy — chờ Admin duyệt từng phase)

**Bước 0 (đã xong):** plan ghi file này + các file liên kết (§C).

## B0. Checklist điều hành (Admin tick theo gate)

- [x] Review directive `[T158-DEBUG-001]` ↔ repo/DB thật (4 P0 + 8 P1) — PART A
- [x] Ghi plan 1 file + T165 §16 + T166 §21 + tasktodo + ADMIN item 19 + session + ROLLBACK + dashboard regen
- [x] **G1** Admin "Đồng ý build" (2026-09-25) → Phase 0 audit read-only → `docs/sessions/2026-09-25_t165-build-phase0-1-2.md` (§1–§5)
- [x] Phase 1 Rule Resolver (`style_constitution.select_rules` ⊕ `_glossary_resolver` · match_terms ≥2 chars) — **build 2026-09-25, absorbed vào T165 Phase 1–2**
- [x] Phase 4 cache `constitution_hash` additive — schema đã `--apply` (3 cột NULL, KHÔNG đụng `source_hash`; lookup dual-key chờ T165 Phase 3)
- [x] Phase 2 tích hợp builder T123 (15 call site truyền `source_text` — T165 Phase 3b) — **app.py 9/9 + admin 7/8 (T126 excluded) + t50 ✅** (session `2026-09-25_t165-build-phase3-4.md` §1–§7)
- [x] Phase 3 Context Compiler + `finalize_lock` (hash sau merge) — **code ✅ (`finalize_lock` + `_t165_finalize` app/admin/t50) · e2e test nằm trong G3 Phase 6**
- [ ] Phase 5 validator audit (`validate_unit` worker:188) mở rộng
- [ ] **G3** Phase 6 tests mới: regression A–I · second cache test · 5 case data thật · benchmark token → PASS 100%
- [x] **G2** `py_compile` + `npm run pipeline` PASS (2026-09-25 — ALL OK)
- [ ] **Phase 7** pilot Groq ≤5 passage (chỉ sau G3) — ghi usage/latency/cache/validator
- [ ] Phase 8 report `T168 RESULT` → Admin confirm → `taskdone.md`

## Phase 0 — READ-ONLY AUDIT (chưa chạy — cần Admin "OK Phase 0")

- Output: `docs/sessions/2026-09-25_t168_phase0_audit.md` (14 mục theo §2 directive,
  ánh xạ sang số liệu §A1 — không re-bịa).
- Dừng & báo blocker nếu phát hiện: rule engine trùng · builder trùng · ngữ nghĩa
  active-rule mơ hồ · cache không an toàn · bypass canonical · migration phá.
- **Không sửa code trong phase này.**

## Phase 1 — Rule Resolver (compose, không viết mới)

- `_select_rules(source_text)` = `always` ∪ `matched(≥2 chars)` (T165 §5).
- Compose `_glossary_resolver` (16330) cho DYNAMIC_TERM/ENTITY → `db_verified` inject,
  `unresolved` → REVIEW.
- Taxonomy dán nhãn theo `rule_type` thật (§A4-2), không thêm cột mới.
- Test: fixture 「大師至少林寺，面壁九年。」 → match theo rule thật trong DB, **không hard-code**.

## Phase 2 — Tích hợp vào builder T123

- Mọi luồng đi qua `_t73_style_lock` + `_t73_build_style_prompt` (+ mirror `admin`, `t50`).
- **Cấm** `_t158_build_prompt` / `_t168_build_prompt`.
- Phase 3b (T165 §14.2 #7): enumerate 15 call site truyền `source_text`.

## Phase 3 — Context Compiler

- `finalize_lock(lock)` = merge resolver **rồi mới** tính hash (sửa P0-3/#6).
- Section theo §7 directive: `<translation_constitution> <dynamic_glossary>
  <canonical_context> <source_text> <output_contract>` — XML = Phase 8 T165.

## Phase 4 — Cache key đúng

- Thêm additive `constitution_hash` (không đụng `source_hash`), lookup đủ
  `source_type` + `status!='invalidated'` + ưu tiên `edited` (T165 #2/#3).
- **Không** câu `DELETE … WHERE selected_rule_codes IS NULL` (T165 #4).
- Hash static/matched/context → **log observability**.

## Phase 5 — Validator (audit mở rộng)

- Audit `validate_unit` (worker:188) + JSON extract (168) + luồng app-side;
  thêm check thiếu: canonical in-lock assert (T166), provenance, rule version.
- Không thay validator cũ.

## Phase 6 — Test (VIẾT MỚI — không có sẵn)

- Regression cache **A–I** (§9) · second cache test (§13) · 5 case data thật (§17:
  term · person · place · unknown · không match) · canonical + unknown-term (T166).
- Benchmark ghi `old_prompt_tokens / new_prompt_tokens / reduction` (dùng `usage` thật).
- `py_compile` · `npm run pipeline` PASS.

## Phase 7 — Groq pilot (CHỈ sau khi Phase 1–6 PASS)

- Tối đa **5 passage** thật (glossary term · person · place · thường · unknown).
- Ghi: passage ID · model · matched codes · `usage.prompt_tokens` · latency ·
  cache status · validator · review status. **Không auto-GOLD.**

## Phase 8 — Report

- Bảng kết quả theo §26 directive, đổi nhãn `T158 RESULT` → **`T168 RESULT`**.

## Gates

| Gate | Điều kiện |
|------|-----------|
| G1 | Admin nói "OK Phase 0" → chạy audit read-only |
| G2 | Phase 0 không blocker → build Phase 1–4 |
| G3 | deterministic tests (Phase 6) **PASS 100%** → mới được pilot |
| G4 | Pilot ≤5 → report → Admin xác nhận → `taskdone.md` |

## Revert

- Code/docs: `git revert --no-edit <sha_T168>` (cấm `cp *.bak`, cấm `reset --hard`).
- DB (nếu đã chạy migration T165): `python scripts/t165_rules_engine_migrate.py --revert`.
- Backup DB trước mọi migration: `data/backups/lineage_t168_<ts>.db`.

## C. Các file liên kết (đã ghi cùng session 2026-09-25)

| File | Vai trò |
|------|---------|
| `docs/Mimo-Flash/T165-rules-constrained-translation-engine-SPEC.md` §14 review · §15 absorb directive v2 · **§16 absorb T168** | SSOT engine |
| `docs/Mimo-Flash/T166-canonical-identity-guard-SPEC.md` §20 review · **§21 absorb T168 §10/§11** | SSOT identity |
| `docs/Mimo-Flash/T167-dynamic-filter-absorb-directive-v2.md` · `T167-…-REVIEW.md` | absorb directive v2 (tiền đề) |
| `docs/tasktodo.md` entry T168 · `docs/ADMIN_REVIEW_DASHBOARD.md` item #19 | trạng thái Admin |
| `docs/sessions/2026-09-25_t168-rule-resolver-review.md` · `docs/ROLLBACK.md` | session + revert |
