---
id: T175
title: "T158-PHASE0C (đổi nhãn T175) — Canonical Buddhist Person Identity Resolution Audit: DILA Han → Local VI → Display Name"
module: Translation / Person Identity
priority: high
status: ready-for-dev
owner: claudecode
depends_on: [T174, T166, T171]
created: 2026-09-25
updated: 2026-09-25
designed_by: mimo-flash
handoff_to: Claude Code Agent (AUDIT ONLY — 0 code/0 DB/0 commit)
plan_approved_at: "2026-09-25 (Admin chốt: ID = T175 · report thêm OVERLAP WITH T174/T166/T171 + AMBIGUITY_RESULT)"
done_when: |
  Agent trả T175-PHASE0C AUDIT REPORT đúng mẫu (16 mục, gồm 2 mục mới
  Admin chốt) · 0 code/0 DB/0 commit · Admin duyệt → mới nhận APPROVED FIX.
---

# T175 — Phase 0C Audit: Canonical Person Identity Resolution (靈祐 → A001984 → Linh Hựu → Quy Sơn Linh Hựu)

> **Gốc:** directive `T158-PHASE0C` — Admin chốt **T175** (T158 đã dùng ×2 task + PHASE0-004→T174).
> **Mode:** AUDIT ONLY — cấm code/DB/table/migration/cache-purge/new resolver/commit. Stop chờ lệnh.
> **Mối quan hệ:** sub-audit **feed T174** (không trùng phần call-chain/dict/cache — ghi DELTA) · kế thừa authority hierarchy **T166** · minimal fix map vào **T171** alias layer.

## 1. Review directive → 4 P0 + 6 P1 (verify DB/source thật)

### P0-1 · TEST-01 `靈祐 → A001984` KHÔNG deterministic
`name_zh='靈祐'` = **5 người**: `A001984` (Quy Sơn Linh Hựu) · `A023322` (Hương Nghiêm Trí Nhàn) · **`A023362`/`A032868`/`A035586` (Linh Hữu, auto 0.7)**. Mâu thuẫn với chính §8 ("đừng giả định variant giống nhau") + §12 (ép kết quả đơn).
→ Absorb: TEST-01 = **candidate list 5 id → disambiguate bằng evidence/authority → >1 unsolved = `REVIEW_REQUIRED`**; identity key = `person_id`, không phải `name_zh`.

### P0-2 · Premise §0/§4/§5/§9 lệch DB thật
- `people[A001984].name_vi` **đã = `Quy Sơn Linh Hựu`** (B+C **đã collapse** trong 1 field — chính là thứ §10 yêu cầu audit).
- **`Linh Hựu` standalone = 0 row `people`** → §4 "show where Linh Hựu stored" sẽ NOT FOUND oan → sửa kỳ vọng theo dữ liệu thật.
- **`Linh Hữu` không chỉ là output AI**: là `name_vi` của **3 người khác cùng 靈祐** → TEST-04 **so theo `person_id`**, không so string.
- vnpa `alias_A001984` status = **`alias_vi_suffix`** (CHƯA tier `verified`).
→ Absorb kỳ vọng §4/§5/§9 theo DB thật.

### P0-3 · Đụng ID T158 lần nữa → Admin chốt **T175**

### P0-4 · Thiếu tham chiếu đã chốt → trùng lặp/design lại
Directive §2 không nhắc **T166** (CanonicalLock SPEC đã duyệt) · **T165/T168** (style_constitution + resolver ĐÃ build) · **T171** (alias layer = chỗ biểu diễn A/B/C: `primary_han_name`/`common_name`/`title`) · **T174** (Phase 0 audit đang chạy cùng call-chain/dict/cache) → "Canonical Buddhist Entity Resolver" mới sẽ trùng T166, vi phạm chính §2.
→ Absorb: REUSE list += 4 task · report += mục **`OVERLAP WITH T174/T166/T171`** (Admin chốt).

