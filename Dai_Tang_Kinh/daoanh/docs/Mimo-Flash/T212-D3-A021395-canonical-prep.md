# T212-D3 — A021395 Canonical/Alias Curation Preparation

**Mode**: PREPARATION ONLY — NO MUTATION  
**Admin authorization**: D3 = CONFIRM SAME PERSON; PREPARE CANONICAL/ALIAS CURATION  
**Date**: 2026-10-02  

---

## 1. Trạng thái hiện tại (live DB, post-T212-D1-A)

```
dila_id: A021395
people.name_zh = '法演'
people.name_vi = 'Pháp Diễn'
```

| id | name_vi | name_zh | status | dila_id |
|---|---|---|---|---|
| `alias_A021395` | Ngũ Tổ Pháp Diễn | `法演` | `alias_vi_suffix` | `A021395` |
| `bao_an_phap_dien` | Báo Ân Pháp Diễn | `` | `pending` | `A021395` |
| `tu_to_phap_dien` | Tứ Tổ Pháp Diễn | `` | `pending` | **NULL** ← pre-existing |

**Thay đổi so với T207**: `tu_to_phap_dien.dila_id` đã bị set NULL bởi pre-existing mutation (không có trong T212 scope). Hiện còn 2 rows với dila_id=A021395.

**T200 winner hiện tại**: `bao_an_phap_dien` (status=pending, id ASC < `tu_to_phap_dien`) → tên hiển thị = `Báo Ân Pháp Diễn`.

---

## 2. Admin Decision xác nhận

Admin (T208 D3=A): Confirm 1 người, cùng Pháp Diễn 法演, 3 tiền tố tự viện.

Vẫn đúng với 2 rows còn lại + `tu_to_phap_dien` (dila_id=NULL nhưng vẫn tồn tại trong DB).

---

## 3. Plausible canonical candidates

| Option | id | basis | authority |
|---|---|---|---|
| **Option A** (recommended) | `alias_A021395` | Có `name_zh='法演'` authoritative; `alias_vi_suffix` ổn định | T207 evidence |
| Option B | `bao_an_phap_dien` | T200 winner hiện tại; `pending` | tên hiển thị hiện tại |

**Nhận xét**: `alias_A021395` là canonical tốt hơn vì có `name_zh='法演'` (Hán tự đúng). T200 ưu tiên `pending` hơn `alias_vi_suffix` — canonical_decision override sẽ cần để cố định tên hiển thị.

**Lưu ý**: có nhiều hơn 1 plausible canonical row (alias_A021395 vs bao_an_phap_dien). Admin phải chọn rõ ràng.

---

## 4. Exact future mutations (KHÔNG thực hiện trong T212)

### Nếu Admin chọn Option A (alias_A021395):

```sql
-- Mutation 1: Thêm canonical_decision row
INSERT INTO canonical_decision (
  entity_ref, canonical_name_vi, canonical_name_zh,
  authority_rank, confidence, verification_status, editor, decided_at
) VALUES (
  'A021395',
  'Ngũ Tổ Pháp Diễn',
  '法演',
  'admin_approved',
  1.0,
  'verified',
  'admin',
  '<timestamp>'
);

-- Mutation 2 (optional): Xóa bao_an_phap_dien (duplicate pending row)
-- Admin phải approve riêng
DELETE FROM vn_person_authority WHERE id='bao_an_phap_dien';

-- Mutation 3 (optional): Xóa hoặc giữ tu_to_phap_dien (hiện dila_id=NULL)
-- Admin phải approve riêng — đang là orphan, không impact T200 cho A021395
```

### Before/after:

| Field | Before | After |
|---|---|---|
| T200 display name | `Báo Ân Pháp Diễn` (pending wins) | `Ngũ Tổ Pháp Diễn` (canonical_decision level=1.0 wins) |
| canonical_lock (法演) | no lock | LOCKED (level=1.0) |
| alias_A021395.status | `alias_vi_suffix` | unchanged (kept as alias) |
| bao_an_phap_dien | present | deleted (if approved) |

### Expected runtime consequence:

- `build_canonical_lock(conn, '法演')` → LOCKED, canonical_value='Ngũ Tổ Pháp Diễn', authority_source='canonical_decision.admin_approved'
- T200 vnpa_lookup('A021395') → returns `alias_A021395` row (alias_vi_suffix wins under canonical_decision override)

### Rollback:

```sql
DELETE FROM canonical_decision WHERE entity_ref='A021395';
-- Nếu đã xóa bao_an_phap_dien:
INSERT INTO vn_person_authority ... -- restore from backup
```

---

## 5. Trạng thái

**PREPARATION COMPLETE. NO MUTATION.**  
Cần Admin xác nhận Option A hoặc B trước khi tạo mutation task.

---

*T212-D3 Preparation · READ-ONLY · 2026-10-02*
