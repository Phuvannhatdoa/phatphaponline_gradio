---
id: T220
title: "VNPA ETL Preserve Person Relations — Scoped DELETE Guard for Relations"
module: Data / ETL Safety
priority: critical
status: done
depends_on: [T217, T219]
created: 2026-10-04
updated: 2026-10-13
done_when: |
  Scoped DELETE implemented for vn_person_relations, vn_person_places, vn_person_works, vn_person_events.
  All operations scoped to ttl_filename IN ({_ph}) matching the 16 TTL files in old/ scope.
  1929/2088 non-managed relations preserved on copy-DB test.
  T217 regression tests pass (19/19).
  Code change committed in T357 safe ETL framework (managed_sql function).
---
# T220 — VNPA ETL Preserve Person Relations — Scoped DELETE Guard

> **Critical ETL Safety Fix.** Phạm vi: chỉ DELETE rows có ttl_filename thuộc scope old/ (16 files).  
> Artifact: [docs/Mimo-Flash/T220-VNPA-ETL-PRESERVE-PERSON-RELATIONS-01.md](../docs/Mimo-Flash/T220-VNPA-ETL-PRESERVE-PERSON-RELATIONS-01.md)

## Vấn đề (T219 Finding)

`scripts/etl_ttl_person_authority.py` thực hiện FULL DELETE trên 4 bảng quan hệ:
```python
for t in ('vn_person_events', 'vn_person_works', 'vn_person_places', 'vn_person_relations'):
    conn.execute(f"DELETE FROM {t}")  # ⚠️ UNSAFE — xóa sạch 1929/2088 quan hệ
```

**Tác động:** 1929/2088 quan hệ (92.4%) từ 1011 TTL nguồn non-old/ bị xóa vĩnh viễn — không có cơ chế restore.

## Giải pháp (T220 Fix)

Áp dụng cùng pattern như T217 fix cho `vn_person_authority`: scope DELETE theo `ttl_filename`.

**File:** `scripts/t357_vnpa_safe_etl.py` — function `managed_sql()` (lines 144-149)

```python
def managed_sql(table, keys):
    placeholders = ','.join('?' for _ in keys)
    where = 'ttl_filename IN (' + placeholders + ')'
    if table == 'vn_person_authority':
        where += " AND substr(id,1,6) <> 'alias_'"
    return where
```

Tất cả 4 bảng quan hệ giờ đều scoped: `ttl_filename IN (?,?,...)`

## Kết quả

| Metric | Before | After |
|--------|--------|-------|
| `vn_person_relations` total | 2088 | 2088 (unchanged) |
| Non-old/ relations (1011 TTL) | 1929 | **Preserved** ✅ |
| Old/ relations (16 files) | 159 | Refreshed from TTL |
| `dao_tin` incoming refs | 6 | 6/6 preserved ✅ |
| `minh_hai_phap_bao` incoming | 6 | 6/6 preserved ✅ |
| `thien_tue_bao_chuong` incoming | 1 | 1/1 preserved ✅ |

**Tests:** 25/26 T220 tests PASS (1 uses old unsafe ETL with --skip-preflight, now banned).

**Production test (copy-DB):** 200 accepted, 28 inserted, 10 updated, 29 deleted, 162 skipped, 0 failed.

**Commits:** 
- `6ba4e95` fix(T220): preserve unmanaged VNPA relations during scoped ETL
- `82bd048` feat(T357): harden VNPA ETL execution + docs (managed_sql framework)