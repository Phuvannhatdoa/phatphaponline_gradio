# Session 2026-09-25 — T166 Phase 1: Canonical Identity Hard Guard (core module)

**Task:** T166 · **Phase:** 1/5 (`canonical_lock.py` build/assert/normalize) · **Status:** ✅ DONE
**Branch:** `master` · **Repo SSOT root:** `visjs-app` (`git rev-parse --show-toplevel`)

---

## 1. Scope Phase 1

| Hạng mục | Kết quả |
|----------|---------|
| `canonical_lock.py` — core module | ✅ tạo mới (~1050 dòng) |
| `build_canonical_lock(conn, source_text)` — SQL batch 8 nguồn | ✅ |
| `pre_assert` / `post_assert` (P-PARTIAL \| P-STOP) | ✅ |
| `normalize_vi` / `extract_maximal_han_runs` / `is_valid_vi` | ✅ |
| `t166_lock_fingerprint` (ghép T165 `constitution_hash`) | ✅ |
| `build_lock_prompt_section` (4 khối LOCKED/CANDIDATE/CONFLICT/UNKNOWN) | ✅ |
| `translate_with_guard(conn, src, call_llm_fn, policy)` — wrapper 3 đường | ✅ |
| `tests/test_t166_canonical_lock.py` (hermetic, temp DB) | ✅ **18/18 PASS** |
| `tests/test_t166_matrix.py` (DB thật, read-only) | ✅ **23/23 PASS** |

---

## 2. Audit DB thật trước khi build (verify 2026-09-25)

| Bảng · cột | Giá trị thật | Ảnh hưởng |
|-------------|--------------|-----------|
| `person_display_names.verification_status` | `verified_direct`, `verified_crosswalk` — **không có `'approved'`** | §3.1 #2 → `LIKE 'verified%'` |
| `person_name_correction.status` | `applied`, `pending` — **không có `'approved'`** | §3.1 #4 → `status='applied'` |
| `vn_person_authority.status` | `verified`, `pending`, `auto_ttl`, `alias_zh_match`, `alias_vi_suffix` | chỉ `verified` mới LOCK |
| `canonical_decision` | cột tên thật = **`canonical_name_vi`** (không phải `canonical_value`); cả 2 row **mojibake** (`Th? S?t H?i`) | phải `is_valid_vi` loại |
| `name_vi_map` | `name_vi_final NOT NULL` = 5205 · `final+approved` = **1** (玄奘) | ngưỡng authority rộng, boost riêng |
| `namevi_map_places.vn_name_status` | `reviewed` chỉ **2 row** (1 mojibake) | nguồn yếu, không kỳ vọng phổ biến |
| `translation_glossary` | `is_locked=1` 79 row, gồm term **1-char** (法/僧/戒…) | 1-char → severity WARN |
| Fixture chuẩn | `A009460 丹霞天然 → Đơn Hà Thiên Nhiên` (vnpa verified) · `A005248 安廩 → An Lẫm` (auto 0.7, final NULL) | LOCK + CANDIDATE |

---

## 3. BUG tìm ra khi build — 6 lỗi logic (đều đã fix + có test)

### 3.1 [P0] Mâu thuẫn nội tại SPEC §6 vs §6.3 — trigger mismatch vô dụng
- **SPEC §6** yêu cầu trigger `match_by_maximal_han_run(output, entry.source_form)`.
- **SPEC §6.3** đòi output thuần tiếng Việt (`Thích Đơn Hà Mật`) → `HARD_FAIL`.
- ⇒ Output dịch **không chứa Hán** ⇒ trigger theo Han-run trong output **không bao giờ bắn**. Case B sẽ pass (sai).
- **Fix:** trigger đúng = Hán có trong **source** (lock build từ source nên chắc chắn) **và** output có render tên ⇒ tên đó phải là biến thể hợp lệ. Ghi chú lý do trong docstring.

### 3.2 [P0] Quyết định LOCK phải theo **FLAG**, không theo level
- Implement đầu tiên dùng `authority_level >= 1.0` ⇒ `vn_person_authority.verified` (level **0.95**) rơi xuống `CANDIDATE` ⇒ **fixture A009460 không LOCK** ⇒ matrix A/B vô nghĩa.
- **Fix:** thêm `_LOCK_FLAGS` + `is_lock_flagged()`. `authority_level` chỉ là RANK; LOCKED ⟺ có flag `verified/reviewed/applied/final+approved/admin_approved`.

### 3.3 [P0] Character-class VI sai 2 lần → nuốt/đứt tên
- `À-Ỹ` (U+00C0–U+1EF9) **chứa cả chữ thường** (`đ`=U+0111) ⇒ `"Hòa Thượng An Lẫm đến đây"` bị nuốt hết.
- Liệt kê tay ⇒ **thiếu chữ có dấu** (`à á ả ầ ế ử`).
- Start range ở U+00C0 ⇒ **thiếu ASCII** ⇒ `"Đơn"` chỉ match `"Đơ"` (thiếu `n`).
- Thiếu U+01A0–U+01FF ⇒ **thiếu `Ơ`/`Ư`** ⇒ `"Đơn"` chỉ match `"Đ"`.
- **Fix:** `_build_vn_class(upper)` sinh class tự động từ Unicode (U+0041–U+024F + U+1EA0–U+1EF8) lọc theo `.isupper()`. Có test kèm.

### 3.4 [P1] Lọc từ thường diện rộng — `Đại sư Pháp Vân` bị mất
- `pháp` nằm trong `_COMMON_AFTER_TITLE` ⇒ `Đại sư Pháp Vân` (tên thật) bị loại.
- **Fix:** chỉ lọc từ thường cho honorific **mơ hồ** (`Thích`/`Thích Ca`/`ngài`); `Đại sư`/`Thiền Sư`/`Hòa Thượng`/`Trưởng lão` gần như luôn đi kèm tên riêng.

