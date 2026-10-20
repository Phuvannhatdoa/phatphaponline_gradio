# T212-D4 — A010511 Nam Nhạc Huyền Thái Correction Preparation

**Mode**: PREPARATION ONLY — NO MUTATION  
**Admin authorization**: D4 = APPROVE INTERPRETATION: nam_nhac_huyen_thai is canonical for A010511  
**Date**: 2026-10-02  

---

## 1. Trạng thái hiện tại (live DB, post-T212-D1-A)

```
dila_id: A010511
people.name_zh = '玄泰'
people.name_vi = 'Huyền Thái'
```

| id | name_vi | name_zh | status | dila_id |
|---|---|---|---|---|
| `dam_chau_bao_cai_uoc` | Đàm Châu Bảo Cái Ước | `` | `auto_ttl` | **A010511** ← WRONG |
| `nam_nhac_huyen_thai` | Nam Nhạc Huyền Thái | `畲山兒無所知年年斫斷青山` | `pending` | **NULL** ← disconnected |
| `the_nham_ton_tho` | Thê Nham Tồn Thọ | `` | `pending` | **NULL** |

**Pre-existing mutation so với T207**:  
- `nam_nhac_huyen_thai.dila_id` bị set NULL (đây là row CANONICAL — bị disconnected sai)  
- `the_nham_ton_tho.dila_id` bị set NULL  
- `dam_chau_bao_cai_uoc.dila_id=A010511` vẫn còn (đây là row SAI — chưa sửa)

**T200 current**: A010511 → chỉ còn 1 row `dam_chau_bao_cai_uoc` (auto_ttl) → tên hiển thị = `Đàm Châu Bảo Cái Ước` ← WRONG PERSON

---

## 2. Evidence cho Admin Interpretation

| Evidence | Nội dung |
|---|---|
| `people.name_zh='玄泰'` | Huyền Thái (玄泰) là tên đúng cho A010511 |
| `nam_nhac_huyen_thai.name_vi` lõi | `Huyền Thái` khớp `people.name_vi='Huyền Thái'` |
| `dam_chau_bao_cai_uoc.name_vi` lõi | `Bảo Cái Ước` ≠ Huyền Thái/玄泰 |
| `the_nham_ton_tho.name_vi` lõi | `Tồn Thọ` ≠ Huyền Thái/玄泰 |
| `nam_nhac_huyen_thai.name_zh` | `畲山兒無所知年年斫斷青山` = câu thơ thiền, KHÔNG phải tên |

**Kết luận**: Admin interpretation CONFIRMED — `nam_nhac_huyen_thai` là canonical cho A010511.

---

## 3. Target DILA IDs cho 2 rows sai

| Row | Current dila_id | Lõi tên | Correct dila_id |
|---|---|---|---|
| `dam_chau_bao_cai_uoc` | A010511 (WRONG) | Bảo Cái Ước | **UNKNOWN — EVIDENCE REQUIRED** |
| `the_nham_ton_tho` | NULL | Tồn Thọ | **UNKNOWN — EVIDENCE REQUIRED** |

> **TARGET DILA ID UNKNOWN — EVIDENCE REQUIRED**  
> Admin approval of the interpretation does NOT authorize fabricating replacement DILA IDs.  
> Both rows need DILA source XML lookup before correct IDs can be assigned.

---

## 4. Exact future mutations (KHÔNG thực hiện trong T212)

### Sub-proposal [4A]: Sửa name_zh của canonical row

```sql
-- Sửa nam_nhac_huyen_thai.name_zh từ câu thơ → tên đúng
UPDATE vn_person_authority
SET name_zh = '玄泰',
    updated_at = '<timestamp>'
WHERE id = 'nam_nhac_huyen_thai';
```

Before: `name_zh='畲山兒無所知年年斫斷青山'`  
After:  `name_zh='玄泰'`

### Sub-proposal [4B]: Gán lại dila_id cho canonical row

```sql
UPDATE vn_person_authority
SET dila_id = 'A010511',
    updated_at = '<timestamp>'
WHERE id = 'nam_nhac_huyen_thai';
```

Before: `dila_id=NULL`  
After:  `dila_id='A010511'`

### Sub-proposal [4C]: Tách dam_chau_bao_cai_uoc khỏi A010511

```sql
-- OPTION 1: Set dila_id=NULL (tách, identity unknown)
UPDATE vn_person_authority
SET dila_id = NULL
WHERE id = 'dam_chau_bao_cai_uoc';

-- OPTION 2: Assign correct DILA ID (BLOCKED — ID unknown)
-- DO NOT USE until correct ID is established
```

### Sub-proposal [4D]: Thêm canonical_decision row

```sql
INSERT INTO canonical_decision (
  entity_ref, canonical_name_vi, canonical_name_zh,
  authority_rank, confidence, verification_status, editor, decided_at
) VALUES (
  'A010511', 'Nam Nhạc Huyền Thái', '玄泰',
  'admin_approved', 1.0, 'verified', 'admin', '<timestamp>'
);
```

---

## 5. Recommended execution order (future task)

1. [4B] Gán `nam_nhac_huyen_thai.dila_id='A010511'` — kết nối canonical row
2. [4A] Sửa `nam_nhac_huyen_thai.name_zh='玄泰'`
3. [4C] Tách `dam_chau_bao_cai_uoc.dila_id=NULL` — UNBLOCK A010511 khỏi wrong person
4. [4D] Thêm canonical_decision — LOCK Huyền Thái
5. `the_nham_ton_tho`: đã NULL, giữ nguyên cho đến khi có DILA evidence

---

## 6. All references affected

- `vn_person_authority.dila_id=A010511`: after fix, only `nam_nhac_huyen_thai` maps to A010511
- `canonical_lock('玄泰')`: hiện không có → sau fix LOCKED
- T200 display for A010511: từ `Đàm Châu Bảo Cái Ước` → `Nam Nhạc Huyền Thái`
- `dam_chau_bao_cai_uoc`: sẽ thành orphan (dila_id=NULL) cho đến khi DILA evidence available

---

## 7. Rollback

```sql
-- Revert [4B]
UPDATE vn_person_authority SET dila_id=NULL WHERE id='nam_nhac_huyen_thai';
-- Revert [4A]
UPDATE vn_person_authority SET name_zh='畲山兒無所知年年斫斷青山' WHERE id='nam_nhac_huyen_thai';
-- Revert [4C]
UPDATE vn_person_authority SET dila_id='A010511' WHERE id='dam_chau_bao_cai_uoc';
-- Revert [4D]
DELETE FROM canonical_decision WHERE entity_ref='A010511';
```

---

## 8. Trạng thái

**PREPARATION COMPLETE. NO MUTATION.**  
Blocked by: correct DILA IDs for `dam_chau_bao_cai_uoc` and `the_nham_ton_tho` are UNKNOWN.  
[4A] + [4B] + [4D] có thể thực hiện sau khi Admin confirm.  
[4C] cần DILA evidence cho correct replacement ID.

---

*T212-D4 Preparation · READ-ONLY · 2026-10-02*
