---
id: T165-PHASE8-IMPL-PLAN
title: "T165 Phase 8 — Entity Alignment — Implementation Plan"
status: ready-for-review
created: 2026-09-29
source_spike: docs/Mimo-Flash/T165-Phase-8-XML Boundary-Entity Alignment.md
admin_decisions: pasted spec 2026-09-29 (sections A–S)
absolute_rule: KHÔNG sửa code, DB, migration, LLM, VPS trong tài liệu này.
---

# T165 Phase 8 — Entity Alignment — Implementation Plan

> **Tài liệu này là SPEC + PLAN ONLY.**  
> Không có production code, không có migration, không có DB thay đổi trong file này.  
> Mọi số dòng (line numbers) phải được xác nhận lại khi bắt đầu build.

---

## 1. Current Architecture (Confirmed by Code Audit 2026-09-29)

Pipeline thực tế đã xác nhận bằng grep + read code:

```
SOURCE HAN (source_text)
    │
    ▼
build_canonical_lock(conn, source_text)
    │  canonical_lock.py:1042
    │  → list[CanonicalLockEntry]
    │    .source_form / .normalized_form / .entity_type
    │    .canonical_id / .canonical_value / .authority_source
    │    .authority_level / .status (LOCKED|CANDIDATE|CONFLICT|UNKNOWN_REVIEW)
    │    .claims
    ▼
style_lock(conn, source_text, ...)
    │  style_constitution.py:234
    │  → lock dict {rules, codes, rules_version, constitution_hash,
    │               glossary, exemplar, known_pending, resolver,
    │               t166_lock_fingerprint, t166_identity_lock,
    │               prompt_label, json_mode, extra_hash, glossary_hash}
    ▼
_t73_build_style_prompt(content, lock, ...)     [app.py → delegates build_style_prompt]
    │  style_constitution.py:552
    │  → prompt: str (XML boundary v2 — <rules>, <glossary>, <exemplars>, <source>)
    ▼
_t73_call_gemini(prompt, ...)                   [app.py:17442]
    │  → (text: str, model_id: str, error_type: str|None)
    │    Groq / qwen/qwen3.8-27b / temperature=0.1 / max_tokens=2048
    ▼
output: PLAIN VI STRING   ← ROOT GAP
    │    (không có entity marker, không có span, không có structure)
    ▼
_t166_post_check_translation(conn, source_text, output, ...)
    │  canonical_lock.py:1185 (alias post_check_translation)
    │  → {ok, output, error_code, identity_status, identity_issues, identity_lock_hash}
    │  post_assert() dùng _extract_personlike_vi() — person-only detection,
    │  PLACE/TEMPLE không detect được deterministically
    ▼
_t165_write_cache(conn, src_hash, source_type, entity_id, source_text,
                  translated_text, model_id, rules_version, status,
                  constitution_hash, selected_rule_codes, glossary_hash,
                  identity_status, identity_issues, identity_lock_hash)
    │  style_constitution.py:703
    │  → INSERT INTO translation_cache (translated_text = PLAIN STRING)
    ▼
CACHE (translation_cache)
```

**Call sites của `_t166_post_check_translation` trong app.py (5 sites, xác nhận grep):**
- line ~6583: relation_evidence  
- line ~17640: person_bio  
- line ~18180: dila_card  
- line ~18260: dila_card (batch path)  
- line ~18383: place bulk path  
- **line ~18833: place_note** ← PILOT TARGET (POST /daoanh/api/place/<dila_id>/translate)

> **Lưu ý:** Line numbers phải re-verify bằng grep khi bắt đầu build vì code tiếp tục thay đổi.

---

## 2. Root Gap

```
HIỆN TẠI:
  call_llm_fn(prompt: str) -> str

MỤC TIÊU:
  call_llm_fn(prompt: str) -> (text: str, entity_assertions: list[EntityAssertion] | None)
```

**Điểm duy nhất cần mở rộng contract:** giữa `_t73_call_gemini` (trả `str`) và
`_t166_post_check_translation` (nhận `str`).

**Tại sao PLACE/TEMPLE không detect được hiện tại:**  
`post_assert()` dùng `_extract_personlike_vi()` — chỉ phát hiện PERSON qua honorific anchor
(ví dụ: "Thiền Sư X", "Ngài X"). Địa danh như "Thiếu Lâm Tự" không có honorific pattern
→ không thể deterministically verify "少林寺 → Thiếu Lâm Tự".

---

## 3. Confirmed Requirements (Admin Decisions A–S)

