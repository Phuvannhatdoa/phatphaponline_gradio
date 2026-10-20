---
id: T166
title: "Canonical Identity Hard Guard — Zero-Tolerance LLM Proper-Name Protection"
module: Editorial / LLM Translation / Identity
priority: high
status: ready-for-dev
owner: claudecode
depends_on: [T73, T123, T158-glossary-resolver, T165]
created: 2026-09-24
updated: 2026-09-25
spec_path: docs/Mimo-Flash/T166-canonical-identity-guard-SPEC.md
task_path: docs/Mimo-Flash/T166-canonical-identity-guard.md
designed_by: mimo-flash (system-design skill)
handoff_to: Claude Code Agent
plan_approved_at: "2026-09-24 — Admin phê chuẩn Phương án A (layer trên T165)"
done_when: |
  CanonicalLock per-request từ authority thật (threshold mới LOCK);
  pre/post assert + invent detect; write-deny path identity;
  fail → identity_status additive, không verified/name_vi_final;
  matrix A–J pass; ghép T165 style_lock/constitution_hash;
  pipeline PASS; có revert.
---

# T166 — Canonical Identity Hard Guard (SPEC bàn giao Claude Code)

**Đọc file này 1 lần → build được.**  
Repo SSOT: `git rev-parse --show-toplevel` == `visjs-app` (không nested git trong daoanh).  
**Đã Admin approve Phương án A** (2026-09-24). Task: `docs/Mimo-Flash/T166-canonical-identity-guard.md`.

---

## 0. Nguyên tắc (không mặc cả)

Đây là **dịch kinh văn Phật học**. Sai 1 ký tự / 1 danh từ / 1 pháp danh / 1 địa danh / 1 thuật ngữ → sai nghĩa nguồn.

| Rule | Nội dung |
|------|----------|
| R1 | Canonical identity protection = **DETERMINISTIC** |
| R2 | LLM (Groq/Qwen) **KHÔNG** là authority identity |
| R3 | Fuzzy / LLM confidence **discover ≠ authorize** |
| R4 | Unknown **an toàn hơn** invented “trông như đúng” |
| R5 | Trust order không đảo: **Canonical authority > verified local > approved TM > rule-constrained LLM > raw LLM** |

Khớp skill §3.5 (DILA ID join key), §3.9 (chỉ dịch text), `docs/rules/naming-and-identity.md`, `data-integrity.md`.

---

## 1. Out of scope

| Không làm | Lý do |
|-----------|--------|
| T95 worker + `translation_segments` batch | Out scope T165 Phase B — T166 Phase B2 sau |
| Bảng persist `canonical_lock` | Lock = **in-memory per request** (Zero-RAM) |
| DROP / ghi đè RAW | Additive / read RAW only |
| Auto-merge entity theo tên | Cấm (naming-and-identity) |
| Suy luận identity bằng LLM | Chỉ dịch text |

---

## 2. Vocabulary map (bắt buộc — draft gốc dùng term không tồn tại)

| Draft [T158-CRITICAL-SAFETY-003] | Repo thật (verify 2026-09-24) |
|----------------------------------|-------------------------------|
| `GOLD` | **Không có.** Dùng: `translation_segments.quality_status='reviewed'` + `review_status='verified'` + optional `identity_pass=1`; cache: `status` + `identity_status` |
| `manual_verified` | **Chỉ** `passage_translation_alignment.alignment_type` (T94) — **không** đồng nhất identity gate |
| `REVIEW_REQUIRED` (translation) | Đang dùng cho **license** (`gate/`, claims). Translation → cột additive **`identity_status`** ∈ `null\|pass\|review_required\|failed\|conflict` |
| `approved translation memory` | `name_vi_final` / cache `edited` + `approved_by` human |
| `authority_source` | Table thật (§3) — không invent |
| `UNCONTROLLED_PROPER_NAME` | **Status lock mới** (không phải token text) — định nghĩa §4.1 |

Cache hiện trạng: `auto` 1752 · `edited` 6 · `draft` 2 · `invalidated` 1.  
Segments: `quality_status=unreviewed` (66) · `review_status=pending` (66).

---

## 3. CanonicalLock (per-request, in-memory)

```text
CanonicalLock entry:
  source_form          # Hán trong source (giữ exact)
  normalized_form      # NFC / strip space — KHÔNG aggressive normalize khác identity
  entity_type          # PERSON|DHARMA_NAME|PLACE|TEMPLE|DYNASTY|ERA|LINEAGE|BUDDHIST_TERM
  canonical_id         # DILA A009460 / PL… / NULL nếu pure glossary term
  canonical_value      # GIÁ TRỊ LOCK (VI) — vd "Đơn Hà Thiên Nhiên"
  authority_source     # table+column thật
  authority_level      # int; ≥ THRESHOLD → status=LOCKED
  status               # LOCKED | CANDIDATE | UNKNOWN_REVIEW | CONFLICT
  claims[]             # nếu conflict: giữ TẤT CẢ claims (không auto-pick)
```

### 3.1 Nguồn build lock (priority — deterministic, reuse resolver)

