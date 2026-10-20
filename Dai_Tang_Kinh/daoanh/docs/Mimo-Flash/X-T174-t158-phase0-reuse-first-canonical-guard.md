---
id: T174
title: "T158-PHASE0-004 (đổi nhãn T174) — Reuse-First Translation + Canonical Identity Hard Guard: Phase 0 Audit"
module: Translation / Canonical Identity
priority: high
status: ready-for-dev
owner: claudecode
depends_on: [T165, T166, T168]
created: 2026-09-25
updated: 2026-09-29
amended_by: "T193 (2026-09-29 — thu hồi directive gốc tự chứa · sửa authority hierarchy · refresh 26 fact · 3 mục audit mới)"
designed_by: mimo-flash
handoff_to: Claude Code Agent (mode ANALYZE_ONLY — Phase 0, 0 code/0 DB)
plan_approved_at: "2026-09-25 (Admin chốt ID = T174 + Đồng ý build docs)"
done_when: |
  Agent trả Phase 0 report **đúng 18 mục §4.2** (dán nguyên mẫu, không thêm/bớt mục),
  báo đủ **34 mục A…AH §4.1**; KHÔNG sửa code/DB/schema/cache/UI;
  xác nhận overlap với T165/T166/T168 (mục 18);
  Admin duyệt → mới nhận lệnh APPROVED FIX cho phase code.
---

# T174 — Phase 0 Audit: Reuse-First Translation + Canonical Identity Hard Guard

> **Gốc:** directive `T158-PHASE0-004` — Admin chốt **đổi nhãn T174** (T158 đã dùng ×2: glossary-resolver + lineage-consensus DONE; directive `[T158-DEBUG-001]`→T168, `[T158-CRITICAL-SAFETY-003]`→T166).
> **Mode:** PHASE 0 ONLY — audit thật, **0 code, 0 migration, 0 Groq quota**. Stop sau report, chờ `APPROVED FIX`.
> **Reuse nguyên tắc:** REUSE FIRST · LLM SECOND · VERIFY AGAIN.

---

## 1. Review directive → 4 P0 + 5 P1 (đã verify source + DB)

### P0-1 — Thiếu T165/T166/T168 trong reuse list → nguy cơ trùng lặp
Kiến trúc §14/§15 (CanonicalLock, post-LLM assertion, reuse builder, cache version) **đã SPEC + build một phần**:
- T166 SPEC `docs/Mimo-Flash/X-T166-canonical-identity-guard-SPEC.md` (**457 dòng**) — task `X-T166-canonical-identity-guard.md` (`ready-for-dev`). *Không có file tên `T166-canonical-identity-guard-SPEC.md`.*
- T165 `style_constitution.py` **đã build** — repo root `daoanh/style_constitution.py` (738 dòng), 24 test PASS, code đã được `app.py` import (alias `_t165_*`, app.py:33-55). *T165 trong `docs/Mimo-Flash/` nay là Phase-8 XML; engine build nằm ở `docs/sessions/2026-09-25_t169-t165-engine-build.md`.*
- T168 `docs/Mimo-Flash/X-T168-rule-resolver-context-compiler-PLAN.md` (182 dòng) — `constitution_hash` **đã có** trong `style_constitution.py:199` + cột `translation_cache.constitution_hash`.
→ Absorb: reuse list += 3 task · report template += `EXISTING T165/T166/T168 WORK`.

### P0-2 — Ví dụ `安廩` mâu thuẫn chốt đã duyệt (T166 rev.2)
Thực tế (verify 2026-09-29): `people` **A005248 安廩 → `An Lẫm`**; `name_vi_map` = `name_vi_auto='An Lẫm'`, `confidence=0.7`, **`name_vi_final=NULL`**, `approved_by=NULL`; `vn_person_authority` **0 row**; `lexicon` **0 row**; `glossary_vi` **0 row** → **KHÔNG tier A**. T166 chốt: `安廩` = **CANDIDATE, không HARD_FAIL**; invent = `CANONICAL_INVENTION` warning → draft only; fixture LOCK = **A009460 丹霞天然 → Đơn Hà Thiên Nhiên** (`vn_person_authority.status='verified'`).
→ Absorb §2/§15: **LOCK chỉ khi đúng tier A theo §2**; auto không final = CANDIDATE → WARN → draft. CASE-1 example = A009460 · `安廩` = CASE-4 CANDIDATE.

### P0-3 — Đụng ID T158 (lần dùng thứ 4/5) → Admin chốt **T174**

