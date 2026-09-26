---
id: T165
title: "Rules-Constrained Translation Engine — Semantic Selective Rules + Constitution Hash Cache"
module: Editorial / LLM Translation
priority: high
status: built
owner: claudecode
depends_on: [T73, T123, T158-glossary-resolver]
created: 2026-09-24
updated: 2026-09-25
spec_path: docs/Mimo-Flash/T165-rules-constrained-translation-engine-SPEC.md
designed_by: mimo-flash (system-design skill)
handoff_to: Claude Code Agent
amended: "2026-09-24 Admin absorb directive (A) · phase2=XML+Trie · glossary_filter_text=1"
build_task: T169
build_date: 2026-09-25
build_commit: de26e02
done_when: |
  _select_rules lọc always∪terms đúng; glossary lock filter theo source_text;
  cache HIT/MISS theo constitution_hash (static full-text + matched full-text
  + filtered glossary + exemplar + PROMPT_FORMAT_VERSION + T166 lock);
  sửa rule static/term dính text X → miss X, giữ HIT text Y;
  wrappers _t73_* + scripts/t50_passage_vi_backfill.py cùng 1 module style_constitution.py;
  admin UI match_scope/match_terms; log prompt_tokens; npm run pipeline PASS;
  mọi thay đổi có revert path. Phase 2 (XML boundary + Trie) KHÔNG gate phase 1.
---

# T165 — Rules-Constrained Translation Engine (SPEC bàn giao Claude Code)

> ✅ **REVIEW-ACCEPTED 2026-09-25 — VERDICT T168 APPLIED (Admin/lead phê chuẩn).**
> Audit §14 (T168, docs-only, 0 code/DB) đã đối chiếu SPEC ↔ DB/code thật. Toàn bộ **15 issue §14.2**
> (P0×6 · P1×6 · P2×3) **ĐÃ ĐƯỢC XÁC NHẬN ĐÚNG → ACCEPTED**, áp dụng theo thứ tự §14.3 lúc build.
> **Hiệu chỉnh thật đã sửa ngay hôm nay (T168):** `admin/app.py` **KHÔNG TỒN TẠI** (số "18865" là ảo giác từ backup
> `docs/sessions/2026-09-16/app.py.bak-dila-person-index.py` 18954 dòng) → **single codebase** `app.py`;
> Bảng thật cập nhật số sau T167 seed (rules **112** · cache **1762** · distinct rv **15** · `RULE-001..015` **15 row**).
> **Kỷ luật build:** dùng **TÊN HÀM**, KHÔNG dùng số dòng (app.py đang dịch chuyển do agent khác); sửa **1 bản**
> app.py + `scripts/t50_passage_vi_backfill.py`, KHÔNG mirror `admin/app.py`. Verdict chi tiết: §14.2b.
> Task: `tasks/T168-t165-spec-v2-review-accepted.md` · Revert: `git revert --no-edit `18262b9``.

**Đọc file này một lần → build được.** Không cần file kèm.  
Repo root SSOT: `git rev-parse --show-toplevel` == `visjs-app` (daoanh là subdir — **không** `git init` trong daoanh).

---

## 0. Mục tiêu (mục đích dự án)

| # | Mục tiêu | Vì sao |
|---|----------|--------|
| 1 | Prompt chỉ nén **rule liên quan** tới đoạn Hán | 96 active rule mọi lúc → LLM loãng attention; T159 (`法嗣`→`Pháp嗣`) chứng minh rule text không enforce |
| 2 | Cache **trung thực theo semantic** | Sửa 1 rule chỉ invalidate bản dịch *đụng rule đó*; glossary/exemplar đổi cũng invalidate đúng dòng |
| 3 | **Một builder** cho mọi luồng interactive | Hết 4 prompt-builder rời; code preservation = wrapper cũ → module mới |
| 4 | Tuân thủ hard rules | Zero-RAM · additive-only · no destructive mặc định · raw bất biến · canonical DILA ID · có revert |
| 5 | **Glossary lock filter theo text** (Admin 2026-09-24) | Chỉ inject cặp `term_zh` xuất hiện trong `source_text` (+ resolver db_verified) → ↓ token TPM · HIT/MISS trung thực |
| 6 | **Log `usage.prompt_tokens`** thật | Đo baseline vs sau filter (target giảm, không hard-gate phase 1) |

**Admin chốt 2026-09-24 (absorb directive “Trie+Dual-Hash+XML”):**

| # | Quyết định | Apply ở |
|---|------------|---------|
| 1A | **Absorb vào T165** — không task mới, không song song engine | Toàn SPEC này = SSOT |
| 2 | **XML boundary + Pure-Python Trie = Phase 2** (sau phase 1–7 PASS + Admin QA) | §7 Phase 8 optional |
| 3 | **Glossary filter theo text = Phase 1 bắt buộc** | §3 + §5 `style_lock` |

**Cấm phase 1 (từ directive đã reject “nguyên trạng”):** static hash chỉ `rule_code` (phải hash **full `rule_text`**) · field `type/content/code` sai schema · hard-gate XML · 1-char match_terms · bỏ qua T166 fingerprint · `cp file.bak` thay `git revert`.

---

## 1. OUT OF SCOPE (không đụng — nếu đụng = deviation cần Admin)

| Không làm | Lý do |
|-----------|--------|
| `scripts/cbeta_translate_worker.py` + `translation_segments` + `translation_jobs` | Stack T95 riêng: JSON `data/glossaries/vi-buddhist.json` + `PROMPT_VERSION='t95-batch-cbeta-v1'` — **Phase B** sau |
| Gộp/rewrite `glossary_vi` ↔ `glossary_term` (248k each) | Debt khác; resolver chỉ SQL batch (Zero-RAM) |
| DROP column / DELETE cache đại trà | Additive; invalidate có mục tiêu + dry-run |
| Lineage / DILA XML / GraphDB | Raw bất biến, không liên quan |
| Suy luận học thuật bằng LLM | Chỉ dịch text qua pipeline có duyệt (T73/T123) |

---

## 2. PHASE 0 AUDIT (đã verify repo 2026-09-24 — trust số này, không re-bịa)

Draft cũ `[T158-DEBUG-001]` **không logic đúng** các điểm sau. Claude Code PHẢI dùng thực tế:

