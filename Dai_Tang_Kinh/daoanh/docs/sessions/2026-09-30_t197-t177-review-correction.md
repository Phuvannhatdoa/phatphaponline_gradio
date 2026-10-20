---
task: T197 + T198
date: 2026-09-30
status: T197 DONE (docs-only, 0 code/0 DB) · T198 OPEN (blocked chờ Admin duyệt)
scope: T177 REVIEW correction (docs) + task mới T198
admin: "1) đồng ý  2) mở task riêng"
commit_pass1: "9774ea4f1f3b43d07aa4c23064a71b50361788d4"
commit_pass2: "b7058317468bfd60b52fd8e4fa79d0b3c997ac4f"
revert: "git revert --no-edit 9774ea4f1f3b43d07aa4c23064a71b50361788d4 b7058317468bfd60b52fd8e4fa79d0b3c997ac4f"
---

# Session 2026-09-30 — T197 T177 REVIEW correction + T198 tách task

## 1. Yêu cầu của Admin

Admin yêu cầu review 2 file T177 (`docs/Mimo-Flash/X-T177-directive-v2-trie-xml-dualhash-REVIEW.md` +
`docs/Mimo-Flash/X-T177-dynamic-filter-absorb-directive-v2.md`) xem claim có đúng logic chưa.
Sau khi trình bày findings, Admin chốt:
1. **P0-1 (429) → đồng ý** phương án *thêm Correction log, KHÔNG viết lại §1.3* (giữ lịch sử audit)
2. **Mục 6 (invalidate DELETE) → mở task riêng**, không gộp vào T197

## 2. Review đã verify (read-only DB + code)

DB mở `mode=ro`, không ghi gì.

### Phần ĐÚNG — giữ nguyên
| Claim | Verify |
|---|---|
| B1 sai field `code/type/content` | schema thật `rule_code`/`rule_type`/`rule_text` |
| B2 hash join-code gây va chạm | đúng; fix đã có — `constitution_hash` nạp FULL `rule_text` + join `\n` |
| B3 hash thiếu thành phần | đúng; fix đúng — tính hash **sau** khi lock dựng xong |
| B4 ghi đè `source_hash` | đúng — `UNIQUE(source_hash, source_type)` có thật, `constitution_hash` additive |
| B5 `達磨`/`面壁` không có thật | đúng — 0 rule / 0 glossary |
| B7 cấm `.bak` | đúng |
| B8 stack bịa (`admin/app.py`) | đúng — không tồn tại |
| D6 fix data | đúng — `HANVIET_NAMES is_active=0`, `NO_PINYIN` 201 chars, `_keep_` active = 0 |
| glossary 79 locked / 14 term 1-char / exemplar 2.692 | khớp tuyệt đối |

### P0-1 — 429: §1.3 đúng tại mốc, nhưng kết luận "phòng vệ" SAI
- §1.3: "429 **chưa từng xảy ra** … retry/backoff là **biện pháp phòng vệ**"
- Task §D3(a): "retry/backoff 429 = **gap thật** (429 **3/5 đo**)"
- Task §D7: "**429 xịt thật 3/5 lần**"
- `app.py:17718-17719` (T178): docstring "**429 thật 3/5 lần theo đo T177 D7**", đã build `_T73_429_MAX_RETRY=2`, backoff `0.5s → 1s`

⇒ 429 là sự cố **thật**, retry là fix **bắt buộc**. A8 + C1 **đã lỗi thời**.

### P1-1 — Fixture: từ khoá là `丹霞`, KHÔNG phải `天然`
| Chuỗi | `translation_rules.rule_text` | `translation_glossary.term_zh` |
|---|---|---|
| `達磨` | 0 | 0 |
| `面壁` | 0 | 0 |
| `丹霞` | **2** (`TERM_DANHA`, `TERM_DAN_HA`) | 0 |
| `天然` | **0** | **0** |

Fixture `A009460`: `name_zh = 丹霞天然`, `name_vi = Đơn Hà Thiên Nhiên`, `status = verified`.
⇒ **Cơ chế vẫn đúng** (sửa rule `丹霞` ⇒ đổi `constitution_hash` ⇒ row A009460 MISS),
chỉ sai **từ khoá ghi trong docs**. Ai viết assert theo `天然` sẽ xây test không phân biệt được.

### P1-2 — `constitution_hash` có 10 phần, không phải 8
`style_constitution.py:211-234`: `rules` · `glossary` · `exemplar` · `FMT:` · `label:` · `json:` ·
`known:` · `fp:` · `extra_hash` · **`p8:alignment_method`** (chỉ khi `!= 'none'`, T165-P8).
Task doc ghi "8 phần" + line-ref `168-199` → sửa thành **10 phần** + **`211-234`**.

### P1-3 — Rendered < Raw do trộn 2 mốc đo (KHÔNG phải lỗi tính toán)
`rendered ≥ raw` là bất biến. §1 ghi rendered `12.287` nhưng raw `13.230` ⇒ `rendered` đo 2026-09-25,
`raw` đo lại 2026-09-26 (sau D6: 13.041 → 13.230). Ước lượng hiện tại: raw 19.014 + overhead ~1.905 ⇒ ≈ **20.919**.

### P1-4 — Line-ref lệch 7/7 (`app.py` 21.232 → **22.896**)
| Cũ | Thực tế 2026-09-30 |
|---|---|
| `app.py:16575` `_t73_call_gemini` | **`17713`** |
| `app.py:16569` `_t73_build_style_prompt` | **`17703`** |
| `app.py:16412` `_t73_rules_version` | **`17520`** |
| `app.py:18396` endpoint invalidate | **`19725`** (`UPDATE` status tại `18350`) |
| `app.py:16606` `_t165_log_prompt_metrics` | **import alias `app.py:44`**, gọi tại **`17771`** |
| `style_constitution.py:436` đọc usage | **`518`** (`log_prompt_metrics`) |
| `app.py:16382` model id | đã trôi (nay qua config) |