### P0-4 — "AI Dịch" ≠ 1 entry, thực tế **4 route** (line-ref đã refresh):

| # | Route (thật) | `@app.route` | `def` | `source_type` cache | số row cache |
|---|---|---|---|---|---|
| 1 | `/daoanh/api/person/<person_id>/translate` | `app.py:17727` | `api_person_translate` 17728 | `person_bio` | 9 |
| 2 | `/daoanh/api/person/<person_id>/dila_translate` | `app.py:18117` | `api_person_dila_translate` 18118 | **`dila_card`** (không phải "dila bio") | 22 |
| 3 | `/daoanh/api/place/<dila_id>/translate` | `app.py:18890` | `api_place_translate` 18891 | `place_note` | 36 |
| 4 | `/daoanh/api/relation/translate` | `app.py:6524` | `api_relation_translate` 6525 | `relation_evidence` | 2 |

*(còn `passage` 1.798 row — route `/daoanh/api/passage/<passage_id>/translate` app.py:19103, ngoài 4 route trên)*

### 6 call site `_t166_post_check_translation` — [T194] đã map về route

| route | `@app.route` | call site |
|---|---|---|
| `/daoanh/api/relation/translate` | 6524 | 6583 |
| `/daoanh/api/person/<person_id>/translate` | 17727 | 17780 |
| `/daoanh/api/person/<person_id>/dila_translate` | 18117 | 18320 |
| `/daoanh/api/admin/person/<person_id>/bio_vi` | 18366 | 18400 |
| `/daoanh/api/admin/person/<person_id>/dila_vi` | 18466 | 18523 |
| `/daoanh/api/place/<dila_id>/translate` | 18890 | 18973 |

*(Dòng 17842 = `def _ok_hanviet_name`; 4 call site inject: 18150, 18198, 18653, 18723.)*

### P1 (5)
1. **§4 "22 từ điển" = 2 lớp:** lớp DB (`glossary_vi` 248.095 · `lexicon` 166.278 · `monk_dict` 2 · `term_glossaries` 18.127 · `glossary_term` 248.095 · `translation_glossary` 79) ≠ lớp code (`hanviet_normalization.load_glossary()` — thật `scripts/hanviet_normalization.py:227`; `data/dictionaries/tudien` 23 file · `data/dict/*.mdx` 1 file). **`_glossary_resolver` = FUNCTION (`app.py:17457`), không phải bảng** — cấm đoán tên bảng. *(Xem mục AE: còn 1 impl thứ hai ở `style_constitution.py:348`.)*
2. **§10 Place:** `places_dila` **không có cột `name_vi`** (đã verify `PRAGMA table_info` → 0 cột chứa "vi") → tiếng Việt = **`namevi_map_places`** (118.296 row). *Lưu ý cột: `namevi_map_places.name_zh` chứa **中文字** (少林寺), `places_dila.name_zh` lại là **bộ dịch Hán Việt** (少室寺) — 2 bảng lệch nhau.*
3. **§5 TTL 1 nơi duy nhất:** `data/ttl` = **1.092 file** (+ `0-template.ttl`). **`data/ontology` KHÔNG tồn tại** → xóa claim "ontology/monks/TTL 7 · ontology/ttl 1". Index = `vn_person_authority.ttl_filename`.
4. **T95/T94 nằm `tasks/backup/`** (đã verify tồn tại) — hint để agent không báo NOT FOUND oan.
5. **"verified" phải định nghĩa theo §2** — và **bắt buộc kèm `approved_by`**, nếu không sẽ LOCK oan 5.204 rows (xem P0-3 mới).

### P1 mới — phát hiện khi viết T193 (2026-09-29)

