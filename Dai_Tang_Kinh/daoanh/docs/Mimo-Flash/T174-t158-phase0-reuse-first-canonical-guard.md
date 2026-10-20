---
id: T174
title: "T158-PHASE0-004 (đổi nhãn T174) — Reuse-First Translation + Canonical Identity Hard Guard: Phase 0 Audit"
module: Translation / Canonical Identity
priority: high
status: ready-for-dev
owner: claudecode
depends_on: [T165, T166, T168]
created: 2026-09-25
updated: 2026-09-25
designed_by: mimo-flash
handoff_to: Claude Code Agent (mode ANALYZE_ONLY — Phase 0, 0 code/0 DB)
plan_approved_at: "2026-09-25 (Admin chốt ID = T174 + Đồng ý build docs)"
done_when: |
  Agent trả Phase 0 report đúng mẫu §18 (≤ hoặc đúng khối báo cáo),
  KHÔNG sửa code/DB/schema/cache/UI; xác nhận overlap với T165/T166/T168;
  Admin duyệt → mới nhận lệnh APPROVED FIX cho phase code.
---

# T174 — Phase 0 Audit: Reuse-First Translation + Canonical Identity Hard Guard

> **Gốc:** directive `T158-PHASE0-004` — Admin chốt **đổi nhãn T174** (T158 đã dùng ×2: glossary-resolver + lineage-consensus DONE; directive `[T158-DEBUG-001]`→T168, `[T158-CRITICAL-SAFETY-003]`→T166).
> **Mode:** PHASE 0 ONLY — audit thật, **0 code, 0 migration, 0 Groq quota**. Stop sau report, chờ `APPROVED FIX`.
> **Reuse nguyên tắc:** REUSE FIRST · LLM SECOND · VERIFY AGAIN.

## 1. Review directive → 4 P0 + 5 P1 (đã verify source + DB)

### P0-1 — Thiếu T165/T166/T168 trong reuse list → nguy cơ trùng lặp (prompt tự hỏi DUPLICATE SYSTEM RISK)
Kiến trúc §14/§15 (CanonicalLock, post-LLM assertion, reuse builder, cache version) **đã SPEC + build một phần**: T166 SPEC 586 dòng (CanonicalLock, matrix A–J) · T165 `style_constitution.py` **đã build** `style_lock(214)/build_style_prompt(288)/finalize_lock(145)` (24 test PASS, G2 PASS, code còn treo) · T168 resolver/context + `constitution_hash`, **Phase 0 audit đã có** `docs/sessions/2026-09-25_t165-build-phase0-1-2.md`.
→ Absorb: reuse list += 3 task · report template += `EXISTING T165/T166/T168 WORK`.

### P0-2 — Ví dụ `安廩` mâu thuẫn chốt đã duyệt (T166 rev.2)
Thực tế (verify): `people` **A005248 安廩 → `An Lẫm`** nhưng name_vi_map = **auto 0.7, final=NULL**; `vn_person_authority` **0 row**; `lexicon` **0 row**; `glossary_vi` **0 row** → **KHÔNG verified authority**. T166 chốt: `安廩` = **CANDIDATE, không HARD_FAIL**; invent = `CANONICAL_INVENTION` warning → draft only; fixture LOCK = **A009460 丹霞天然 → Đơn Hà Thiên Nhiên** (vnpa verified).
→ Absorb §2/§15: **HARD_FAIL chỉ khi vnpa verified / `name_vi_final` admin**; auto <0.9 = CANDIDATE → WARN → draft. CASE-1 example = A009460 · `安廩` = CASE-4 CANDIDATE.

### P0-3 — Đụng ID T158 (lần dùng thứ 4/5) → Admin chốt **T174**

### P0-4 — "AI Dịch" ≠ 1 entry, thực tế **4 route**:
| Route | app.py | source_type |
|---|---|---|
| `/daoanh/api/person/<id>/translate` | 16792 | person_bio |
| `/daoanh/api/person/<id>/dila_translate` | 17145 | (dila bio) |
| place note translate | 17958 | place_note |
| relation evidence translate | 6343 | relation_evidence |

