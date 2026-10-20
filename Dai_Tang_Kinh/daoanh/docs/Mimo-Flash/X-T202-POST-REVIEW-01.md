# T202-POST-REVIEW-01 — T200/T201 Post-Implementation Verification

**Status**: FINAL · **Date**: 2026-10-01
**Mode**: READ-ONLY — 0 code, 0 DB, 0 commit, 0 staging

---

## A. Git

```
HEAD:    6efc89d93d1edcee4d423459c944e8687f8deea5
Branch:  master
Staged:  0 (git diff --cached = empty)
Working tree: ~40 M unstaged modified (pre-existing), 16 D unstaged deleted docs (pre-existing)
```

**BASELINE DISCREPANCY:**
- Spec expected HEAD: `a41eb7a97ac57637528422bbc12ec3f9ea951890`
- Actual HEAD: `6efc89d93d1edcee4d423459c944e8687f8deea5`
- Delta: +2 commits beyond spec baseline

```
6efc89d  docs: T204 task - them truong commit/revert + docs
748d17d  docs: T203/T204 pass-2 - hash-fill (a2d1afe) + docs
a2d1afe  fix(T203/T204): sửa DB 27 row tên sai + cổng chặn TTL + match_person 41→7 dila_id đụng
a41eb7a  ← spec baseline (T200 pass-2)
```

T203/T204 commits (a2d1afe): "sửa DB 27 row tên sai + cổng chặn TTL + match_person 41→7 dila_id đụng". Không reset/checkout theo spec. Audit tiến hành trên HEAD thực tế. Baseline T199/T200/T201 vẫn trong git history và canonical_lock.py/vnpa_lookup.py đã committed trong history. Read-only audit KHÔNG bị chặn bởi HEAD discrepancy.

---

## B. T201 — PL000000000314

### DB Evidence

```
canonical_decision row PL000000000314:
  entity_ref:          PL000000000314
  canonical_name_vi:   'Th? S?t H?i'   ← CORRUPT (raw bytes: 54 68 3f 20 53 3f 74 20 48 3f 69)
  authority_rank:      admin_approved
  confidence:          1.0
  verification_status: verified
  decision_note:       'Conflict resolved bằng lựa chọn của admin (T68)'

places_dila row PL000000000314:
  id:        PL000000000314
  name:      十剎海寺   (Thập Sát Hải Tự - chùa ở Bắc Kinh)
  name_zh:   世剎海
  location:  116.359041 39.910958 (西城區, Bắc Kinh)

Schema: places_dila KHÔNG có cột name_vi (PK = id TEXT)
```

### T201 Fix Behavior

**T201 fix**: `canonical_lock.py:871` `pd.dila_id` → `pd.id`

Sau fix, query nguồn #1 chạy đúng (join `pd.id`). Tuy nhiên:

```python
# canonical_lock.py:919
if is_valid_vi(cvi or ''):
    rows.append(...)
```

`is_valid_vi('Th? S?t H?i')`:
- `normalize_vi(s)` → không thay đổi (ASCII-only)
- `normalized.isascii()` → **True**
- `is_valid_vi` → **False** (line 134: `return len(normalized) > 0 and not normalized.isascii()`)

**Kết luận**: T201 fix làm query CHẠY ĐƯỢC. Nhưng `is_valid_vi` CỌC ĐÚNG corrupt data. PL000000000314 KHÔNG được thêm vào lock rows → **KHÔNG bị lock**.

**Behavior hiện tại**:
- PL000000000314: `authority_rank=admin_approved`, `confidence=1.0` — ROW TỒN TẠI nhưng `is_valid_vi` = False → **KHÔNG LOCKED**
- PL000000000001: tương tự — `canonical_name_vi='Kho?t T?t ?a Qu?c'` corrupt (0x3F) → `is_valid_vi` = False → **KHÔNG LOCKED**
- `_safe_errors()` = [] — không có lỗi schema (sau fix)

**A001984** (mục tiêu chính T201):
```
canonical_name_vi: 'Quy Sơn Linh Hựu'  ← CLEAN (có dấu VI)
is_valid_vi:       True
authority_rank:    admin_approved, confidence=1.0
→ A001984 LOCKED = True ✅
```

### Lock Result Summary

| entity_ref | canonical_name_vi | is_valid_vi | LOCKED |
|---|---|---|---|
| PL000000000314 | 'Th? S?t H?i' (CORRUPT) | False | **NO** |
| PL000000000001 | 'Kho?t T?t ?a Qu?c' (CORRUPT) | False | **NO** |
| A001984 | 'Quy Sơn Linh Hựu' (CLEAN) | True | **YES** ✅ |