### P1 (6)
1. **§13 "T79 translation system" sai** — T79 = `person-birth-death-extraction` (tasks/backup) → đổi **T73/T95**.
2. **§1 "Google transliteration" = NOT FOUND**; `public/transliterate` (app.py:10861, gọi **hvdic.thivien.net**) chỉ 2 file admin place (`admin/places.html`, `placevn.html`) dùng cho **địa danh**. Person path thật = seed `people.name_vi` + namevimap priority `curated final > people.name_vi > auto_transliterate` (app.py:12953) + AI Dịch **4 route** (16792/17145/17958/6343).
3. **22 từ điển = 2 lớp** (DB: `glossary_vi` 248.095, `lexicon` 166.278, `monk_dict`, `term_glossaries`, `glossary_term`, `translation_glossary` + code StarDict `hanviet_normalization`); **`_glossary_resolver` = function** (~app.py:16330), không phải bảng.
4. **`name_vi_map.dila_id` không join được blind** — row `A021462` ghi "Quy Sơn Linh Hựu" nhưng `people A021462 = 鏡堂覺圓` (thuộc 322 lệch/51 dup đã biết) → dùng `people` + `vnpa` + `canonical_decision`.
5. **HITL còn rất nhỏ**: `canonical_decision` **2 row** + sample mojibake `Th? S?t H?i` → ghi "exists-but-tiny + data quality flag"; `entity_claims` 447.885 · `source_authority` 14.
6. **§12 tách cache-stale vs source-data-wrong** — "Quy Sơn Linh Hữu" sai có thể nằm ở `people.name_vi`/`name_vi_map` (nguồn), không chỉ `translation_cache` (`UNIQUE(source_hash, source_type)`, không tự invalidation).

## 2. Verified facts (pre-audit, read-only)

| Hạng mục | Thật |
|---|---|
| A001984 | `people` 靈祐 唐 Thiền Tông · name_vi = **Quy Sơn Linh Hựu** |
| 靈祐 | **5 id** (xem P0-1) |
| `Linh Hựu` | standalone `people` = **0** · `name_vi_map` LIKE = 15 (substring tên dài) |
| `Linh Hữu` | name_vi của A023362/A032868/A035586 (cùng 靈祐, auto) |
| vnpa A001984 | `alias_A001984` · ttl `TS-Quy-Son-Linh-Huu` · status `alias_vi_suffix` |
| canonical_decision | 2 row (cột: `canonical_name_vi/authority_rank/verification_status/evidence_citations`) — sample mojibake |
| entity_claims / source_authority | 447.885 / 14 |
| hvdic API | `public_transliterate` app.py:10861 → `hvdic.thivien.net` (place-only, 2 admin file) |
| Google translit | **NOT FOUND** |
| Machine filter | `_ok_hanviet_name()` app.py:16891 (4 chỗ inject) |

## 3. Prompt Phase 0C ĐÃ CHỐT — paste cho Claude Code

> So với directive gốc: **title = T175**; §0/§4/§5/§7/§9/§12 kỳ vọng theo DB thật (P0-1/P0-2) · §1 sửa path thật · §2 += T166/T165/T168/T171/T174 · §6 2 lớp dict · §13 T73/T95 · **§14 report += 2 mục `OVERLAP WITH T174/T166/T171` + `AMBIGUITY_RESULT` (Admin chốt)**. Các section còn lại (§3 call-chain format, §8 variants, §10 A/B/C, §11 RULE A–J, §13 forbidden, §15 final goal, STOP) **giữ nguyên nguyên văn**.

