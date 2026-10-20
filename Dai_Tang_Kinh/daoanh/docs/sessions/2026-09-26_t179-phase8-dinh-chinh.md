# Session — T179: T165 Phase 8 + Đính chính kết luận "KNOWN ARCH GAP" của T178

> **Ngày:** 2026-09-26 · **Trigger:** Admin "T179 và cả phase 8 làm luôn"
> **Task:** `tasks/T179-per-rule-fingerprint-phase8.md`
> **Bối cảnh:** T178 build 4/5 gap D3/D8 và **báo Admin một gap kiến trúc** (`constitution_hash`
> GLOBAL ⇒ §8 mục 2/2c không thỏa). T179 được mở để sửa gap đó + build Phase 8.

## 0. Đo thật trước khi build

| Đại lượng | Giá trị | Hệ quả |
|----------|---------|--------|
| `match_scope='always'` / `'terms'` (rule active) | 40 / 70 | — |
| **Unique `match_terms`** | **76** | **Gate Trie (≥1000) CHƯA ĐẠT ⇒ 8b DORMANT** |
| Tổng term kể trùng | 91 | — |
| exemplar active / glossary rows | 3 / 79 | — |
| `selected_rule_codes` NOT NULL | **0 / 1762** | không backfill được retro |
| T167 benchmark baseline | 15/15 PASS | regression guard |

## 1. ĐÍNH CHÍNH — kết luận T178 SAI (phần quan trọng nhất)

T178 đã báo Admin: *"`constitution_hash` là GLOBAL toàn ruleset ⇒ sửa rule nào cũng làm mọi
dòng cache MISS ⇒ §8 mục 2/2c không thỏa, cần per-rule fingerprint."*

**Đo lại với hash THẬT** (temp DB, `style_lock(source_text=...)`):

```
A chọn {R_NATURAL, NO_ADDITION}  → hash 47a61a125222f711
B chọn {NO_ADDITION}             → hash 5dc01ebfd01a6e1b

sửa R_NATURAL (B KHÔNG chọn):
   A → dd930f932660322c   ĐỔI
   B → 5dc01ebfd01a6e1b   KHÔNG ĐỔI   ← B không chọn R nên hash của B không đụng

thêm R_BIJING (không match source X):
   hash A → 21007b8f904c0e17  KHÔNG ĐỔI  ⇒ X HIT 100% (§8 mục 2c thỏa)

sửa NO_ADDITION (static, mọi dòng đều chọn):
   hash → c4af2c720e33ca42  ĐỔI  ⇒ tất cả MISS (§8 mục 2b thỏa)
```

⇒ `constitution_hash` là **PER-ROW**: nó chỉ gồm các rule mà dòng đó chọn.
**§8 mục 2, 2b, 2c đã thỏa sẵn từ T165.**

**Nguyên nhân sai lầm:** test T178 dùng sentinel hash **giả** (`'HASH_V1'` → `'HASH_V2'`)
thay vì hash thật, nên ép kết quả "over-invalidate" rồi báo như phát hiện kiến trúc.

**Bài học (ghi lại để không lặp lại):** test "chứng minh" điều gì đó phải dùng **giá trị
thật** từ DB/model. Dùng sentinel cố định sẽ dẫn kết luận sai rồi báo Admin như gap thật.

## 2. Gỡ hướng per-rule fingerprint (dead code)

Đã xây rồi rồi gỡ: `rules_fingerprint` + `context_fingerprint` (2 cột DB), `_rule_compat_hit`,
`lookup_cache(allow_rule_compat=…)`, 4 nhánh `write_cache`, wrapper `_t73_lookup_cache` + 6 read
site + 4 write site ở `app.py`, index `idx_cache_rules_fp`, cột trong migration.

**Lý do gỡ:** fast path `constitution_hash` **đã đúng**; nhánh rule-compat không bao giờ hợp lệ
kích hoạt mà chỉ thêm 2 cột + 1 nhánh SQL + rủi ro sai lệch. Giữ lại là nợ kỹ thuật vô nghĩa.

Cách gỡ an toàn: `app.py` trích lại từ HEAD bằng `git cat-file -p` (byte-safe) — **không** dùng
redirect `>` của PowerShell ( nó ghi UTF-16, làm hỏng file) và **không** dùng `git checkout`
(index đang bị agent khác khóa).

## 3. Gap THẬT mà T178 phát hiện gián tiếp — đã sửa

`lookup_cache` có fallback legacy theo `rules_version`. Vì `rules_version` **chỉ hash
`rule_text`**, nên đổi **glossary / `prompt_label` / `json_mode`** không đổi `rules_version`
⇒ dòng vẫn HIT qua fallback ⇒ **§8 mục 3** ("đổi glossary đã inject → MISS") và **mục 5b**
(label/json khác → hash khác → MISS) **không thỏa**.

**Fix (1 điều kiện SQL):** fallback chỉ dành cho row **chưa có** `constitution_hash`
(`AND constitution_hash IS NULL`), có guard `_has_col` cho pre-migration DB (lần đầu quên
guard → test `test_pre_migration_guards_16` fail `no such column: constitution_hash`, đã sửa).