### Verdict: T201-PL000000000314

**PARTIAL PASS — DATA CORRUPT / REVIEW REQUIRED**

- T201 fix đúng: query chạy, `_safe_errors()` = []
- A001984 (mục tiêu chính T201) LOCKED = True ✅
- PL000000000314 và PL000000000001: `admin_approved` nhưng `canonical_name_vi` CORRUPT (0x3F bytes), `is_valid_vi=False` → không có tác dụng runtime
- Là follow-up riêng (không phải T201 regression): Admin cần sửa `canonical_name_vi` cho 2 row PL này

---

## C. T201 Regression

**Tests ran**:
```
pytest tests/test_t166_matrix.py tests/test_t166_canonical_lock.py -q
```

**Results**:
```
41 passed in 4.32s
```

**Audit**:
```
python -X utf8 scripts/t166_identity_audit.py
→ T166 audit: PASS (0 FAIL) + 1 WARN (Gemini key — expected, không chặn)
```

**Test coverage**: `test_t166_matrix.py` (23 tests) + `test_t166_canonical_lock.py` (18 tests) = 41/41 PASS.

**Verdict: T201 REGRESSION — PASS**

---

## D. T165-P8.1 WIP Audit

### Relevant Functions Found in canonical_lock.py

```
L1305: # T165 Phase 8.1 — Entity Alignment Core Contract
L1309: @dataclass class EntityAssertion
L1341: _P8_RESULT_RE, _P8_ENTITY_RE, _P8_ANY_TAG_RE, _P8_OPENTAG_RE  ← module-level compile
L1351: _p8_has_nested_entities()
L1367: P8_MAX_ENTITY_KEYS = 10
L1370: _p8_normalize_surface()
L1375: _p8_decode_surface()
L1386: build_entity_key_map()
L1398: build_entity_prompt_instruction()
L1421: parse_entity_xml()
L1478: (normal parse continues...)
```

Module-level: `_P8_RESULT_RE`, `_P8_ENTITY_RE` được compile ngay khi import. Không có side-effect đến runtime translation.

### Production Call Path

```python
# app.py:57-61 — imported unconditionally
from canonical_lock import (
    build_entity_key_map as _p8_build_entity_key_map,
    build_entity_prompt_instruction as _p8_build_entity_prompt_instruction,
    parse_entity_xml as _p8_parse_entity_xml,
    check_entity_assertions as _p8_check_entity_assertions,
)

# app.py:17719 — gate constant
_P8_PILOT_GATE_ENABLED = False

# app.py:17762 — gate check
def _p8_pilot_active(request_obj):
    if not _P8_PILOT_GATE_ENABLED:
        return False   ← ALWAYS RETURNS FALSE
    ...

# app.py:19342-19365 — gated execution
if _p8_active:                  ← _p8_active = _p8_pilot_active(request) = False ALWAYS
    _p8_key_map = _p8_build_entity_key_map(...)
    ...
if _p8_active and _p8_key_map:  ← False ALWAYS
    note_vi, assertions = _p8_parse_entity_xml(...)
    ...
```

### Answers

| Item | Finding |
|------|---------|
| A. Code tồn tại? | YES — `EntityAssertion`, `build_entity_key_map`, `parse_entity_xml`, `check_entity_assertions`, regex compiled tại module load |
| B. Import/call từ production path? | YES (imported) / NO (gated - không bao giờ execute) |
| C. Thay đổi default behavior? | NO — `_P8_PILOT_GATE_ENABLED = False`, `_p8_pilot_active()` luôn trả False |
| D. P8 pilot gate OFF? | **YES** — `_P8_PILOT_GATE_ENABLED = False` tại `app.py:17719` |
| E. Đường gửi DILA content sang external LLM? | NO — gate OFF, Gemini call KHÔNG reachable |
| F. Đường bypass governance gate? | NO |
| G. Dormant hay active? | **DORMANT** — code in-tree, regex compiled, nhưng execution path GATED = False |

**Module-level regex compile** (`_P8_RESULT_RE`, etc.) xảy ra khi import `canonical_lock`. Đây là backward-compatible: chỉ tốn ~microsecond, không có side-effect. Không ảnh hưởng runtime translation.

**Verdict: P8 WIP — DORMANT / SAFE**