| ID | Decision | Nội dung | Impact |
|----|---------|---------|--------|
| A | XML Boundary | Output format đã chọn | LLM emits `<result>...<entity key="E1">...</entity>...</result>` |
| B | LLM không emit canonical ID | LLM chỉ thấy opaque key | `key="E1"` không phải `id="PL000000023255"` |
| C | Opaque request-local keys | E1, E2, E3... | Server giữ mapping: key → CanonicalLockEntry |
| D | Server giữ canonical mapping | Full CanonicalLockEntry per key | Canonical identity KHÔNG từ LLM output |
| E | Multiple candidates → REVIEW | Không silent chọn | CONFLICT/CANDIDATE entries → REVIEW |
| F | source_span/target_span | Runtime only | Không bắt buộc persist lâu dài |
| G | Cache giữ assertion_status, entity_type, target_surface, alignment_method | Additive | 4 cột mới (additive) |
| H | DHARMA_NAME out of scope | P8 không xử lý | Chỉ PLACE + PERSON trong pilot |
| I | Batch: kiến trúc support, không activate pilot | Designed but OFF | cbeta_translate_worker.py không đổi logic |
| J | Interactive pilot trước batch | | Chỉ /api/place/.../translate kích hoạt pilot |
| K | Valid aligned: PASS/HARD_FAIL | | Theo assertion_status |
| L | Malformed XML → fallback plain-string | | Không HARD_FAIL khi parser lỗi |
| M | Missing marker → REVIEW | | LOCKED entity không có marker → REVIEW |
| N | Unknown key → REVIEW | | LLM bịa key → REVIEW (không HARD_FAIL) |
| O | Wrong entity_type → HARD_FAIL hoặc REVIEW | theo severity | Nếu PLACE declared as PERSON → HARD_FAIL |
| P | Multiple candidates → REVIEW | | Không auto-resolve |
| Q | Repeated entity: tất cả phải pass | | Một occurrence sai → HARD_FAIL |
| R | Overlap/ambiguity → REVIEW | | Parser ambiguity không đoán |
| S | LLM không phải authority | | canonical_value luôn từ CanonicalLockEntry |

---

## 4. XML Contract (Admin Decision A + B + C)

### 4.1 LLM Output Format

```xml
<result>
Ông đến <entity key="E1">Thiếu Lâm Tự</entity> để tu học.
Ngài gặp <entity key="E2">Bách Trượng Hoài Hải</entity> tại đây.
</result>
```

### 4.2 Rules

- `key` = opaque string: `E1`, `E2`, ..., `E{n}` (ascending, request-local)
- `key` KHÔNG chứa canonical ID, DILA ID, hoặc Hán tự
- Content giữa tags = `target_surface` (bản dịch VI của entity)
- Text ngoài tags = bản dịch bình thường
- Nếu LLM bỏ `<result>...</result>` wrapper → coi là malformed, fallback plain-string
- Nếu LLM bỏ một `<entity>` tag → marker đó bị missing (xử lý theo Rule M)

### 4.3 Prompt Instruction (thêm vào prompt khi P8 active)

Phần instruction thêm vào prompt (sau `<glossary>` block, trước `<source>`):

```
<entity_alignment_instruction>
QUAN TRỌNG: Với mỗi thực thể quan trọng (địa danh, nhân danh) trong bản dịch,
hãy bọc bằng thẻ <entity key="Ei"> khi đó là thực thể được liệt kê trong danh sách
sau. Chỉ dùng key được cung cấp, KHÔNG tự tạo key mới.
Bọc toàn bộ bản dịch trong <result>...</result>.

Danh sách thực thể:
E1: 少林寺 [PLACE]
E2: 懷海 [PERSON]
...
</entity_alignment_instruction>
```

> Wording chính xác của instruction là OPEN DECISION (xem mục 20).

### 4.4 Server-side Entity Key Map

```python
entity_key_map: dict[str, CanonicalLockEntry] = {
    "E1": CanonicalLockEntry(
        source_form="少林寺",
        entity_type="PLACE",
        canonical_id="PL000000023255",
        canonical_value="Thiếu Lâm Tự",
        authority_source="namevi_map_places.reviewed",
        authority_level=0.9,
        status="LOCKED",
        ...
    ),
    "E2": ...,
}
```

**Chỉ LOCKED entries được gán key** (CANDIDATE, CONFLICT, UNKNOWN_REVIEW không tham gia P8 mapping).  
Mapping này build từ `lock['t166_identity_lock']` trước khi gọi LLM.

---

## 5. EntityAssertion Dataclass (New — in canonical_lock.py)

```python
@dataclass
class EntityAssertion:
    key: str                    # "E1", "E2" — opaque request-local
    source_form: str            # from CanonicalLockEntry.source_form (Hán)
    entity_type: str            # from CanonicalLockEntry.entity_type (không từ LLM)
    canonical_id: str           # from CanonicalLockEntry.canonical_id (không từ LLM)
    canonical_value: str        # from CanonicalLockEntry.canonical_value (không từ LLM)
    authority_source: str       # from CanonicalLockEntry.authority_source
    target_surface: str         # LLM output (candidate — không phải authority)
    source_span: Optional[Tuple[int, int]]   # runtime only, không persist
    target_span: Optional[Tuple[int, int]]   # runtime only, không persist
    alignment_method: str       # 'xml' (Phase 8), 'none' (plain-string fallback)
    assertion_status: str       # 'pass'|'mismatch'|'missing'|'unknown_key'|'type_error'|'review'
```

**Nguyên tắc bất biến:**
- `entity_type`, `canonical_id`, `canonical_value`, `authority_source` → LUÔN từ `CanonicalLockEntry` (server authority)
- `target_surface` → từ LLM output (candidate, verify sau)
- `canonical_value` từ LLM KHÔNG bao giờ được tin cậy

---

## 6. Entity Key Lifecycle