```text
===============================================================
[T175-PHASE0C]   (gốc: T158-PHASE0C — Admin chốt đổi nhãn T175)
CANONICAL BUDDHIST PERSON IDENTITY RESOLUTION AUDIT
DILA HAN NAME → LOCAL VIETNAMESE NAME → DISPLAY NAME
===============================================================

ROLE / AUDIT ONLY / DO NOT MODIFY (giữ nguyên directive gốc toàn bộ:
non-coding operator, inspect REAL repo+SQLite+pipeline, cấm code/DB/table/
migration/new resolver/commit).

===============================================================
0. BUSINESS PROBLEM — MUST UNDERSTAND EXACTLY
===============================================================
(giữ nguyên nguyên văn) + ABSORB THEO DB THẬT:
- people[A001984].name_vi HIỆN ĐÃ = "Quy Sơn Linh Hựu"
  → B (canonical VI) và C (display) ĐANG bị collapse trong 1 field.
  Đây là phát hiện trọng tâm §10, KHÔNG phải mặc định cần chứng minh.
- "Linh Hựu" standalone: NOT FOUND trong people (0 row).
  audit phải ghi rõ tìm thấy ở đâu (nếu có) hoặc NOT FOUND — không bịa.
- "Linh Hữu" (sai dấu) LÀ name_vi của 3 người khác CÙNG tên Hán 靈祐
  (A023362, A032868, A035586 — auto 0.7) → không được coi thuần túy
  là "AI sai chính tả" của A001984; mọi so sánh PHẢI theo person_id.
- name_zh "靈祐" = 5 person (A001984, A023322, A023362, A032868, A035586)
  → DILA ID là key; Han name KHÔNG unique.

===============================================================
1. CURRENT FAILURE
===============================================================
Sửa câu cho khớp thực tế (không viết như đã kết luận):
- "Google transliteration" = NOT FOUND trong repo → ghi NOT FOUND.
- Viện Hán Nôm: GET /daoanh/api/public/transliterate (app.py:10861)
  → https://hvdic.thivien.net — CHỈ được admin/places.html +
  admin/placevn.html dùng cho ĐỊA DANH, không phải person path.
- Person path thật (audit lại): seed people.name_vi + namevimap priority
  "curated final > DILA people.name_vi > auto_transliterate" (app.py:12953)
  + AI Dịch 4 route: person translate (16792) · dila_translate (17145)
  · place note (17958) · relation evidence (6343).
Giữ nguyên nguyên tắc: local approved = REUSE · external = FALLBACK ·
AI = CANDIDATE ONLY.

===============================================================
2. EXISTING PROJECT KNOWLEDGE THAT MUST BE REUSED
===============================================================
Giữ nguyên list gốc (translation_rules, translation_cache, people.name_vi,
DILA person data, dictionaries, canonical_decision/entity_claims,
glossary infra) + BẮT BUỘC thêm:
- T166 Canonical Identity Hard Guard SPEC (CanonicalLock, authority
  hierarchy A/B/C, matrix A–J) — đọc TRƯỚC khi thiết kế §11.
- T165/T168: style_constitution.py (style_lock/build_style_prompt/
  finalize_lock — ĐÃ build) · resolver + constitution_hash.
- T171 name layer: person_name_alias (primary_han_name / han_viet_reading /
  common_name / title / legacy_name_unverified) = chỗ biểu diễn A/B/C —
  minimal fix §11 PHẢI map vào đây, không bảng mới.
- T174 Phase 0 audit (report này là SUB-AUDIT feed T174 — phần
  call-chain/dict/cache chung: ghi DELTA, không viết lại).
VẪN CÒN ÁP DỤNG: verify tên thật trong code/DB · không tạo
person_resolver_v2 / canonical_name_resolver_new / cache mới / person-name
table mới khi chưa có owner approve.

===============================================================
3. PRIMARY AUDIT QUESTION — call-chain THẬT
===============================================================
Giữ nguyên mẫu call-chain (UI → route → function → resolver → SQL →
API → LLM → cache → response) với tên file/function/route/SQL THẬT.
Bắt buộc liệt kê đủ 4 route AI Dịch (xem §1) — dạng BẢNG, không phải 1 route.

===============================================================
4. AUDIT DILA IDENTITY RESOLUTION
===============================================================
Test theo DB THẬT, không giả định đơn nhất:
    name_zh "靈祐" → CANDIDATE SET = {A001984, A023322, A023362,
    A032868, A035586} → disambiguate bằng evidence/authority
    (people.dynasty/sect, vnpa, canonical_decision, entity_claims,
    TTL) → nếu >1 ứng viên không phân giải được:
    status = REVIEW_REQUIRED.
Report: source table (people) · canonical ID column (id, 7 ký tự) ·
Han column (name_zh) · VI column (name_vi — ĐANG collapse display) ·
aliases (vnpa alias_*, name_vi_map, person_name_alias nếu đã build) ·
lineage/place (people.sect/dynasty, lineage_edge_consensus) ·
evidence/provenance (entity_claims, source_authority) ·
canonical decision state (canonical_decision — 2 row, ghi rõ exists-but-tiny).
KHÔNG join name_vi_map.dila_id blind (đã biết 322 row lệch / 51 dup,
VD A021462 ghi "Quy Sơn Linh Hựu" nhưng people = 鏡堂覺圓).

===============================================================
5. AUDIT LOCAL VIETNAMESE NAME REUSE
===============================================================
Giữ nguyên list 9 lớp ưu tiên (concept) NHƯNG: xác định lớp nào THẬT SỰ
tồn tại + authority/status thực (vd tier A = vnpa.status=verified hoặc
name_vi_final admin — vnpa A001984 hiện CHỈ alias_vi_suffix, KHÔNG phải
verified). Khôngblind-apply list.

===============================================================
6. AUDIT 22 BUDDHIST DICTIONARIES
===============================================================
Verify 2 LỚP: (1) DB: glossary_vi 248.095 · lexicon 166.278 · monk_dict ·
term_glossaries · glossary_term · translation_glossary;
(2) code: hanviet_normalization.load_glossary() (data/dictionaries/tudien,
data/dict/*.mdx). _glossary_resolver = FUNCTION (~app.py:16330),
KHÔNG phải bảng. Report storage/lookup/index/result type/authority.
KHÔNG rebuild/duplicate dict.

===============================================================
7. CRITICAL IDENTITY TEST — theo DB thật
===============================================================
    靈祐 → (5 candidates, xem §4) → A001984 (nếu evidence phân giải)
    → local VI: people.name_vi = "Quy Sơn Linh Hựu" (ĐÃ collapse)
    → "Linh Hựu" standalone: NOT FOUND (ghi rõ)
    → display form: "Quy Sơn Linh Hựu" (source: people.name_vi + vnpa
      alias_vi_suffix + entity_claims nếu có).
KHÔNG yêu cầu DILA chứa chuỗi hiển thị đúng từng chữ — test là
IDENTITY resolution (giữ nguyên tinh thần gốc).

===============================================================
8. SECONDARY SURFACE-FORM TESTS — giữ nguyên nguyên văn
===============================================================
(釋靈祐 / 潙山靈祐 / 潙山靈祐禪師 … → A001984 nếu có evidence;
không evidence → REVIEW_REQUIRED; không tạo person mới; không hỏi Qwen.)

===============================================================
9. NEGATIVE TEST — MUST BE HARD
===============================================================
Giữ nguyên, thêm 2 cảnh báo theo DB thật:
- "Linh Hữu" đã tồn tại cho 3 person KHÁC cùng 靈祐 → so sánh PHẢI
  theo person_id, cấm flag nhầm người thật (dùng người khác làm
  negative-fixture, không sửa data người đó — audit only).
- Expected: canonical_identity = A001984 · approved/local =
  people.name_vi "Quy Sơn Linh Hựu" (tier theo T166: name_vi legacy/auto
  → CANDIDATE/WARN nếu chưa admin-approved) · AI "Linh Hữu…" = rejected/
  overridden/reviewed. Không modify code/data.

===============================================================
10. Distinguish A/B/C — giữ nguyên nguyên văn
===============================================================
A = DILA ID A001984 · B = approved VI "Linh Hựu"(nếu có nguồn)/hoặc
name_vi hiện tại · C = display "Quy Sơn Linh Hựu".
Phát hiện được: B+C ĐANG gộp trong people.name_vi (report chính xác vị trí
vd app.py SELECT/UPDATE chạm cột) + đề xuất smallest additive fix (không
implement) — map vào T171 alias roles, không bảng mới.

===============================================================
11. HARD SAFETY RULES A–J — giữ nguyên nguyên văn
===============================================================

===============================================================
12. CACHE AUDIT
===============================================================
Giữ nguyên, bổ sung phân định 2 lớp:
(a) translation_cache: key = source_hash sha256(text)[:24] + source_type
    (UNIQUE), rules_version/constitution_hash — audit có tự invalidate
    không → dự kiến "không": kết quả cũ sống tiếp (VERIFY, đừng đổi cache);
(b) SOURCE DATA WRONG: tên sai nằm ngay people.name_vi/name_vi_map
    (không phải cache) → "sửa DB hôm nay, cache cũ còn trả sai không?"
    phải trả lời TỪNG lớp riêng. Không purge/invalidate gì trong audit.

===============================================================
13. DO NOT IMPLEMENT — giữ nguyên nguyên văn (cấm code/DB/migration/
cache purge/new table/new API/new resolver/commit).

===============================================================
14. REQUIRED REPORT FORMAT — mẫu GỐC 14 mục + 2 MỤC MỚI (Admin chốt)
===============================================================
# T175-PHASE0C AUDIT REPORT
## 1. VERDICT (PASS/PARTIAL/FAIL)
## 2. REAL TRANSLATION CALL CHAIN (bảng 4 AI Dịch routes)
## 3. DILA IDENTITY (candidate set 5 id + disambiguation evidence)
## 4. LOCAL VIETNAMESE NAME (kỳ vọng DB thật: "Linh Hựu" standalone
     NOT FOUND nếu đúng — hoặc trỏ đúng chỗ tìm thấy)
## 5. DISPLAY NAME ("Quy Sơn Linh Hựu": people.name_vi + vnpa
     alias_vi_suffix + evidence; ghi rõ tier CHƯA verified)
## 6. 22 DICTIONARIES (2 lớp)
## 7. CURRENT PRIORITY ORDER (actual, không desired)
## 8. CACHE BEHAVIOR (tách cache-stale vs source-data-wrong)
## 9. REAL TEST RESULTS (TEST-01..05; TEST-01 = candidate set +
     disambiguation; TEST-04 so theo person_id)
## 10. ROOT CAUSE
## 11. MINIMAL FIX DESIGN (map vào T171 alias + T166 CanonicalLock;
      files/functions/tables to consume/caches to preserve/tests — NO CODE)
## 12. REGRESSION TEST PLAN (giữ nguyên, sửa TEST-01 theo candidate set)
## 13. SCOPE / RISK (giữ nguyên; ĐỔI "T79 translation system" →
     T73/T95 — T79 = birth/death extraction, không phải translation)
## 14. STOP CONDITION
## 15. (MỚI — Admin chốt) OVERLAP WITH T174/T166/T171:
     [phần report này TRÙNG T174 Phase 0 · phần DELTA riêng PHASE0C ·
      phần đã có sẵn trong T166 CanonicalLock / T171 alias layer]
## 16. (MỚI — Admin chốt) AMBIGUITY_RESULT:
     [mỗi TEST: candidates list · status (resolved/REVIEW_REQUIRED/
      NOT FOUND) · evidence dùng để phân giải]

===============================================================
15. FINAL IMPORTANT CONSTRAINT — giữ nguyên nguyên văn
(Canonical identity first. Translation second.)
END T175-PHASE0C
STOP. Do not implement. Do not commit.
```

## 4. Phases
1. **(session này)** Review → 4 P0+6 P1 → prompt chốt (docs-only) ✅.
2. Admin paste prompt §3 cho Claude Code → `T175-PHASE0C AUDIT REPORT` (16 mục) → Admin duyệt.
3. `APPROVED FIX` → minimal fix (map T171/T166, tách commit từng bước, pipip trước mỗi commit).

## 5. Revert
Docs: `git revert --no-edit <sha_T175>`. Audit không đụng DB/cache/code.

## 6. Files
- Task này: `docs/Mimo-Flash/T175-phase0c-canonical-person-identity-audit.md`
- Session: `docs/sessions/2026-09-25_t175-phase0c-audit-plan.md`
- Đọc trước phase code: `T166-…-SPEC.md` · `T171-…-SPEC.md` (§14) · `T174-…md`
