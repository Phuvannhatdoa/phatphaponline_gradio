---
id: T176
title: "T158-PHASE0C rev.2 (đổi nhãn T176) — Canonical Buddhist Person Identity Resolution Audit v2: BUG-025 + 22 Dictionaries + Cache/Transliteration"
module: Translation / Person Identity
priority: high
status: ready-for-dev
owner: claudecode
depends_on: [T175, T174, T166, T171]
created: 2026-09-25
updated: 2026-09-25
designed_by: mimo-flash
handoff_to: Claude Code Agent (AUDIT ONLY — 0 code/0 DB/0 commit)
plan_approved_at: "2026-09-25 (Admin chốt: (1) tách task mới = T176 cho bản v2 · (2) GIỮ 2 mục report cũ → §12b + §14b)"
done_when: |
  Agent trả T176-PHASE0C AUDIT REPORT đúng mẫu (19 mục + 2 mục giữ chốt cũ
  §12b/§14b) · 0 code/0 DB/0 commit · Admin duyệt → mới nhận APPROVED FIX.
---

# T176 — Phase 0C rev.2 Audit: Canonical Person Identity (DILA Han → Local VI → Display → LLM → Cache)

> **Gốc:** directive `[T158-PHASE0C]` **bản v2** (Admin viết lại, có thêm BUG-025 + 13 compat task + format 19 mục).
> **Chốt Admin 2026-09-25:** (1) **Tách task mới = T176** — T175 (v1, commit `dbb77ef`) giữ nguyên, không sửa; (2) **GIỮ 2 mục report đã chốt** → `§12b. OVERLAP WITH T174/T166/T171` + `§14b. AMBIGUITY_RESULT`.
> **Mode:** AUDIT ONLY — cấm code/DB/ALTER/INSERT/cache-purge/new resolver/commit. Stop chờ lệnh.
> **Mối quan hệ:** T175 = v1 (đã review 4 P0+6 P1) · T176 = v2 (paste prompt §3 này thay cho T175 §3 khi Admin chạy audit) · sub-audit **feed T174** · kế thừa **T166** authority · minimal fix map **T171**.

## 1. Review v2 → 2 P0 đã chốt + 4 P1 delta (verify DB/source thật)

### v2 ĐÃ SỬA được so với v1 (không cần吸收 lại)
- §14 chỉ yêu cầu "tương thích" → **không còn claim sai "T79 = translation system"** (v1 P1-1) ✓
- §8 "hoặc thứ tự khác" = câu hỏi mở thay vì giả định thứ tự ✓
- §3 thêm rule "chỉ kết luận mapping khi evidence chứng minh · fuzzy = không làm canonical proof" ✓
- **§5 BUG-025 là bug THẬT** đã có sẵn (xem dưới) + §13 TEST-07 cache + format 19 mục đủ chỗ ✓

### P0-1 · Đụng label `T158-PHASE0C` lần nữa (T175 v1 đã commit `dbb77ef`) → **Admin chốt: T176**

### P0-2 · Format v2 (19 mục) bỏ mất 2 mục report Admin đã chốt (v1) → **Admin chốt: GIỮ** → `§12b` + `§14b`