```
1. build_canonical_lock(conn, source_text)
   → list[CanonicalLockEntry]

2. build_entity_key_map(lock_entries: list[CanonicalLockEntry])
   → {E1: entry, E2: entry, ...}  (chỉ LOCKED entries)
   → lưu trong lock dict: lock['p8_entity_key_map']

3. build_entity_prompt_instruction(key_map)
   → str (thêm vào prompt, danh sách: "E1: source_form [entity_type]")

4. _t73_call_gemini(prompt_with_entity_instruction)
   → (raw_output: str, model_id, error_type)

5. parse_entity_xml(raw_output, key_map)
   → (plain_text: str, assertions: list[EntityAssertion])
   → malformed XML → (raw_output, assertions=[]) → fallback plain-string path

6. check_entity_assertions(assertions, key_map, lock)
   → list[dict] issues
   → PASS/HARD_FAIL/REVIEW theo failure matrix

7. post_assert(lock, plain_text, entity_assertions=assertions, ...)
   → (identity_status, identity_issues)

8. _t165_write_cache(..., entity_evidence=..., alignment_method='xml')
```

---

## 7. Server-side Key Mapping — Functions to Create

### 7.1 `build_entity_key_map` (canonical_lock.py)

```python
def build_entity_key_map(lock: list[CanonicalLockEntry]) -> dict[str, CanonicalLockEntry]:
    """Gán key E1, E2, ... cho từng LOCKED entry.
    CANDIDATE/CONFLICT/UNKNOWN_REVIEW không được gán key."""
    result = {}
    n = 1
    for entry in lock:
        if entry.status == 'LOCKED':
            result[f"E{n}"] = entry
            n += 1
    return result
```

### 7.2 `build_entity_prompt_instruction` (canonical_lock.py hoặc style_constitution.py)

```python
def build_entity_prompt_instruction(key_map: dict) -> str:
    """Build XML instruction thêm vào prompt khi P8 active."""
    # Returns prompt section listing E1: source [type] ...
    # Wording là OPEN DECISION — xem mục 20
```

### 7.3 `parse_entity_xml` (canonical_lock.py)

```python
def parse_entity_xml(output: str, key_map: dict) -> tuple[str, list[EntityAssertion]]:
    """Parse <result>...<entity key="Ei">...</entity>...</result>.
    Returns: (plain_text, assertions).
    Malformed → returns (output, []) — fallback plain-string."""
```

### 7.4 `check_entity_assertions` (canonical_lock.py)

```python
def check_entity_assertions(
    assertions: list[EntityAssertion],
    key_map: dict,
    lock: list[CanonicalLockEntry]
) -> list[dict]:
    """Verify assertions theo failure matrix (mục 8 dưới).
    Returns list[issue_dict] với severity HARD|WARN."""
```

---

## 8. Parser Behavior

```python
def parse_entity_xml(output: str, key_map: dict):
    # 1. Tìm <result>...</result> wrapper
    #    → không tìm thấy → MALFORMED → return (output, [])
    
    # 2. Trong <result>, tìm tất cả <entity key="Ei">...</entity>
    #    → dùng regex dung sai (không strict XML parse — LLM thường sinh gần đúng)
    
    # 3. Với mỗi match:
    #    a. key = Ei
    #    b. target_surface = content giữa tags
    #    c. Lookup key trong key_map
    #       → NOT IN key_map → assertion_status = 'unknown_key'
    #       → IN key_map → assertion_status pending check
    
    # 4. Tính target_span từ vị trí trong plain_text
    #    (plain_text = <result> content với tags stripped)
    
    # 5. Build list[EntityAssertion]
    
    # 6. Trả (plain_text, assertions)
```

**Tolerance rules:**
- `<entity key=E1>` (thiếu quote) → accept nếu regex bắt được
- `<Entity key="E1">` (capital E) → normalize lowercase
- Nested entities → REVIEW (parser ambiguity Rule R)
- Unclosed tag → malformed → fallback
- Escaped HTML entities trong content → decode trước khi lấy target_surface

---

## 9. Assertion Model

### 9.1 Assertion Status Values

| Status | Ý nghĩa | → Identity |
|--------|---------|------------|
| `pass` | target_surface khớp canonical_value (exact hoặc normalized) | PASS |
| `mismatch` | target_surface KHÔNG khớp canonical_value (entity type confirmed) | HARD_FAIL |
| `missing` | LOCKED entity không có marker trong output | REVIEW |
| `unknown_key` | LLM dùng key không có trong key_map | REVIEW |
| `type_error_hard` | entity_type trong key_map = PERSON nhưng context chỉ rõ PLACE | HARD_FAIL |
| `type_error_review` | entity_type unclear conflict | REVIEW |
| `multi_candidate` | CONFLICT status → không resolve | REVIEW |
| `repeated_pass` | Tất cả occurrences khớp canonical | PASS |
| `repeated_fail` | Ít nhất 1 occurrence không khớp | HARD_FAIL |
| `overlap` | Hai assertion keys chỉ vào cùng span | REVIEW |

### 9.2 Khớp (matching) canonical_value

```
PASS nếu:
    normalize(target_surface) == normalize(canonical_value)

normalize():
    - strip whitespace
    - lowercase
    - KHÔNG bỏ dấu (vì dấu là phần của canonical VI)
    - bỏ honorific prefix nếu canonical_value không có honorific

VD: "Thiếu Lâm Tự " → strip → "Thiếu Lâm Tự" → PASS
VD: "thiếu lâm tự" → lowercase OK → "thiếu lâm tự" → compare
```