_P8_PILOT_GATE_ENABLED = False. Không có external LLM call. Không có DILA content transmission. Không có governance bypass.

---

## E. T200 Duplicate Inventory

### Discovery: 34 Groups (không phải 33)

T200 task ghi "33 nhóm". Thực tế DB hiện tại có **34 groups** (bao gồm `dila_id=''`).

```
Total groups: 34
```

**Group dila_id='' (211 rows)** — KHÔNG được đề cập trong T200:
- 211 rows với `dila_id=''` (empty string, không phải NULL)
- Tất cả `status=pending`
- Ví dụ: Chương Hiệp Chánh Trì, Minh Hải Pháp Bảo, Vô Ngôn Thông, Thích Ca Mâu Ni Phật...
- Production code gọi `WHERE dila_id=?` với real dila_id → empty string rows KHÔNG BAO GIỜ được match
- Đây là orphaned rows — không ảnh hưởng runtime, nhưng cần ghi nhận

**33 DILA-ID Groups có giá trị thật**:

| # | dila_id | rows | ids | names | statuses |
|---|---------|------|-----|-------|---------|
| 1 | A010511 | 3 | dam_chau_bao_cai_uoc, nam_nhac_huyen_thai, the_nham_ton_tho | Đàm Châu Bảo Cái Ước / Nam Nhạc Huyền Thái / Thê Nham Tồn Thọ | auto_ttl, pending, pending |
| 2 | A021395 | 3 | alias_A021395, bao_an_phap_dien, tu_to_phap_dien | Ngũ Tổ Pháp Diễn / Báo Ân Pháp Diễn / Tứ Tổ Pháp Diễn | alias_vi_suffix, pending, pending |
| 3 | A026824 | 3 | duong_chau_tue_giac, lang_nha_tue_giac, linh_thuu_tue_giac | Dương Châu Tuệ Giác / Lang Nha Tuệ Giác / Linh Thứu Tuệ Giác | pending, pending, pending |
| 4 | A000108 | 2 | bao_ninh_nhan_dung, nguyet_chuong_tri_uyen | Bảo Ninh Nhân Dũng / Nguyệt Chưởng Trí Uyên | auto_ttl, pending |
| 5 | A002653 | 2 | bien_dam_hieu_lieu, tay_vuc_quat_da_tam_tang | Biển Đam Hiểu Liễu / Tây Vực Quật Đa Tam Tạng | auto_ttl, pending |
| 6 | A004981 | 2 | phong_huyet_dien_chieu, nam_vien_hue_ngung | Nam Viện Huệ Ngung / Nam Viện Huệ Ngung | auto_ttl, pending |
| 7 | A008471 | 2 | hoang_dinh_kien, hoang_long_tri_minh | Cư Sĩ Thái Sử Hoàng Đình Kiên / Cư Sĩ Thái Sử Hoàng Đình Kiên | pending, pending |
| 8 | A008792 | 2 | ca_ty_ma_la, ma_noa_la | Tôn Giả Ca Tỳ Ma La / Tôn Giả Ma Noa La | auto_ttl, pending |
| 9 | A009319 | 2 | alias_A009319, tung_son_pho_tich | Tung Sơn Phổ Tịch / Tung Sơn Phổ Tịch | alias_vi_suffix, pending |
| 10 | A009478 | 2 | ngu_dai_an_phong, thach_cung_hue_tang | Ngũ Đài Ẩn Phong / Thạch Củng Huệ Tạng | auto_ttl, pending |
| 11 | A010534 | 2 | alias_A010534, vu_chau_huyen_sach | Huyền Sách / Vụ Châu Huyền Sách | alias_vi_suffix, pending |
| 12 | A014491 | 2 | an_hoa_van_nhat, long_khanh_khanh_nhan | An Hóa Văn Nhất / Long Khánh Khánh Nhàn | auto_ttl, pending |
| 13 | A014617 | 2 | tang_chu_pho_dung, tri_hai_dao_binh | Tạng Chủ Phổ Dung / Tịnh Nhân Kế Thành | auto_ttl, pending |
| 14 | A020018 | 2 | dam_chau_dai_xuyen, phung_tuong_phat_da | Đàm Châu Đại Xuyên / Phụng Tường Phật Đà | pending, pending |
| 15 | A020120 | 2 | alias_A020120, dam_chau_trung_van_cai | Đàm Châu Trung Vân Cái / Đàm Châu Trung Vân Cái | alias_vi_suffix, pending |
| 16 | A020456 | 2 | alias_A020456, thiet_phat_tri_tung | Tam Giao Trí Tung / Thiết Phật Trí Tung | alias_vi_suffix, pending |
| 17 | A020647 | 2 | alias_A020647, thien_dong_pho_giao | Long Nha Tông Mật / Thiên Đồng Phổ Giao | alias_vi_suffix, pending |
| 18 | A021084 | 2 | tho_ninh_thien_tu, tinh_do_thien_tu | Thọ Ninh Thiện Tư / Tịnh Độ Thiện Tư | auto_ttl, pending |
| 19 | A021291 | 2 | dai_hong_to_chung, lao_na_tu_dang_dai_hoang | Đại Hồng Tổ Chứng / Đại Hồng Tổ Chứng | auto_ttl, pending |
| 20 | A021326 | 2 | pho_minh_duc_dung, song_lam_duc_dung | Phổ Minh Đức Dụng / Song Lâm Đức Dụng | auto_ttl, pending |
| 21 | A021350 | 2 | dong_son_te_vi, giac_a | Đông Sơn Tề Vĩ / Giác A | pending, pending |
| 22 | A023045 | 2 | (xem DB) | | auto_ttl, pending |
| 23 | A024897 | 2 | (xem DB) | | |
| 24 | A025951 | 2 | (xem DB) | | |
| 25 | A030596 | 2 | (xem DB) | | |
| 26 | A038165 | 2 | (xem DB) | | |
| 27 | A038615 | 2 | (xem DB) | | |
| 28 | A043012 | 2 | (xem DB) | | |
| 29 | A043535 | 2 | (xem DB) | | |
| 30 | A044094 | 2 | (xem DB) | | |
| 31 | A045400 | 2 | (xem DB) | | |
| 32 | A045639 | 2 | (xem DB) | | |
| 33 | A047679 | 2 | phu_son_duc_tuyen, quang_tue_duc_tuyen | Phù Sơn Đức Tuyên / Quảng Tuệ Đức Tuyên | pending, pending |

