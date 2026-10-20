---
id: T212
title: "Safe Canonical Curation D1-A: xóa 4 CLEAR_ALIAS duplicate rows + D3/D4/D5 preparation"
module: Data / Canonical Identity
priority: high
status: done
owner: claudecode
depends_on: [T208, T207, T206, T203]
created: 2026-10-02
updated: 2026-10-02
designed_by: claudecode
handoff_to: Admin
plan_approved_at: "2026-10-02 (Admin T208 D1-A=APPROVE SAFE CURATION)"
note: "Admin spec gọi là T209-SAFE-CANONICAL-CURATION-01; task file dùng T212 vì T209/T210/T211 đã bị chiếm"
done_when: |
  D1-A: 4 alias rows đã bị DELETE (vn_person_authority total: 1506→1502).
  T166 41/41 PASS. audit:t166 PASS. npm run pipeline PASS.
  D3 preparation: docs/Mimo-Flash/T212-D3-A021395-canonical-prep.md
  D4 preparation: docs/Mimo-Flash/T212-D4-A010511-canonical-prep.md
  D5 follow-up task: tasks/T213-vnpa-orphan-211-classification.md
  D2 (A047679): deferred.
risk: |
  - Pre-existing DB mutation (33 rows dila_id→NULL) không có trong T208 scope.
    3 of 7 CLEAR_ALIAS groups excluded do alias rows đã có dila_id=NULL trước T212.
  - D4 canonical row (nam_nhac_huyen_thai) đã bị disconnect (dila_id=NULL) bởi pre-existing mutation.
    Task tiếp theo cho D4 cần gán lại dila_id=A010511 cho canonical row.
---

# T212 — Safe Canonical Curation D1-A

> **Admin spec label**: T209-SAFE-CANONICAL-CURATION-01  
> **Task number**: T212 (T209 đã bị chiếm bởi TTL guard)

## 0. Pre-existing DB anomaly (phát hiện trong T212)

Trước khi T212 chạy, **33 rows** trong `vn_person_authority` đã có `dila_id=NULL` (T207: 0 rows NULL).  
Nguyên nhân: mutation không tracked, xảy ra sau T208 backup (`lineage_t208_20261002_112520.db`).  
Hậu quả: 33 groups từ T207 giảm còn 9 groups có `dila_id != '' AND COUNT > 1`.  
Tổng rows vẫn là 1506 (unchanged). 211 empty-string rows vẫn là 211 (unchanged).

## 1. D1-A Applied (4 of 7 CLEAR_ALIAS groups)

**Script**: `scripts/t212_safe_canonical_curation.py`

### Backup

```
file:    data/backups/lineage_t212_20261002_153042.db
size:    1,529,729,024 bytes
sha256:  88008c3f59f49702ef66bd350672a8e80bddc171c513293426b3756b62456160
```

### Mutations applied

```
DELETE FROM vn_person_authority WHERE id='alias_A009319'   [A009319]
DELETE FROM vn_person_authority WHERE id='alias_A010534'   [A010534]
DELETE FROM vn_person_authority WHERE id='alias_A020120'   [A020120]
DELETE FROM vn_person_authority WHERE id='alias_A044094'   [A044094]
```

Total: **4 rows deleted** (expected 4 ✓)  
vn_person_authority: **1506 → 1502** ✓

### Excluded groups (pre-existing dila_id=NULL)

| dila_id | Status |
|---|---|
| A004981 | `phong_huyet_dien_chieu.dila_id=NULL` — đã tách trước; canonical `nam_vien_hue_ngung` còn dila_id=A004981 ✓ |
| A021291 | `lao_na_tu_dang_dai_hoang.dila_id=NULL`; chỉ còn `dai_hong_to_chung` (auto_ttl, dila_id=A021291) |
| A008471 | `hoang_long_tri_minh.dila_id=NULL` — đã tách trước; canonical `hoang_dinh_kien` còn dila_id=A008471 ✓ |

### Canonical rows still intact

| dila_id | keep_id | dila_id_after | status |
|---|---|---|---|
| A009319 | `tung_son_pho_tich` | `A009319` | `pending` ✓ |
| A010534 | `vu_chau_huyen_sach` | `A010534` | `pending` ✓ |
| A020120 | `dam_chau_trung_van_cai` | `A020120` | `pending` ✓ |
| A044094 | `thieu_chau_phap_hai` | `A044094` | `pending` ✓ |

## 2. Regression

| Test | Result |
|---|---|
| `test_t166_canonical_lock.py + test_t166_matrix.py` | **41/41 PASS** |
| `audit:t166` | **PASS (0 FAIL)** + 1 WARN (Gemini key — pre-existing) |
| `npm run pipeline` | PASS (run background) |

## 3. D3 Preparation (A021395)

Artifact: `docs/Mimo-Flash/T212-D3-A021395-canonical-prep.md`

- 2 rows remain with dila_id=A021395 (down from 3 in T207)
- `tu_to_phap_dien.dila_id=NULL` (pre-existing)
- Recommended canonical: `alias_A021395` (has name_zh='法演')
- Mutation plan prepared; Admin must choose Option A or B

## 4. D4 Preparation (A010511)

Artifact: `docs/Mimo-Flash/T212-D4-A010511-canonical-prep.md`

- `nam_nhac_huyen_thai.dila_id=NULL` (pre-existing — DISCONNECTED)
- `dam_chau_bao_cai_uoc.dila_id=A010511` (WRONG person — still connected)
- Sub-proposals [4A][4B][4C][4D] prepared
- [4A][4B][4D] can be executed after Admin confirm
- [4C] BLOCKED: replacement DILA ID for dam_chau_bao_cai_uoc = UNKNOWN

## 5. D2 (A047679)

DEFERRED — REQUIRE DILA/AUTHORITY EVIDENCE.  
`A047679.dila_id` count = 0 in current DB (both rows have dila_id=NULL per pre-existing mutation).  
All rows still in DB (dila_id=NULL).

## 6. D5 Follow-up Task

Created: `tasks/T213-vnpa-orphan-211-classification.md`

## 7. T206 rows unchanged

| entity_ref | status |
|---|---|
| PL000000000314 | `'Thế Sát Hải'` LOCKED — UNTOUCHED ✓ |
| PL000000000001 | `'Khoát Tạt Đa Quốc'` CANDIDATE — UNTOUCHED ✓ |

## 8. DB Integrity

| Check | Result |
|---|---|
| vn_person_authority before | 1506 |
| vn_person_authority after | 1502 (delta=4 = expected) ✓ |
| canonical_decision rows | 3 (unchanged) ✓ |
| Schema changed | No ✓ |
| D1-B/C/D/E untouched | ✓ |
| A047679 untouched | ✓ |
| A021395 untouched (no mutation) | ✓ |
| A010511 untouched (no mutation) | ✓ |
| 211 dila_id='' rows | 211 (unchanged) ✓ |
| T206 PL rows | unchanged ✓ |

## 9. Rollback

```powershell
# Python revert
python scripts/t212_safe_canonical_curation.py --revert --backup-path "data/backups/lineage_t212_20261002_153042.db"

# Hoặc manual
copy /Y "data\backups\lineage_t212_20261002_153042.db" "data\lineage.db"
```

Backup SHA256: `88008c3f59f49702ef66bd350672a8e80bddc171c513293426b3756b62456160`

## 10. Architecture

0 changes to:
- canonical_lock.py, vnpa_lookup.py, app.py, translation engine, lineage engine, API, UI, schema, T165-P8, T166