Đúng bệnh stale line-ref mà **T194** vừa sửa cho T176; T177 chưa qua đợt sửa đó.

### P2 — Snapshot trôi + context thiếu
| Hạng mục | Docs 2026-09-26 | Verify 2026-09-30 |
|---|---|---|
| `translation_rules` active | 110 | **119** |
| `sum(length(rule_text))` | 13.230 | **19.014** |
| terminology / forbidden / grammar | 88 / 6 / 1 | **91 / 10 / 2** |
| `translation_rules` total | 112 | **123** |
| `translation_cache` rows | 1.762 | **1.900** |
| glossary locked / 1-char | 79 / 14 | 79 / 14 (không đổi) |
| `translation_exemplar` | 2.692 | 2.692 (không đổi) |

**B4** "15 chỗ `FROM translation_cache`" → **18** · **B8** "12 app + 3 style" → **13 + 4**.

**Context chưa ai ghi:**
1. `constitution_hash` chỉ populate **1/1900 row** (`id=1899`, `A010291`, 2026-09-29) ⇒ **dual-hash có schema nhưng chưa backfill**
2. **1900/1900 row `status='invalidated'`** ⇒ cache rỗng hiệu lực; lần "Dịch lại" kế = 1.900 lượt LLM
3. `invalidate_cache_for_rule` / `invalidate_cache_all_semantic` dùng **`DELETE`** thật (`style_constitution.py:452`, `:467`),
   khác endpoint `POST …/translate/invalidate` (`UPDATE status='invalidated'`, `app.py:18350`)
   ⇒ A4 chỉ mô tả nửa "soft"; nhánh DELETE **mất vĩnh viễn** bản dịch + audit trail (`report_count`, `approved_by`)
   ⇒ **TÁCH TASK T198** theo chỉ đạo Admin

## 3. T197 đã sửa gì

**File `X-T177-directive-v2-trie-xml-dualhash-REVIEW.md`:**
- §1.3: **giữ nguyên toàn bộ** + thêm marker ⚠ trỏ §8 P0-1 (không sửa kết luận cũ)
- Thêm banner "Line-ref đã re-verify 2026-09-30" + hàng "8 mốc đo" vào bảng §1
- §1.3 thêm dòng chú thích mốc đo (P1-3)
- Bảng A1–A8: đổi line-ref sang vị trí hiện tại; A8 thêm cảnh báo "ĐÃ LỖI THỜI → xem §8 P0-1"; A4 thêm cảnh báo 2 hành vi soft/hard
- B3: ghi rõ **10 phần** + `style_constitution.py:211-234`
- B4: 15 → **18** chỗ
- B5: match substring `天然` → **`丹霞`** (rule `TERM_DANHA` + `TERM_DAN_HA`)
- Bảng D: thêm dòng trỏ §8
- Thêm **§8 CORRECTION LOG — verify lại 2026-09-30** (P0-1, P1-1, P1-2, P1-3, P1-4, P2) + bảng so số + 3 context thiếu

**File `X-T177-dynamic-filter-absorb-directive-v2.md`:**
- D2-B3: "8 phần" → "**10 phần**", line-ref `168-199` → `211-234`, ghi hash tính tại L234 sau lock L304-320
- D2-B5: match substring `天然` → **`丹霞`** + ghi DB verify 0/0
- D8: acceptance §8 mục 17 `天然` → **`丹霞`**

**Task mới:** `tasks/T197-t177-review-correction.md`, `tasks/T198-invalidate-soft-vs-hard.md`

## 4. T198 (task riêng, blocked chờ Admin)

`tasks/T198-invalidate-soft-vs-hard.md` — matrix soft vs hard invalidate:
- soft: `POST /daoanh/api/admin/translate/invalidate` (`rv=ALL`/`rule_code`/`ids`) → `UPDATE status='invalidated'` + `invalidated_at/by/reason` (giữ row, có audit)
- hard: `invalidate_cache_for_rule` (`DELETE ... source_hash IN / source_text LIKE`) + `invalidate_cache_all_semantic` (`DELETE ... selected_rule_codes IS NOT NULL`)
- docs-first: `docs/db_schema.md` + T169 task + session; **không** đổi behavior code trong T198
- Admin cần quyết: giữ soft cho semantic-wide, hay thêm cờ hard-purge, hay chấp nhận hard

## 5. Verify + commit

- `npm run guard` PASS (SSOT root = `visjs-app`, không `.git` trong `daoanh/`)
- `npm run lint` PASS (7 script blocks)
- `npm run test` PASS
- DB re-verify 10/10 khớp §8 (active 119 · chars 19.014 · 91/10/2 · total 123 · cache 1.900 ·
  invalidated 1.900 · constitution_hash 1 · glossary 79/14 · exemplar 2.692)
- `天然` còn sót trong 2 doc T177 = **0** (chỉ còn trong Correction log dạng giải thích)
- Commit pass-1: `9774ea4f1f3b43d07aa4c23064a71b50361788d4` (4 file: REVIEW + absorb + T197 task + T198 task)
- Commit pass-2: `b7058317468bfd60b52fd8e4fa79d0b3c997ac4f` (hash-fill 2 dòng tasktodo/ROLLBACK)

## 6. ROLLBACK

`git revert --no-edit 9774ea4f1f3b43d07aa4c23064a71b50361788d4 b7058317468bfd60b52fd8e4fa79d0b3c997ac4f` — docs-only, 0 code/0 DB.