---

## 10. Failure Matrix (Admin Decisions K–R)

| # | Tình huống | assertion_status | identity_status | Ghi chú |
|-|-|-|-|-|
| 1 | Valid: target_surface khớp canonical | `pass` | `pass` | Quyết định K |
| 2 | Malformed XML (no `<result>`) | N/A | FALLBACK (person-only) | Quyết định L |
| 3 | Missing entity marker (LOCKED, không có tag) | `missing` | `review_required` | Quyết định M |
| 4 | Unknown key (LLM bịa key) | `unknown_key` | `review_required` | Quyết định N |
| 5 | Wrong entity_type (PLACE→PERSON, hoặc ngược lại, affects severity) | `type_error_hard` | `failed` | Quyết định O |
| 6 | Wrong entity_type (unclear conflict) | `type_error_review` | `review_required` | Quyết định O |
| 7 | Target khác canonical (mismatch) | `mismatch` | `failed` | Quyết định K |
| 8 | Multiple candidates (CONFLICT in lock) | `multi_candidate` | `review_required` | Quyết định P |
| 9 | Repeated entity, TẤT CẢ pass | `repeated_pass` | `pass` | Quyết định Q |
| 10 | Repeated entity, có 1 occurrence sai | `repeated_fail` | `failed` | Quyết định Q |
| 11 | Overlapping spans | `overlap` | `review_required` | Quyết định R |
| 12 | Hallucinated marker (LLM bịa entity không có trong LOCK) | `unknown_key` | `review_required` | — |
| 13 | Plain-text fallback (malformed) | — | hành vi T166 hiện tại | Quyết định L |
| 14 | Parser ambiguity (2 parse valid) | `overlap` | `review_required` | Quyết định R |
| 15 | Gate OFF (P8 không active) | — | hành vi T166 hiện tại | — |
| 16 | Wrong pilot entity (không phải PL000000023255) | — | gate reject | Pilot scope |
| 17 | Missing pilot header | — | gate reject | Pilot scope |

---

## 11. Cache Impact

### 11.1 constitution_hash — cần thêm `alignment_method`

`constitution_hash` trong `style_constitution.py:199` hiện hash:
```python
parts.append(f"FMT:{PROMPT_FORMAT_VERSION}")
parts.append(f"label:{lock.get('prompt_label') or ''}")
parts.append(f"json:{bool(lock.get('json_mode'))}")
```

**Cần thêm:**
```python
parts.append(f"p8:{lock.get('alignment_method') or 'none'}")
```

→ Khi P8 active (alignment_method='xml'), hash thay đổi → cache miss đúng 1 lần.  
→ Khi P8 không active (alignment_method='none' hoặc None), hash không đổi → cache hiện tại vẫn HIT.  
→ Tương tự tiền lệ `json_mode` đã có.

### 11.2 write_cache — cần thêm cột mới

**4 cột additive mới** (Admin Decision G):

| Cột | Type | Nội dung | Nullable |
|-----|------|---------|---------|
| `entity_evidence` | TEXT (JSON) | `list[EntityAssertion]` dạng JSON | YES |
| `alignment_method` | TEXT | `'xml'` \| `'none'` \| NULL (legacy) | YES |
| `entity_assertion_status` | TEXT | summary status: `'pass'`\|`'review'`\|`'failed'`\|NULL | YES |
| `entity_types_covered` | TEXT (JSON) | list of entity_types có assertion | YES |

> `entity_assertion_status` = summary để UI query nhanh (không cần parse entity_evidence JSON).  
> `entity_types_covered` dùng cho audit filter.

**Backward compatibility:**
- Tất cả 4 cột nullable → cache cũ (NULL) đọc được không thay đổi
- `_has_col()` guard như pattern T165/T166 hiện có
- Cache cũ: `alignment_method=NULL` → coi là legacy, KHÔNG suy diễn `'none'`

### 11.3 Mass-miss estimate

- Cache miss **100% 1 lần** cho `source_type='place_note'` khi bật `alignment_method='xml'`
- Các source_type khác (person_bio, dila_card, relation_evidence) KHÔNG bị miss vì pilot chỉ bật cho place_note
- Bật từng source_type theo stage như T165 Phase 7 đã làm

---

## 12. constitution_hash Impact — Chính xác

Cần modify `style_lock()` để thêm `alignment_method` vào lock dict trước khi tính hash:

```python
# style_constitution.py:style_lock() — thêm vào lock dict:
lock['alignment_method'] = 'xml' if p8_active else 'none'

# constitution_hash() — thêm vào parts:
parts.append(f"p8:{lock.get('alignment_method') or 'none'}")
```

Và `style_lock()` cần biết `p8_active` (bool) — được truyền từ caller.

---

## 13. Migration Requirements

### Script: `scripts/t165_phase8_alignment_migrate.py`

**Pattern:** Theo hệt `scripts/t166_identity_migrate.py` (additive, dry-run/apply/verify/revert).