### P1 (5)
1. **§4 "22 từ điển" = 2 lớp:** code `hanviet_normalization.load_glossary()` (StarDict `data/dictionaries/tudien`, `data/dict/*.mdx`) ≠ bảng DB (`glossary_vi` 248.095 · `lexicon` 166.278 · `monk_dict` · `term_glossaries` · `glossary_term` · `translation_glossary`). **`_glossary_resolver` = FUNCTION (app.py ~16330), không phải bảng** — cấm đoán tên bảng.
2. **§10 Place:** `places_dila` **không có cột `name_vi`** (name/name_zh/name_en/name_san/name_jpn/…) → tiếng Việt = **`namevi_map_places`** (`少林寺 → Thiếu Lâm Tự`).
3. **§5 TTL 3 nơi:** `data/ttl` = **1.046 file** + archive (canonical) · `ontology/monks/TTL` 7 · `ontology/ttl` 1 · index link `vn_person_authority.ttl_filename`.
4. **T95/T94 nằm `tasks/backup/`** (T95-cbeta-translation-pipeline.md, T94-cbeta-alignment-schema.md) — hint để agent không báo NOT FOUND oan.
5. **"verified" phải định nghĩa:** = `vn_person_authority.status` + `name_vi_final` admin-approved. `people.name_vi` phần lớn auto/legacy (T171/T172) → không được coi là verified (tránh HARD_FAIL oan, e.g. `Thích An Lẫm` = PASS theo T166 §6.1).

## 2. Verified facts (Phase 0 pre-audit, read-only)

| Hạng mục | Thật |
|---|---|
| Builder | `_t73_style_lock`(2660)/`_t73_build_style_prompt`(16633) → delegate `style_constitution.py` |
| Jobs/cache/rules | `translation_jobs` 3 · `translation_job_items` 12 · `translation_cache` 1.761 (`UNIQUE(source_hash, source_type)`, key `sha256(text)[:24]`, có `rules_version`) · `translation_rules` **97** (active 96/dismissed 1) |
| TM (translation memory) | `translation_segments` · `passage_translation_alignment` · `translation_exemplar` · `translation_glossary` |
| Glossary | `glossary_vi` 248.095 (`term/term_vi/match_type/vi_confidence/source_glossary_id`) |
| DILA person | `people` (48.673) · authority `vn_person_authority` (cột: `ttl_filename, name_vi, name_zh, dila_id, status…`) |
| DILA place | `places_dila` 59.167 (KHÔNG name_vi) + `namevi_map_places` |
| TTL | `data/ttl` 1.046 |
| `安廩` | SQL = A005248 `An Lẫm` (auto 0.7) · vnpa/lexicon/glossary = **0 row** · status dự kiến **PARTIAL/CANDIDATE** |

## 3. Prompt Phase 0 ĐÃ CHỐT — paste cho Claude Code

> So với directive gốc: **title = T174**; §1 += T165/T166/T168; §2/§15 authority hierarchy + example A009460; §3 report template += 2 mục mới; §4 2 lớp dict + `_glossary_resolver`=function; §5 TTL canonical + backup hint; §10 namevi_map_places; §9 kỳ vọng PARTIAL. Các section khác (§6,7,8,11,12,13,14,16,17,18, rules ZERO-TOLERANCE, DO NOT BUILD) **giữ nguyên nguyên văn**.