| # | Vấn đề | Bằng chứng |
|---|---|---|
| P1-6 | **`finalize_lock` không tồn tại** | 0 hit toàn repo (`app.py`, `style_constitution.py`, `scripts/*.py`). Hàm assertion thật là **`post_check_translation`** (`style_constitution.py`, import app.py:55) |
| P1-7 | **Post-LLM assertion chưa từng chạy** | `translation_cache.identity_status` NULL **1.867/1.867**; `translation_rules.identity_lock_policy` = `P-PARTIAL` **112/112** |
| P1-8 | ~~Route place_note không có post-LLM guard~~ **[T194 ĐÃ SỬA: SAI — place ĐÃ CÓ guard]** | `_t166_post_check_translation` có **6 call site** (đã map về route, xem bảng dưới) — gồm cả `/daoanh/api/place/<dila_id>/translate`. Nguồn gốc lỗi: T193 verify ở thời điểm app.py còn 3 call site; agent khác đã thêm 2 route admin-person + 1 place trong lúc T193 chạy. |
| P1-9 | **Ví dụ 少林寺 sẽ ra NOT FOUND oan** | `places_dila(id='PL000000023255', name='少林寺', name_zh='少室寺')` → lọc `name_zh='少林寺'` = **0 row**. Và **2 ID namespace lệch nhau**: `places_dila.id='PL000000023255'` vs `namevi_map_places.dila_id='PL023255'` |
| P1-10 | **Tier A thực tế cực hiếm** | person: 3 rows (2 `vnpa verified` + 1 `name_vi_final` có `approved_by`) / 48.673 = **0.006%**. place: 2 rows `vn_name_status='reviewed'` / 118.296. Phải nêu để dev không kỳ vọng LOCK phủ rộng |
| P1-11 | **Duplicate resolver** | `app.py:17457 _glossary_resolver` (shape cũ) vs `style_constitution.py:348 glossary_resolver` (shape `{resolved, unresolved}`) → 2 impl, REUSE-FIRST bắt buộc chọn 1 |
| P1-12 | **Nguy cơ build trùng phase** | T175 (`depends_on:[T174]`) + T176 đã tồn tại `ready-for-dev`; T177 `done`; T165-P8.1 đã commit `82d595f` |

---

## 2. Authority hierarchy (chốt — đã sửa P0-2/P0-3 của T193)

> **Đây là phần quan trọng nhất. Đọc trước khi viết code phase.**

### 2.1 PERSON — quyết định tier bằng **SQL**, không suy đoán

| tier | điều kiện SQL (đã verify trên `data/lineage.db`) | số row | hành động |
|---|---|---|---|
| **A — LOCK** | `vn_person_authority.status='verified'` → **A009460**, **A010616** (2)<br>HOẶC (`name_vi_map.name_vi_final` khác NULL **AND** `approved_by` khác NULL) → **1** | **3** | LOCK cứng. Evidence mâu thuẫn → REVIEW |
| **B — CANDIDATE** | `name_vi_map.name_vi_auto` khác NULL **AND** `name_vi_final` IS NULL | **41.508** | WARN, chỉ `draft`. KHÔNG auto-canonical, KHÔNG hard-fail |
| **C — UNKNOWN** | không có row `name_vi_map` (48.673 − 46.711) | ~1.962 | UNKNOWN/REVIEW. Tuyệt đối không đoán |

> **KHÔNG BAO GIỜ coi `people.name_vi` là tier A** — 48.673 row, phần lớn auto/legacy (T171/T172).

**Vì sao bỏ ngưỡng `confidence < 0.9`:** 41.508 row có `name_vi_auto` và **0 row** có `confidence ≥ 0.9` ⇒ ngưỡng 0.9 là *dead threshold*, không phân biệt được gì. Tier B giờ định nghĩa bằng **vắng mặt `name_vi_final`** — vẫn đúng ý T166 nhưng kiểm được, không đụng đội trống.

**Vì sao bắt buộc kèm `approved_by`:** `name_vi_final` có 5.205 row nhưng `approved_by` chỉ **1** row khác NULL. Nếu tier A chỉ test `name_vi_final IS NOT NULL` sẽ **HARD_FAIL oan 5.204 row chưa qua duyệt** — đúng lỗi mà P1-5 cảnh báo.

### 2.2 PLACE — tier riêng (doc cũ thiếu mục này)

`places_dila` không có `name_vi`; authority là `namevi_map_places` (118.296 row):

| tier | điều kiện | số row | hành động |
|---|---|---|---|
| **A — LOCK** | `vn_name_status='reviewed'` → **2**<br>HOẶC `source IN ('manual','manual_fix')` → **5** | ~5–7 | LOCK cứng |
| **B — CANDIDATE** | `source='ttl_confirmed'` hoặc `confidence ≥ 0.9` | **31** (`ttl_confirmed`) | WARN, draft only |
| **C — UNKNOWN** | `source LIKE 'auto_transliterate%'` (118.259) hoặc `vn_name_status IS NULL` (118.293) | 118.259 | UNKNOWN/REVIEW |

> ⚠️ **少林寺 là tier B, KHÔNG phải tier A.** Nó có `confidence=0.9` + `source='ttl_confirmed'` nhưng `vn_name_status IS NULL`. Tên `Thiếu Lâm Tự` nghe rất "chắc" nhưng theo hierarchy thì chỉ được WARN — cần Admin `review` mới lên tier A. Đây là case kiểm tra để agent **không tự nâng tier**.