```python
CACHE_COLS = [
    ("entity_evidence",         "TEXT"),
    ("alignment_method",        "TEXT"),
    ("entity_assertion_status", "TEXT"),
    ("entity_types_covered",    "TEXT"),
]

# Index bổ sung:
INDEX = "CREATE INDEX IF NOT EXISTS idx_tc_alignment_method ON translation_cache(alignment_method)"
```

**Cần chạy:** TRƯỚC khi deploy bất kỳ code P8 nào.  
**Revert:** DROP INDEX + DROP COLUMN (SQLite 3.35+ supports DROP COLUMN).  
**Backup:** Tạo backup trước `--apply`, đặt tên `lineage_t165_p8_migration_YYYYMMDD_HHMMSS.db`.

---

## 14. Interactive Flow (Pilot)

```
POST /daoanh/api/place/PL000000023255/translate
Header: X-T165-P8-Pilot: 1

1. PILOT GATE CHECK:
   - P8_PILOT_GATE_ENABLED == True?           → else: return standard flow
   - Header 'X-T165-P8-Pilot' == '1'?         → else: return standard flow
   - dila_id == 'PL000000023255'?             → else: return standard flow (non-pilot entity)

2. Standard cache lookup (dual-key với constitution_hash including 'p8:xml')
   → HIT → serve cached (may have entity_evidence if P8 was used before)
   → MISS → continue

3. build_canonical_lock(conn, note_zh) → list[CanonicalLockEntry]

4. build_entity_key_map(lock_entries) → key_map = {"E1": entry, ...}

5. lock = style_lock(conn, source_text=note_zh, alignment_method='xml')
   → constitution_hash includes 'p8:xml' part

6. prompt = _t73_build_style_prompt(note_zh, lock, ...) 
   + build_entity_prompt_instruction(key_map) appended

7. raw_output, model_id, err_type = _t73_call_gemini(prompt, ...)

8. plain_text, assertions = parse_entity_xml(raw_output, key_map)
   → malformed XML → (raw_output, assertions=[]) → fallback path (skip step 9)

9. [P8 path] check_entity_assertions(assertions, key_map, lock_entries) → issues
   post_assert(lock_entries, plain_text, entity_assertions=assertions) → identity_status, identity_issues

10. [fallback path] post_assert(lock_entries, raw_output) → hành vi T166 hiện tại

11. _t165_write_cache(..., translated_text=plain_text,
                        entity_evidence=json(assertions),
                        alignment_method='xml' if P8 path else 'none',
                        entity_assertion_status=summary_status,
                        identity_status=..., identity_issues=...)

12. Return {ok, note_vi: plain_text, entity_evidence, alignment_method, ...}
```

---

## 15. Batch Flow

**Admin Decision I:** Kiến trúc phải support nhưng KHÔNG activation trong pilot đầu tiên.

`scripts/cbeta_translate_worker.py` hiện dùng `call_llm_fn(prompt: str) -> str`.

**Design cho future batch (KHÔNG implement trong pilot):**
- Worker nhận `p8_config: dict | None` param (None = P8 off)
- Nếu `p8_config` có, build key_map cho mỗi item trước khi gọi LLM
- Parse XML sau mỗi LLM call
- Ghi `entity_evidence` vào translation_segments (cột additive mới nếu cần)

**Pilot batch bypass guard:**
- Route batch `/daoanh/api/admin/translate/batch` KHÔNG có pilot header check
- Để batch không bypass gate: trong `build_entity_key_map`, chỉ activate nếu explicit `p8_enabled=True` flag truyền từ caller
- Batch route không truyền flag → auto OFF

---

## 16. Pilot Gate

### Flags

```python
# app.py hoặc style_constitution.py — file vị trí TBD khi implement
P8_PILOT_GATE_ENABLED = False          # DEFAULT OFF — phải flip thủ công khi test
P8_PILOT_ENTITY_ID = 'PL000000023255' # 少林寺 — entity duy nhất được pilot
P8_PILOT_SOURCE_TYPE = 'place_note'   # source_type duy nhất được pilot
P8_PILOT_HEADER = 'X-T165-P8-Pilot'
P8_PILOT_HEADER_VALUE = '1'
```

### Gate Logic

```python
def _is_p8_pilot_request(request, dila_id):
    if not P8_PILOT_GATE_ENABLED:
        return False
    if request.headers.get(P8_PILOT_HEADER) != P8_PILOT_HEADER_VALUE:
        return False
    if dila_id != P8_PILOT_ENTITY_ID:
        return False
    return True
```

### Security

- Gate OFF by default → không thể bị kích hoạt từ client
- Gate ON chỉ khi `P8_PILOT_GATE_ENABLED = True` trong code (không từ request)
- Batch route không có header check → batch không bypass
- LLM không nhận canonical ID trong bất kỳ trường hợp nào

---

## 17. Security Constraints

1. **LLM KHÔNG BAO GIỜ thấy canonical ID** (`PL000000023255`) — chỉ thấy `E1`, `E2`
2. **LLM KHÔNG BAO GIỜ là canonical authority** — `canonical_value` luôn từ CanonicalLockEntry
3. **KHÔNG tự resolve CONFLICT** — multiple candidates → REVIEW, không auto-pick
4. **Injection guard:** `target_surface` từ LLM chỉ được dùng để compare với `canonical_value`,
   không được đưa thẳng vào DB canonical tables