> **Đã sửa theo §20.3 (2026-09-25, Admin duyệt absorb SAFETY-003).** Giá trị cột khớp DB thật;
> **không có bảng priority thứ 2** — `build_canonical_lock` và `_glossary_resolver` cùng đọc
> hằng `SOURCE_PRIORITY` này (sửa luôn resolver P4/P6 chết — §20.2 #2/#8).

Ưu tiên cao → thấp (chỉ entry **đạt flag** mới `LOCKED`):

1. `canonical_decision` — **join** `places_dila`/`people` để lấy `name_zh` làm `source_form`
   (`entity_ref` là ID `PL000…`, không phải Hán — không join = nguồn chết)
2. `person_display_names` WHERE `verification_status LIKE 'verified%'` AND `is_preferred=1`
   (giá trị thật = `verified_direct`(6) / `verified_crosswalk`(2) — **không** có `'approved'`)
3. `vn_person_authority` WHERE `status='verified'`
4. `person_name_correction` WHERE `status='applied'`
   (giá trị thật = `applied`(2326)/`pending`(107) — **không** có `'approved'`)
5. `translation_glossary` WHERE `is_locked=1`
6. `name_vi_map` WHERE `name_vi_final IS NOT NULL` = authority · `approved_by NOT NULL` = boost.
   ⚠️ Ngưỡng hẹp (`final+approved`) chỉ **1 row** (`玄奘`) — đừng kỳ vọng nguồn này phổ biến
7. `namevi_map_places` WHERE `vn_name_status='reviewed'` (chỉ **2 row**) — **confidence → chỉ `CANDIDATE`**
8. `people.name_vi` **CHỈ** nếu provenance approved — **default: KHÔNG lock** `people.name_vi` đại trà
9. GLOSSARY term từ `translation_rules` terminology extract — `BUDDHIST_TERM` (không ghi đè person)

**Nguyên tắc lock (chốt — không mặc cả):**
- **Auto confidence → `CANDIDATE`, bất kể entity type.** `confidence>=0.8` **KHÔNG** lock
  (8079 row places sẽ bị máy tự chấm → false HARD_FAIL hàng loạt; §20.2 #4).
- `LOCKED` chỉ khi flag `verified / reviewed / applied / final+approved`.
- **Validate trước khi LOCK** (hàm chung `is_valid_vi(s)`): bỏ mọi giá trị chứa `?`/`�`/rỗng
  (mojibake `name_vi_map` 56 row · `canonical_decision` 2/2 row · places 2 row) → `UNKNOWN_REVIEW`,
  không đưa vào prompt lock section (§20.2 #3/#17).
- Config `identity_lock_policy` (mặc định **hẹp**, Admin đổi được) + dict **`SOURCE_LEVELS`**:
  `verified/applied/final+approved=1.0 · reviewed=0.9 · vn_person_authority verified=0.95 ·
  confidence auto (0.5–0.7) = 0.7 → CANDIDATE` (§20.2 #16 — cột chủ yếu là flag/string, không bịa level).

**Threshold:** flag hợp lệ + `is_valid_vi` + `SOURCE_LEVELS ≥ 1.0` (hoặc `reviewed/verified`) → **`LOCKED`**.
`name_vi_auto` / `auto_transliterate` / `local_translate` (conf 0.5–0.7) → **`CANDIDATE`**
(không LOCK, không HARD_FAIL khi LLM khác — vào hàng đợi `admin_namevi_queue` để human duyệt).

### 3.2 UNMATCHED_CJK
N-gram Hán từ source **không** match authority nào:
- Chỉ liệt kê **maximal Han run ≥2** (chuỗi Hán dài nhất, **không** n-gram chồng lấp 2–5 kiểu
  `_glossary_resolver` sinh ngram) — **cap ~40 run/prompt**; phần còn lại gộp **1 instruction chung**
  *"giữ nguyên Hán cho các tên chưa xác định"* (§20.2 #10 — cấm 400 unknown nổ prompt, đối mục tiêu
  T165 giảm `prompt_tokens`)
- entity_type theo evidence (context person / place…) nếu detect được → else `UNKNOWN_REVIEW`
- **Không** hỏi LLM “phát minh” tên VI chuẩn

### 3.3 CONFLICT
Nhiều nguồn ≥2 giá trị VI khác nhau cho cùng `source_form`+entity class  
→ status=`CONFLICT`, giữ `claims[]`, route HITL (`canonical_decision` / `conflict_pending` pattern).  
**Cấm:** chọn theo Qwen, frequency, string-similarity một mình, thứ tự source tùy tiện.

### 3.4 Alias + `allowed_vi_set` (bắt buộc — sửa P0 #6)
Cùng 1 entity có nhiều dạng Hán (`people(A009460).name_zh='天然'` vs `vn_person_authority='丹霞天然'`):

- Lock build **gom mọi alias**: `people.name_zh` · `display_name_zh` · `vn_person_authority.name_zh` ·
  `person_name_correction.name_zh` · `name_vi_map.name_zh`.
- `allowed_vi_set(entity)` = **mọi biến thể VI đã biết** của entity đó; `CANONICAL_INVENTION` chỉ khi
  output ≠ **tất cả** biến thể của entity liên quan (không so với 1 giá trị duy nhất).
- `UNKNOWN_REVIEW` (cảnh báo, chưa resolve) **không đồng nghĩa** `failed` (hard) — không gắn cờ
  `failed` cho token chưa phân loại.
- Match theo **maximal Han run** (không `entry.source_form in source_text` kiểu substring) —
  tránh term ngắn nằm trong từ ghép bị require sai chỗ (§20.2 #13).

---

## 4. Policy unknown — chốt **P-PARTIAL** (đã approve)

| | P-PARTIAL (mặc định) | P-STOP (Admin flag) |
|--|----------------------|---------------------|
| Unknown / CONFLICT / invent | **Vẫn call LLM** nhưng unknown token **giữ Hán** trong contract; **không** auto-accept thành identity/trusted | **Không call LLM** → response `{ok:false, error_code:'REVIEW_REQUIRED'}` |
| Mâu thuẫn draft §4 vs §6 | Sửa thành: **cấm auto-accept + cấm trusted cache**, không nhất thiết cấm call | Dùng cho strict batch |

Response luôn kèm `identity_status` + `identity_issues[]`.

### 4.1 `UNCONTROLLED_PROPER_NAME` (absorb SAFETY-003 — P0-4)

| Loại token | Mã | Hành vi |
|------------|-----|---------|
| N-gram **khớp nguồn authority** nhưng **chưa gán status** (lỗi phân loại lock) | `UNCONTROLLED_PROPER_NAME` | **STOP** = bug → `review_required` (không để lọt qua policy) |
| N-gram **không authority** đã gán `UNKNOWN_REVIEW` | `UNKNOWN_REVIEW` | **P-PARTIAL: vẫn dịch** + giữ Hán cho tên riêng + flag (không invent identity) |
| Khác (mâu thuẫn 2 nguồn) | `CONFLICT` | Theo bảng trên — giữ `claims[]` |

→ **P-PARTIAL được giữ nguyên** (Admin chốt 2026-09-25): STOP chỉ áp cho token **bị phát hiện nhưng
chưa phân loại** (`UNCONTROLLED_PROPER_NAME` = bug phân loại, không phải unknown thật).

---

## 5. Pre-LLM Hard Guard

Trước `_t73_call_gemini` / mọi luồng interactive (bio, place, passage legacy, context):

```text
1. lock = build_canonical_lock(conn, source_text)   # §3 — Zero-RAM, SQL batch
2. inject prompt section:
    === LOCKED CANONICAL CONTEXT (BẮT BUỘC, KHÔNG ĐỔI) ===
    丹霞天然 → Đơn Hà Thiên Nhiên  [PERSON A009460]  authority=vn_person_authority.status=verified
    === CANDIDATE (đề xuất máy, CHỈ ĐỀ XUẤT — không bắt buộc) ===
    安廩 → (auto_transliterate 0.7, final=NULL)  [PERSON A005248]
    === UNKNOWN / REVIEW (GIỮ HÁN, KHÔNG SÁNG TÁC) ===
    <unknown ngrams>
   === LLM-CANDIDATE CONTEXT ===   # phần còn lại — chỉ dịch nghĩa
3. pre_assert(lock, policy):
   - mọi entry LOCKED đã vào prompt lock section
   - mọi UNMATCHED/CONFLICT xử lý theo policy P-PARTIAL|P-STOP
   - fail → return REVIEW_REQUIRED (strict) hoặc continue draft (partial)
```

Prompt wording: lock = **constraint**, không “suggestion/hint/example”.

**Deterministic detection:** dùng n-gram + exact authority match (như `_glossary_resolver`) — **không** “LLM tự nhận proper name”.

---

## 6. Post-LLM Hard Assertion

```text
issues = []   # severity: HARD (failed) vs WARNING (không hạ identity_status)
for entry in lock where status==LOCKED and match_by_maximal_han_run(output, entry.source_form):
    if not normalize_contains(output, entry.canonical_value, honorifics):
        if entry.entity_type in (PERSON,PLACE,DHARMA_NAME) or (TERM and len(entry.source_form)>=2):
            issues.append(HARD: CANONICAL_IDENTITY_MISMATCH)
        else:
            issues.append(WARN: TERM_LEN1_MISMATCH)   # term 1-char: warning (§20.2 #11)
for token in extract_personlike_vi(output):   # "Thích X" / X大师-style VI
    if not position_is_title(token) or token in allowlist_from_tu_thuong:
        continue                               # "tôi thích trà" → 0 issue (§20.2 #12)
    if token not in lock.allowed_vi_set(entity_of(token)) and token not in allowed_common:
        issues.append(HARD: CANONICAL_INVENTION)

if any HARD issues:
    identity_status = failed | conflict
elif any WARN issues:
    identity_status = review_required           # vẫn đọc được, không trusted
    # KHÔNG ghi name_vi_final / glossary LOCKED / rules active / people.name_vi
    # cache: vẫn lưu + serve DRAFT nhưng identity_status != pass (§8)
    # segments: KHÔNG auto quality_status=reviewed
```

### 6.1 Normalize compare (bắt buộc)
- Strip honorific/title theo rules `HONORIFIC_*`, `BUDDHIST_TITLES`: `Thích|Thích Ca|ngài|Hòa Thượng|Thiền Sư|…`
  (gộp cụm nhiều từ: `"Thích Đơn Hà Thiên Nhiên"` → so `"Đơn Hà Thiên Nhiên"`; strip space + dấu câu)
- NFC + casefold; **không** strip ký tự Hán-Việt khác identity; **không** đổi `canonical_value` (chỉ đổi span so sánh)
- So `canonical_value` vs **maximal Han run / span** trong output (exact after normalize)
- ⚠️ **Cấm so khớp raw `output != canonical_value`** → `"Thích An Lẫm"` vs `An Lẫm` sẽ FAIL oan
  (so khớp sau strip title = **PASS**). Unit test bắt buộc: `Thích An Lẫm → PASS · Thích An Nạp → FAIL`.

### 6.2 Cấm auto-correct theo LLM
- **Được:** post-edit deterministic theo lock/glossary đã biết (`_post_edit_hanzi_leakage` pattern T159)
- **Cấm:** “LLM suggest better name → tự sửa people.name_vi”

### 6.3 Ví dụ mandatory (§9 draft)

> **Fixture chuẩn (Admin chốt 2026-09-25 — absorb SAFETY-003):** LOCKED = **`A009460 丹霞天然 →
> Đơn Hà Thiên Nhiên`** (`vn_person_authority.status='verified'`) · PLACE = **`少林寺`** (trong 2 row
> `vn_name_status='reviewed'` thật) · TERM = glossary `is_locked=1` ≥2 ký tự.
> **安廩 = CANDIDATE** (auto_transliterate 0.7, final=NULL, 0 row authority) → **không** HARD_FAIL.
> `source_text` = câu mẫu **tự viết** (bio A005248 không chứa chữ `安廩`).

| Input | Local authority | Qwen out | Expect |
|-------|-----------------|----------|--------|
| 丹霞天然 | **A009460 LOCK `Đơn Hà Thiên Nhiên`** (vnpa verified) | `Thích Đơn Hà Mật` | **HARD_FAIL** `CANONICAL_IDENTITY_MISMATCH` → `failed` → REVIEW |
| 丹霞天然 | same | `Thích Đơn Hà Thiên Nhiên` | **PASS** (title strip §6.1) |
| 安廩 | A005248 **auto 0.7 → CANDIDATE** (final=NULL) | `Thích An Lẫm` | **PASS** (không hard-fail; vào hàng đợi `admin_namevi_queue`) |
| 安廩 | same | invent tên mới hoàn toàn | flag `CANONICAL_INVENTION` **cảnh báo** → draft only, không auto identity |
| unknown 2-char | no authority | invent VI name | `REVIEW_REQUIRED` — không auto identity |

---

## 7. LLM output ≠ identity update (write-deny inventory)

**Cấm path từ LLM draft tự ghi thành canonical:**

| Target | Path code (verify lại line khi build) | Cho phép |
|--------|----------------------------------------|----------|
| `people.name_vi` | `UPDATE people SET name_vi` (~app 13066, 17318) | **Chỉ** ETL/HITL admin — **không** từ parse JSON translate |
| `name_vi_final` / `approved_by` | admin accept `namevimap` / `name_vi_map` | **Chỉ** human |
| `name_vi_auto` | auto_suggest / local_translate | OK **như suggestion** (`CANDIDATE`), confidence ≤0.7, **không** auto-LOCK |
| `translation_glossary` LOCKED | **không** INSERT từ LLM output | seed/admin only |
| `translation_rules` active | `_save_suggested_rules` → **`status='pending'` only** | approve HITL |
| `canonical_decision` | `_persist_canonical_decision` | **Chỉ** admin decision |
| `people.bio_vi` / cache `translated_text` | translate draft / admin edit | Draft OK; **không** derive identity từ bio |
| `translation_segments` → reviewed | `POST …/translation/verify` human | **Chỉ** human + identity_pass |

Implement: decorator/helper `assert_not_identity_autowrite()` hoặc audit grep test trong CI test.

**7.1 Auth chặn “đúc” nguồn LOCK (P1-15):** endpoint ghi `name_vi_final + approved_by`
(`/daoanh/api/admin/namevi-map/update`, `admin_namevi_map_update`) **thiếu `verify_session`**
(khác `api_admin_save_person_name_vi` có check) → **bắt buộc `verify_session`** + audit auth toàn
bộ endpoint ghi authority. CI grep mở rộng endpoint này.

**7.2 `name_vi_auto` carve-out + hiển thị (Admin 2026-09-25 chốt A+C):**
- **A (keep):** `name_vi_auto` = **suggestion** (guồn: `admin_namevi_suggest` auto_suggest conf 0.7 ·
  `admin_namevi_translate_local` conf 0.5 · ETL `auto_transliterate` **41.507 row**, 41.506 row final=NULL)
  → **không lock, không prompt lock section** (§3.1 #6/#7), không ghi `name_vi_final` — chỉ vào
  hàng đợi **`admin_namevi_queue`** human duyệt. **Không cấm** `name_vi_auto` (cấm sẽ làm chết
  queue + search; 41.507 row ETL).
- **C (display):** `api_name_vi_lookup` (`app.py` ~`api_name_vi_lookup`/fallback `name_vi_final or
  name_vi_auto or name_vi`) trả thêm cờ **`name_vi_source ∈ final|people|auto`** để UI gắn nhãn
  *"máy đề xuất"* (không đổi giá trị trả về → ít rủi ro). Mirror `admin/app.py` cùng sửa.
  **Dev task → Claude Code** (md-only session này không sửa code).

---

## 8. Cache safety

1. Lookup HIT **không** coi `identity_status IN ('failed','conflict','review_required')` là trusted HIT cho UI “duyệt chuẩn”.
   - **Trusted read** = `identity_status IS NULL OR identity_status='pass'` (NULL = legacy, không đoán lịch sử).
2. Retry từ cache **không** bypass lock (re-run post-assert nếu policy lock đổi).
3. **Chốt vòng lặp (P1-14):** row `failed/conflict/review_required` **vẫn serve như DRAFT**
   (kèm `identity_status` + cờ UI “chưa duyệt”, **không** trusted) — **không** tự re-LLM mỗi request
   (tránh lặp vô hạn + chi phí TPM); chỉ re-run khi admin bấm “Dịch lại” (force).
4. **Cấm dùng `cache.status` làm cờ failed.** Enum thật của `translation_cache.status` =
   `auto`(1752) · `edited`(6) · `draft`(2) · `invalidated`(1) — **không** có `REVIEW`/`FAILED`;
   và `draft` **đang được serve** (reader chỉ lọc `status!='invalidated'`, **0 site** lọc `draft`).
   → cờ identity dùng cột **riêng** `identity_status`, không lồng vào `status`.
5. Migration additive (P3):

```sql
ALTER TABLE translation_cache ADD COLUMN identity_status TEXT;  -- NULL = pass legacy
-- optional: identity_issues TEXT (JSON), identity_lock_hash TEXT
CREATE INDEX IF NOT EXISTS idx_tc_identity ON translation_cache(identity_status);
-- giá trị: pass | review_required | failed | conflict  (NULL = legacy — KHÔNG đoán lại)
```

- `--dry-run` / backup `data/backups/lineage_t166_*.db` / `--revert`
- Không DROP; row cũ `identity_status=NULL` = legacy (không fail cứng retroactive)

---

## 9. Ghép T165

```text
style_lock (T165):
  rules ⊕ glossary ⊕ exemplar ⊕ **canonical_lock fingerprint**
constitution_hash = sha16(parts + PROMPT_FORMAT_VERSION + lock_hash)
```

- Lock đổi → hash đổi → cache miss (đúng “không reuse bản dịch với lock cũ”).
- T166 build **sau** hoặc **cùng** module `style_constitution.py` — **không** 2 lock rời.
- ⚠️ **Mass-miss khi bật fingerprint (P2-18):** thay đổi wording prompt lock section =
  đổi `PROMPT_FORMAT_VERSION` (T165) → `constitution_hash` đổi → ước tính **toàn bộ cache 1761 row**
  miss 1 lần. Bật **từ từ theo `source_type`** (pilot ≤5 như T165 Phase 7) + đo `prompt_tokens`
  (`log_prompt_metrics`), xem T165 §14.2 #12. **Không** bật mass-miss trước khi đo baseline.

---

## 10. Entity types (minimum)

`PERSON · DHARMA_NAME · PLACE · TEMPLE · DYNASTY · ERA · LINEAGE · BUDDHIST_TERM`  
**Không** assume mọi noun Hán = proper name → evidence-driven (n-gram match authority).

---

## 11. Fuzzy rule

- Fuzzy **mày mò candidate** → UI research / conflict pool  
- Fuzzy **không bao giờ** set `status=LOCKED`  
- Không aggressive normalize làm mất distinction identity

---

## 12. No LLM confidence bypass

`confidence=0.99` từ model **không** override `canonical_decision` / verified local / approved TM.  
Không code path: `if llm_confidence > authority: use llm`.

---

## 13. “GOLD gate” → map thực

| Điều kiện | Hành vi |
|-----------|---------|
| `identity_status=pass` | Cho phép flow verify human bình thường |
| mismatch / conflict / unknown / invention | **Không** auto `quality_status=reviewed` · **Không** `name_vi_final` · **Không** glossary LOCK · **Không** rules active |

Không tồn tại thuật ngữ `GOLD` trong DB — **không** tạo enum `GOLD`除非 Admin yêu cầu add UI badge riêng.

---

## 14. Test matrix (P5 — DB copy, không prod write)

| # | Case | EXPECT |
|---|------|--------|
| A | Known person lock đúng → out đúng (sau strip title) | PASS `identity_status=pass` |
| B | Known person → đổi tên | HARD_FAIL mismatch |
| C | Known place → đổi tên | HARD_FAIL |
| D | Known dharma name → đổi | HARD_FAIL |
| E | Unknown person → invent VI | REVIEW_REQUIRED / invention |
| F | DILA/SQL/TTL conflict values | CONFLICT — 0 auto-pick |
| G | Locked Buddhist term giữ đúng | PASS |
| H | Locked term bị đổi | HARD_FAIL |
| I | “High conf” nhưng mismatch | HARD_FAIL (conf không bypass) |
| J | Retry cache failed draft | Không bypass lock |

Fixture (**Admin chốt 2026-09-25**): **A009460 丹霞天然 → `Đơn Hà Thiên Nhiên`** (LOCK,
`vn_person_authority status='verified'`, DB thật); out `Thích Đơn Hà Mật` → FAIL (B) ·
`Thích Đơn Hà Thiên Nhiên` → PASS (A). Hàng CANDIDATE: **A005248 安廩** (auto 0.7) → invent →
cảnh báo không hard-fail. `source_text` = câu mẫu tự viết (bio A005248 không chứa `安廩`;
A005248 có cache row `status='edited'` id 1768 → chạy trên **DB copy**).

---

## 15. Acceptance

1. **Không tồn tại executable path** mà LLM sinh tên canonical mới **tự** thành `name_vi_final` / glossary LOCK / rules active / `people.name_vi` **chỉ vì model output**.  
2. Matrix 14 PASS.  
3. P-PARTIAL: unknown vẫn dịch được passage, output flag `identity_status`, không trusted auto.  
4. `npm run pipeline` PASS.  
5. Session log + `docs/db_schema.md` + revert path đầy đủ.  
6. Admin QA ×1 trên case LOCK (`丹霞天然` sai tên → FAIL) + case CANDIDATE (`安廩`) + 1 unknown token.

---

## 16. Trust order (final)

```text
CANONICAL AUTHORITY
  > VERIFIED LOCAL EVIDENCE
  > APPROVED TRANSLATION MEMORY
  > RULE-CONSTRAINED LLM
  > LLM INFERENCE
```

**Never reverse.**

---

## 17. Phases build

| Phase | Việc | Output |
|-------|------|--------|
| 0 | (đã) Audit draft vs repo — file này | SPEC + task T166 |
| 1 | `canonical_lock.py` build/assert/normalize | unit test A–D |
| 2 | Wire pre/post vào interactive translate + admin/app.py mirror | py_compile |
| 3 | Write-deny audit + optional `identity_status` migrate | script + db_schema |
| 4 | Matrix A–J + pipeline | tests green |
| 5 | Dashboard regen + Admin confirm | tasktodo → taskdone |

**Commit:** `feat: T166 canonical identity guard + docs`  
**Revert:** `git revert --no-edit <sha>` + migrate `--revert` + backup path.

**Coverage bắt buộc (absorb SAFETY-003):** 3 đường dịch — ① `app.py` interactive
(`api_person_dila_translate`/bio/place) · ② `scripts/cbeta_translate_worker.py` batch
(STOP = item → `review_required` + `job.last_error`, **không** exception treo job) ·
③ mirror `admin/app.py`. Zero-RAM: lock build = SQL `IN (…)` theo maximal Han run (không load bảng lớn).

---

## 18. File I/O

| Loại | Path |
|------|------|
| SPEC | `docs/Mimo-Flash/T166-canonical-identity-guard-SPEC.md` |
| Task | `docs/Mimo-Flash/T166-canonical-identity-guard.md` |
| Đọc | `app.py`, `_glossary_resolver`, `canonical_decision`, `person_display_names`, `docs/rules/*`, T165 SPEC |
| Ghi mới | `canonical_lock.py` / extend `style_constitution.py`, `scripts/t166_identity_migrate.py`, `tests/test_t166_*.py`, session log |
| Sửa | `app.py`, `admin/app.py`, `docs/db_schema.md`, `docs/tasktodo.md` |
| Không sửa | T95 worker, RAW tables, `glossary_vi` bulk |

---

## 19. Quick start Claude Code

```bash
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
# Đọc: docs/Mimo-Flash/T166-canonical-identity-guard.md + file này + T165 SPEC (ghép lock)
# Build P1–P4; fixture A009460 丹霞天然 (LOCK) + A005248 安廩 (CANDIDATE); npm run pipeline
# Commit toplevel visjs-app: feat: T166 canonical identity guard + docs
```

**Filename bàn giao:**  
`docs/Mimo-Flash/T166-canonical-identity-guard-SPEC.md`

---

## 20. REVIEW 2026-09-25 — Đối chiếu SPEC ↔ DB/code thật + Đề xuất chỉnh sửa

> Audit read-only trên `data/lineage.db` (RO) + `app.py`/`admin/app.py`.
> **Không sửa code** — đây là đề xuất để Admin/owner SPEC chốt trước khi build Phase 1.
> Mức độ: **P0** = build theo SPEC hiện tại sẽ 0 row lock / test không chạy được / sai logic · **P1** = false-fail hàng loạt hoặc lặp vô hạn · **P2** = lệch nhỏ.

### 20.1 Những gì SPEC ghi ĐÚNG (đã verify)

| Mục | Kết quả |
|-----|---------|
| §2 số liệu cache | `auto` **1752** · `edited` **6** · `draft` **2** · `invalidated` **1** ✓ |
| §2 segments | 66 row = `quality_status='unreviewed'` + `review_status='pending'` ✓ |
| Bảng §3.1 tồn tại | `canonical_decision`(2) · `person_display_names`(8) · `vn_person_authority`(1074) · `person_name_correction`(2433) · `translation_glossary`(79 locked) · `name_vi_map`(46711) · `namevi_map_places`(118296) · `people`(48673) · `passage_translation_alignment`(11, `alignment_type` ✓) ✓ |
| §2 `REVIEW_REQUIRED` đang dùng cho license | grep: `REVIEW_REQUIRED` là license/gate code — đúng như SPEC §2 nói ✓ |
| §7 write-deny đường ghi `people.name_vi` | chỉ **2 site**: app.py:**13066** (`admin_namevi_map_update`) + **17318** (`api_admin_save_person_name_vi`, có `verify_session`) — **không** path translate nào ghi `name_vi` ✓ |
| §7 `_save_suggested_rules` | `status='pending'` (app.py:16804, 17164) ✓ · `_post_edit_hanzi_leakage` app.py:16888 ✓ |
| §14/§15 vocabulary map | `identity_status` **chưa có** trong `translation_cache` → ALTER ADD là additive thật ✓ |
| Fixture A005248 tồn tại | `people(A005248, 安廩, An Lẫm)` ✓ |

### 20.2 Vấn đề + Đề xuất chỉnh sửa

| # | Mức | Vấn đề (SPEC nói gì / Thực tế gì) | Bằng chứng | Đề xuất chỉnh sửa SPEC |
|---|-----|-------------------------------------|------------|--------------------------|
| **1** | **P0** | §3.1 **#2 sai giá trị cột** → `WHERE verification_status IN ('verified','approved')` khớp **0/8 row**. | `person_display_names.verification_status` ∈ `verified_direct`(6), `verified_crosswalk`(2). | Sửa thành `verification_status LIKE 'verified%' AND is_preferred=1` (đồng bộ với resolver Priority 2, app.py:16374). |
| **2** | **P0** | §3.1 **#4 sai giá trị cột** → `status='approved'` khớp **0 row**. Bug này **copy từ resolver cũng đang chết**. | `person_name_correction.status` ∈ `applied`(2326), `pending`(107). resolver app.py:16390 `AND status='approved'` → nguồn Priority 6 **chưa từng trả kết quả**. | Sửa **cả 2 chỗ** thành `status='applied'` (SPEC §3.1 + `_glossary_resolver` Priority 6) → 2326 row `name_zh` dùng được. |
| **3** | **P0** | §3.1 **#1 không build được lock**: `canonical_decision.entity_ref` là **ID** không phải Hán tự → không tạo được `source_form`; và **cả 2 row đều mojibake**. | row1 `('PL000000000314','Th? S?t H?i')` · row2 `('PL000000000001','Kho?t T?t ?a Qu?c')` — có `?` thay ký tự. | (a) join `places_dila`/`people` để lấy `name_zh` làm `source_form`; (b) **validate `canonical_value` trước khi LOCK**: chứa `?`/`�`/rỗng → bỏ, ghi `CONFLICT`/`UNKNOWN_REVIEW`, **không** đưa vào prompt lock section (không lock mojibake). |
| **4** | **P0** | **Chuẩn lock không nhất quán giữa người/địa danh** — §3.1 #7 cho `confidence>=0.8` **LOCK**, nhưng #8 lại cấm auto 0.5–0.7 lock người. 8079 row places sẽ bị LOCK từ **máy tự chấm confidence** → mâu thuẫn R3/R5 + false HARD_FAIL hàng loạt cho place. | `count(confidence>=0.8 AND !needs_review)` = **8079**; `vn_name_status='reviewed'` chỉ **2 row**. | Chốt nguyên tắc: **auto confidence → chỉ `CANDIDATE`, bất kể entity type**; `LOCKED` chỉ khi flag `verified/reviewed/applied/final+approved`. Nếu Admin muốn rộng → thêm config `identity_lock_policy` (mặc định hẹp), ghi vào §3.1. |
| **5** | **P0** | **Fixture A005248 không thể LOCK** → §6.3 hàng 1 ("A005248 lock `An Lẫm` (verified)") và Acceptance 6 **không chạy được**. | Truy vấn toàn bộ nguồn #1–#8 cho A005248: person_display_names **0** · vn_person_authority **0** · person_name_correction **0** · canonical_decision **0** · name_vi_map row `('安廩','An Lẫm',final=NULL,approved=NULL,confidence=0.7)` → theo threshold = **CANDIDATE** · people.name_vi = `An Lẫm` nhưng #8 **mặc định không lock**. | (a) Đổi fixture LOCKED sang **`A009460 丹霞天然 → Đơn Hà Thiên Nhiên`** (vn_person_authority `status='verified'`) hoặc **`玄奘 → Huyền Trang`** (name_vi_map final+approved, nguồn duy nhất); (b) A005248 giữ làm **case CANDIDATE** (matrix hàng 3); (c) **lưu ý: bio của A005248 không chứa chữ `安廩`** → fixture phải là `source_text` mẫu tự viết, không lấy bio thật; A005248 còn có row cache `status='edited'` (id 1768) → test trên DB copy. |
| **6** | **P0** | **Alias/short-form → `CANONICAL_INVENTION` giả.** Cùng 1 người có nhiều dạng Hán; lock match `source_form` exact → nguồn không match → LLM dịch **đúng** nhưng token không nằm `lock.VI_set` → báo invention. | `people(A009460).name_zh = '天然'` nhưng `vn_person_authority` = `'丹霞天然'`; `person_display_names` nhiều row `display_name_zh = NULL` (chỉ có `display_name_vi`). | §3 bổ sung: (a) lock build gom **mọi alias** từ `people.name_zh`, `display_name_zh`/`authority_name_zh`, `vn_person_authority.name_zh`, `person_name_correction.name_zh`, `name_vi_map.name_zh`; (b) `allowed_vi_set` theo **entity** = mọi biến thể VI đã biết; `CANONICAL_INVENTION` chỉ khi output ≠ **tất cả** biến thể của entity liên quan; (c) `UNKNOWN_REVIEW` (cảnh báo) ≠ `failed` (hard) — tránh gắn cờ failed cho token chưa resolve. |
| **7** | **P0** | **§3.1 thứ tự nguồn ≠ `_glossary_resolver` (14 priority)** → cùng 1 Hán tự có thể bị 2 hệ lock 2 giá trị VI khác nhau → prompt tự mâu thuẫn + post-assert false HARD_FAIL. | Resolver: `glossary#1 · person_display_names#2 · vnpa#3 · canonical_decision#4 · name_vi_map#5 · pnc#6 · places#9`<br>§3.1: `canonical_decision#1 · pdn#2 · vnpa#3 · pnc#4 · glossary#5 · name_vi_map#6 · places#7` | **Chốt 1 `SOURCE_PRIORITY` duy nhất** (module chung) — `build_canonical_lock` và `_glossary_resolver` cùng đọc; resolver output = **input** của lock (lock không tự tra bảng lần 2). Ghi vào §3.1: *"không có bảng priority thứ 2"*. |
| **8** | **P1** | Resolver Priority 4 **chết**: `canonical_decision WHERE entity_ref IN (ngram Hán)` — `entity_ref` là `PL000…` ASCII, không bao giờ match Hán. | app.py:16381–16383 | Sửa resolver (join lấy name_zh) khi build T166, ghi vào §7/§18 "Sửa". |
| **9** | **P1** | §3.1 **#6 gần như nguồn chết**: `name_vi_final IS NOT NULL AND approved_by NOT NULL` = **1 row**; trong khi resolver P5 dùng `name_vi_final IS NOT NULL` = **5205 row** → 2 ngưỡng khác nhau trên cùng bảng. | `count`=1 (玄奘) vs `count`=5205 | Chốt lại ngưỡng: `name_vi_final NOT NULL` = authority (level theo `confidence`), `approved_by NOT NULL` = boost thêm. Hoặc giữ ngưỡng hẹp nhưng **ghi rõ "nguồn này chỉ 1 row, đừng kỳ vọng"**. |
| **10** | **P1** | §3.2 **UNMATCHED_CJK nổ prompt**: n-gram 2–5 ký tự mọi run Hán (giới hạn 400 như resolver) → passage 500 chữ Hán có thể list ~400 "unknown" → **đối lập trực tiếp Mục tiêu T165 giảm `prompt_tokens`**. | `_glossary_resolver` sinh ngram 2–5, `max_ngrams=400` (app.py:16340–16357) | §3.2 đổi: chỉ list **maximal unmatched Han runs ≥2** (không chồng lấp), **cap ~40**, còn lại gộp 1 instruction chung *"giữ nguyên Hán cho các tên chưa xác định"*. Không list ngram chồng lấp. |
| **11** | **P1** | §6 post-assert **hard-fail trên term 1-char** của glossary locked → false `CANONICAL_IDENTITY_MISMATCH`. | 14/79 locked term 1-char: 法僧戒定慧因果緣性相經律論鉢 (`法→pháp`, `經→kinh`…) | Tách severity: `HARD_FAIL` chỉ cho `PERSON/PLACE/DHARMA_NAME/BUDDHIST_TERM ≥2 chars`; term 1-char → `warning` (không hạ `identity_status` xuống `failed`). |
| **12** | **P1** | §6 `extract_personlike_vi` **false positive**: `Thích` là từ thường tiếng Việt ("tôi thích…") → `CANONICAL_INVENTION` giả. | rule HONORIFIC/BUDDHIST_TITLES có `Thích` (app.py `_NON_HANVIET_NAME_WORDS`, T123 rules) | §6.2 bổ sung: case-sensitive `"Thích "` + phải ở **vị trí title** (đầu câu/sau dấu phẩy) + allowlist từ thường; thêm unit test case `"Tôi thích uống trà"` → **0 issue**. |
| **13** | **P1** | §6 `entry.source_form in source_text` = **substring** → term ngắn nằm trong từ ghép → require `canonical_value` sai chỗ → false fail. | glossary có term 1-char; resolver sinh ngram 2–5 chồng lấp | Match theo **maximal Han run** (khớp chuỗi Hán dài nhất chứa entry), không `in` tùy ý. |
| **14** | **P1** | **Vòng lặp cache chưa chốt** (§8): nếu lookup coi `identity_status IN ('failed',…)` là miss → mỗi request lại gọi LLM → chi phí/TPM tăng vô hạn; nếu là hit → "trusted HIT" lại bị §8.1 cấm. SPEC mâu thuẫn giữa §8.1 và §8.2. | §8.1 vs §8.2 | Chốt: **draft vẫn serve** (kèm `identity_status` + cờ UI "chưa duyệt", không trusted), **không** tự re-LLM; chỉ re-run khi admin bấm "Dịch lại" (force). Ghi rõ trong §8. |
| **15** | **P1** | §7 write-deny nguồn tạo authority `name_vi_final`+`approved_by='admin'` là endpoint **không kiểm tra phiên đăng nhập** → ai cũng có thể "đúc" nguồn LOCK. | `admin_namevi_map_update` app.py:**13024** — không có `verify_session` (khác hẳn `api_admin_save_person_name_vi` 17187 có check) | §7 thêm mục: **bắt buộc `verify_session` ở `/daoanh/api/admin/namevi-map/update`** (P0 kèm audit auth toàn bộ endpoint ghi authority) + CI grep test `assert_not_identity_autowrite` mở rộng sang endpoint này. |
| **16** | **P1** | §3 `authority_level >= 0.8` **không có bảng ánh xạ** — các nguồn chủ yếu là flag/ chuỗi: `canonical_decision.authority_rank` = `'admin_approved'`/`'auto_transliterate'` (string), `confidence` = 0.7/1.0 float → implementer phải bịa level. | schema `canonical_decision.authority_rank TEXT`, `confidence REAL` | §3.1 thêm dict `SOURCE_LEVELS` (vd: verified/applied/final+approved=1.0 · reviewed=0.9 · vnpa verified=0.95 · confidence place=0.7 → CANDIDATE) + ghi *"Admin sửa được, mặc định như sau"*. |
| **17** | **P2** | `name_vi_map.name_vi_final` có **56 row mojibake** (chứa `?`), places `>=0.8` có 2 row → cùng cần validate như #3. | mojibake scan | Gộp vào 1 hàm `is_valid_vi(s)` dùng cho **mọi** nguồn trước khi LOCK. |
| **18** | **P2** | §9 ghép T165: khi `t166_lock_fingerprint` đổi → `constitution_hash` đổi → **mass-miss toàn bộ cache** (1761 row) chưa được cảnh báo chi phí. | T165 §3/§9 | §9 thêm: kích hoạt fingerprint = mass-miss dự kiến; bật từ từ theo source_type + đo `prompt_tokens` (xem T165 §14.2 #12). |

### 20.3 Thứ tự sửa SPEC trước khi build

1. **Sửa §3.1 nguồn lock**: #1 entity_ref→join+validate mojibake · #2 `LIKE 'verified%'` · #4 `'applied'` · #7 chỉ `reviewed`/flag (confidence → CANDIDATE) · #6 chốt ngưỡng · thêm `SOURCE_LEVELS` → #1 #2 #3 #4 #7 #9 #16.
2. **Chốt 1 `SOURCE_PRIORITY` chung** với `_glossary_resolver` (sửa resolver P4/P6) → #7 #8.
3. **Đổi fixture** sang `A009460`/`玄奘`; A005248 = case CANDIDATE; source_text tự viết → #5.
4. **§3 bổ sung alias + `allowed_vi_set`**, tách severity UNKNOWN vs failed → #6 #11 #13.
5. **§3.2 cap unknown n-grams** · **§6 title-position rule** · **§8 chốt vòng lặp cache** → #10 #12 #14.
6. **§7 thêm auth check `admin_namevi_map_update`** → #15.

**Chưa sửa §3.1 (các giá trị cột sai) + §6.3 fixture = Phase 1 `canonical_lock.py` sẽ build ra nguồn rỗng → matrix A–J không có ý nghĩa.**

---

## 21. ABSORB T168 §10/§11/§15 (Canonical Entity Safety + Unknown Term + GOLD) — Admin duyệt 2026-09-25

> Nguồn: `docs/Mimo-Flash/T168-rule-resolver-context-compiler-PLAN.md` (review directive `[T158-DEBUG-001]`).
> **Không có gì mới cho T166** — chỉ xác nhận 3 điều khoản của directive thuộc sở hữu SPEC này:

| Directive § | Khớp T166 ở đâu | Ghi chú |
|-------------|------------------|---------|
| §10 Canonical entity safety (AI không được tạo identity; không có verified vi → REVIEW) | §3 CanonicalLock · post-LLM in-lock assert · write-deny | đúng chủ đề; directive cấm "silently choose canonical" = T166 zero-tolerance |
| §11 Unknown term/entity → REVIEW · suggestion = candidate/pending, KHÔNG active/GOLD | §3 policy **P-PARTIAL** · lifecycle `pending` (code thật app.py:16804) | **không** dùng mã `RULE-011…015` (0 row trong DB — xem T168 P0-2) |
| §15 Chỉ human tạo L3 GOLD · tôn trọng T94 `manual_verified` | §5 write-deny + T94 admin/app.py:18193 | không auto-promote |

**Ảnh hưởng acceptance:** test T168 Phase 6 (5 case data thật, gồm case unknown) **phải chạy
qua** matrix A–J của T166; fixture chuẩn = `A009460 丹霞天然` (đã ghi ở §20.3).

---

## 22. ABSORB `[T158-CRITICAL-SAFETY-003]` — Canonical Identity Hard Guard (Admin duyệt 2026-09-25)

> **Bản chất: 100% thuộc sở hữu SPEC này** — không tạo task mới, không tạo ID mới
> (T158 đã dùng ×2: glossary-resolver + lineage-consensus → **không** dùng lại; absorb = ghi vào
> §22 này + §3/§4/§6/§7/§8 đã sửa ở trên). Review do Mimo-Flash 2026-09-25: 4 P0 + 6 P1.

### 22.1 Bảng ánh xạ §directive → §T166

| Directive [T158-CRITICAL-SAFETY-003] | Sở hữu ở T166 | Ghi chú |
|--------------------------------------|---------------|---------|
| §3 CanonicalLock / pre-LLM lock section | §3 · §3.1 · §3.4 · §5 | đã có; sửa giá trị cột theo §20.3 |
| §6 post-LLM assertion | §6 · §6.1 (normalize) · §6.3 (fixture) | so khớp **sau strip title** (cấm raw `!=`) |
| §7 write-deny inventory | §7 · §7.1 (auth) · §7.2 (carve-out A+C) | LLM ≠ identity update |
| §8 cache safety | §8 (chốt vòng lặp + `identity_status`) | enum thật: `status` không có REVIEW/FAILED |
| §4 policy unknown vs strict | §4 **P-PARTIAL** + §4.1 `UNCONTROLLED_PROPER_NAME` | giữ P-PARTIAL |
| §9 test matrix | §14 (fixture `A009460`/`少林寺`/glossary ≥2) | chạy trên DB copy |
| §15 acceptance / GOLD | §13 (map `GOLD` → `quality_status='reviewed'`+`review_status='verified'` / T94 `manual_verified`) | **không** invent enum `GOLD` |

### 22.2 4 P0 của review — đã sửa trong SPEC (2026-09-25)

| # | P0 | Sửa ở đâu |
|---|----|-----------|
| P0-1 | Cả 2 fixture directive (`§2`/`§9`) **không LOCK được** | **§6.3 + §14 + §19 + §5 + §15** → fixture **`A009460 丹霞天然 → Đơn Hà Thiên Nhiên`** (LOCK) + place **`少林寺`** + term glossary ≥2; **`安廩` = CANDIDATE** case |
| P0-2 | `安廩` expected HARD_FAIL là **không thể xảy ra** (0 row authority) | **§6.3**: `安廩` → CANDIDATE → PASS/cảnh báo, **không** `identity_status=failed` |
| P0-3 | §8/raw so khớp `!=` false-fail `Thích An Lẫm` | **§6.1**: normalize = NFC + strip title `Thích`/`Thích Ca` + space/punct; unit test `Thích An Lẫm → PASS` |
| P0-4 | §6 STOP mâu thuẫn P-PARTIAL | **§4.1**: chỉ `UNCONTROLLED_PROPER_NAME` (chưa phân loại) → STOP; unknown thật (`UNKNOWN_REVIEW`) → vẫn dịch + flag |

### 22.3 6 P1 — disposition

| # | P1 | Disposition |
|---|----|-------------|
| P1-1 | `name_vi_auto` bị cấm write → chết queue/ETL 41.507 row | **A: giữ** như suggestion + carve-out ghi **§7.2** (không lock, không prompt) |
| P1-2 | `draft`/enum cache không có REVIEW/FAILED | **§8.4**: dùng cột riêng `identity_status` ∈ `pass\|review_required\|failed\|conflict\|NULL`; **cấm** lồng vào `cache.status` (0 site lọc `draft`) |
| P1-3 | `GOLD` không tồn tại trong repo | **§13/§2**: map → `quality_status='reviewed'`+`review_status='verified'` (segments) · `cache.status='auto'` · glossary `is_locked` · rules `status='active'` · T94 `manual_verified` |
| P1-4 | 3 token term lạ (`UNCONTROLLED_PROPER_NAME`… ) | **§4.1** định nghĩa + map sang status lock chuẩn |
| P1-5 | Tên LLM “Qwen/Groq” mơ hồ | **§0 R2**: `LLM (Groq/Qwen · model qwen/qwen3.8-27b · code _t73_call_gemini)` |
| P1-6 | Place fixture chỉ 2 row `reviewed` + 1 row mojibake `('????','Th? S?t H?i')` | **§6.3**: place fixture = **`少林寺`** (1 trong 2 row reviewed); mojibake → `is_valid_vi` reject (§3.1) |

### 22.4 3 câu Admin chốt (2026-09-25)

| Câu | Quyết định |
|-----|------------|
| (a) `安廩` = CANDIDATE (đúng theo evidence), fixture đổi sang `A009460`? | **ĐỒNG Ý** — `安廩` = CANDIDATE, `A009460`/`玄奘` làm fixture LOCK |
| (b) Giữ **P-PARTIAL** (không switch sang STOP toàn cục)? | **ĐỒNG Ý** — STOP chỉ cho `UNCONTROLLED_PROPER_NAME` (§4.1) |
| (c) `name_vi_auto`: A (keep + carve-out) hay B (ban) / C (tighten display)? | **A + C** — giữ suggestion (§7.2 A) + trả `name_vi_source` để UI gắn nhãn (§7.2 C) |

### 22.5 Handoff

- **Code/migration = Claude Code AI** (task `T166-canonical-identity-guard.md` → mục **DEV TASK**).
- Session log: `docs/sessions/2026-09-25_t166-safety-003-absorb.md` · Revert: `git revert --no-edit <sha_docs>`.