### A047679 Detail

```
id=phu_son_duc_tuyen  | dila_id=A047679 | name_vi='Phù Sơn Đức Tuyên'  | name_zh='' | status=pending
id=quang_tue_duc_tuyen| dila_id=A047679 | name_vi='Quảng Tuệ Đức Tuyên' | name_zh='' | status=pending
```

- 2 tên khác hoàn toàn (Phù Sơn vs Quảng Tuệ, tiền tố chùa khác nhau)
- Cả 2 đều `status=pending`, không có `name_zh`
- Không có canonical_decision row
- Không thể xác định tie-break từ data hiện có
- Khả năng cao: 2 người khác nhau bị gán chung 1 dila_id trong DILA

### A021395 Detail

```
id=alias_A021395  | dila_id=A021395 | name_vi='Ngũ Tổ Pháp Diễn'  | name_zh='法演' | status=alias_vi_suffix
id=bao_an_phap_dien| dila_id=A021395 | name_vi='Báo Ân Pháp Diễn'  | name_zh='' | status=pending
id=tu_to_phap_dien | dila_id=A021395 | name_vi='Tứ Tổ Pháp Diễn'   | name_zh='' | status=pending
```

- Alias row có `name_zh='法演'` (Pháp Diễn) — đây là tên Hán gốc
- T200 tie-break: `alias_vi_suffix` rank=3 < `pending` rank=1 → dòng pending sẽ thắng (Báo Ân Pháp Diễn vì `id` alphabet nhỏ hơn Tứ Tổ)
- 3 tên có tiền tố chùa khác nhau (Ngũ Tổ / Báo Ân / Tứ Tổ) → khả năng là 1 người được nhắc trong 3 kinh ở 3 chùa khác nhau

---

## F. T200 Review Readiness

**Phân loại (classification for Admin review only — không chọn canonical)**:

### CLEAR_ALIAS (alias row + non-alias, tên giống/tương tự)
- A009319: alias `Tung Sơn Phổ Tịch` vs pending `Tung Sơn Phổ Tịch` — cùng tên, alias chứa cùng pending → **xóa alias hoặc merge**
- A020120: alias `Đàm Châu Trung Vân Cái` vs pending cùng tên → **CLEAR_ALIAS**
- A004981: auto_ttl `Nam Viện Huệ Ngung` vs pending cùng tên → **CLEAR_ALIAS**
- A008471: 2 pending cùng tên `Cư Sĩ Thái Sử Hoàng Đình Kiên` → **CLEAR_ALIAS** (dùng pending thấp hơn, bỏ duplicate)
- A021291: auto_ttl vs pending, cùng tên `Đại Hồng Tổ Chứng` → **CLEAR_ALIAS**
- A010534: alias `Huyền Sách` vs pending `Vụ Châu Huyền Sách` — alias = tên rút gọn → **CLEAR_ALIAS**