5. **Gate default OFF:** `P8_PILOT_GATE_ENABLED = False` trong code
6. **XML parsing:** dùng regex dung sai, KHÔNG dùng `xml.etree` để tránh XXE injection
   (LLM output không trusted XML — chỉ scan pattern)

---

## 18. Backward Compatibility

| Scenario | Behavior |
|---------|---------|
| Cache cũ (NULL alignment_method) | Đọc được, serve như trước — NULL = legacy |
| Cache cũ (NULL entity_evidence) | Đọc được, entity_evidence=None trong response |
| Code P8 OFF (gate off) | Toàn bộ pipeline T165/T166 hiện tại không đổi |
| post_assert(lock, output) cũ | Backward compat: entity_assertions=None → path cũ |
| write_cache cũ callers | entity_evidence không truyền → NULL trong DB |
| constitution_hash cũ row | 'p8:none' là giá trị mặc định → hash khác 1 lần (mass-miss 1 lần) |

> **Lưu ý quan trọng:** Khi deploy code P8 (dù gate OFF), `constitution_hash` sẽ thay đổi vì thêm `p8:none` vào hash parts. Điều này gây mass-miss 1 lần cho TẤT CẢ source_types. Phải plan migration window.

**Giải pháp:** Chỉ thêm `p8` part vào hash khi `alignment_method != 'none'`:

```python
# Không mass-miss khi p8 off:
if lock.get('alignment_method') and lock.get('alignment_method') != 'none':
    parts.append(f"p8:{lock['alignment_method']}")
```

→ Khi gate OFF, hash không đổi → zero cache disruption.

---

## 19. Rollback Plan

**Code revert:**
```bash
git revert --no-edit <sha_p8_build_commit>
```

**DB revert (nếu migration đã chạy):**
```bash
python -X utf8 scripts/t165_phase8_alignment_migrate.py --revert
# Hoặc restore backup:
cp data/lineage_t165_p8_migration_YYYYMMDD_HHMMSS.db data/lineage.db
```

**Scope rollback:** Toàn bộ P8 columns additive → DROP không mất data cũ.  
`translated_text` không đổi → UI tiếp tục serve plain text.

---

## 20. OPEN DECISIONS (Cần Admin quyết trước khi build)

### OD-1: Wording của entity_alignment_instruction trong prompt
Phải viết instruction sao cho qwen3.8-27b (model nhỏ) comply tốt nhất.  
**Đề xuất (chưa test):** Instruction ngắn gọn, ví dụ mẫu 1 câu, danh sách key ngắn.  
**Cần test thực tế** với ít nhất 10 lần trước khi chốt wording.  
**→ Chưa quyết.**

### OD-2: Vị trí lưu `entity_key_map` trong request flow
Option A: Trong `lock` dict (`lock['p8_entity_key_map']`) — consistent với `t166_identity_lock`  
Option B: Local variable trong route handler, truyền qua function params  
**Ảnh hưởng:** Nếu trong lock, phải thêm `p8_entity_key_map` vào `constitution_hash` (không muốn — map thay đổi theo source text, không phải rule).  
**→ Đề xuất: Option B (local variable)** — không làm ô nhiễm constitution_hash với nội dung source.  
**Chưa quyết chính thức.**

### OD-3: Normalization rule cho target_surface matching
`normalize()` cụ thể: có bỏ honorific không? Có accent-fold không?  
**Đề xuất:** KHÔNG accent-fold (dấu là ngữ nghĩa trong VI), có strip whitespace.  
**Chưa quyết chính thức.**

### OD-4: Maximum số entity keys per request
Quá nhiều key (>10) làm prompt dài + model nhỏ dễ bị confused.  
**Đề xuất:** Max 10 keys per request; nếu >10 LOCKED entries → chỉ lấy 10 đầu (theo authority_level).  
**Chưa quyết chính thức.**

---

## 21. Exact File Impact

Dựa trên code audit thực tế (không copy line numbers cũ):

| File | Function/Vị trí | Thay đổi |
|------|----------------|---------|
| `canonical_lock.py` | New: `EntityAssertion` dataclass | Thêm mới |
| `canonical_lock.py` | New: `build_entity_key_map()` | Thêm mới |
| `canonical_lock.py` | New: `build_entity_prompt_instruction()` | Thêm mới |
| `canonical_lock.py` | New: `parse_entity_xml()` | Thêm mới |
| `canonical_lock.py` | New: `check_entity_assertions()` | Thêm mới |
| `canonical_lock.py` | `post_assert()` | Thêm `entity_assertions: list[EntityAssertion] \| None = None` param; giữ backward compat khi `entity_assertions=None` |
| `style_constitution.py` | `constitution_hash()` | Thêm `p8:alignment_method` part (chỉ khi != 'none') |
| `style_constitution.py` | `style_lock()` | Thêm `alignment_method` param |
| `style_constitution.py` | `write_cache()` | Thêm `entity_evidence`, `alignment_method`, `entity_assertion_status`, `entity_types_covered` params với `_has_col` guard |
| `app.py` | `P8_PILOT_GATE_ENABLED` const | Thêm mới (default False) |
| `app.py` | `_is_p8_pilot_request()` | Thêm mới |
| `app.py` | `/daoanh/api/place/<dila_id>/translate` route (~line 18790) | Thêm pilot gate + XML path |
| `app.py` | `_t73_build_style_prompt()` | Thêm `p8_key_map` optional param; delegate xuống `build_style_prompt()` |
| `app.py` | `build_style_prompt()` (style_constitution.py:552) | Thêm `p8_key_map` optional param; nếu có thì inject entity instruction |
| Migration | `scripts/t165_phase8_alignment_migrate.py` | Tạo mới — 4 cột additive + index |