```text
============================================================
T174 — PHASE 0 (gốc: T158-PHASE0-004)
REUSE-FIRST TRANSLATION + CANONICAL IDENTITY HARD GUARD
============================================================

ROLE
You are the senior implementation/debugging agent for PTDA.
The operator is NO-CODING.
You MUST inspect the real repository and real database/runtime.
Do not ask the operator to guess file paths, table names, schema,
or existing functions when the repository can discover them.
THIS SESSION IS PHASE 0 ONLY. DO NOT MODIFY PRODUCTION CODE YET.

============================================================
1. CURRENT ARCHITECTURAL DECISION
============================================================
T174 (gốc T158) is NOT a new translation engine. T158/T174 MUST EXTEND:
- T95 existing CBETA translation pipeline (task doc: tasks/backup/T95-cbeta-translation-pipeline.md)
- T123 existing Style Constitution / unified prompt builder
- T94 manual verification workflow (tasks/backup/T94-cbeta-alignment-schema.md)
- T110 glossary_vi
- existing DILA canonical data · translation cache · translation jobs/items
- existing local Buddhist dictionaries · local TTL/XML monk biographies
*** ADD (đã chốt — audit overlap, KHÔNG thiết kế lại) ***
- T165 style_constitution.py (style_lock / build_style_prompt / finalize_lock — ĐÃ build)
- T166 Canonical Identity Hard Guard SPEC (CanonicalLock, matrix A–J, post-LLM assert)
- T168 Rule Resolver + Context Compiler (constitution_hash trong cache)
DO NOT rebuild any of these.

The new architecture is:
CBETA SOURCE → ENTITY/TERM DETECTION → LOCAL KNOWLEDGE RESOLVER
(DILA person/place · SQL canonical · Buddhist dictionaries · glossary_vi
 · translation memory · TTL/XML biographies · verified evidence)
→ CANONICAL LOCK / REVIEW GATE → T123 EXISTING STYLE BUILDER
→ QWEN/GROQ ONLY WHERE NEEDED → POST-LLM CANONICAL ASSERTION
→ DETERMINISTIC VALIDATOR → HUMAN REVIEW → GOLD
Core principle: REUSE FIRST · LLM SECOND · VERIFY AGAIN.

============================================================
2. ZERO-TOLERANCE CANONICAL SAFETY
============================================================
Canonical person names, Dharma names, places, temples, dynasties, eras
and established Buddhist terminology MUST NOT be invented by Qwen when
authoritative local evidence exists.

*** AUTHORITY HIERARCHY (chốt — theo T166) ***
tier A  LOCK/HARD_FAIL : vn_person_authority.status=verified  HOẶC
                         name_vi_map.name_vi_final (admin approved)
tier B  CANDIDATE/WARN : name_vi_auto / auto_transliterate <0.9
tier C  UNKNOWN/REVIEW : không có evidence
*** Không bao giờ coi people.name_vi (auto/legacy) là tier A. ***

Mandatory regression (đã chốt lại theo T166):
SOURCE: 安廩
QWEN PREVIOUSLY PRODUCED: Thích An Nạp
LOCAL REALITY: A005248 An Lẫm = tier B (auto 0.7, vnpa/lexicon/glossary = 0 row)
→ 安廩 = CASE-4 CANDIDATE: invent mới = CANONICAL_INVENTION cảnh báo →
  draft only, KHÔNG hard-fail identity, KHÔNG auto canonical.
CASE-1 LOCK example DÙNG: A009460 丹霞天然 → Đơn Hà Thiên Nhiên (vnpa verified).

If tier A exists: LOCK IT. If evidence conflicts: REVIEW.
If no evidence: UNKNOWN / REVIEW. Never: UNKNOWN → QWEN INVENTION → CANONICAL.

============================================================
3. PHASE 0 — DISCOVER REAL DATA (A→AH như directive gốc)
============================================================
Inspect the real project and report exact A…AH (giữ nguyên danh sách
directive gốc), TRỪ các mục đã chốt sửa sau:
- B/C "active translation code + T95": kể cả route person translate
  (app.py:16792), dila_translate (17145), place note (17958),
  relation evidence (6343) — đủ 4 đường.
- D/E: task docs T95/T94 nằm tasks/backup/ (đừng báo NOT FOUND).
- F…K: bảng thật đã verify: translation_jobs, translation_job_items,
  translation_cache, glossary_vi, translation_rules; bảng TM:
  translation_segments, passage_translation_alignment,
  translation_exemplar, translation_glossary.
- K/M/N: dictionary = 2 LỚP: (1) DB: glossary_vi, lexicon, monk_dict,
  term_glossaries, glossary_term, translation_glossary;
  (2) code: hanviet_normalization.load_glossary() (data/dictionaries/tudien,
  data/dict/*.mdx). _glossary_resolver = FUNCTION (app.py ~16330), KHÔNG phải bảng.
- R/S: people + vn_person_authority (cột ttl_filename, name_vi, name_zh,
  dila_id, status); places_dila KHÔNG có name_vi → tiếng Việt =
  namevi_map_places.
- U…Z: TTL canonical = data/ttl (1.046 file + archive); ontology/monks/TTL (7),
  ontology/ttl (1); index = vn_person_authority.ttl_filename; báo format
  TTL thật, có parse/index/cache không.
- T/AF/AG/AH: canonical lookup + _t73_style_lock/_t73_build_style_prompt
  → style_constitution.py; cache key = source_hash sha256[:24] +
  source_type, UNIQUE(source_hash, source_type), rules_version,
  constitution_hash (T165/T168).

============================================================
4. DO NOT ASSUME 22 DICTIONARIES
Verify both layers (DB tables + code-loaded sources). Report
dictionary_count / dictionary_entry_count / tables / source names / indexes.
Do not create/import/modify/duplicate any dictionary data.

============================================================
5. TTL/XML IS AUTHORITY EVIDENCE
Find the canonical local biography repo (data/ttl), determine
TTL/XML/TEI/mixed + indexed/parsed/cached; how identity connects to
DILA ID (vn_person_authority.ttl_filename), Chinese/Vietnamese names,
aliases, places. Do not create a new parser if one exists.
Do not parse all files per request — future resolver uses index/cache.

============================================================
6. FIND THE REAL "AI DỊCH" ENTRY POINT (BẢNG, không phải 1 route)
UI → API → backend → translation function → prompt builder →
Groq/Qwen → cache → validator → DB. Report table đủ 4 route:
person translate (16792) · dila_translate (17145) · place note (17958)
· relation evidence (6343): file, function, route, table, cache behavior.
Do not change anything.

============================================================
7/8/9/10/11/12 (giữ nguyên directive gốc)
============================================================
7. Prompt builder: _t73_style_lock/_t73_build_style_prompt (delegate
   style_constitution.py) — T174 MUST EXTEND, không tạo builder cạnh tranh.
8. Cache key audit (đừng đổi).
9. Person resolution thật cho 安廩 — KHÔNG gọi Qwen; kỳ vọng report =
   PARTIAL (SQL A005248 An Lẫm tier B; vnpa/lexicon/glossary 0 row).
10. Place test thật (VD 少林寺): name_zh, places_dila id, VI =
    namevi_map_places (Thiếu Lâm Tự), TTL evidence nếu có.
11. Term resolution thật từ dictionary (không bịa).
12. Translation memory: translation_segments / passage_alignment /
    translation_exemplar / translation_glossary / approved entries.

============================================================
13/14/15/16 (giữ nguyên directive gốc + chốt authority)
============================================================
13. Decision model CASE 1–5 (giữ nguyên), CASE 1 chỉ khi tier A.
14. CanonicalLock {source_form, normalized_form, entity_type, canonical_id,
   canonical_value, authority_source, evidence_refs, status
   ∈ LOCKED|CONFLICT|UNKNOWN_REVIEW} — ưu tiên mở rộng cấu trúc có sẵn
   trong T166/T165; KHÔNG tạo bảng/đối tượng trùng.
15. Post-LLM assertion (giữ nguyên), severity theo authority hierarchy §2
   (tier B → WARN/draft, không HARD_FAIL).
16. PRE-LLM LOCK + POST-LLM ASSERTION — cả hai, không thay bằng
   "validator fixes it".

============================================================
17. DO NOT BUILD YET (giữ nguyên nguyên văn directive gốc)
============================================================

============================================================
18. REQUIRED PHASE 0 REPORT (mẫu gốc + 2 mục mới)
============================================================
T158 PHASE 0 AUDIT → đổi tiêu đề: T174 PHASE 0 AUDIT
Thêm 2 mục vào cuối:
EXISTING T165/T166/T168 WORK:
  [files/functions đã có · phần Phase 0 này TRÙNG · phần DELTA còn thiếu]
AI DỊCH ENTRY TABLE:
  [4 route × file/function/route/table/cache]
Các mục còn lại (REPOSITORY…PHASE 0 STATUS) giữ nguyên directive gốc.
Constraints giữ nguyên: không sửa code/DB/schema/CSS trước APPROVED FIX;
report tối đa 80 dòng (trừ khối báo cáo mẫu); NOT FOUND thay vì đoán;
chỉ kết luận từ source + runtime thật.
STOP HERE. DO NOT BUILD.
```

## 4. Phases
1. **(session này)** Review directive → 4 P0 + 5 P1 → prompt chốt (docs-only) ✅.
2. Admin paste prompt §3 cho Claude Code → Phase 0 report → Admin duyệt.
3. `APPROVED FIX` → phase code (tách commit từng bước, pipip trước mỗi commit).
4. Report + ROLLBACK hash-fill.

## 5. Revert
Docs: `git revert --no-edit <sha_T174>`. Code phase (tương lai): từng commit riêng; schema change dự kiến: xem report (SP 0 chưa quyết — nhưng theo T166, `identity_status` additive đã thiết kế sẵn).

## 6. Files
- Task này: `docs/Mimo-Flash/T174-t158-phase0-reuse-first-canonical-guard.md`
- Session: `docs/sessions/2026-09-25_t174-phase0-audit-plan.md`
- Đọc trước khi chạy phase code: `T166-canonical-identity-guard-SPEC.md` · `T168-rule-resolver-context-compiler-PLAN.md` · `docs/sessions/2026-09-25_t165-build-phase0-1-2.md`
