# Session 2026-10-02 — T206: Sửa 2 PL corrupt canonical_name_vi

## Tasks hoàn thành

### T206: Data curation — PL000000000314 + PL000000000001

**Status**: DONE

**Phạm vi**: Data-only. 2 UPDATE duy nhất vào `canonical_decision.canonical_name_vi`.

**Kết quả**:

| entity_ref | OLD (corrupt) | NEW (authoritative) | LOCKED |
|---|---|---|---|
| `PL000000000314` | `'Th? S?t H?i'` | `'Thế Sát Hải'` | **YES** (level=1.0) |
| `PL000000000001` | `'Kho?t T?t ?a Qu?c'` | `'Khoát Tạt Đa Quốc'` | CANDIDATE (level=0.7) |

**Backup**: `data/backups/lineage_t206_20261002_005334.db`
**SHA256**: `50fd01fc25d939a2088dddb26e5da6fc2e99e8a912f073733acf572f2174958e`

**Tests**: T166 41/41 PASS · audit:t166 PASS · npm run pipeline exit 0

**Canonical lock behavior sau correction**:
- `PL000000000314` (世剎海): `canonical_decision.admin_approved` → `LOCKED` at level 1.0 ✅
- `PL000000000001` (闊悉多國): `canonical_decision.auto_transliterate` → `CANDIDATE` at level 0.7

## Tasks đang dở / Todo tiếp theo

### Cần Admin decision (không được tự làm):

1. **A010511** — TRUE_CANONICAL_CONFLICT
   - `nam_nhac_huyen_thai` là canonical (khớp people.name_zh=玄泰)
   - `dam_chau_bao_cai_uoc` + `the_nham_ton_tho` sai dila_id → cần tách
   - `nam_nhac_huyen_thai.name_zh` = câu thơ thiền → cần xóa/sửa
   - **Pending Admin approval**

2. **A047679** — Phù Sơn Đức Tuyên vs Quảng Tuệ Đức Tuyên
   - Insufficient evidence; cần tra DILA source XML
   - **Pending Admin approval**

3. **A021395** — Ngũ Tổ / Báo Ân / Tứ Tổ Pháp Diễn
   - 1 người, 3 tiền tố. Admin chọn canonical row
   - **Pending Admin approval**

4. **33 nhóm dila_id duplicate** (T200 data curation)
   - 7 CLEAR_ALIAS: approve xóa duplicate
   - 10 POSSIBLE_DUPLICATE: xác nhận 1 người
   - 11 POSSIBLE_ID_COLLISION: tra DILA, tách nếu 2 người
   - **Pending Admin approval từng nhóm**

5. **211 dila_id='' orphan rows**
   - Phân loại 4 sub-categories
   - **Pending Admin approval**

6. **PL000000000001 vstatus** nâng từ `needs_review` → `verified` (nếu Admin approve)

7. **namevi_map_places + places_pending** corrupt cho PL314+PL001 — task riêng

### Blocked (không thể tiến hành):

- **T165-P8**: FROZEN — DILA license required
- **T196**: Admin diagnose git handle
- **T198**: Admin approve soft vs hard invalidate
- **T74b**: T73 in_progress