### 2.3 Regression bắt buộc (3 case, kèm số liệu thật)

| case | input | thực tế | kỳ vọng |
|---|---|---|---|
| **CASE-1 LOCK** | A009460 丹霞天然 | `vnpa.status='verified'`, `name_vi='Đơn Hà Thiên Nhiên'`<br>**nhưng** `people.name_vi='Đan Hà Thiên Nhiên'` | LOCK `Đơn Hà Thiên Nhiên`. **Tier A phải THẮNG `people.name_vi`** — đây là conflict thật, không phải lý thuyết |
| **CASE-4 CANDIDATE** | 安廩 (A005248) | `name_vi_auto='An Lẫm'` 0.7, `name_vi_final=NULL`, vnpa 0 row | tier B. Qwen từng sinh `Thích An Nạp` → `CANONICAL_INVENTION` warning → **draft only**, KHÔNG hard-fail |
| **CASE-5 PLACE tier B** | 少林寺 | `places_dila.name='少林寺'`, `name_zh='少室寺'`, id `PL000000023255`<br>`namevi_map_places` 2 row: `PL023255` conf 0.9 `ttl_confirmed`; `PL000000023255` conf 0.72 `manual` | tier B. KHÔNG lock. **Báo cả 2 dòng + cảnh báo 2 ID namespace lệch nhau** |

**Nếu evidence mâu thuẫn:** REVIEW. **Nếu không có evidence:** UNKNOWN/REVIEW.
**Never:** UNKNOWN → QWEN INVENTION → CANONICAL.

---

## 3. Directive gốc `T158-PHASE0-004` — mất, đã phục hồi

Bản directive gốc **không tồn tại trong repo** (chỉ là câu nhắc trong T174/T175) và không truy được từ git history. Doc cũ tham chiếu nó ở §3/§7/§8/§11/§12/§13/§14/§16/§17/§18 nhưng **không in nội dung** ⇒ prompt không tự chứa, agent không thể tạo report đúng mẫu ⇒ `done_when` không thể đạt.

**Cách phục hồi:** 34 mục A…AH (§4 mục 3) + mẫu report 18 mục (§4 mục 18) được **dựng lại có căn cứ** từ: §2 verified facts của bản doc cũ + các nhắc dẫn còn sót (`B/C`, `D/E`, `F…K`, `K/M/N`, `R/S`, `U…Z`, `T/AF/AG/AH`) + verify lại toàn bộ trên source/DB ngày 2026-09-29.

> ⚠️ Đánh dấu **RECONSTRUCTED**. Nếu Admin nhớ bản directive gốc khác, hãy sửa §4 trước khi paste — **đừng sửa sau khi agent chạy.**

---

## 4. PROMPT PHASE 0 — paste-ready, tự chứa

> Dán nguyên khối dưới đây cho Claude Code. **Không thêm/bớt.** Agent không cần đọc file nào khác để biết phải báo cáo gì.

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
Repo root = the git toplevel of visjs-app. App dir = Dai_Tang_Kinh/daoanh.
DB = Dai_Tang_Kinh/daoanh/data/lineage.db (open read-only).

============================================================
1. CURRENT ARCHITECTURAL DECISION
============================================================
T174 is NOT a new translation engine. T174 MUST EXTEND:
- T95 CBETA translation pipeline (tasks/backup/T95-cbeta-translation-pipeline.md)
- T123 Style Constitution / unified prompt builder (tasks/T123-style-constitution-ban-dich-ptda.md)
- T94 manual verification workflow (tasks/backup/T94-cbeta-alignment-schema.md)
- T110 glossary_vi (tasks/T110-glossary-vietnamese-pipeline.md)
- existing DILA canonical data · translation cache · translation jobs/items
- existing local Buddhist dictionaries · local TTL/XML monk biographies
*** REUSE (đã có — KHÔNG build lại) ***
- T165 style_constitution.py — REPO ROOT daoanh/style_constitution.py (738 dòng),
  đã được app.py import bằng alias _t165_* (app.py:33-55):
  source_hash:53 · select_rules:90 · constitution_hash:199 · glossary_hash:191
  style_lock:234 (app.py:17301 _t73_style_lock chỉ là wrapper delegate)
  build_style_prompt:552 (app.py:17432 _t73_build_style_prompt delegate)
  post_check_translation (import app.py:55) · identity_lock_policy:806