### P1 delta (4) — đã nhúng vào prompt §3
1. **MỤC TIÊU "canonical = Linh Hựu" = GIẢ THIẾT, không phải fact:** DB thật `people[A001984].name_vi` = **đã gộp `Quy Sơn Linh Hựu`** (B+C collapse) · **`Linh Hựu` = T51g curated** (`scripts/t51g_import_curated.py:52` → ghi `marcus_reference.label_vi`) · vnpa `alias_A001984` = status **`alias_vi_suffix`** · `people` **không có cột** title/thụy hiệu/alias (đặt ở `vn_person_authority.dharma_title`/`appellations`) · `monk_name_index` = bảng thật nhưng **37 row, khóa `monk_id`** (không `dila_id`) · TEST-01 **candidate set 5 id** (A001984/A023322/A023362/A032868/A035586).
2. **§5 BUG-025 = ĐÃ FIX MỘT PHẦN (verify trước):** `docs/bugs.md:411` — data-only fix 2026-09-22, status **`pending_confirm`**; `people` đã đúng (A021462=`Kính Đường Giác Viên`, A001984=`Quy Sơn Linh Hựu`) — **NHƯNG còn row stale `name_vi_map (dila_id=A021462, name_vi='Quy Sơn Linh Hựu', source=daoanh_dict)`** + đường search `n.name_vi LIKE` (app.py:3811) + script `scripts/verify_bug025_026.py` → prompt §5 thêm hint "phần nào còn sót" (agent xác minh, KHÔNG sửa).
3. **§6 "22 dictionary" = StarDict layer, không phải 22 bảng DB:** `docs/pipelines.md:68` "Parse all 22 dictionary `.idx` + `.dict` files" + `DEV_HISTORY.md:30` "22 bộ từ điển → 166.278 terms" (merge vào `lexicon`) → đếm qua **`lexicon.source` + `ls data/dictionaries/*.idx`**, không đếm tên bảng (bảng keyword dict/gloss ≈22 nhưng gồm 5 shadow FTS + jobs/segments) · `_glossary_resolver` = **function** (~app.py:16330) · `monk_dict` chỉ **2 row** · `glossary_vi` **0 entry `靈祐`**.
4. **Verify mới đưa vào prompt** (để agent không phát biểu sai): route **`/api/translate/google` (app.py:13269) backend = MyMemory** (mislabeled) · `translate_hvdic` :13246 = thivien.net · `translate_all` :13289 = hvdic → MyMemory · **cache key = `sha256(excerpt)[:24]` + `source_type` + `rules_version` + `constitution_hash` + `selected_rule_codes` + `glossary_hash` — canonical identity KHÔNG nằm trong hash** → TEST-07 stale risk có thật · `admin_namevi_translate_local` (app.py:15011) **ghi thẳng `name_vi_map`** (`name_vi_auto`, conf **0.5**, source `local_translate`) → §12 mục 4/10 · TTL **runtime đọc file `{lookup_id}.ttl`** (app.py:11359/11380/12387/12496/12520) + ETL `t05_ttl_namevi_etl`/`etl_ttl_person_authority` → `vn_person_authority`.

## 2. Verified facts (pre-audit, read-only — 2026-09-25)

| Hạng mục | Thật |
|---|---|
| BUG-025 | `docs/bugs.md:411` · fix data-only 2026-09-22 · **pending_confirm** · revert = 2 câu UPDATE people (ghi trong bugs.md) |
| `name_vi_map` stale | row `dila_id=A021462 → "Quy Sơn Linh Hựu"` **CÒN SỐT** (people đã fix) |
| "Linh Hựu" nguồn local | `t51g_import_curated.py:52` A001984→('Linh Hựu', 1.0, '…祐=Hựu không phải Hữu') → `marcus_reference.label_vi` |
| `monk_name_index` | 37 row · cols `monk_id/lang/name_form/name_type/normalized` |
| 22 từ điển | StarDict 22 file `.idx/.dict` → `lexicon` 166.278 (`source` phân nguồn) · DB dict-ish 22 tên bảng gồm FTS shadow/jobs → KHÔNG dùng cách này đếm |
| Glossary/test | `glossary_vi` 248.095 nhưng **0 `靈祐`** · TEST-05 sẽ NOT FOUND ở glossary (đúng) |
| Transliterate | hvdic thivien.net :13246 · "google" = **MyMemory** :13269 · `translate_all` :13289 |
| Cache | `translation_cache` `UNIQUE(source_hash, source_type)` 1.761 row · key hash **không gồm canonical** |
| TTL | runtime read `{lookup_id}.ttl` (5 vị trí) + 2 script ETL → `vnpa` |
| Compat 13 task | T05/T51g/T68/T71/T72/T78/T79/T94/T95/T110/T123/T126 + BUG-025 = **đủ file thật** (`tasks/` + `tasks/backup/`) |
| A001984 | `people` 靈祐 唐 Thiền Tông · name_vi = **Quy Sơn Linh Hựu** · 靈祐 = **5 id** |

---

## 3. PROMPT CHỐT — dán Claude Code (AUDIT ONLY)