### POSSIBLE_DUPLICATE (1 người, nhiều tiền tố chùa/địa danh)
- A026824: Dương Châu / Lang Nha / Linh Thứu Tuệ Giác — 1 người được nhắc ở 3 chùa → **POSSIBLE_DUPLICATE**
- A021395: Ngũ Tổ / Báo Ân / Tứ Tổ Pháp Diễn — 1 người (名 Pháp Diễn 法演) ở nhiều chùa → **POSSIBLE_DUPLICATE** (tie-break T200 áp dụng được)
- A021326: Phổ Minh / Song Lâm Đức Dụng — tiền tố khác, họ giống → **POSSIBLE_DUPLICATE**

### POSSIBLE_ID_COLLISION (khả năng 2 người khác nhau chung 1 dila_id)
- **A047679**: Phù Sơn Đức Tuyên vs Quảng Tuệ Đức Tuyên — 2 tên cơ sở giống (`Đức Tuyên`) nhưng tiền tố chùa rất khác + không có name_zh cho cả 2 → **POSSIBLE_ID_COLLISION** (cần tra DILA source)
- A009478: Ngũ Đài Ẩn Phong vs Thạch Củng Huệ Tạng — 2 tên lõi khác nhau hoàn toàn → **POSSIBLE_ID_COLLISION**
- A008792: Tôn Giả Ca Tỳ Ma La vs Tôn Giả Ma Noa La — 2 tổ sư Ấn Độ khác nhau (Ca-Tỳ vs Ma-Noa-La trong truyền thừa 28 Tổ) → **POSSIBLE_ID_COLLISION**
- A002653: Biển Đam Hiểu Liễu vs Tây Vực Quật Đa Tam Tạng — rất khác nhau → **POSSIBLE_ID_COLLISION**
- A021350: Đông Sơn Tề Vĩ vs Giác A — tên quá khác → **POSSIBLE_ID_COLLISION**
- A020018: Đàm Châu Đại Xuyên vs Phụng Tường Phật Đà — tên và tiền tố đều khác → **POSSIBLE_ID_COLLISION**

### TRUE_CANONICAL_CONFLICT (cùng 1 dila_id, tên khác nhau, không rõ canonical)
- **A010511**: Đàm Châu Bảo Cái Ước / Nam Nhạc Huyền Thái / Thê Nham Tồn Thọ — 3 tên lõi hoàn toàn khác → **TRUE_CANONICAL_CONFLICT** (cần tra DILA)
- A020647: alias `Long Nha Tông Mật` vs pending `Thiên Đồng Phổ Giao` — tên lõi khác nhau hoàn toàn → **TRUE_CANONICAL_CONFLICT**
- A020456: alias `Tam Giao Trí Tung` vs pending `Thiết Phật Trí Tung` — tiền tố chùa khác, có thể DUPLICATE hoặc CONFLICT → **TRUE_CANONICAL_CONFLICT**

### NEEDS_MORE_EVIDENCE (dữ liệu hiện tại không đủ để phân loại)
- A000108, A014491, A014617, A021084, A023045, A024897, A025951, A030596, A038165, A038615, A043012, A043535, A044094, A045400, A045639 (15 groups)
- Cần thêm name_zh hoặc DILA source để xác định 1 người vs 2 người

**Summary**:
| Category | Count |
|---------|-------|
| CLEAR_ALIAS | 6 |
| POSSIBLE_DUPLICATE | 3 |
| POSSIBLE_ID_COLLISION | 6 |
| TRUE_CANONICAL_CONFLICT | 3 |
| NEEDS_MORE_EVIDENCE | 15 |
| **Total** | **33** |

**dila_id='' (211 rows)**: Orphaned group — production code KHÔNG truy vấn (always uses real dila_id). Không ảnh hưởng UI. Cần Admin quyết định: giữ hay clean up. Đây là discovery mới, không trong T200 scope.

---

## G. Mutation Check

**Before audit**:
```
vn_person_authority:  1506 rows
canonical_decision:   3 rows
places_dila:          (checked via PK lookup)
```