- T166 Canonical Identity Guard SPEC: docs/Mimo-Flash/X-T166-canonical-identity-guard-SPEC.md
  (457 dòng; task X-T166-canonical-identity-guard.md, ready-for-dev)
  -> code đã có 1 phần trong style_constitution.py: _t166_identity_lock:321 ·
  _t166_identity_fingerprint:334 · _t166_identity_block:614 · identity_lock_policy:806
- T168 Rule Resolver + Context Compiler: docs/Mimo-Flash/X-T168-rule-resolver-context-compiler-PLAN.md
  (182 dòng) -> constitution_hash:199 + cột translation_cache.constitution_hash ĐÃ có
DO NOT rebuild any of these.

Architecture:
CBETA SOURCE -> ENTITY/TERM DETECTION -> LOCAL KNOWLEDGE RESOLVER
(DILA person/place · SQL canonical · Buddhist dictionaries · glossary_vi
 · translation memory · TTL/XML biographies · verified evidence)
-> CANONICAL LOCK / REVIEW GATE -> T123 EXISTING STYLE BUILDER
-> QWEN/GROQ ONLY WHERE NEEDED -> POST-LLM CANONICAL ASSERTION
-> DETERMINISTIC VALIDATOR -> HUMAN REVIEW -> GOLD
Core principle: REUSE FIRST · LLM SECOND · VERIFY AGAIN.

============================================================
2. ZERO-TOLERANCE CANONICAL SAFETY
============================================================
Canonical person names, Dharma names, places, temples, dynasties, eras
and established Buddhist terminology MUST NOT be invented by Qwen when
authoritative local evidence exists.

*** AUTHORITY HIERARCHY — PERSON (bắt buộc theo SQL, không suy đoán) ***
tier A LOCK/HARD_FAIL : vn_person_authority.status='verified'  (2 rows)
                       HOAC name_vi_map.name_vi_final khac NULL
                          VA name_vi_map.approved_by khac NULL  (1 row)
                       => tong 3 row
tier B CANDIDATE/WARN : name_vi_map.name_vi_auto khac NULL
                       VA name_vi_final IS NULL   (41.508 row)
tier C UNKNOWN/REVIEW : khong co row name_vi_map
*** TUYET DOI KHONG coi people.name_vi la tier A (48.673 row, auto/legacy). ***
*** KHONG dung nguong confidence<0.9 de xac dinh tier B: 0 row co
    confidence>=0.9, nguong nay la dead threshold. ***

*** AUTHORITY HIERARCHY — PLACE (places_dila KHONG co name_vi;
    authority = namevi_map_places) ***
tier A LOCK : vn_name_status='reviewed' (2) HOAC source IN ('manual','manual_fix') (5)
tier B WARN : source='ttl_confirmed' (31) HOAC confidence>=0.9
tier C UNKNOWN : vn_name_status IS NULL (118.293) / source LIKE 'auto_transliterate%' (118.259)

Mandatory regression (đã verify số liệu thật):
CASE-1 LOCK: A009460 丹霞天然 -> vnpa verified 'Đơn Hà Thiên Nhiên'
   LUU Y: people.name_vi của A009460 là 'Đan Hà Thiên Nhiên' (KHAC).
   Tier A PHAI THANG people.name_vi. Báo rõ mâu thuẫn này.
CASE-4 CANDIDATE: 安廩 (A005248) = tier B (auto 'An Lẫm' 0.7, name_vi_final NULL,
   vnpa 0 row). QWEN từng sinh 'Thích An Nạp' -> CANONICAL_INVENTION warning ->
   DRAFT ONLY. KHONG hard-fail, KHONG auto canonical.
CASE-5 PLACE tier B: 少林寺 -> places_dila(id='PL000000023255', name='少林寺',
   name_zh='少室寺') và namevi_map_places có 2 row (PL023255 conf 0.9
   ttl_confirmed; PL000000023255 conf 0.72 manual). Chi tier B, KHONG lock.
   Báo CA 2 dong + canh bao 2 ID namespace lech nhau.

If tier A exists: LOCK IT. If evidence conflicts: REVIEW.
If no evidence: UNKNOWN / REVIEW. Never: UNKNOWN -> QWEN INVENTION -> CANONICAL.

============================================================
3. PHASE 0 — 34 MUC A...AH (bao du, dung nhan, KHONG tu them muc)
============================================================
A.  ENTRY CHAIN tong the: UI -> API -> backend -> translation function ->
    prompt builder -> Groq/Qwen -> cache -> validator -> DB.