```text
[T176-PHASE0C rev.2]
CANONICAL BUDDHIST PERSON IDENTITY RESOLUTION AUDIT

MỤC TIÊU
--------
Audit thực tế pipeline hiện tại của PTDA/Đạo Ảnh để xác định:

DILA Han name
    ↓
DILA canonical person ID
    ↓
local Vietnamese canonical/approved name
    ↓
Vietnamese display/surface form
    ↓
translation / Qwen / transliteration
    ↓
cache
    ↓
final rendered result

ĐẶC BIỆT AUDIT CASE THỰC:
    靈祐
    DILA ID = A001984
    [DELTA-P1a] "Vietnamese canonical = Linh Hựu" là GIẢ THIẾT cần verify, không phải fact.
      Kỳ vọng DB thật (đã verify 2026-09-25, agent re-verify):
      - people[A001984].name_vi = "Quy Sơn Linh Hựu" (B+C ĐÃ gộp 1 field — chính là thứ §11 yêu cầu tách)
      - "Linh Hựu" = T51g curated (scripts/t51g_import_curated.py:52 → marcus_reference.label_vi)
      - vnpa alias_A001984 status = alias_vi_suffix (CHƯA verified tier)
      - people KHÔNG có cột title/thụy hiệu/alias → nằm vn_person_authority.dharma_title/appellations
    KHÔNG được đồng nhất 3 lớp này thành một field duy nhất.


==================================================
1. QUY TẮC BẮT BUỘC
==================================================

CHỈ AUDIT.

KHÔNG:
- sửa code
- sửa DB
- ALTER schema
- INSERT/UPDATE/DELETE dữ liệu
- rebuild cache
- đổi API
- đổi canonical ID
- commit
- tạo migration
- tạo resolver mới

Nếu phát hiện bug:
CHỈ ghi nhận root cause + vị trí + đề xuất fix tối thiểu.

Không được "tiện tay sửa".

Không đoán tên file/function.
Phải truy tìm từ code/runtime thực tế.

==================================================
2. PHẢI TRACE CALL CHAIN THỰC
==================================================

Trace từ:

UI
→ route
→ backend function
→ resolver
→ DB query
→ DILA lookup
→ local name lookup
→ dictionary/glossary lookup
→ transliteration API
→ LLM/Qwen/Groq
→ post-processing
→ cache
→ final response/render

Ghi chính xác:

- file
- function
- route
- table
- relevant columns
- cache key
- cache table/file
- thứ tự ưu tiên hiện tại

Không chỉ mô tả kiến trúc dự kiến.
Tôi cần call chain ĐANG CHẠY THỰC TẾ.

==================================================
3. AUDIT DILA IDENTITY
==================================================

Kiểm tra:

靈祐
A001984

Xác định:

A001984 hiện có:
- name_zh?
- name_vi?
- alias?
- title?
- posthumous name?
- alternative name?
- index/search mapping?

[DELTA-P1a] people KHÔNG có cột title/posthumous/alias — check thêm
vn_person_authority (dharma_title, appellations, alias_*) và
monk_name_index (bảng thật, 37 row, khóa monk_id chứ không phải dila_id).

Kiểm tra tất cả đường dẫn có thể map:

靈祐
釋靈祐
潙山靈祐
潙山靈祐禪師

→ A001984

Nhưng CHỈ kết luận mapping nếu DB/evidence hiện tại chứng minh được.
Không được dùng fuzzy matching làm canonical proof.

[DELTA-P1a] Lưu ý test case: name_zh='靈祐' trong people = 5 người
(A001984 / A023322 / A023362 / A032868 / A035586) — TEST-01 phải trả
candidate set + cách disambiguate, không trả 1 id như đã chắc.

==================================================
4. AUDIT LOCAL VIETNAMESE NAME
==================================================

Kiểm tra A001984 trong toàn bộ local knowledge:

- people
- name_vi
- name_vi_map
- monk_name_index
- monk_dict
- dictionary tables
- glossary_vi
- translation memory
- TTL/XML
- curated data
- historical translation data

Đặc biệt tìm:

A001984 → Linh Hựu
và:
A001984 → Quy Sơn Linh Hựu

[DELTA-P1a] Gợi ý đã verify (re-verify): "Linh Hựu" không nằm ở people
(một hàng cũng không) mà ở T51g curated → marcus_reference.label_vi;
name_vi_map dila_id=A001984 có các row tự động (conf 0.7); monk_name_index
37 row — check có entry nào cho A001984 không.

Phân loại rõ:

CANONICAL_VI
APPROVED_VI
DISPLAY_VI
ALIAS_VI
SURFACE_FORM
TITLE
POSTHUMOUS_NAME

Không được tự suy luận nếu database không có evidence.

==================================================
5. AUDIT BUG-025
==================================================

Kiểm tra thực tế:

A021462 = 鏡堂覺圓
A001984 = 靈祐

Xác minh:

A021462.name_vi
A001984.name_vi

và toàn bộ search/index/cache liên quan.

Tìm chính xác tại sao:

"Quy Sơn Linh Hựu"

đang resolve tới A021462.

Phải xác định:

- nguồn nào tạo ra giá trị sai
- ETL nào
- transliteration nào
- mapping nào
- manual data nào
- cache nào
- search index nào

Nếu BUG-025 đã được sửa một phần, xác định phần nào đã sửa và phần nào còn sai.
KHÔNG sửa.

[DELTA-P1b] Gợi ý đã verify (re-verify) — bug có hồ sơ: docs/bugs.md:411,
fix data-only 2026-09-22, status pending_confirm. people ĐÃ sửa đúng;
phần còn sót nghi ngờ: row name_vi_map (dila_id=A021462,
name_vi='Quy Sơn Linh Hựu', source=daoanh_dict) + đường search
n.name_vi LIKE (app.py ~3811) + scripts/verify_bug025_026.py.
Xác minh phần nào còn chạy/resolve sai — chỉ ghi nhận.

==================================================
6. AUDIT 22 BUDDHIST DICTIONARIES
==================================================

Xác định DB thật sự đang có 22 dictionary nào.

[DELTA-P1c] Cách đếm đúng (đã verify, re-verify): "22 từ điển" = 22 file
StarDict .idx/.dict được parse (docs/pipelines.md:68) → merge vào bảng
lexicon 166.278 rows (DEV_HISTORY.md v10.4). KHÔNG đếm 22 tên bảng
trong sqlite (kết quả đó gồm FTS shadow + jobs/segments). Đếm qua:
SELECT source, COUNT(*) FROM lexicon GROUP BY source
+ ls data/dictionaries/*.idx (hoặc data/dict).

Cho từng dictionary:

- table/file
- key field
- Han field
- Vietnamese field
- authority/confidence nếu có
- query function hiện tại
- có được AI translation pipeline gọi hay không

[DELTA-P1c] Lưu ý: _glossary_resolver = FUNCTION (~app.py:16330),
không phải bảng; monk_dict chỉ 2 row; glossary_vi 248.095 nhưng 0 entry 靈祐.

Đặc biệt kiểm tra:

靈祐
潙山靈祐
Quy Sơn Linh Hựu
Linh Hựu

Có entry nào không?

==================================================
7. AUDIT TTL/XML
==================================================

Kiểm tra pipeline TTL/XML hiện tại.
T05 đã xác nhận TTL được dùng cho Vietnamese name.

Xác định:

- TTL data nằm ở đâu
- parser/index nào
- có lookup runtime hay chỉ ETL
- authority/confidence
- A001984 có evidence gì
- TTL có được translation pipeline sử dụng không

[DELTA-P1d] Gợi ý đã verify (re-verify): runtime đọc file
{lookup_id}.ttl trực tiếp (app.py ~11359/11380/12387/12496/12520)
+ ETL scripts t05_ttl_namevi_etl.py, etl_ttl_person_authority.py →
vn_person_authority, ttl_person_name_extractor.py. A001984 có row
vnpa alias_A001984, ttl_filename TS-Quy-Son-Linh-Huu, status alias_vi_suffix.

KHÔNG parse lại toàn bộ corpus.

==================================================
8. AUDIT TRANSLITERATION
==================================================

Kiểm tra thứ tự hiện tại:

DB
→ Viện Hán Nôm
→ Google
→ Qwen
hay thứ tự khác.

Xác định function thực tế.

Test read-only:

靈祐

và nếu pipeline hỗ trợ:

潙山靈祐

Mục tiêu:

Nếu local verified value tồn tại:
phải biết pipeline hiện tại có sử dụng nó hay không.

Nếu không tồn tại:
xác định API nào tạo candidate.

Không sửa.

[DELTA-P1d] Gợi ý đã verify (re-verify): route /api/translate/google
(app.py ~13269) backend THẬT = MyMemory (api.mymemory.translated.net)
— tên route ≠ provider; translate_hvdic ~13246 = hvdic.thivien.net;
translate_all ~13289 gọi hvdic trước rồi google/MyMemory. Person name path
khác: admin_namevi_translate_local (~15011) đọc CUSTOM_HANVIET + _HV_CACHE
và GHI thẳng name_vi_map (name_vi_auto, confidence 0.5, source
'local_translate').

==================================================
9. AUDIT LLM PATH
==================================================

Kiểm tra Qwen/Groq translation path.

Đặc biệt tìm xem model hiện nhận được context nào cho person name.

Test/audit case:

Input:
靈祐

Expected identity context nếu hệ thống đã có:

DILA_ID = A001984
HAN_NAME = 靈祐
CANONICAL_VI = Linh Hựu

Nếu model trả:

Linh Hữu
hoặc
Quy Sơn Linh Hữu

phải xác định hiện tại system có cơ chế:

- reject
- override
- review
- hoặc accept

KHÔNG thay đổi behavior.

==================================================
10. AUDIT CACHE
==================================================

Tìm translation cache hiện tại.

Xác định:

- table/file
- key
- hash
- rules_version
- prompt/context có nằm trong key không
- canonical identity có nằm trong key không
- stale cache có thể giữ tên sai không

Đặc biệt:

Nếu trước đây model trả:
"Quy Sơn Linh Hữu"

sau này local canonical được xác định:
"Linh Hựu"

cache cũ có thể tiếp tục trả kết quả sai không?
Phải chứng minh bằng code/key structure.

[DELTA-P1d] Gợi ý đã verify (re-verify): bảng translation_cache,
key = source_hash (sha256(excerpt)[:24]) + source_type
UNIQUE(source_hash, source_type); các cột rules_version, constitution_hash,
selected_rule_codes, glossary_hash CÓ trong key/context; entity_id chỉ là
cột kèm — canonical identity (DILA id) KHÔNG nằm trong hash → cùng text
khác canonical context = cùng key. Chiều ngược lại cũng phải test:
stale cache giữ tên sai vs source data sai (people/name_vi_map) — tách bạch.

==================================================
11. PHẢI PHÂN BIỆT 3 LỚP
==================================================

Audit phải trả lời riêng:

A. CANONICAL IDENTITY

Ví dụ:
A001984
靈祐

B. CANONICAL / APPROVED VI NAME

Ví dụ:
Linh Hựu

C. DISPLAY / TRADITIONAL SURFACE FORM

Ví dụ:
Quy Sơn Linh Hựu

Không được thiết kế:

name_vi = tất cả mọi thứ.
DILA ID mới là identity anchor.
Display name không được tạo ra person mới.

==================================================
12. HARD SAFETY REQUIREMENTS
==================================================

Audit phải kiểm tra hiện tại có/không:

1. Canonical identity hard lock
2. DILA ID preservation
3. Local verified name reuse
4. Transliteration = candidate only
5. LLM = candidate/synthesis only
6. Post-LLM canonical verification
7. Conflict → REVIEW_REQUIRED
8. Unknown → REVIEW_REQUIRED
9. Fuzzy matching = discovery only
10. No automatic canonical promotion
11. Cache cannot override newer canonical evidence
12. Failed validation cannot become GOLD

==================================================
13. MANDATORY TEST CASES
==================================================

Không sửa dữ liệu.

Chạy read-only tests nếu có thể:

TEST-01
靈祐 → A001984
[DELTA-P1a] Bắt buộc: trả CANDIDATE SET (5 id: A001984/A023322/
A023362/A032868/A035586) + tiêu chí disambiguate + status
(đúng = REVIEW_REQUIRED nếu không gỡ được) — KHÔNG trả 1 id đơn.

TEST-02
A001984 → current local Vietnamese data

TEST-03
Search "Quy Sơn Linh Hựu"
→ identify all returned IDs
→ identify why
[DELTA-P1b] Chạy đủ 3 đường: people.name_vi LIKE · name_vi_map.name_vi LIKE
(row A021462 còn sót) · vn_person_authority.name_vi LIKE. Trả về mỗi đường
một danh sách id riêng + lý do.

TEST-04
Compare:
A001984
vs
A021462

TEST-05
Check local dictionary/glossary for:
靈祐 / Linh Hựu

TEST-06
Check transliteration fallback for:
靈祐

TEST-07
Check cache behavior for same source text under different canonical context.
[DELTA-P1d] Dùng key structure đã verify (không có canonical trong hash)
để chứng minh/giả thiết kết quả, ghi rõ cách verify read-only.

Nếu test nào không thể chạy:
ghi rõ lý do, không tạo mock.

==================================================
14. KIỂM TRA TƯƠNG THÍCH HỆ THỐNG CŨ
==================================================

Audit compatibility với:

T05
T51g
T68
T71
T72
T79
T78
T94
T95
T110
T123
T126
BUG-025

Đặc biệt KHÔNG tạo resolver/cache thứ hai nếu hệ thống đã có resolver tương đương.
Phải xác định:

REUSE
hay
EXTEND
hay
REPLACE

và tại sao.

==================================================
15. OUTPUT BẮT BUỘC
==================================================

Trả report theo format:

# T176-PHASE0C AUDIT REPORT

## 1. VERDICT
PASS / PARTIAL / BLOCKED

## 2. REAL CALL CHAIN
UI → ... → final

## 3. DILA IDENTITY
A001984 / 靈祐

## 4. LOCAL VI
Current evidence

## 5. DISPLAY NAME
Current evidence

## 6. BUG-025 ROOT CAUSE

## 7. 22 DICTIONARIES
Actual list + lookup path

## 8. TTL/XML
Actual lookup/index path

## 9. TRANSLITERATION
Actual priority

## 10. LLM
Actual context + validation

## 11. CACHE
Actual key + stale-cache risk

## 12. EXISTING RESOLVERS
REUSE / EXTEND / REPLACE

## 12b. OVERLAP WITH T174/T166/T171   [GIỮ CHỐT CŨ — bắt buộc]
Đối chiếu phần audit này với:
- T174 (Phase 0 reuse-first + canonical guard) — phần trùng / phần DELTA
- T166 (CanonicalLock SPEC đã duyệt) — safety nào đã có sẵn, audit này chỉ verify
- T171 (alias/name chuẩn hóa) — minimal fix map vào đâu
Ghi rõ: OVERLAP (không làm lại) / DELTA (audit này thêm) / CONFLICT (mâu thuẫn, cần Admin).

## 13. HARD SAFETY GAPS
List only evidence-backed gaps

## 14. MANDATORY TEST RESULTS
TEST-01 ... TEST-07

## 14b. AMBIGUITY_RESULT   [GIỮ CHỐT CŨ — bắt buộc]
Liệt kê mọi điểm mơ hồ đã gặp (đặc biệt TEST-01 5 id của 靈祐,
"Linh Hựu" vs "Quy Sơn Linh Hựu", status vnpa alias_vi_suffix):
mỗi dòng = case · evidence · phương án resolve · REVIEW_REQUIRED hay không.

## 15. MINIMAL FIX DESIGN
Không code.
Chỉ architecture-level proposal.

## 16. REGRESSION TEST PLAN

## 17. FILES/FUNCTIONS/TABLES TO MODIFY
Chỉ nêu những gì đã xác minh thực tế.

## 18. RISK / SCOPE

## 19. FINAL
BUILD READY
hoặc
NOT BUILD READY

DỪNG TẠI ĐÂY.
Không build.
Không commit.
Không sửa DB.
Không sửa code.
```

---

## 4. Phases & Gates (T176)

| Gate | Nội dung |
|---|---|
| **G0** | Admin duyệt task này (docs-only, 0 code/0 DB/0 commit) |
| **G1** | Admin paste **§3** → Claude Code trả **T176-PHASE0C AUDIT REPORT** (19 + §12b + §14b) |
| **G2** | Admin review report → chốt `BUILD READY` / `NOT BUILD READY` |
| **G3** | Chỉ khi `BUILD READY` + lệnh `APPROVED FIX` → mở phase code (tách commit riêng từng bước, `npm run pipeline` trước mỗi commit) |

## 5. Revert

Docs-only session này: `git revert --no-edit <sha_T176>` (sha trong `docs/ROLLBACK.md`, hash-fill sau commit).

## 6. Session

`docs/sessions/2026-09-25_t176-phase0c-rev2-audit-plan.md`
