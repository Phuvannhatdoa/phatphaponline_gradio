---
id: T179
title: "T165 Phase 8 (XML boundary + Trie có gate) + ĐÍNH CHÍNH kết luận T178"
module: Editorial / LLM Translation
priority: high
status: done
owner: claudecode
depends_on: [T165, T177, T178]
created: 2026-09-26
updated: 2026-09-27
spec: docs/Mimo-Flash/X-T165-rules-constrained-translation-engine-SPEC.md
absorbed_from: tasks/T178-t165-build-gap-d3-13-17.md
plan_approved_at: "2026-09-26 (Admin: 'T179 và cả phase 8 làm luôn')"
done_when: |
  1) **ĐÍNH CHÍNH:** chứng minh bằng hash THẬT rằng `constitution_hash` là **PER-ROW** (chỉ gồm
     rule dòng đó chọn) ⇒ T165 §8 mục 2/2b/2c **đã thỏa sẵn**; kết luận "KNOWN ARCH GAP" ở
     T178 là SAI (do test dùng hash giả) ⇒ đã gỡ hướng per-rule fingerprint.
  2) Sửa gap THẬT mà T178 phát hiện gián tiếp: fallback legacy của `lookup_cache` áp cho MỌI
     row nên đổi glossary/label/json vẫn HIT ⇒ §8 mục 3 + 5b KHÔNG thỏa. Giới hạn fallback
     chỉ cho row `constitution_hash IS NULL` (tương thích ngược: 1.762/1.762 row hiện NULL).
  3) Phase 8a: XML boundary trong prompt + bump PROMPT_FORMAT_VERSION 't165-v1'→'t165-v2'.
  4) Phase 8b: Trie/Aho-Corasick (`term_matcher.py`) + gate n_terms>=1000, DORMANT vì đo thật
     chỉ 76 unique term; auto-bật khi vượt ngưỡng (test 1.000/1.200 term).
  5) Phase 8c: đo token v1 vs v2 + cột `prompt_fmt` để theo dõi theo thời gian.
  6) KHÔNG regression: T165 11/11 · T166 18/18 · T167 15/15 · T178 69/69 · T179 49/49 ·
     npm run pipeline PASS; revert range 0 conflict (chứng minh trong scratch worktree).
---

# T179 — T165 Phase 8 + Đính chính kết luận T178

## 0. Đo thật trước khi build

| Đại lượng | Giá trị | Hệ quả |
|----------|---------|--------|
| `match_scope='always'` (rule active) | 40 | luôn inject |
| `match_scope='terms'` (rule active) | 70 | lọc theo source |
| **Unique `match_terms`** | **76** | **Gate Trie (≥1000) CHƯA ĐẠT ⇒ Phase 8b DORMANT** |
| exemplar active / glossary rows | 3 / 79 | — |
| `selected_rule_codes` NOT NULL | **0 / 1762** | không backfill được retro |
| T167 benchmark baseline | 15/15 PASS | regression guard |

## 1. ĐÍNH CHÍNH — kết luận T178 là SAI

T178 kết luận: *"`constitution_hash` là GLOBAL toàn ruleset ⇒ sửa rule nào cũng làm mọi dòng
cache MISS ⇒ §8 mục 2/2c không thỏa, cần per-rule fingerprint."*

**Đo lại với hash THẬT** (`tests/test_t179_phase8.py` A–C):

```
A chọn {R_NATURAL, NO_ADDITION} → hash 47a61a125222f711
B chọn {NO_ADDITION}            → hash 5dc01ebfd01a6e1b
sửa R_NATURAL (B KHÔNG chọn):
  A → dd930f932660322c  (ĐỔI)
  B → 5dc01ebfd01a6e1b  (KHÔNG đổi  ← B không chọn R)
thêm R_BIJING (không match source):
  hash A → 21007b8f904c0e17 (KHÔNG đổi ⇒ A HIT 100%)
sửa NO_ADDITION (static, mọi dòng đều chọn):
  hash → c4af2c720e33ca42 (ĐỔI ⇒ tất cả MISS)
```

⇒ `constitution_hash` là **PER-ROW**: nó chỉ gồm các rule mà `style_lock(source_text=...)`
chọn cho dòng đó. **§8 mục 2, 2b, 2c đã thỏa sẵn từ T165.**

**Nguyên nhân sai lầm:** test T178 dùng hash **GIẢ** (`'HASH_V1'` → `'HASH_V2'`) thay vì
hash thật, nên ép kết quả "over-invalidate". Đây là lỗi của **test**, không phải của code —
và tôi đã báo cáo kết luận đó cho Admin như một "phát hiện kiến trúc".

**Hành động:** hướng per-rule fingerprint (2 cột DB + nhánh lookup + 10 call site) **đã bị
GỠ** — vì fast path đã đúng, nhánh đó là **dead code** có nguy cơ sai lệch. Giữ lại sẽ là
nợ kỹ thuật vô nghĩa.

## 2. Gap THẬT mà T178 phát hiện gián tiếp (đã sửa)

`lookup_cache` có fallback legacy theo `rules_version`. Vì `rules_version` chỉ hash
`rule_text`, nên khi **đổi glossary / prompt_label / json_mode** thì `rules_version` **không
đổi** → dòng vẫn HIT qua fallback ⇒ **§8 mục 3** ("đổi glossary đã inject → MISS") và
**mục 5b** (label/json khác → hash khác → MISS) **không thỏa**.

**Fix (tối thiểu, tương thích ngược):** fallback chỉ dành cho row **chưa có**
`constitution_hash` (`AND constitution_hash IS NULL`), có guard `_has_col` cho pre-migration DB.