- Tương thích ngược: **1.762/1.762 row hiện NULL** ⇒ hành vi không đổi.
- `test_lookup_dual_key` (T165) cập nhật: vẫn giữ ca legacy row, nhưng row đã có hash thì
  **không** được fallback.

## 4. Phase 8a — XML boundary

- `build_style_prompt` bọc `<rules>` / `<glossary>` / `<exemplars>` / **`<source>`**
  (contract B6 directive: tách "văn bản cần dịch" khỏi "chỉ dẫn").
- Escape `& < >` (`_xesc`) — không phá prompt khi rule text chứa ký tự đặc biệt.
- `json_mode=True` **không** bọc kết quả ⇒ caller `json.loads` không đổi.
- `xml=False` → khung v1 (chỉ để đo token 8c).
- Bump `PROMPT_FORMAT_VERSION` `'t165-v1'` → **`'t165-v2'`** ⇒ cache cũ miss **đúng 1 lần**
  rồi ổn định (hash per-row nên chỉ ảnh hưởng dòng đã dịch, không phải 1.762 dòng).

## 5. Phase 8b — Trie/Aho-Corasick (DORMANT theo gate)

`term_matcher.py`:
- `TermMatcher(terms)` — trie + fail links + output gộp; `scan(text)` 1 lần quét.
- `scan_terms(text, terms)` chọn đường theo `TRIE_MIN_TERMS = 1000`.
- `select_rules` chỉ dựng trie khi **vượt** ngưỡng ⇒ ở 76 term **không dựng gì** (Zero-RAM,
  hành vi y hệt trước T179).

**Tôn trọng gate, không ép dùng:** SPEC §7 phase 8 nói rõ "chỉ khi `n_terms≥1000`". Đo thật
76 ⇒ DORMANT. Test chứng minh: trie ≡ substring trên fixture thật, và auto-bật ở 1.000 /
1.200 term (kể cả 1.000 term thật trong temp DB).

## 6. Phase 8c — Đo token trước/sau XML

- Cột `translation_prompt_metrics.prompt_fmt` (additive, idempotent, có guard vì
  `ALTER TABLE ADD COLUMN` không có `IF NOT EXISTS`).
- Đo offline, **không** gọi Groq. Không có `tiktoken` ⇒ ước lượng có cơ sở (Hán 2×, ASCII 1×)
  và **ghi rõ là ước lượng** trong `data/t179_token_measure.json` (không bịa số chính xác).
- **Kết quả:** v1 **1.106** token → v2 **955** token = **−151 (−13,7%)**. XML **rút ngắn**
  prompt (thay mấy tiêu đề `=== … ===` dài bằng thẻ ngắn).
  File kất quả: `data/t179_token_measure.json` — thư mục `data/` bị `.gitignore` nên **KHÔNG commit**;
  số đã ghi đúng session này (v1=1106 · v2=955 · delta=−151 · −13,7% · cơ sở ước lượng).

## 7. Migration

`--apply` prod: chỉ thêm cột `prompt_fmt` (5 cột T165 + bảng metrics đã có ⇒ `[skip]`).
Backup `data/backups/lineage_t165_20260926_220446.db`. Verify prod: cache 1.762 · rules active
110 · edited 6 (bảo vệ) · **0 cột fingerprint** (đã gỡ sạch) · metrics 0 row.

## 8. Test

| Suite | Kết quả |
|-------|---------|
| T165 style_constitution | 11/11 |
| T166 canonical_lock | 18/18 |
| T167 benchmark | 15/15 |
| T178 gap_d3 | 69/69 (đã đính chính 17k/17m-bis dùng hash thật) |
| **T179 phase8 (mới)** | **49/49** |
| `npm run pipeline` | PASS (chỉ `e2e:runtime` EPERM pre-existing) |

`package.json`: thêm `test:t179` + `test:t167` vào `test:translation` (trước đó benchmark T167
không chạy trong CI).

## 9. Revert — **ĐÃ KIỂM CHỨNG** (scratch worktree, đã xoá)

T179 là series 3 commit (`2e252d0` build → `d9b236f` hash-fill → `cc54249` pass3) ⇒ revert
**cả range** (không revert commit giữa):

```bash
git revert --no-commit --no-edit 2e252d0~1..cc54249   # 0 conflict
```

| Kiểm tra | Kết quả |
|----------|---------|
| Conflict | **0** file |
| 6/6 marker T179 (`term_matcher` · `t165-v2` · `<source>` · `prompt_fmt` · `TRIE_MIN_TERMS` · `test_t179`) | **0** |
| 2 file mới (`term_matcher.py` · `tests/test_t179_phase8.py`) | **đã xoá** |
| `py_compile style_constitution.py` | **PASS** |

## 10. Còn lại

- **Admin QA 1 lần dịch thật** để xác nhận XML không làm hỏi output (offline mới chỉ chứng
  minh prompt đúng hình dạng + token giảm).
- **Phase 9**: Trie khi `n_terms ≥ 1000` (hiện 76) — chỉ cần đo lại, code đã sẵn.
- Backfill `constitution_hash`/`selected_rule_codes` cho cache cũ: **không thể retroactively**
  (không biết rule nào đã chọn lúc dịch) ⇒ giữ `unverified` là trung thực.