B.  ACTIVE TRANSLATION CODE trong app.py + cach T95 pipeline duoc noi vao.
C.  CBETA passage/segment translate: route /daoanh/api/passage/<id>/translate
    (app.py:19103) + /daoanh/api/segments/translate (app.py:21421) +
    /daoanh/api/translate (app.py:5001) — co dung chung builder/cache khong.
D.  Task doc T95: tasks/backup/T95-cbeta-translation-pipeline.md (co ton tai).
E.  Task doc T94: tasks/backup/T94-cbeta-alignment-schema.md (co ton tai).
F.  Bang translation_jobs + translation_job_items (jobs + items, cot, quan he).
G.  Bang translation_cache: schema day du, UNIQUE constraint, index, key sinh ra
    the nao, cache hit/miss flow.
H.  Bang translation_rules: schema, status, cach rules_version duoc tinh.
I.  Bang translation_exemplar.
J.  Bang translation_segments.
K.  Bang passage_translation_alignment + translation_glossary.
L.  Bang glossary_vi: schema, so dong, index, ai ghi vao.
M.  DICTIONARY LOP 1 (DB): glossary_vi · lexicon · monk_dict · term_glossaries ·
    glossary_term · translation_glossary — so dong tung bang.
N.  DICTIONARY LOP 2 (code): hanviet_normalization.load_glossary()
    (scripts/hanviet_normalization.py:227) — doc data/dictionaries/tudien,
    data/dict/*.mdx. So file, dinh dang, cache.
O.  TERM RESOLUTION that tu dictionary — trace 1 vi du Han tu, khong bia.
P.  STYLE CONSTITUTION module: style_constitution.py — ham nao dung o dau,
    ConstitutionLock shape thuc te.
Q.  PROMPT BUILDER: style_lock:234 · build_style_prompt:552, va 2 wrapper
    _t73_style_lock (app.py:17301) / _t73_build_style_prompt (app.py:17432).
R.  Bang people: so dong, cot, nguon name_vi.
S.  Bang vn_person_authority + name_vi_map: schema day du, phan bo status,
    doi chieu tier A/B/C o §2 bang SQL that.
T.  CANONICAL LOOKUP: ham nao thuc su tra canonical identity khi dich —
    trace tu 1 route, khong doan ten ham.
U.  TTL repo: vi tri, tong so file, cau truc thu muc.
V.  TTL FORMAT: TTL/XML/TEI/mixed? doc 1 file that, in header.
W.  TTL INDEX/PARSE/CACHE: da co parser/index chua, o dau, co bi parse lai
    moi request khong.
X.  IDENTITY LINK TTL <-> DILA: vn_person_authority.ttl_filename — resolve thu
    1-2 file that, co khop khong.
Y.  TTL EVIDENCE: ten Trung/Viet, aliases, places, dharma_title, lineage —
    parser co doc duoc khong.
Z.  PLACE RESOLUTION: places_dila (khong name_vi) + namevi_map_places — trace
    少林寺 hoan chinh, neu 2 ID namespace lech nhau.
AA. AUTHORITY TIER AUDIT (person): chay SQL dem tier A/B/C theo §2, doi chieu
    voi con so 3 / 41.508 / ~1.962. Lech thi bao lech.
AB. AUTHORITY TIER AUDIT (place): dem tier A/B/C theo §2.
AC. TIER A REALITY CHECK: tier A phu bao nhieu % du lieu? Neu he qua van hanh
    (LOCK gan nhu khong kich hoat o phan lon du lieu).
AD. POST-LLM ASSERTION BASELINE: translation_cache.identity_status /
    identity_issues / identity_lock_hash — co dong nao khac NULL khong?
    translation_rules.identity_lock_policy doc duoc gi? post_check_translation
    duoc goi o route nao / KHONG duoc goi o route nao?
    [T194 XAC MINH ROI: co 6 call site — relation :6583 · person :17780 ·
     dila :18320 · admin bio_vi :18400 · admin dila_vi :18523 · PLACE :18973.
     => KHONG con route AI DICH nao thieu guard. Van con 3 route
     /.../translate/report co the chua co — do la report, khai bao neu gap.]
    Task phai verify LAI 6 call site nay (app.py dang bi agent khac sua lien tuc).
AE. RESOLVER DUPLICATION: app.py:17457 _glossary_resolver vs
    style_constitution.py:348 glossary_resolver — 2 impl, shape khac nhau.
    De xuat chon 1 (REUSE FIRST) + blast radius neu doi.
AF. PHASE ORDER: doc docs/Mimo-Flash/X-T175-*, X-T176-*, X-T177-*, X-T166-*, X-T168-*
    -> T174 co bi supersede khong? Liet ke phan T174 dinh lam ma T175/T176
    da lam hoac sap lam, de khong build trung.
AG. CACHE KEY AUDIT: source_hash = sha256(text)[:24]? UNIQUE(source_hash,
    source_type)? rules_version va constitution_hash tham gia the nao?
    is_rules_outdated / is_trusted_translation / is_draft_translation.
AH. CONFLICT REGRESSION: A009460 (people.name_vi vs vnpa) — code hien tai co
    phat hien mau thuan nay khong? O dau? Neu khong thi gap o muc nao.

============================================================
4. KHONG DINH NGHIA 22 TU DIEN
============================================================
Verify ca 2 lop (M + N). Bao dictionary_count / dictionary_entry_count /
tables / source names / indexes. Do not create/import/modify/duplicate any
dictionary data.

============================================================
5. TTL/XML IS AUTHORITY EVIDENCE
============================================================
Xac dinh canonical local biography repo (data/ttl), TTL/XML/TEI/mixed +
indexed/parsed/cached; identity noi sang DILA ID qua
vn_person_authority.ttl_filename; ten Trung/Viet, aliases, places.
Do not create a new parser if one exists.
Do not parse all files per request — future resolver uses index/cache.

============================================================
6. TIM 4 ENTRY POINT THAT CUA "AI DICH"
============================================================
UI -> API -> backend -> translation function -> prompt builder -> Groq/Qwen ->
cache -> validator -> DB. Bao du 4 route:
  person  /daoanh/api/person/<person_id>/translate        app.py:17727 (person_bio)
  dila    /daoanh/api/person/<person_id>/dila_translate   app.py:18117 (dila_card)
  place   /daoanh/api/place/<dila_id>/translate           app.py:18890 (place_note)
  relation/daoanh/api/relation/translate                  app.py:6524  (relation_evidence)
Bao: file, function, route, table doc/ghi, cache behavior.
Line-ref tren la diem khoi dau — XAC MINH LAI, dung tin tuyet doi.
Do not change anything.

============================================================
7-12. RESOLVER / BUILDER / CACHE / PERSON / PLACE / TERM / TM
============================================================
7.  Prompt builder: style_constitution.py style_lock:234 + build_style_prompt:552
    (delegate qua _t73_style_lock app.py:17301 / _t73_build_style_prompt
    app.py:17432). T174 MUST EXTEND, khong tao builder canh tranh.
8.  Cache key audit (dung doi) — chi tiet o AG.
9.  Person resolution that cho 安廩 (A005248) — KHONG goi Qwen; ky vong
    report = tier B / CANDIDATE (SQL An Lẫm 0.7, final NULL; vnpa 0 row).
10. Place test that (少林寺): places_dila id=PL000000023255,
    name='少林寺', name_zh='少室寺'; VI tu namevi_map_places (2 dong, tier B).
    KHONG loc name_zh='少林寺' (ra 0 row). Bao ca 2 ID namespace.
11. Term resolution that tu dictionary (khong bia).
12. Translation memory: translation_segments / passage_translation_alignment /
    translation_exemplar / translation_glossary / approved entries.

============================================================
13-16. DECISION / LOCK / ASSERTION
============================================================
13. Decision model CASE 1-5. CASE 1 chi khi tier A dung §2.
14. CanonicalLock {source_form, normalized_form, entity_type, canonical_id,
    canonical_value, authority_source, evidence_refs,
    status ∈ LOCKED|CONFLICT|UNKNOWN_REVIEW} — mo rong cau truc co san
    trong T166/T165; KHONG tao bang/doi tuong trung.
15. Post-LLM assertion (post_check_translation trong style_constitution.py),
    severity theo authority hierarchy §2 (tier B -> WARN/draft, KHONG HARD_FAIL).
16. PRE-LLM LOCK + POST-LLM ASSERTION — ca hai, khong thay bang
    "validator fixes it".

============================================================
17. DO NOT BUILD YET
============================================================
Khong sua code / DB / schema / cache / UI. Khong chay migration. Khong goi
Groq/Qwen. Khong tao bang moi. Khong tao/import/sua du lieu tu dien.
Khong sua style_constitution.py. Khong merge branch. Khong commit.

============================================================
18. MAU BAO CAO — 18 MUC, DAN NGUYEN VAN
============================================================
T174 PHASE 0 AUDIT REPORT
1.  REPOSITORY
    - root, branch, HEAD sha, dirty?, python version
2.  PHASE 0 SCOPE & CONSTRAINTS
    - xac nhan 0 code/0 DB/0 migration/0 LLM call da thuc hien
3.  AI DICH ENTRY TABLE                                    [bat buoc]
    - 4 route x file/function/route/table/cache
4.  A. ENTRY CHAIN
5.  B/C. TRANSLATION CODE + T95 PIPELINE
6.  D/E. TASK DOCS T95/T94
7.  F. translation_jobs / translation_job_items
8.  G. translation_cache (schema · UNIQUE · index)
9.  H. translation_rules
10. I/J/K. TM (exemplar · segments · alignment · glossary)
11. L. glossary_vi
12. M/N. DICTIONARY 2 LAYER
13. O. TERM RESOLUTION
14. P/Q. STYLE CONSTITUTION + PROMPT BUILDER
15. R/S. PERSON IDENTITY + AUTHORITY TIER
16. T. CANONICAL LOOKUP
17. U-Z. TTL/XML + PLACE
18. EXISTING T165/T166/T168 WORK                          [bat buoc]
    - AD identity baseline · AE resolver duplication · AF phase order
    - AG cache key · AH conflict regression
    - files/functions da co · phan Phase 0 nay TRUNG · phan DELTA con thieu

Rang buoc bao cao:
- Dan nguyen 18 tieu de muc tren, theo dung thu tu, KHONG them/bot muc.
- Muc nao khong xac dinh duoc: ghi NOT FOUND + ly do cu the. CAM doan.
- Chi ket luan tu source + runtime that; moi con so phai kem cau SQL/duong dan
  da chay de tai lap.
- toi da 80 dong NGOAI khoi bao cao mau.
- Neu ro muc nao lech voi so lieu Admin dua o §2 cua T174 va lech bao nhieu.
STOP HERE. DO NOT BUILD.
```

---

## 5. Phases

| # | Nội dung | Trạng thái |
|---|---|---|
| 1 | Review directive → 4 P0 + 5 P1 → prompt chốt (docs-only) | ✅ 2026-09-25 |
| 2 | **T193: sửa doc (thu hồi directive · authority hierarchy · refresh facts · 3 mục mới)** | ✅ 2026-09-29 |
| 3 | Admin paste prompt §4 cho Claude Code → Phase 0 report 18 mục → Admin duyệt | ⏳ chờ |
| 4 | `APPROVED FIX` → phase code (tách commit từng bước, pipip trước mỗi commit) | ⏳ sau |
| 5 | Report + ROLLBACK hash-fill | ⏳ sau |

**Lưu ý phase order (P1-12):** T175 (`depends_on:[T174]`) + T176 đã tồn tại `ready-for-dev`; T177 `done`; T165-P8.1 đã commit `82d595f`. Mục **AF** trong prompt bắt agent báo cáo overlap để **không build trùng** — Admin nên đọc mục 18 trước khi quyết định `APPROVED FIX`.

## 6. Revert

Docs: `git revert --no-edit b95d3008eef4a17527fe30c846e37cdd102288e1` (sửa T174) hoặc `git revert --no-edit <sha_T174>` (bản gốc).
Code phase (tương lai): từng commit riêng; schema change dự kiến xem report (SP 0 chưa quyết — nhưng theo T166, `identity_status` additive đã thiết kế sẵn và **đã có cột trong `translation_cache` + `translation_rules.identity_lock_policy`**, chỉ chưa có dữ liệu).

## 7. Files

- Task này: `docs/Mimo-Flash/T174-t158-phase0-reuse-first-canonical-guard.md`
- Sửa bởi: `tasks/T193-t174-plan-doc-correction.md` + `docs/sessions/2026-09-29_t193-t174-plan-doc-correction.md`
- Đọc trước khi chạy phase code:
  - `docs/Mimo-Flash/X-T166-canonical-identity-guard-SPEC.md` (457 dòng)
  - `docs/Mimo-Flash/X-T168-rule-resolver-context-compiler-PLAN.md` (182 dòng)
  - `docs/Mimo-Flash/X-T177-dynamic-filter-absorb-directive-v2.md` (`done`)
  - `style_constitution.py` (repo root, 738 dòng)
  - `docs/sessions/2026-09-25_t169-t165-engine-build.md` (T165 engine build)