| Lệch draft | Thực tế repo | Hành động |
|-------------|--------------|-----------|
| Task ID `T158` | Đã dùng ×2 done: `T158-glossary-resolver-pre-translation-lookup.md`, `T158-lineage-consensus.md`. Free: `T160,T161,T163,T164` taken; **`T162` missing file** (chỉ có trong tasktodo); **`T165` = task này** | Dùng **T165**; ghi chú T162 debt docs |
| Rules `RULE-011`…`RULE-015` | **0 match**. Codes thật: `PERSONA_BAN_DICH`, `NO_PINYIN`, `HANVIET_*`, `BUDDHIST_TITLES`, `TERM_*`, `GLOSSARY_LOCK_STABLE`… (~97 rows) | Match theo `rule_code` thật; **không** tạo ID bịa |
| Glossary = `glossary_vi` | Prompt lock = **`translation_glossary` WHERE `is_locked=1`** (~79). `glossary_vi` chỉ authority trong `_glossary_resolver` (14 bảng) | Lock chính = `translation_glossary` ⊕ resolver |
| Cache key đủ | `rules_version = sha16(join ALL active rule_text)` → 1 sửa = invalidate **toàn bộ** 1761 row. **Glossary/exemplar KHÔNG trong hash** → bug: đổi glossary không miss cache | Thêm `constitution_hash` (§5) |
| 1 builder | ≥4: `_t73_build_style_prompt` (app.py), `t50 _style_lock_blocks/build_prompt`, worker prompt riêng + vài fragment inline GLOSSARY LOCK | Gộp 3 interactive (app.py + t50 + worker) vào `style_constinction.py`; worker **out of scope** |
| Active rule filter thống nhất | Trộn: `is_active=1` (T50, seed) vs `status='active'\|'pending'\|'dismissed'` (resolver, admin). Data 2026-09-24: 96 active + 1 dismissed, **0 mismatch** | Selector: `WHERE status='active' AND is_active=1` |
| Dual codebase | **KHÔNG tồn tại** — **single codebase**: `app.py` ~21061 dòng chứa toàn bộ `_t73_*`; `admin/app.py` KHÔNG có trong repo/git history (số "18865" = số dòng backup `docs/sessions/2026-09-16/app.py.bak-dila-person-index.py` 18954 — auditor nhầm bản chụp cũ thành admin app); `admin/` chỉ chứa HTML/CSS/JS · ETL T50 = `scripts/t50_passage_vi_backfill.py` | Chỉ sửa **1 bản** app.py + t50; BỎ mọi mirror `admin/app.py` |
| `match_terms` | Cột **chưa có**; UI `admin/translation_rules.html` chưa có field | ALTER ADD + UI |
| Cache unique | Index `(rules_version,status)` + `(entity_id,source_type)`; **không** UNIQUE `(source_hash, rules_version)` **nhưng CÓ** `UNIQUE(source_hash, source_type)` (autoindex — ràng buộc mọi write: mỗi nguồn chỉ 1 row → write PHẢI `INSERT OR REPLACE`/DELETE+INSERT, lookup kèm `source_type`; xem #1/#2) ; có rv=`'1'` hỏng | Lookup fallback; row hỏng → skip, không DELETE mặc định |
| Số liệu visjs (2865 names, 912 nodes) | Thuộc nhánh thientong **ngoài** daoanh | Không đưa vào acceptance T165 |

**Bảng thật (verify 2026-09-24):**

```
translation_rules     112 rows  cols: id, rule_code, rule_type, description, rule_text,
                                is_active, priority, created_by, created_at, updated_at,
                                status, suggested_by
                                (97 → 112 sau seed T167 RULE-001..015 2026-09-24; RULE-% = 15 row)
translation_cache     1762 rows cols: id, source_hash, source_type, entity_id, source_text,
                                translated_text, model_id, rules_version, status,
                                report_count, approved_by, approved_at, created_at, …
                                (status: auto 1753 · draft 2 · edited 6 · invalidated 1 · distinct rv 15)
translation_glossary  79 rows   (is_locked) — locked 1-char 14 term (法僧戒定慧因果緣性相經律論鉢)
translation_exemplar  2692 rows (is_active — lock limit 3)
translation_segments  66 rows
translation_jobs      3 · translation_job_items — OUT OF SCOPE worker
glossary_vi/glossary_term 248095 each — resolver only
rule_type: forbidden|grammar|style|terminology|gate (terminology=90 · style=10 · forbidden=6 · gate=3 · grammar/provenance/structure=1)
```

---

## 3. Kiến trúc Phương án A (đã chốt — build đúng này)

```
source_text
  │
  ├─ _glossary_resolver(conn, text)          # T158 cũ — GIỮ, không rewrite
  │     └─ db_verified ──────────────┐
  │                                  ▼
  ├─ _select_rules(conn, text)  ◄── MỚI CORE
  │     active ∩ (always ∪ terms-matched)
  │     include iff match_scope!='terms' OR any(match_terms ⊆ source_text)
  │     field names DB: rule_code / rule_type / rule_text  (KHÔNG code/type/content)
  │     → rules[], selected_rule_codes[], rule_block
  │
  ├─ glossary_lock = filter(translation_glossary is_locked=1, source_text)
  │                  ⊕ resolver.db_verified   # Admin #3: filter theo text, KHÔNG always-79
  ├─ exemplar (is_active, limit 3)
  │
  ▼
constitution_hash = sha256.hexdigest()[:16](
      SORT("rule_code + '\n' + rule_text" for each selected)   # FULL text cả static+terms
    ⊕ SORT("zh→vi" for each filtered_glossary)
    ⊕ SORT("zh:vi" for each exemplar)
    ⊕ PROMPT_FORMAT_VERSION          # 't165-v1'; bump nếu đổi khung prompt phase 2
    ⊕ t166_lock_fingerprint          # NULL/skip nếu T166 chưa build; SAU T166 = bắt buộc
)
  │
  ▼
SELECT … FROM translation_cache
 WHERE source_hash=? AND constitution_hash=?   -- HIT
 -- fallback HIT: source_hash=? AND rules_version=? AND constitution_hash IS NULL
  │ miss
  ▼
_t73_call_gemini(prompt) → log usage.prompt_tokens
  → INSERT + selected_rule_codes CSV + constitution_hash + glossary_hash
```

**Invariant hash (reject directive static_sig chỉ-code):**  
Sửa `rule_text` của **bất kỳ** selected rule (kể cả `PERSONA_BAN_DICH`, `NO_ADDITION`) → hash **luôn** lệch → MISS. Không code path `static_hash = sha(codes_only)`.

**Invalidate khi admin sửa/toggle rule R** (upsert API / approve pending):

```sql
DELETE FROM translation_cache
WHERE selected_rule_codes IS NULL  -- backfill cũ: coi như dính mọi rule (conservative)
   OR instr(',' || selected_rule_codes || ',', ',' || :rule_code || ',') > 0;
```

- Codes **không chứa** `,` (chỉ `[A-Z0-9_]`) → delimiter `,` an toàn.  
- Trả JSON `{ok, invalidated: n}` tiếng Việt cho UI.

---

## 4. Schema — additive-only

### 4.1 Migration script

**File mới:** `scripts/t165_rules_engine_migrate.py`

```
python scripts/t165_rules_engine_migrate.py --stats
python scripts/t165_rules_engine_migrate.py --dry-run
python scripts/t165_rules_engine_migrate.py --apply     # có backup trước
python scripts/t165_rules_engine_migrate.py --revert
```

- Backup: `data/backups/lineage_t165_<YYYYMMDD_HHMMSS>.db` (sqlite backup API).  
- SQLite 3.45.1 → `ALTER TABLE … ADD COLUMN` OK.  
- **Không** DROP trong `--apply` mặc định.  
- Idempotent: check `pragma table_info` trước khi ADD.  
- Cập nhật `docs/db_schema.md` (mục translation_rules / translation_cache) + session log.

### 4.2 `translation_rules` — +2 cột

| Cột | Type | Default | Ý nghĩa |
|-----|------|---------|---------|
| `match_scope` | TEXT | `'always'` | `always` \| `terms` |
| `match_terms` | TEXT | NULL | JSON array Hán, ví dụ `["法嗣","三昧"]` |

**Backfill `match_scope`:**

1. `rule_type='terminology'` **và** `rule_text` extract được ≥1 cặp Hán (regex见 §6.2) → `match_scope='terms'`, `match_terms` = JSON list.  
2. Còn lại → **`always`** (an toàn — không giảm rule oan).  
3. In stats: n always / n terms / n extract fail→always.

### 4.3 `translation_cache` — +3 cột

| Cột | Type | Ý nghĩa |
|-----|------|---------|
| `constitution_hash` | TEXT NULL | sha16[:16] prompt thật đã dùng |
| `selected_rule_codes` | TEXT NULL | CSV sorted codes đã inject; **NULL = legacy “dính mọi rule”** |
| `glossary_hash` | TEXT NULL | sha16[:16] **filtered** glossary pairs + exemplar ids (bắt buộc — Admin #3 + invalidate glossary) |

- Giữ nguyên cột `rules_version` (global hiện tại) — **dual-key transition**.  
- **Backfill 1761 row:** `constitution_hash`/`selected_rule_codes`/`glossary_hash` = NULL (không đoán lịch sử).  
- Row `rules_version` không match `^[0-9a-f]{16}$` (vd `'1'`) → đánh dấu ở log stats; lookup **không** match fallback đó; **không DELETE**.

### 4.4 Lookup cache (thay INSERT/SELECT hiện tại)

Đọc cột write sites (đối chiếu, không hardcode sai dòng):

- `app.py` ~6303, ~16644, ~17154, ~17220, ~17679 — `INSERT OR REPLACE/INSERT INTO translation_cache` (5 site; line cũ — thực tại +84 shift, xem §14.1)  
- `scripts/t50_passage_vi_backfill.py` ~414  
- **`admin/app.py` KHÔNG TỒN TẠI** (ảo giác từ backup snapshot — xem §14.1 "Dual codebase")  

**Lookup mới (pseudocode):**

```python
row = SELECT * FROM translation_cache
      WHERE source_hash=? AND constitution_hash=? AND constitution_hash IS NOT NULL
      LIMIT 1
if not row:
    row = SELECT * FROM translation_cache
          WHERE source_hash=? AND rules_version=?   -- legacy
          ORDER BY id DESC LIMIT 1
# optional: nếu rules_outdated badge cần, so current_constitution_hash vs row
```

**Write:** luôn ghi `constitution_hash`, `selected_rule_codes` (CSV `",".join(codes)`), `glossary_hash`, **và** `rules_version` (giữ compat panel admin).

---

## 5. Module SSOT mới — `style_constitution.py`

**File mới** (cùng cấp `app.py` — import được từ app, admin, scripts):

```python
# style_constitution.py — T165
# Vietnamese errors; try-except thân thiện; Zero-RAM (không nạp 248k glossary).

PROMPT_FORMAT_VERSION = 't165-v1'

def source_hash(text) -> str
    # dời logic _t73_source_hash (sha256 hex — GIỮ format cũ nếu callers phụ thuộc)

def extract_match_terms(rule_text: str) -> list[str]
    # regex gợi ý (test kỹ):
    #   r'([一-鿿]{1,8})\s*[→->]+\s*\S+'   → group 1
    #   r'[（(]([一-鿿]{2,8})[）)]'          → group 1
    # union, dedup, giữ 2–8 chars Hán; fail → []

def select_rules(conn, source_text: str) -> dict
    # SQL: SELECT rule_code, rule_type, rule_text, priority, match_scope, match_terms
    #      FROM translation_rules
    #      WHERE status='active' AND is_active=1
    #      ORDER BY priority ASC, id ASC
    # include if match_scope != 'terms' OR any term in source_text (plain substring)
    #   match_terms ≥2 chars Hán (reject 1-char noise); extract fail → treat as always
    # KHÔNG dùng keys rule["code"]/["type"]/["content"] — DB = rule_code/rule_type/rule_text
    # return {rules, codes (sorted unique), rule_block, rules_version_global}

def constitution_hash(lock: dict) -> str
    # sha256(concat parts).hexdigest()[:16]
    # parts = sorted(f"{code}\n{rule_text}" for each selected rule)   # FULL text
    #       ⊕ sorted filtered glossary "zh→vi"
    #       ⊕ sorted exemplar "zh:vi"
    #       ⊕ PROMPT_FORMAT_VERSION
    #       ⊕ lock.get('t166_lock_fingerprint') or ''
    # CẤM: hash chỉ rule_code (static_sig bug directive)

def glossary_hash(glossary: list, exemplar: list) -> str

def filter_glossary_for_text(locked_rows, source_text, resolver_verified) -> list
    # Admin #3 Phase 1: giữ row nếu term_zh in source_text
    #   OR term_zh in resolver_verified keys
    #   OR (optional safety) term_zh length≥2 appears in any 2–5 n-gram already resolved
    # always-inject tối đa: PERSONA overlap không cần — persona đã ở static rules
    # return [{term_zh, term_vi}] sorted stable; limit max_glossary after filter

def style_lock(conn, source_text: str, labels=None, max_glossary=120, max_exemplar=3,
               resolver=None) -> dict
    # rules = select_rules(conn, source_text)   # filtered if source_text else all-active
    # glossary = filter_glossary_for_text(locked, source_text, resolver) ⊕ db_verified
    # exemplar = translation_exemplar is_active=1
    # known_pending = status='pending' (GIỮ hành vi T158)
    # return {rules, codes, rules_version, constitution_hash, glossary_hash,
    #         glossary, exemplar, known_pending, t166_lock_fingerprint: None}

def log_prompt_metrics(response_json, source_text) -> None
    # usage.prompt_tokens / completion_tokens / total_tokens → logger INFO (Vietnamese)
    # KHÔNG hard-fail phase 1 theo ngưỡng 150–250; chỉ measure + in dashboard/session

def build_style_prompt(content, lock, label='văn bản', json_mode=False) -> str
    # DÁN Y cấu trúc _t73_build_style_prompt hiện tại (app.py ~16444)
    # persona + Style Constitution + GLOSSARY LOCK + FEW-SHOT + nguyên bản + how
    # KHÔNG đổi wording / KHÔNG XML trong phase 1 (Admin #2 phase 2)
    # chỉ đổi nguồn rule_block + glossary_block (đã filter)

def invalidate_cache_for_rule(conn, rule_code: str) -> int
    # DELETE theo §3; conn.commit(); return rowcount

def invalidate_cache_all_semantic(conn) -> int
    # fallback admin nút “Dịch lại hàng loạt” T123: DELETE WHERE constitution_hash IS NOT NULL
    # hoặc bump PROMPT_FORMAT_VERSION rồi lookup miss dần — chọn 1, ghi trong session
```

### 5.1 Wrappers (code preservation — GIỮ tên hàm cũ)

| File | Hàm cũ | Thân mới |
|------|--------|----------|
| `app.py` | `_t73_get_active_rules` ~16257 | → `select_rules` (all active, không filter text — hoặc giữ query cũ; **nên** delegate) |
| `app.py` | `_t73_rules_version` | → hash toàn bộ active như cũ **hoặc** delegate constitution phần global — **giữ đúng semantic global** cho panel |
| `app.py` | `_t73_source_hash` ~16272 | → `source_hash` |
| `app.py` | `_t73_style_lock` ~16291 | → `style_lock(conn, source_text=…)` — **thêm param source_text**; callers cũ không truyền text → fallback `select_rules` all-active (hành vi = hôm nay) |
| `app.py` | `_t73_build_style_prompt` ~16444 | → `build_style_prompt` |
| `app.py` | `_build_dila_card_prompt` (~16700) | → **bắt buộc** chuyển sang `build_style_prompt` (hoặc hash khớp phần nó inject) — #6 |
| `app.py` | `_t126_build_qa_prompt` (~20609) | → **excluded** (không ghi `translation_cache`) nhưng nhận `select_rules` filtered — #6 |
| `app.py` | `_t73_call_gemini` | → trả về/tự log `usage.prompt_tokens` qua `log_prompt_metrics` — #8 |
| `scripts/t50_passage_vi_backfill.py` | `_style_lock_blocks` ~97, `build_prompt` ~132 | body → import `style_constitution`; **xoá** query rule cục bộ |
| **KHÔNG có** `admin/app.py` | — | **single codebase** — không mirror (chi tiết §14.1) |

Import pattern (tránh circular): module **không** import `app.py`.

```python
from style_constitution import (
    select_rules, style_lock, build_style_prompt,
    constitution_hash, invalidate_cache_for_rule, source_hash,
)
```

`app.py` chạy khác cwd (khi chạy qua `scripts/` hoặc bằng read-only RO) → dùng:

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # đã có pattern类似?
```

(Kiểm tra cách admin hiện import `scripts.*` — `importlib` ~17755 app.py.)

### 5.2 Gắn invalidate vào write-rule

| Site | Việc |
|------|------|
| `api_admin_translation_rules_upsert` `app.py` ~17556 | Sau UPDATE/INSERT rule có sửa `rule_text`/`is_active` → `invalidate_cache_for_rule` |
| Approve pending `app.py` ~17520 | Sau `status='active'` → invalidate rule_code đó |
| UI toggle `admin/translation_rules.html` `toggleRule` | response hiện `new_rules_version` → **bổ sung** `invalidated_cache_count` |

---

## 6. Admin UI — `admin/translation_rules.html`

Hiện có: edit `rule_type`, `priority`, `is_active`, `rule_text`, pending panel; **chưa có** match fields.

### 6.1 Thêm field

- Form create/edit: select **Match scope** (`always`/`terms`) + textarea **Match terms** (1 Hán từ/line → JSON).  
- List: chip `ALWAYS` / `TERMS: 法嗣,三昧`.  
- Gửi API: body thêm `match_scope`, `match_terms` (array hoặc JSON string).

### 6.2 API upsert

Mở rộng body (backward compatible — thiếu field → default `always` / NULL terms):

```json
{
  "rule_code": "TERM_PHAP_SI",
  "rule_type": "terminology",
  "rule_text": "...",
  "priority": 50,
  "is_active": 1,
  "match_scope": "terms",
  "match_terms": ["法嗣"]
}
```

Response: `{ok, rule_code, new_rules_version, invalidated_cache_count}`.

---

## 7. Lộ trình build (thứ tự bắt buộc)

| Phase | Việc | Output |
|-------|------|--------|
| **1** | `scripts/t165_rules_engine_migrate.py` + `--stats/--dry-run` trên DB thật | stats always/terms; backup path in ra |
| **2** | `style_constitution.py` + unit test (test file mới `tests/test_t165_style_constitution.py` hoặc pattern `tests/` hiện có) | select/invalidate/hash |
| **3** | Wrap `app.py` `_t73_*` + cache read/write dual-key + invalidate ở upsert/approve | py_compile OK |
| **4** | Refactor `t50` import chung + **Phase 3b enumerate 8 call site `_t73_style_lock` (toàn app.py) truyền text** | grep hết `_style_lock_blocks` body query rule; builder đã thêm `_build_dila_card_prompt`/`_t126_build_qa_prompt` (#6 #7 #8) |
| **5** | UI + API match fields + `invalidated_cache_count` | admin smoke 1 toggle |
| **6** | `--apply` migration (nếu Phase 1 dry-run sạch) + backfill match_scope | stats cuối |
| **7** | `npm run pipeline` (guard→lint→test→uat→compliance→gov→e2e→e2e:runtime) | PASS (xử lý EPERM `.last-run.json` pre-existing như T152) |
| **8** | **Phase 2 optional (Admin #2 — KHÔNG gate phase 1–7):** (a) XML Boundary prompt + bump `PROMPT_FORMAT_VERSION='t165-v2'`; (b) Pure-Python Trie/Aho-Corasick thay substring **chỉ khi** `n_terms≥1000` (hiện 85 → substring đủ); (c) measure token before/after XML | Separate commit `feat: T165 phase2 xml-trie + docs` · Admin QA riêng |

**Task file khi build:** `tasks/T165-rules-constrained-translation-engine.md`  
(frontmatter `spec: docs/Mimo-Flash/T165-rules-constrained-translation-engine-SPEC.md`)  
**Session:** `docs/sessions/2026-09-24_t165-rules-engine.md`  
**Commit:** `feat: T165 semantic rules engine + docs`  
**tasktodo:** thêm entry ACTIVE; khi Admin xác nhận → move `docs/taskdone.md`.

---

## 8. Acceptance (done_when — đo bằng test/script, không cảm tính)

1. Rule `match_scope=terms`, terms=`["法嗣"]`, source **không** chứa `法嗣` → `rule_block` **không** có rule đó; source **có** → **có**.  
2. Source A dùng rule R, source B không: sửa `rule_text` của R →  
   - cache A: miss (dòng bị DELETE hoặc hash lệch)  
   - cache B: **vẫn HIT** (nếu B không selected R)  
2b. Sửa `rule_text` rule **static** (`NO_ADDITION` / `PERSONA_BAN_DICH`) → **tất cả** dòng constitution_hash cũ MISS (không còn path static_sig chỉ-code).  
2c. Thêm terminology rule mới `汴京` **không** xuất hiện trong source X → `select_rules` không include → **X HIT 100%**, 0 call Groq (`from_cache=true`).  
3. Glossary filter: `translation_glossary` có cặp `汴京→Biện Kinh` locked nhưng source **không** chứa `汴京` → **không** inject cặp đó vào prompt; source **có** → inject. Đổi cặp đã inject → hash lệch → MISS dòng đó.  
3b. `glossary_hash` **bắt buộc** ghi khi INSERT (không optional).  
4. Caller cũ không truyền `source_text` → fallback all-active + glossary unfiltered (hành vi = hôm nay) = **0 crash**.  
5. `app.py` + `t50` cùng formula hash (1 fixture Python assertEquals).  
5b. Field names: unit test assert module đọc `rule_code`/`rule_text` (fail nếu dùng `code`/`content`).  
5c. `_t73_call_gemini` log `usage.prompt_tokens` thật (xác nhận qua ít nhất 1 HIT + 1 MISS) — #8.  
6. `npm run pipeline` PASS.  
7. Smoke case T159: text `孝義性空禪師法嗣。` → prompt chứa glossary/rules `法嗣` khi terms match; post-edit `_post_edit_hanzi_leakage` **giữ nguyên**.  
8. Zero-RAM: không `SELECT *` 248k glossary_vi vào list; chỉ LIMIT/IN; filter glossary per-text in-memory ≤ max_glossary.  
9. Migration `--revert` chạy sạch trên backup copy (test trên DB copy, **không** prod undo bừa).  
10. Không commit API key; không sửa RAW.  
11. **Measure:** log `usage.prompt_tokens` ít nhất 1 HIT + 1 MISS; ghi vào session (target ↓ so với baseline, **không** fail build nếu chưa 150–250).  
12. Phase 2 XML/Trie **không** xuất hiện trong acceptance phase 1.

**D3/D8 (bổ sung 2026-09-26 — absorb DIRECTIVE v2, task T177):**

13. **D3(a)** `_t73_call_gemini` (app.py:16575) log + **persist** `usage.prompt_tokens/total_tokens` thật (qua `_t165_log_prompt_metrics` app.py:16606); retry/backoff tối đa 2 lần khi 429 (đang return ngay tại app.py:16602). Ngân sách = baseline **đo được** (3.422 prompt_tokens đã chốt — T177 D7), **cấm** hard-gate 150–250.
14. **D3(b)** Sửa rule → row `status='edited'` (6 row) **không** bị `INSERT OR REPLACE` ghi đè: lookup ưu tiên nhánh `edited` → trả row + `rules_outdated=true`; chỉ ghi đè khi Admin bấm "Dịch lại" (`UPDATE ... SET status='auto'`).
15. **D3(c)** Invalidate burst có giới hạn: thêm mode "Dịch lại có giới hạn" (batch N row/request) bên cạnh nút full 1.762 row (app.py:18396 — soft-delete `status='invalidated'`); không xoá mass không kiểm soát.
16. **D3(d)** Sau khi thêm cột `constitution_hash`, badge `rules_outdated` + danh sách admin cache vẫn đúng (audit ~22 read site `FROM translation_cache` app.py đổi lookup/mark theo hash — T165 §14.2 #9).
17. **D8** Test Case 2 = acceptance chính (item 2/2b/2c): sửa 1 rule → chỉ dòng **selected** rule đó MISS, dòng khác HIT — chạy với **fixture thật** `A009460 丹霞天然` (vnpa `don_ha_thien_nhien` verified, match substring `天然`), không dùng `達磨/面壁` bịa.

---

## 9. Revert / Rollback (bắt buộc ghi session)

| Lớp | Revert |
|-----|--------|
| Code/docs | `git revert --no-edit <sha>` |
| Schema | `python scripts/t165_rules_engine_migrate.py --revert` + path `data/backups/lineage_t165_*.db` |
| Cache sai sau deploy | Admin invalidate semantic hoặc `PROMPT_FORMAT_VERSION` bump → miss dần (chọn 1, ghi log) |
| Data rule | UPDATE rule обратно; invalidate lại |

Không có dòng revert = **chưa đủ điều kiện commit** (skill §bug-revert).

---

## 10. File I/O map

| Loại | Path |
|------|------|
| **SPEC (bạn đang đọc)** | `docs/Mimo-Flash/T165-rules-constrained-translation-engine-SPEC.md` |
| **Đọc** | `app.py`, `scripts/t50_passage_vi_backfill.py`, `scripts/seed_style_constitution.py`, `admin/translation_rules.html`, `data/lineage.db` (RO cho audit), `docs/db_schema.md`, `docs/rules/*` |
| **Ghi mới** | `style_constitution.py`, `scripts/t165_rules_engine_migrate.py`, `tests/test_t165_*.py`, `tasks/T165-….md`, `docs/sessions/2026-09-24_t165-*.md` |
| **Sửa** | `app.py`, `scripts/t50_passage_vi_backfill.py`, `admin/translation_rules.html`, `docs/db_schema.md`, `docs/tasktodo.md` |
| **(KHÔNG TỒN TẠI)** | `admin/app.py` — single codebase, không có mirror (T168 đã xác minh) |
| **Backup** | `data/backups/lineage_t165_<ts>.db` |
| **Không sửa** | `scripts/cbeta_translate_worker.py`, RAW tables, `glossary_vi` bulk, lineage.* |

---

## 11. Quy ước build (từ AGENTS + skill — không lặp lại bằng mọi giá, tuân thủ)

1. **Code preservation:** wrapper cũ giữ tên; body delegate.  
2. **Additive-only migration** + dry-run + backup + revert.  
3. **Zero-RAM.**  
4. LLM **chỉ dịch text**.  
5. Git: **từ toplevel `visjs-app`**; message `feat: T165 … + docs`.  
6. Session log **bắt buộc** sau build; Admin confirm → `taskdone.md`.  
7. `npm run pipeline` trước khi nói “done”.  
8. Không lộ path nhạy cảm / API key.

---

## 12. Câu hỏi Admin (nếu blocking — dừng báo BLOCKED, đừng bịa)

| # | Câu hỏi | Admin trả lời (2026-09-24) |
|---|---------|------------------------------|
| 1 | Absorb directive (A) hay T167 riêng? | **A** — absorb vào T165 |
| 2 | XML + Trie khi nào? | **Phase 2** (Phase 8) — không gate phase 1–7 |
| 3 | Glossary filter theo text phase 1? | **Có** — bắt buộc |
| (cũ) | Làm luôn `glossary_hash`? | **Có** (đã harden trong §4.3) |
| (cũ) | Backfill terms chỉ extract được? | **Có**, còn lại `always` |

Không blocking — build Phase 1 ngay.

---

## 13. Quick start cho Claude Code (copy-paste mental)

```bash
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
# 1. Audit nhanh (read-only)
python3 -c "import sqlite3;c=sqlite3.connect('data/lineage.db');print(c.execute('select count(*) from translation_rules').fetchone())"
# 2. Tạo tasks/T165-*.md trỏ spec_path này
# 3. Phase 1: scripts/t165_rules_engine_migrate.py --stats/--dry-run
# 4. Phase 2: style_constitution.py + tests
# 5. Phase 3–5 wrappers + admin + UI
# 6. npm run pipeline
# 7. Commit từ toplevel visjs-app: feat: T165 semantic rules engine + docs
```

**Filename bàn giao duy nhất:**  
`docs/Mimo-Flash/T165-rules-constrained-translation-engine-SPEC.md`

---

## 14. REVIEW 2026-09-25 — Đối chiếu SPEC ↔ DB/code thật + Đề xuất chỉnh sửa

> Audit read-only trên `data/lineage.db` (RO) + `app.py`/`scripts/t50_passage_vi_backfill.py`
> (KHÔNG có `admin/app.py` — xem §14.1 "Dual codebase").
> **Không sửa code** — toàn bộ dưới đây là đề xuất để Admin/owner SPEC chốt trước khi build.
> Mức độ: **P0** = build theo SPEC hiện tại sẽ sai/crash/mất dữ liệu · **P1** = không đạt mục tiêu · **P2** = lệch nhỏ.
> **Cập nhật T168 (2026-09-25):** toàn bộ 15 issue §14.2 đã ACCEPTED (verdict §14.2b); số liệu Bảng thật
> §14.1/§2 đã sửa theo thực tế sau T167 seed; mọi ref `admin/app.py` đã bỏ.

### 14.1 Những gì SPEC ghi ĐÚNG (đã verify — không cần sửa)

| Mục | Kết quả đối chiếu |
|-----|--------------------|
| Bảng thật (§2) | ✅ **Đã sửa 2026-09-25 (T168)** — GHI CŨ 97/1761 lệch: thực tế `translation_rules` **112** (sau T167 seed RULE-001..015) · `translation_cache` **1762** · `translation_glossary` 79 locked · `translation_exemplar` 2692 · `translation_segments` 66 ✓ |
| Rule filter | ✅ **Đã sửa 2026-09-25 (T168)** — **111** `(active,1)` + 1 `(dismissed,0)` → `status='active' AND is_active=1` = **111** · `rule_code LIKE 'RULE-%'` = **15 row** (RULE-001..015, seed T167; trước T167 = 0) · rule_type: terminology 90 / style 10 / forbidden 6 / gate 3 / grammar+provenance+structure 1 ✓ |
| Index cache (§2) | ✅ **Đã sửa 2026-09-25 (T168)** — distinct rv = **15** (cũ 14) · rv hỏng `'1'` = 1 row ✓ · CÓ `UNIQUE(source_hash, source_type)` (autoindex) ✓ |
| Write sites (§4.4) | ✅ **Đã sửa 2026-09-25 (T168)** — `app.py` 5 site (line cũ 6303/16644/17154/17220/17679 ↔ thực tại 6391/16732/17242/17308/17767 — +84 shift do agent khác) · `t50:414` (1) · **`admin/app.py` 3 site = ẢO GIÁC — bỏ** (`admin/app.py` không tồn tại) |
| Vị trí wrapper (§5.1) | ✅ đúng hướng — **dùng TÊN HÀM** (line đã dịch chuyển): `_t73_get_active_rules` · `_t73_rules_version` · `_t73_source_hash` · `_t73_style_lock` · `_t73_build_style_prompt` · `_glossary_resolver` (toàn bộ **app.py** — KHÔNG có `admin/_t73_style_lock`) · `t50 _style_lock_blocks` 97 / `build_prompt` 132 · upsert ~17556 / approve ~17520 — khớp |
| ≥4 builder (§2) | `_t73_build_style_prompt` (app.py) + `t50 build_prompt` + `_build_dila_card_prompt` + `_t126_build_qa_prompt` (2 builder thiếu trong §5.1 — xem #6) ✓ |
| Bug "glossary/exemplar không trong hash" (§2) | **Đúng**: `_t73_rules_version` = `sha256(join rule_text)[:16]` (app.py) — glossary/exemplar/resolver không tham gia → đổi glossary **không** miss cache ✓ |
| Dual codebase | ✅ **SỬA 2026-09-25 (T168)** — **single codebase** `app.py` (~21061); `admin/app.py` **KHÔNG TỒN TẠI** ("18865" = backup snapshot `docs/sessions/2026-09-16/app.py.bak-dila-person-index.py`) |
| Writer ngoài 3 file | grep repo-wide: chỉ có `app.py`, `t50` (KHÔNG có `admin/app.py`; các `.bak` trong `docs/sessions/` không phải live code) → scope write-list đủ ✓ |

### 14.2 Vấn đề + Đề xuất chỉnh sửa

| # | Mức | Vấn đề (SPEC nói gì / Thực tế gì) | Bằng chứng | Đề xuất chỉnh sửa SPEC |
|---|-----|-------------------------------------|------------|--------------------------|
| **1** | **P0** | §2 "Cache unique" **thiếu `UNIQUE(source_hash, source_type)`** — SPEC chỉ ghi "không UNIQUE (source_hash, rules_version)" (đúng chữ nhưng bỏ sót unique đang ràng buộc mọi write). | `CREATE TABLE translation_cache … UNIQUE(source_hash, source_type)`; autoindex `sqlite_autoindex_translation_cache_1`; comment app.py:17150 *"DELETE trước để tránh UNIQUE(source_hash, source_type) conflict"*. Hiện 0 source_hash trùng, nhưng constraint điều khiển mọi INSERT. | **§2 bổ sung cột "Có UNIQUE (source_hash, source_type)"**; §4.4 ghi rõ hệ quả: (a) mỗi nguồn chỉ **1 row** → không thể giữ song song 2 constitution; (b) write PHẢI `INSERT OR REPLACE` (hoặc DELETE+INSERT) — site 17154/17220 dùng plain `INSERT` nên bắt buộc có DELETE trước; (c) lookup PHẢI kèm `source_type`. |
| **2** | **P0** | §4.4 pseudocode lookup **thiếu `source_type`** và **thiếu `status != 'invalidated'`**. | Mọi lookup hiện tại đều filter: app.py 6279, 16611, 17004, 17640 · admin 15502, 15557, 15747 · invalidate endpoint 18221 dùng `status='invalidated'` làm soft-delete. Pseudocode mới sẽ **hồi sinh row đã invalidate** và có thể HIT nhầm row khác `source_type`. | Sửa pseudocode thành:<br>`WHERE source_hash=? AND source_type=? AND constitution_hash IS NOT NULL AND constitution_hash=? AND status!='invalidated'`<br>fallback: `… AND rules_version=? AND status!='invalidated'` + **nhánh ưu tiên `status='edited'`** (xem #3). |
| **3** | **P0** | **Bản dịch human bị LLM ghi đè mất.** 6 row `status='edited'` (1743,1744,1745 person_bio · 1751,1752,1768 dila_card — 1768 = A005248). Lookup theo `constitution_hash` sẽ MISS (backfill = NULL) → fallback rv lệch sau khi admin sửa rule → gọi LLM → `INSERT OR REPLACE` **xoá bản human**. Code hiện tại không bao giờ mất (lookup trả row theo `id DESC` bất kể rv). | `select status,count(*)` → edited 6; admin save = app.py:17187–17230 (`status='edited'`, `approved_by` human). | §4.4 thêm **hard rule**: `status='edited'` **không bao giờ bị REPLACE** — trả về row + `rules_outdated=true`; chỉ ghi đè khi admin bấm "Dịch lại" (force, có chủ đích) → dùng `UPDATE … SET status='auto', translated_text=?` (không REPLACE). Acceptance bổ sung: *sửa rule → row edited vẫn giữ nguyên text + báo outdated*. |
| **4** | **P0** | §5.2 `DELETE … WHERE selected_rule_codes IS NULL` → **1761/1761 row legacy đều NULL** → lần toggle đầu tiên **xoá sạch toàn bộ cache** = mâu thuẫn thẳng với Mục tiêu 2 ("invalidate có chọn lọc"), vô nghĩa vì legacy row đã tự miss nhờ `rules_version` lệch, và **phá luôn fallback legacy** (mất lịch sử + mất row edited nếu nằm trong đó). | backfill §4.3 quy định NULL cho cả 1761 row; `rules_version` đổi khi sửa rule → fallback `rules_version=?` đã miss. | **Bỏ câu DELETE này.** Thay bằng: legacy row để nguyên (tự miss theo rv); invalidate có chọn lọc **chỉ áp row có `selected_rule_codes`**; row edited được bảo vệ (#3). Nếu Admin vẫn muốn "xoá ngay" thì dùng endpoint sẵn `POST /daoanh/api/admin/translate/invalidate` (app.py:18221, soft-delete `status='invalidated'` — **không DELETE**). |
| **5** | **P0** | **`constitution_hash` ≠ prompt thật → under-invalidation (HIT cũ khi prompt đổi).** 3 nguồn thực bị bỏ khỏi hash: | | §3/§5 sửa công thức hash = **hash phần THẬT đã inject**, tính **sau** khi lock đầy đủ: |
| | | (a) dila_card: `_t73_style_lock(conn)` tính hash **trước** rồi app.py:17078–17085 mới `lock['glossary'].append(resolver db_verified)` → đổi authority table vẫn HIT. | app.py:17070–17090 | (a) `style_lock(source_text)` phải **tự chạy resolver** và tính hash sau merge; hoặc tách `finalize_lock(lock)` gọi ngay trước `build_style_prompt` + trước khi INSERT. |
| | | (b) `label` + `json_mode`: prompt 'tiểu sử' vs 'đoạn kinh' (JSON) khác hẳn nhưng hash không chứa → cùng `source_text` 2 loại prompt khác nhau → HIT chéo. | `_t73_build_style_prompt(content, lock, label, json_mode)` | (b) đưa `source_type ⊕ label ⊕ json_mode` vào hash (hoặc đơn giản: **lookup luôn kèm `source_type`** + hash kèm `label`). |
| | | (c) `known_pending` inject trong dila_card prompt nhưng không hash. | app.py:16316 | (c) đưa `known_pending` (sorted rule_code) vào hash nếu block đó được inject. |
| | | *Ghi chú không phải bug:* dila_card chỉ inject `rule_type IN (terminology,grammar)` và **cắt `rule_text[:120]`** → hash full-text sẽ over-invalidation (an toàn, chấp nhận được — ghi rõ trong SPEC). | app.py:16731–16735 | |
| **6** | **P1** | §5.1 **thiếu 2 builder**: `_build_dila_card_prompt` (app.py:16700, tự dựng rule block riêng, không qua `_t73_build_style_prompt`) và `_t126_build_qa_prompt` (app.py:20609, nhận `lock` nhưng không ghi cache). | grep `GLOSSARY LOCK`: app 16475 (unified) · 16713 (dila_card) · t50:143 | §5.1 thêm 2 dòng: **dila_card → bắt buộc** chuyển sang `build_style_prompt` (hoặc ghi "excluded nhưng hash phải khớp phần nó inject"); **T126 → excluded** (không ghi `translation_cache`) nhưng vẫn nhận `select_rules` filtered. |
| **7** | **P0** | **Không ai truyền `source_text`** → mục tiêu 1 (prompt nén rule liên quan) **không xảy ra** nếu chỉ thêm param. **8 site** gọi `_t73_style_lock(conn)` **không có text** — KHÔNG phải 15, KHÔNG có site admin local (admin/app.py không tồn tại). | app.py 2659, 6295, 16640, 17074, 17675, 17822, 17997, 20687 (8 site) | §7 thêm **Phase 3b bắt buộc**: enumerate 8 call site (toàn app.py) + truyền text tương ứng (`bio_zh`, `note_zh`, `preview`, `source_data`, unit `zh`, …); site không có text (T126) → all-active. Ghi rõ: *không sửa caller = chưa đạt Mục tiêu 1 + `prompt_tokens` không giảm*. ✅ **ACCEPTED (T168)** |
| **8** | **P1** | Mục tiêu 6 "log `usage.prompt_tokens`" **không khả thi** với code hiện tại: `_t73_call_gemini` đọc `data['choices']` rồi bỏ `data['usage']`. Không nằm trong §5.1/§10 edit list. | `app.py::_t73_call_gemini` (single codebase — KHÔNG có mirror admin/app.py) | §10 "Sửa" thêm `app.py::_t73_call_gemini`: trả về/tự log `usage` qua `log_prompt_metrics`. ✅ **ACCEPTED (T168)** |
| **9** | **P1** | §4.4 liệt kê **9 write site** (chứa **3 admin ảo**) — thực tế **5 app.py + 1 t50**. Có **~22 chỗ `FROM translation_cache`** trong app.py — KHÔNG phải 30/39 (admin reader không tồn tại). Reader theo `rules_version`/`status` cũ sẽ hiển thị HIT/outdated sai sau khi đổi key. | grep `FROM translation_cache` app.py ≈ 22 site; INSERT thực: 6391, 16732, 17242, 17308, 17767 (5 app.py) + t50 | §4.4 thêm mục **"READ sites phải audit"** + acceptance: *badge `rules_outdated` + danh sách admin cache vẫn đúng sau khi có `constitution_hash`*. ✅ **ACCEPTED (T168)** |
| **10** | **P1** | `extract_match_terms` regex `{1,8}` nhưng `select_rules` yêu cầu term **≥2 chars** → rule trích được **toàn term 1-char** sẽ không match bao giờ → **bị loại im lặng** (mất rule oan — đúng lỗi T159 đang cố tránh). | §5 `r'([一-鿿]{1,8})…'` vs §5 `match_terms ≥2 chars` | §5 `extract_match_terms`: **lọc ≥2 chars trước**, danh sách rỗng → `match_scope='always'`; in stats `n rules kept-terms / n forced-always`. |
| **11** | **P1** | Backfill §4.2 không có **coverage check** — convert 86 rule terminology sang `terms` mà không đo tỷ lệ rule bị "tắt" trên dữ liệu thật. | 1761 row `source_text` sẵn có để đo | §7 Phase 1 output thêm: *chạy `select_rules` trên toàn bộ 1761 `source_text` → in: số rule bị loại TB/row, số row nhận <5 rule, **list rule chưa từng match lần nào** (review tay trước khi `--apply`)*. |
| **12** | **P1** | Frontmatter `done_when` bắt buộc "**T166 lock**" trong `constitution_hash`, nhưng T166 build **sau** T165 → mâu thuẫn với §3 "NULL/skip nếu T166 chưa build". Và khi T166 fingerprint bắt đầu != rỗng → **toàn bộ cache HIT trở thành MISS** (mass re-translate 1761 row) — SPEC chưa cảnh báo chi phí. | depends_on T165, T166 §17 Phase 1–5 | `done_when` sửa: *"fingerprint = NULL khi T166 chưa build; bắt buộc sau khi T166 merge"*. §9 thêm dòng: *kích hoạt T166 fingerprint = mass-miss dự kiến, bấm "Dịch lại" từng phần / budget TPM trước khi bật*. |
| **13** | **P2** | §5.1 `_t73_get_active_rules` "hoặc giữ query cũ" → query cũ **chỉ `is_active=1`**, không `status='active'` → 2 selector khác nhau song song (hiện 0 lệch, nhưng toggle endpoint set cả 2 cột → có thể lệch sau). | app.py:16260 | Chốt **1 selector**: `status='active' AND is_active=1` cho cả wrapper cũ. |
| **14** | **P2** | `_glossary_resolver` docstring ghi "**12 authority tables**", SPEC §2 ghi 14 → thực tế **14 priority** (P1 glossary … P14 places-all). | app.py:16330 + P1–P14 trong 16371–16438 | Sửa docstring "14" khi build (không đổi logic). |
| **15** | **P2** | `translation_glossary` locked có **14 term 1-char** (法僧戒定慧因果緣性相經律論鉢) → filter theo text gần như luôn match (không giảm token) và là noise cho post-assert T166. | `WHERE is_locked=1 AND length(term_zh)=1` → 14 | Không chặn T165; ghi chú để T166 tách severity (xem T166 §14 mục 11). |

### 14.2b Verdict tổng T168 (Admin/lead phê chuẩn 2026-09-25)

| Nhóm | # | Verdict | Trạng thái trong SPEC v2 |
|------|---|---------|--------------------------|
| Logic ĐÚNG — giữ đề xuất | #1 #2 #3 #4 #5 #6 #10 #11 #12 #13 #14 #15 | ✅ **ACCEPTED** (P0×5 · P1×4 · P2×3) | Nội dung đề xuất đã nguyên vẹn ở cột "Đề xuất chỉnh sửa SPEC" — áp vào §2/§4.4/§5/§5.1/§7/§9/§10 lúc build Phase 3 |
| Logic ĐÚNG nhưng SAI SỐ | #7 | ✅ **ACCEPTED** — **8 site** (toàn app.py), KHÔNG có 15/admin | Đã sửa cột bằng chứng/đề xuất (#7 ở trên) |
| Logic ĐÚNG nhưng SAI SỐ | #9 | ✅ **ACCEPTED** — **~22 reader + 5 INSERT** (app.py) + t50, KHÔNG phải 30/39 | Đã sửa cột bằng chứng/đề xuất (#9 ở trên) |
| Ref ảo "admin/app.py" | #8 | ✅ **ACCEPTED** — single codebase, bỏ mirror admin | Đã sửa #8 + toàn bộ ref admin/app.py trong SPEC |
| Số liệu Bảng thật lệch do T167 seed | — | ✅ **Sửa ngay hôm nay** | §2 Bảng thật + §14.1 cập nhật 112/1762/rv15/RULE-001..015 |

**Kết luận:** 15/15 issue §14.2 ĐƯỢC XÁC NHẬN ĐÚNG (7 sai-số/ref đã hiệu chỉnh trong SPEC v2 hôm nay). SPEC v2 = sẵn sàng cho Phase 3 build theo §14.3 checklist.

### 14.3 Đề xuất thứ tự sửa SPEC trước khi build (đã ACCEPTED — T168, 2026-09-25)

> Checklist này nay là **BUILD PHASE 3 CHECKLIST** (biến đổi code). Sửa docs §2/§14.1/§14.2 đã apply trong SPEC v2 hôm nay.

1. **Sửa §2** (thêm UNIQUE thật — **đã sửa**) + **§4.4** (lookup đủ `source_type`/`status`/`edited` nhánh) → #1 #2 #3.
2. **Bỏ DELETE `selected_rule_codes IS NULL`** → #4.
3. **Sửa công thức hash** (post-resolver + label/json_mode/known_pending) + **Phase 3b enumerate 8 caller** → #5 #7.
4. **§5.1/§10 bổ sung** `_build_dila_card_prompt`, `_t126_build_qa_prompt` (app.py), `_t73_call_gemini` (app.py), READ sites (~22) → #6 #8 #9.
5. **§5/§7/§8** (extract ≥2 chars, coverage dry-run, fingerprint mass-miss) → #10 #11 #12.
6. **§14.1/§2 Bảng thật** số mới (112/1762/rv15/RULE-001..015) — **đã sửa**.

**Chưa áp checklist Phase 3 = chưa đủ điều kiện Phase 3 (wrap app.py).**

---

## 15. ABSORB DIRECTIVE v2 (2026-09-25 — Admin duyệt Phương Án D → task T177)

> Review đầy đủ: `docs/Mimo-Flash/T177-directive-v2-trie-xml-dualhash-REVIEW.md` (Bảng A/B/C/D).
> Task quản lý: `docs/Mimo-Flash/T177-dynamic-filter-absorb-directive-v2.md`.
> **Nguyên tắc:** absorb vào T165 (SSOT này), KHÔNG tạo engine/task song song; mọi thay đổi nằm trong
> `app.py` + `scripts/t50_passage_vi_backfill.py` + module `style_constitution.py` (T165 §5).

| Directive v2 | Quyết định absorb | Nơi áp |
|--------------|-------------------|--------|
| Dynamic filter (Trie) thay substring | **GATE phase**: chỉ build Trie/Aho-Corasick khi **`n_terms ≥ 1000`** (hiện **89** term terminology active sau D6 → substring đủ); đo lại khi > 1000 | §7 Phase 8 |
| XML boundary cho prompt | **T165 Phase 8** (optional, sau Admin QA phase 1 — KHÔNG gate phase 1–7); XML block gồm `<source>` + output-format contract + rule theo `match_scope` (Bảng B B6) | §7 Phase 8 |
| Dual-hash cache | Đã có `constitution_hash` (additive, KHÔNG ghi đè `source_hash`); hash phần **THẬT đã inject** sau `finalize_lock` (glossary ⊕ exemplar ⊕ label ⊕ json_mode ⊕ PFV ⊕ T166 fingerprint) — xem §3/§5 + Bảng B B1–B4 | §3/§5 |
| Retry/backoff 429 + persist `prompt_tokens` | **D3(a)** acceptance §8 (mục 13) | §8 |
| Row `status='edited'` chống REPLACE | **D3(b)** acceptance §8 (mục 14) | §8 |
| Invalidate burst có giới hạn | **D3(c)** acceptance §8 (mục 15) | §8 |
| Badge `rules_outdated` + cache list đúng | **D3(d)** acceptance §8 (mục 16) | §8 |
| Test Case 2 (sửa rule → chỉ dòng dính rule MISS) | **D8** = acceptance chính, fixture thật `A009460 丹霞天然` | §8 mục 2/2b/2c/17 |
| Data fix `NO_PINYIN` + `HANVIET_NAMES` | **✅ D6 (2026-09-26):** NO_PINYIN restore text seed T73; HANVIET_NAMES DEACTIVATE; script `scripts/t177_d6_rules_fix.py --stats/--dry-run/--apply/--revert` | T177 D6 |
| Baseline `prompt_tokens` thật (không bịa 150–250) | **✅ D7 (2026-09-26):** prompt_tokens **= 3.422** thật (Groq `qwen/qwen3.8-27b`); ngân sách ~3.400–3.700, cấm hard-gate | session T177 + §8 mục 11/13 |
| P0 code reference sai (Bảng B B1–B8) | ✓ **Đã ghi cách sửa** trong `T177-directive-v2-trie-xml-dualhash-REVIEW.md` §3 — KHÔNG copy nguyên trạng | REVIEW §3 |