- Tương thích ngược: **1.762/1.762 row hiện có NULL** ⇒ hành vi của chúng **không đổi**;
  row mới (có hash) mới bị chi phối bởi hash ⇒ miss là miss thật.
- Đây là fix **1 điều kiện SQL**, không thêm bảng/cột.

## 3. Phase 8a — XML boundary

- `build_style_prompt` bọc `<rules>` / `<glossary>` / `<exemplars>` / **`<source>`**
  (contract B6 của directive: model phân biệt "văn bản cần dịch" với "chỉ dẫn").
- Escape `& < >` để rule/glossary text chứa ký tự đặc biệt không phá prompt.
- `json_mode=True` **không** bọc kết quả → caller `json.loads` vẫn được (contract giữ nguyên).
- `xml=False` cho khung v1 (chỉ để đo token 8c).
- Bump `PROMPT_FORMAT_VERSION` `'t165-v1'` → **`'t165-v2'`** ⇒ hash đổi ⇒ cache cũ miss
  **đúng một lần** rồi ổn định (vì hash là per-row nên chỉ ảnh hưởng dòng đã dịch).

## 4. Phase 8b — Trie/Aho-Corasick (DORMANT theo gate)

`term_matcher.py`:
- `TermMatcher(terms)` — trie + fail links, `scan(text)` trả set term có mặt (1 lần quét).
- `scan_terms(text, terms)` — chọn đường theo gate `n_unique_terms >= TRIE_MIN_TERMS (1000)`;
  dưới ngưỡng dùng `in` (substring) như trước ⇒ **hành vi không đổi** ở trạng thái hiện tại.
- `select_rules` chỉ dựng trie khi **vượt** ngưỡng ⇒ Zero-RAM (không dựng gì ở 76 term).

**Tôn trọng gate, không ép dùng:** SPEC §7 phase 8 nêu rõ "chỉ khi `n_terms≥1000`"; đo thật
76 ⇒ trie **DORMANT**. Test chứng minh auto-bật ở 1.000/1.200 term và trie ≡ substring.

## 5. Phase 8c — Đo token trước/sau XML

- Cột `translation_prompt_metrics.prompt_fmt` (additive, idempotent) để theo dõi theo thời gian.
- Đo offline, **không** gọi Groq. Không có `tiktoken` ⇒ dùng ước lượng có cơ sở
  (Hán 2×, ASCII 1×) và **ghi rõ là ước lượng** trong `data/t179_token_measure.json`.
- Kết quả đo (fixture `A009460`): v1 **1.106** token → v2 **955** token ⇒ **−151 (−13,7%)**.
  XML **rút ngắn** prompt (bỏ mấy tiêu đề `=== ... ===` dài, thay bằng thẻ ngắn).

## 6. Files

| File | Việc |
|------|------|
| `term_matcher.py` | **MỚI** — Aho-Corasick + gate |
| `style_constitution.py` | `PROMPT_FORMAT_VERSION='t165-v2'` · XML trong `build_style_prompt` · `lookup_cache` giới hạn fallback legacy · `persist_prompt_metrics(prompt_fmt=)` · `select_rules` dùng gate |
| `scripts/t165_rules_engine_migrate.py` | +cột `prompt_fmt` (idempotent) + `--stats` theo `prompt_fmt` |
| `tests/test_t179_phase8.py` | **MỚI** — 49 assert (A–H) |
| `tests/test_t178_gap_d3.py` | đính chính 17k/17m-bis dùng hash THẬT |
| `tests/test_t165_style_constitution.py` | `test_lookup_dual_key` cập nhật theo hành vi fallback mới |
| `package.json` | `test:t179` + `test:t167` vào `test:translation` |
| `data/t179_token_measure.json` | kết quả đo 8c |

## 7. Ràng buộc
- **Additive-only**: chỉ `ADD COLUMN`; 0 `DROP` bảng đang dùng; 0 `DELETE` dữ liệu.
- **KHÔNG** thay đổi contract JSON của `json_mode`.
- Dòng cũ NULL ⇒ hành vi giữ nguyên (tương thích ngược).
- Cấm `cp *.bak`; revert bằng `git revert` range + `--revert` migration.

## 8. Revert — **ĐÃ KIỂM CHỨNG** (scratch worktree, đã xoá sau test)

```bash
# SSOT repo root = visjs-app
git revert --no-commit --no-edit 2e252d0~1..cc54249
git commit -m "revert: T179 - phase 8 + fix legacy fallback"
```

| Kiểm tra | Kết quả |
|----------|---------|
| Conflict khi revert range | **0** file |
| Marker `term_matcher` | 0 |
| Marker `t165-v2` | 0 |
| Marker `<source>` (XML) | 0 |
| Marker `prompt_fmt` | 0 |
| Marker `TRIE_MIN_TERMS` | 0 |
| File mới `term_matcher.py` | **đã xoá** |
| File mới `tests/test_t179_phase8.py` | **đã xoá** |
| `py_compile style_constitution.py` sau revert | **PASS** |

| Loại | Lệnh | Trạng thái |
|------|------|-----------|
| Code + tests + docs (cả series) | `git revert --no-commit --no-edit 2e252d0~1..cc54249` | ✅ **0 conflict** |
| Cột `prompt_fmt` | `python scripts/t165_rules_engine_migrate.py --revert` | ✅ (kèm DROP bảng metrics — append-only, chỉ log đo) |
| Backup DB | `data/backups/lineage_t165_20260926_220446.db` | ✅ có |
| **Cấm** | `cp *.bak` | ⛔ |