**Files KHÔNG đổi:**
- `scripts/cbeta_translate_worker.py` — batch không activate pilot
- Tất cả test files hiện có — T165 11/11, T166 18/18 phải vẫn pass
- `translation_cache` schema cũ — additive only, không DROP

---

## 22. Database Changes (Chi tiết)

### Existing translation_cache schema (relevant columns, xác nhận qua write_cache code):

```sql
translation_cache (
    id                   INTEGER PK,
    source_hash          TEXT,            -- SHA256[:24] của source_text
    source_type          TEXT,            -- 'place_note'|'person_bio'|'dila_card'|...
    entity_id            TEXT,            -- dila_id hoặc person_id
    source_text          TEXT,
    translated_text      TEXT,            -- PLAIN STRING (unchanged by P8)
    model_id             TEXT,
    rules_version        TEXT,
    status               TEXT,            -- 'auto'|'edited'|'invalidated'
    created_at           TEXT,
    updated_at           TEXT,
    constitution_hash    TEXT,            -- T165 migration
    selected_rule_codes  TEXT,            -- T165 migration
    glossary_hash        TEXT,            -- T165 migration
    identity_status      TEXT,            -- T166 migration: 'pass'|'review_required'|'failed'
    identity_issues      TEXT (JSON),     -- T166 migration
    identity_lock_hash   TEXT             -- T166 migration
)
```

### New columns to add (T165-P8 migration):

```sql
ALTER TABLE translation_cache ADD COLUMN entity_evidence         TEXT;
ALTER TABLE translation_cache ADD COLUMN alignment_method        TEXT;
ALTER TABLE translation_cache ADD COLUMN entity_assertion_status TEXT;
ALTER TABLE translation_cache ADD COLUMN entity_types_covered    TEXT;

CREATE INDEX IF NOT EXISTS idx_tc_alignment_method
    ON translation_cache(alignment_method);
```

**Schema compatibility:** `translated_text` KHÔNG đổi → UI không cần update.

---

## 23. Test Plan

### P8.1 — Parser tests (KHÔNG cần LLM)

| Test | Mô tả |
|------|------|
| A | 1 LOCKED entity, XML well-formed, target khớp canonical → `pass` |
| B | Multiple LOCKED entities, tất cả khớp → all `pass` |
| C | Repeated entity (E1 xuất hiện 2 lần), cả 2 khớp → `repeated_pass` |
| D | Missing marker: E1 không có tag → `missing` |
| E | Unknown key: LLM dùng E9 (không trong key_map) → `unknown_key` |
| F | Wrong entity_type: PLACE entity được mark as PERSON context → `type_error_*` |
| G | Target khác canonical: E1 → "Thiếu Lâm Sơn" (không phải "Thiếu Lâm Tự") → `mismatch` |
| H | Malformed XML (thiếu `<result>` wrapper) → (raw_output, assertions=[]) |
| I | Overlapping markers (E1 lồng E2) → `overlap` |
| J | Hallucinated marker (E1 trong key_map nhưng LLM tự thêm E99) → `unknown_key` |
| K | Legacy cache (NULL entity_evidence) → đọc được, assertion=None |
| L | Cache không có alignment_method → NULL = legacy pass (không đổi hành vi) |
| M | Gate OFF → toàn bộ pipeline T166 hiện tại, không có P8 |
| N | Wrong pilot entity (dila_id != PL000000023255) → gate reject, standard flow |
| O | Missing pilot header → gate reject, standard flow |
| P | Correct pilot gate (gate ON + header + entity match) → P8 path |

### P8.2 — Hash tests (KHÔNG cần LLM)

- constitution_hash với alignment_method='xml' KHÁC với alignment_method='none'
- constitution_hash với alignment_method='none' = constitution_hash hiện tại (backward compat)
- migration dry-run: liệt kê 4 cột sẽ thêm, không thay đổi DB
- migration apply: 4 cột được thêm, existing rows có NULL
- migration verify: tất cả 4 cột tồn tại
- migration revert: 4 cột bị drop, existing rows (legacy) không mất

### P8.3 — Integration tests (KHÔNG cần LLM thật)

- Mock `_t73_call_gemini` trả về pre-defined XML string
- Verify full flow: gate → build key_map → build prompt → parse XML → check assertions → write cache
- Verify `entity_evidence` được ghi vào cache
- Verify `translated_text` = plain text (tags stripped)
- Verify fallback: mock trả malformed XML → legacy path, `translated_text` = raw output

### P8.4 — E2E tests (CẦN LLM thật — chỉ sau khi P8.1-P8.3 xanh)

- Real LLM call với PL000000023255 source text
- Verify LLM compliance rate (số lần emit `<result>...<entity>...</result>`)
- Verify malformed rate
- Đo token overhead vs plain text baseline