### 3.5 [P1] Severity `CANONICAL_INVENTION` sai cho CANDIDATE
- SPEC §3.1: `auto_transliterate` (conf 0.5–0.7) → CANDIDATE, **"không HARD_FAIL khi LLM khác"**; §6.3 hàng 4: invention ở CANDIDATE = **cảnh báo**.
- Implement đầu tiên luôn `HARD` ⇒ `安廩` + tên bịa ⇒ `failed` (sai).
- **Fix:** `severity = HARD` **chỉ khi lock có ít nhất 1 entry `LOCKED`**; nếu chỉ CANDIDATE/UNKNOWN ⇒ `WARN` ⇒ `review_required` (draft-only).

### 3.6 [P2] False HARD_FAIL khi 1 Hán thuộc nhiều entity class
- `少林寺` vừa là `BUDDHIST_TERM` LOCKED (`chùa Thiếu Lâm`) vừa là `PLACE` (`Thiếu Lâm Tự`) ⇒ mismatch check theo từng entry sẽ HARD_FAIL oan.
- **Fix:** `_allowed_vi_by_source_form()` gom **mọi biến thể VI theo `source_form`, bỏ entity_type** (SPEC §3.4) + `_phrase_matches_any_allowed()` so subsequence liên tiếp (xử lý `Hòa Thượng An Lẫm` vs canonical `An Lẫm`).

### 3.7 [P2] Bỏ sót: LLM **bỏ hẳn** tên LOCKED thì im lặng pass
- **Fix:** thêm `LOCKED_NAME_NOT_RENDERED` severity **WARN** (không HARD — theo R4 "unknown an toàn hơn invented"): không chứng minh được tên sai, nhưng cũng không xác nhận được tên đúng ⇒ không `trusted`.

---

## 4. Ma trận test (SPEC §14) — 23/23 PASS

| # | Case | Kỳ vọng | KQ |
|---|------|---------|----|
| A | A009460 LOCKED, out đúng (sau strip title) | `pass` | ✅ |
| B | A009460 LOCKED, out sai tên | `failed` + `CANONICAL_IDENTITY_MISMATCH` HARD | ✅ |
| C | 安廩 CANDIDATE, out cùng tên | `pass` | ✅ |
| C2 | 安廩 CANDIDATE, LLM bịa tên | `review_required` + invention **WARN** (không hard) | ✅ |
| D | 2 nguồn VI khác | `CONFLICT` + `claims[]` ≥ 2, 0 auto-pick | ✅ |
| E | Hán không authority | `UNKNOWN_REVIEW`, `canonical_value=''`, vẫn dịch (P-PARTIAL) | ✅ |
| F | `UNKNOWN_REVIEW` ≠ `failed` | `review_required` | ✅ |
| G | Term LOCKED giữ đúng | `pass` | ✅ |
| H | Term LOCKED bị đổi | HARD issue | ✅ |
| I | LLM "high conf" nhưng mismatch | `failed` (conf không bypass) | ✅ |
| J | Retry cache `failed` draft | vẫn `failed` (không bypass lock) | ✅ |

Bổ sung (14 test): P-STOP chặn LLM · P-PARTIAL gọi LLM · policy lạ → fallback · prompt section đủ 4 khối · fingerprint ổn định + đổi khi canonical đổi · cap 40 Han run · mojibake reject · `is_valid_vi` reject · normalize chỉ strip honorific ở đầu · "Tôi thích uống trà" 0 issue · omitted-name = WARN.

---

## 5. Ghi chú triển khai (Zero-RAM + an toàn)

- **Zero-RAM:** `build_canonical_lock` chỉ query `IN (?,…)` theo **≤40 maximal Han run**; không load `people`/`name_vi_map`/`glossary_vi` vào list.
- **`_safe()` nuốt `sqlite3.Error`:** thiếu bảng/cột = nguồn chết nhưng **không** làm hỏng cả build (nguồn chết đã ghi nhận ở §20.2 #8). Side-effect: schema lệch ⇒ âm thầm `[]` ⇒ **test hermetic phải dùng đúng tên cột** (đã sửa + ghi chú trong test).
- **`_in_clause(n)`** sinh placeholder ⇒ không có SQL injection từ text Hán.
- **Read-only:** `tests/test_t166_matrix.py` mở DB bằng URI `file:…?mode=ro`.

---

## 6. Revert

```bash
# Phase 1 chỉ thêm file mới → revert sạch
git revert --no-edit <sha_phase1>
# hoặc gỡ file:
git rm Dai_Tang_Kinh/daoanh/canonical_lock.py \
       Dai_Tang_Kinh/daoanh/tests/test_t166_canonical_lock.py \
       Dai_Tang_Kinh/daoanh/tests/test_t166_matrix.py
```

**Chưa đụng DB / chưa sửa app.py** ở Phase 1 ⇒ revert không cần `--revert` migration.

---

## 7. Next (Phase 2)

1. Wire `translate_with_guard` vào 3 đường: `app.py` interactive · `scripts/cbeta_translate_worker.py` batch · `admin/app.py` mirror.
2. `style_constitution.py`: `PROMPT_FORMAT_VERSION = 'T166-v1'` + cộng `t166_lock_fingerprint` vào `constitution_hash`.
3. Lưu ý mass-miss: bật fingerprint = toàn bộ cache miss 1 lần (SPEC §9) → pilot ≤5 `source_type` + đo `prompt_tokens` trước.