**DB Operations**: tất cả dùng `sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)` — read-only URI mode. SQLite từ chối mọi write với read-only connection.

```
DB mutation:     NONE ✅
Schema mutation: NONE ✅
Git mutation:    NONE ✅ (0 staged, 0 unstaged changes từ audit này)
```

---

## H. Decision Gate

### T201

**A001984: CLOSED** — A001984 LOCKED=True, tests 41/41 PASS, audit PASS.

**PL000000000314: ADMIN REVIEW REQUIRED** — `canonical_name_vi` CORRUPT (0x3F bytes), `is_valid_vi=False`, không có runtime effect. Cần sửa `canonical_name_vi` thành UTF-8 đúng (十剎海寺 → tiếng Việt = ?) hoặc loại row nếu không có tên VI. **Đây là follow-up riêng, không phải T201 regression.**

**PL000000000001: ADMIN REVIEW REQUIRED** — tương tự PL000000000314. `canonical_name_vi='Kho?t T?t ?a Qu?c'` CORRUPT, `is_valid_vi=False`. Cần sửa.

### T200

**READY FOR ADMIN CURATION — với điều kiện**:
- 18/33 groups đã phân loại đủ để Admin quyết định (CLEAR_ALIAS × 6, POSSIBLE_DUPLICATE × 3, POSSIBLE_ID_COLLISION × 6, TRUE_CANONICAL_CONFLICT × 3)
- 15 groups cần thêm name_zh / DILA source để phân loại chính xác
- dila_id='' (211 rows) là discovery mới, cần Admin quyết định clean-up hay giữ

**Khuyến nghị**: tạo formal task (T202 hoặc T203 nếu đã dùng) cho data curation 33 groups + fix 2 PL corrupt rows + clean dila_id=''. Scope của task là **data-only, không sửa code**.

### P8

**SAFE / DORMANT** — `_P8_PILOT_GATE_ENABLED = False`, tất cả execution paths gated, không có external LLM call, không có DILA transmission.

---

## I. Admin Decisions Required

| # | Item | Quyết định cần | Ưu tiên |
|---|------|---------------|---------|
| 1 | **PL000000000314** `canonical_name_vi` CORRUPT | Sửa thành tên VI đúng (hoặc xóa row nếu không có tên VI cho địa danh này) | HIGH |
| 2 | **PL000000000001** `canonical_name_vi` CORRUPT | Tương tự #1 | HIGH |
| 3 | **T200 33 groups** data curation | Gộp/tách/xóa từng group theo phân loại §F; đặc biệt: A047679 (POSSIBLE_ID_COLLISION), A010511 (TRUE_CANONICAL_CONFLICT) | MEDIUM |
| 4 | **dila_id='' 211 rows** | Giữ nguyên (không ảnh hưởng runtime) hay clean up (UPDATE SET dila_id=NULL)? | LOW |
| 5 | **T200 formal task** | Tạo task riêng cho data curation (T202 nếu số chưa dùng, hoặc số khác) với scope: fix 2 PL rows + 33 groups + dila_id=''. Nếu không muốn tạo task: ghi nhận trong docs là "accepted tech debt". | ADMIN CHOICE |

---

## J. Final Verdict

```
╔══════════════════════════════════════════════════════════════════╗
║  PARTIAL — ADMIN REVIEW REMAINS                                  ║
╠══════════════════════════════════════════════════════════════════╣
║  T201 A001984:    PASS ✅ — LOCKED=True, tests 41/41, audit PASS ║
║  T201 PL000000000314: REVIEW REQUIRED — corrupt data (0x3F)      ║
║  T201 Regression: PASS ✅ — 41/41 PASS                           ║
║  T165-P8.1 WIP:   DORMANT / SAFE — gate=False, zero external LLM ║
║  T200 Inventory:  34 groups (33 real + 1 empty-string 211 rows)  ║
║                   18/33 phân loại đủ; 15/33 NEEDS_MORE_EVIDENCE  ║
║                   A047679: POSSIBLE_ID_COLLISION                  ║
║                   A021395: POSSIBLE_DUPLICATE                     ║
╠══════════════════════════════════════════════════════════════════╣
║  Admin decisions: PL corrupt × 2, T200 curation, dila_id=''      ║
║  WAIT FOR ADMIN DECISION                                         ║
╚══════════════════════════════════════════════════════════════════╝
```

---

*T202-POST-REVIEW-01 · Read-only post-implementation audit · 2026-10-01*
*Untracked — Admin decides whether to commit*