---

## 24. Deployment Plan

```
Phase P8.0: Migration only
  - Chạy migration (4 cột additive) trên local test DB
  - Verify tất cả existing routes vẫn hoạt động (zero new behavior)
  - Migration chỉ thêm cột NULL, không đổi logic

Phase P8.1: Code deploy, gate OFF
  - Deploy tất cả P8 code với P8_PILOT_GATE_ENABLED = False
  - T165 11/11 PASS, T166 18/18 PASS, new P8 parser tests PASS
  - Verify: không có hành vi mới trong production (gate OFF)

Phase P8.2: Pilot test (gate ON, local only)
  - Flip P8_PILOT_GATE_ENABLED = True trong local dev
  - Test với entity PL000000023255 + header X-T165-P8-Pilot: 1
  - Verify XML compliance rate ≥ 70% (benchmark cần đo thật)
  - Verify fallback path khi malformed

Phase P8.3: Admin QA (gate ON, staging)
  - Deploy lên VPS test với gate ON
  - Admin verify UI: note_vi correct, entity_evidence accessible
  - No regression in existing translation flows

Phase P8.4: Production gate ON
  - Flip gate ON trên production
  - Monitor: error rate, entity_assertion_status distribution
  - Ready to rollback: git revert + migration revert
```

---

## 25. Acceptance Criteria

- [ ] Canonical ID KHÔNG BAO GIỜ xuất phát từ LLM output
- [ ] Mọi entity key map entry = request-local, chỉ từ CanonicalLockEntry (server authority)
- [ ] Multiple candidates KHÔNG bao giờ auto-resolve (luôn REVIEW)
- [ ] Malformed XML KHÔNG corrupt `translated_text` (plain text vẫn serve được)
- [ ] Legacy cache (NULL alignment_method) đọc được, hành vi không đổi
- [ ] Gate default OFF — client không thể kích hoạt P8
- [ ] Non-pilot entity (≠ PL000000023255) không vào pilot path
- [ ] Batch route không bypass gate
- [ ] Unit tests KHÔNG cần LLM thật (P8.1-P8.3)
- [ ] T165 11/11 PASS, T166 18/18 PASS sau khi deploy P8 code
- [ ] constitution_hash với alignment_method='none' không thay đổi (zero mass-miss khi gate OFF)

---

## 26. Production Risks

| Risk | Mức độ | Mitigation |
|------|--------|-----------|
| LLM compliance thấp (qwen3.8-27b model nhỏ bỏ tag) | MEDIUM | Fallback plain-string; chỉ mất entity evidence, không corrupt translation |
| Mass-miss khi bật P8 cho source_type | LOW | constitution_hash chỉ đổi khi alignment_method='xml'; gate OFF → zero miss |
| XML injection từ LLM output | LOW | Dùng regex, không trust XML parse; target_surface chỉ dùng để compare |
| 429 rate limit (prompt dài hơn do entity instruction) | LOW | +entity instruction ~200-400 chars; baseline đã 14.874 chars → +3% |
| Parse lỗi phá vỡ route | VERY LOW | try/except toàn bộ parse flow → fallback plain-string |
| DB migration lock | LOW | Migration additive, có backup, có revert |

---

## Estimated Implementation Phases

### P8.1 — Dataclass + Parser (1-2 sessions, không cần LLM)
- `EntityAssertion` dataclass
- `build_entity_key_map()`
- `parse_entity_xml()`
- `check_entity_assertions()`
- `post_assert()` extension
- Tests A–L (unit)

### P8.2 — Hash + Cache + Migration (1 session, không cần LLM)
- `constitution_hash()` extension
- `style_lock()` extension
- `write_cache()` extension (4 cột)
- `t165_phase8_alignment_migrate.py`
- Tests hash, migration

### P8.3 — Pilot Gate + App.py Wiring (2 sessions)
- `P8_PILOT_GATE_ENABLED` + gate logic
- `build_entity_prompt_instruction()`
- `_t73_build_style_prompt()` + `build_style_prompt()` extension
- Pilot route wiring
- Tests M–P (gate tests, mock LLM)

### P8.4 — E2E + Benchmark (1+ session, cần LLM thật)
- Real LLM call với PL000000023255
- Đo compliance rate + malformed rate
- Đo token overhead
- Admin QA

---

## FINAL VERDICT

> **READY_FOR_IMPLEMENTATION_PLAN_REVIEW**  
> Spec đầy đủ. Không có SPEC CONFLICT. Mọi Admin decision đã được incorporate.  
> 4 OPEN DECISIONS cần Admin xác nhận trước khi bắt đầu P8.1 build.

---

*Tài liệu này tổng hợp từ:*  
- *Architecture spike: `docs/Mimo-Flash/T165-Phase-8-XML Boundary-Entity Alignment.md`*  
- *Admin decisions: pasted spec session 2026-09-29 (sections A–S)*  
- *Code audit: canonical_lock.py, style_constitution.py, app.py (2026-09-29)*  
- *T177 review: `docs/Mimo-Flash/X-T177-directive-v2-trie-xml-dualhash-REVIEW.md`*

*Generated by: Claude Sonnet 4.6 — Session e9fa65e0 — 2026-09-29*
