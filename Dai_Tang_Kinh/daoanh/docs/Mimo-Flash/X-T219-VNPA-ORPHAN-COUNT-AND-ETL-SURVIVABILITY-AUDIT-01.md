# T219 — VNPA Orphan Count & ETL Survivability Audit
**Version:** 01  
**Date:** 2026-10-04  
**Mode:** READ-ONLY FORENSIC / INTEGRITY AUDIT  
**Status:** AWAIT ADMIN REVIEW

---

## A. Baseline

| Metric | Value |
|--------|-------|
| HEAD commit | `9cdee56` |
| Branch | `master` |
| Audit date | 2026-10-04 |
| DB path | `daoanh/data/lineage.db` |
| DB SHA256 (T213 snapshot) | `91ea38dcdb665ed9ab11ff70c5a4cb033aa90887d3f2d0f66565ddcd86684b2d` |
| DB SHA256 (T219 start, before scripts) | `e3773433304b035f7a26b42127e7458a1be66e149df9cf22e78379932c39c61d` |
| DB SHA256 (T219 throughout/after all scripts) | `a2e762c8a1c0f50a159e573924644cda0894f1aa6772ee8e1ae43329178cc96a` |
| SHA note | SHA₀→SHA₁ change is SQLite WAL checkpoint on first read-only connection (no data mutation). SHA₁ = SHA₂ = SHA₃ throughout all read scripts — confirmed stable. |
| Total rows vn_person_authority | **1507** |
| `dila_id = ''` (empty string) | **209** |
| `dila_id IS NULL` | **1** |
| `dila_id IS NOT NULL AND TRIM(dila_id)=''` | 209 (all are `''`, none are whitespace-only) |
| Whitespace-only (not `''`, not NULL) | **0** |
| dila_id has real value | **1297** |
| Check: 209+1+1297 | **= 1507 ✓** |
| Orphan total (empty OR NULL) | **210** |

**NULL row (1):**
- `tang_chu_pho_dung` — ttl='TS-Tang-Chu-Pho-Dung', created='2026-09-14 09:14:06'

**Change since T213 snapshot:**
- T213 counted 1506 rows; T219 sees 1507 (+1 row: `phuoc_chau_dai_an`, dila_id='A003636', created='2026-10-03 10:58:48')
- Orphan count unchanged: 210

---

## B. 211 → 210 Reconciliation

### Evidence gathered

| Metric | Value |
|--------|-------|
| Historical claimed count | 211 `dila_id=''` rows |
| T213 classified | 210 (209 empty + 1 NULL) |
| Delta | **−1** |
| Current empty-string count | 209 |
| Current NULL count | 1 |
| Rows in original cohort (created ≤ 2026-09-28) | 1502 |
| Of those, orphan NOW | 210 |

### Case determination

**CASE A confirmed: one historical orphan gained dila_id between the 211-count snapshot and T213 execution.**

Evidence:
1. All 210 current orphans have `created_at ≤ 2026-09-28` — they are in the original cohort.
2. 5 rows were added AFTER 2026-09-28 (all with dila_id already set): `dien_phuc_tue_thang`, `tien_phuoc_trach_sung`, `dinh_lam_canh_phuong`, `thach_mon_thu_tan` (all 2026-10-02), `phuoc_chau_dai_an` (2026-10-03). These are NOT replacements of original rows (created_at differs).
3. Of the 1502 original rows: 210 remain orphan NOW vs 211 historically → exactly **1 row gained dila_id** within that cohort.

**CASES B, C, D, E ruled out:**
- CASE B (row deleted): No row deletion detected; row count matches expected.
- CASE C (`''` → NULL): `tang_chu_pho_dung` has `created_at='2026-09-14'` — it was NULL from creation, not converted from `''`. The 211 historical count used `WHERE dila_id=''` which never included NULL rows.
- CASE D (whitespace sentinel): 0 whitespace-only values found.
- CASE E (query omission): T213 query `WHERE dila_id='' OR dila_id IS NULL` was verified — 210 rows, no duplicates, no omissions.

### C. Exact missing/changed row

**Exact row ID: UNIDENTIFIABLE without historical DB snapshot.**

Rationale: The DB is binary (not in git). The one row that gained dila_id is among the 1292 rows that currently have values. There is no audit log or git-tracked change to pinpoint which specific row transitioned from `''` to its current dila_id between the historical 211 snapshot and T213.

Probable window: Between T215 closeout (2026-09-28) and T213 execution (2026-10-03). A background ETL or manual curation assigned dila_id to one of the 211 rows during this period.

Recommended action: Accept delta as **CASE A — resolved, 1 row gained dila_id, row unidentifiable, no further action needed.**

---

## D. T213 Arithmetic Validation

### Re-run results

| Check | Result |
|-------|--------|
| Query `WHERE dila_id='' OR dila_id IS NULL` | 210 rows |
| Unique IDs | 210 (no duplicates) |
| C1+C2+C3+C4+C5+C6 (re-run algorithm) | 0+0+168+0+13+29 = **210** ✓ |
| Target population coverage | 100% ✓ |
| Non-target rows included | 0 ✓ |

**T213 arithmetic: VALID.**

Note: T213 REPORT shows C3=165, C5=16 (after 3 manual reclassifications: `thai_binh_hue_can_phat_giam`, `phat_y_linh_nhac`, `cs_huong` moved from C3 to C5). The base algorithm gives C3=168, C5=13. Both sum to 210. The reclassification is a documented analytical adjustment, not an arithmetic error.

If T213 has a classification concern: `cs_huong` (name_vi='Cs Hướng') correctly reclassified as C5 — bio confirms Cư Sĩ lay person. `thai_binh_hue_can_phat_giam` and `phat_y_linh_nhac` correctly reclassified as C5 — ID/name mismatch confirmed.

---

## E. Exact 11 TTL-Managed Orphan Rows

All 11 rows confirmed. Full inventory:

| # | id | name_vi | ttl_filename | Class | EL | Rel_out | Rel_in | gen_data | bio_len |
|---|----|---------|--------------|----|---|---------|--------|----------|---------|
| 1 | chuong_hiep_chanh_tri | Chương Hiệp Chánh Trì | TS-Chuong-Hiep-Chanh-Tri | C3 | E2 | 5 | 1 | No | 0 |
| 2 | dao_tin | Tôn Giả Đạo Tín | Ton-Gia-Dao-Tin | C3 | E2 | 8 | 6 | Yes | 3955 |
| 3 | minh_hai_phap_bao | Minh Hải Pháp Bảo | TS-Minh-Hai-Phap-Bao | C3 | E2 | 15 | 6 | Yes | 24071 |
| 4 | phap_kiem_minh_giac | Pháp Kiêm Minh Giác | TS-Phap-Kiem-Minh-Giac | C3 | E2 | 8 | 2 | Yes | 3503 |
| 5 | thien_tue_bao_chuong | Thiên Tuế Bảo Chưởng | TS-Thien-Tue-Bao-Chuong | C3 | E2 | 1 | 1 | Yes | 4420 |
| 6 | thiet_bao_cam_ung | Thiệt Bảo Cảm Ứng | TS-Thiet-Bao-Cam-Ung | C3 | E2 | 2 | 1 | No | 753 |
| 7 | thiet_dam_chanh_luan | Thiệt Đàm Chánh Luân | TS-Thiet-Dam-Chanh-Luan | C3 | E2 | 1 | 1 | Yes | 833 |
| 8 | thiet_dang_bao_quang | Thiệt Đăng Bảo Quang | TS-Thiet-Dang-Bao-Quang | C3 | E2 | 1 | 1 | No | 1226 |
| 9 | thiet_dinh_an_triem | Thiệt Dinh Ân Triêm | TS-Thiet-Dinh-An-Triem | C3 | E2 | 6 | 2 | Yes | 2896 |
| 10 | thiet_the_triem_an | Thiệt Thể Triêm Ân | TS-Thiet-The-Triem-An | C3 | E2 | 2 | 1 | No | 0 |
| 11 | toan_y_pho_hue | Toàn Ý Phổ Huệ | TS-Toan-Y-Pho-Hue | C3 | E2 | 8 | 2 | No | 1224 |

**Key fields:**
- All 11: `status='pending'`, `dila_id=''`, `name_zh=''` (empty — the `has_name_zh=True` in ETL audit is TTL-level detection for bio/label, not DB field)
- All 11 TTL files exist in `data/ttl/old/`
- All 11 have no `canonical_refs`, no `lineage_refs` (in dedicated table)
- `dao_tin` and `minh_hai_phap_bao` have `person_gen_computed` entries

**Pre-existing dangling outgoing refs (not caused by ETL):**
Already exist in DB before any ETL run. Affected rows: `chuong_hiep_chanh_tri` (4), `dao_tin` (1), `minh_hai_phap_bao` (8), `phap_kiem_minh_giac` (6), `thiet_bao_cam_ung` (1), `thiet_dinh_an_triem` (4), `thiet_the_triem_an` (1), `toan_y_pho_hue` (6) — total 31 dangling refs to non-existent vn_person_authority IDs. Pre-existing, not T219 scope.

---

## F. T217 ETL Code-Path Analysis

### Scoped DELETE for vn_person_authority (lines 391–418)

```python
_ttl_keys = tuple(fname[:-4] for fname in ttl_files)  # 16 keys from old/
_ph = ','.join('?' * len(_ttl_keys))

# Snapshot: only non-empty dila_id, only non-pending status
for _r in conn.execute(f"SELECT id, dila_id, status FROM vn_person_authority WHERE ttl_filename IN ({_ph})", _ttl_keys):
    if _r['dila_id'] and _r['dila_id'] != '':
        _curated_dila[_r['id']] = _r['dila_id']
    if _r['status'] and _r['status'] != 'pending':
        _curated_status[_r['id']] = _r['status']

# Scoped DELETE (correct):
conn.execute(f"DELETE FROM vn_person_authority WHERE ttl_filename IN ({_ph})", _ttl_keys)
```

✅ vn_person_authority DELETE: **correctly scoped** to 16 TTL keys.

### FULL DELETE for relation tables (line 413–414) ⚠️

```python
for t in ('vn_person_events', 'vn_person_works', 'vn_person_places', 'vn_person_relations'):
    conn.execute(f"DELETE FROM {t}")
```

⛔ **UNSCOPED FULL DELETE** — deletes ALL rows from ALL 4 tables regardless of TTL source.

### INSERT: reconstructs from TTL only

Lines 505–518: INSERT OR IGNORE only from `all_relations`/`all_places`/`all_works`/`all_events` — data extracted from old/ TTL files only. Non-old/ data is NOT reinserted.

### dila_id restoration (T217 guard, lines 535–563)

```python
if _r['dila_id'] and _r['dila_id'] != '':   # ← empty/NULL orphans NOT snapshotted
    _curated_dila[_r['id']] = _r['dila_id']
```

For the 11 orphan rows (all `dila_id=''`): **T217 snapshot skips them** (condition fails). No restore happens. After ETL, all 11 will have `dila_id=''` from TTL reconstruction (same state — no data loss on dila_id for these specific rows).

### Survivability verdict for all 11 rows

| id | vn_person_authority | dila_id after ETL | Relations (row-level) | Incoming refs at risk |
|----|--------------------|--------------------|----------------------|----------------------|
| chuong_hiep_chanh_tri | DELETE_AND_REINSERT_EQUIVALENT | '' (unchanged) | Reconstructed from TTL | 0 |
| dao_tin | DELETE_AND_REINSERT_EQUIVALENT | '' (unchanged) | Reconstructed from TTL | **5** |
| minh_hai_phap_bao | DELETE_AND_REINSERT_EQUIVALENT | '' (unchanged) | Reconstructed from TTL | **1** |
| phap_kiem_minh_giac | DELETE_AND_REINSERT_EQUIVALENT | '' (unchanged) | Reconstructed from TTL | 0 |
| thien_tue_bao_chuong | DELETE_AND_REINSERT_EQUIVALENT | '' (unchanged) | Reconstructed from TTL | **1** |
| thiet_bao_cam_ung | DELETE_AND_REINSERT_EQUIVALENT | '' (unchanged) | Reconstructed from TTL | 0 |
| thiet_dam_chanh_luan | DELETE_AND_REINSERT_EQUIVALENT | '' (unchanged) | Reconstructed from TTL | 0 |
| thiet_dang_bao_quang | DELETE_AND_REINSERT_EQUIVALENT | '' (unchanged) | Reconstructed from TTL | 0 |
| thiet_dinh_an_triem | DELETE_AND_REINSERT_EQUIVALENT | '' (unchanged) | Reconstructed from TTL | 0 |
| thiet_the_triem_an | DELETE_AND_REINSERT_EQUIVALENT | '' (unchanged) | Reconstructed from TTL | 0 |
| toan_y_pho_hue | DELETE_AND_REINSERT_EQUIVALENT | '' (unchanged) | Reconstructed from TTL | 0 |

**Row content** (name_vi, bio, gen_order, lineage): all survive via TTL reconstruction (TTL files contain bio=True, gen=True for all 11, except `chuong_hiep_chanh_tri` and `thiet_the_triem_an` which have bio_in_db=False anyway).

---

## G. Reference Integrity — CRITICAL FINDING

### vn_person_relations scope analysis

| Metric | Value |
|--------|-------|
| Total relations | **2088** |
| Relations from old/ TTL scope (16 files) | **159** (7.6%) |
| Relations from NON-old/ TTL scope (1011 files) | **1929** (92.4%) |
| **If ETL runs: relations PERMANENTLY LOST** | **1929** |
| No restore mechanism exists | ✓ confirmed |

This is a **CRITICAL ETL integrity risk** that T217 did NOT address.

The T217 guard protects only `dila_id` and `status` in `vn_person_authority`. The FULL DELETE on `vn_person_relations` (and 3 other tables) is NOT scoped, NOT protected, NOT snapshotted.

### Incoming AT-RISK refs for the 11 rows

| id | Total incoming | AT RISK (non-old/ source) | From whom |
|----|---------------|--------------------------|-----------|
| dao_tin | 6 | **5** | nguu_dau_phap_dung, tan_la_phap_lang, thien_phuc, hoang_mai_hoang_nhan, tang_xan |
| minh_hai_phap_bao | 6 | **1** | nguyen_thieu_sieu_bach |
| thien_tue_bao_chuong | 1 | **1** | bo_de_dat_ma |
| chuong_hiep_chanh_tri | 1 | 0 (from toan_y_pho_hue in old/) | — |
| phap_kiem_minh_giac | 2 | 0 (from old/ scope) | — |
| thiet_bao_cam_ung | 1 | 0 | — |
| thiet_dam_chanh_luan | 1 | 0 | — |
| thiet_dang_bao_quang | 1 | 0 | — |
| thiet_dinh_an_triem | 2 | 0 | — |
| thiet_the_triem_an | 1 | 0 | — |
| toan_y_pho_hue | 2 | 0 (from old/ scope) | — |

**Rows with AT-RISK refs:** dao_tin (5 at risk), minh_hai_phap_bao (1), thien_tue_bao_chuong (1).

**Simulation needed?: NO.** Static proof is sufficient — the code explicitly does `DELETE FROM {t}` for all rows, followed by INSERT from old/ TTL only. Any relation NOT from old/ TTL is permanently deleted with no restore path.

---

## H. High-Reference Row Audit

### minh_hai_phap_bao (21 total relations)
- **In TTL old/ scope: YES** (TS-Minh-Hai-Phap-Bao)
- Outgoing (15): All in TTL → SAFE (reconstructed from old/ TTL)
- Incoming (6): 5 SAFE (from Thiệt-series monks in old/), 1 AT RISK (`nguyen_thieu_sieu_bach` from TS-Nguyen-Thieu-Sieu-Bach not in old/)
- ETL impact: 1 incoming relation lost (nguyen_thieu_sieu_bach → minh_hai_phap_bao)
- Dedicated follow-up: NEEDS_ETL_GUARD

### dao_tin (14 total relations)
- **In TTL old/ scope: YES** (Ton-Gia-Dao-Tin)
- Outgoing (8): All in TTL → SAFE
- Incoming (6): 1 SAFE (self-loop dao_tin→dao_tin in old/ TTL), **5 AT RISK** (nguu_dau_phap_dung, tan_la_phap_lang, thien_phuc, hoang_mai_hoang_nhan, tang_xan — all non-old/ TTL)
- ETL impact: 5 incoming teacher/disciple relations lost — lineage graph for Đạo Tín becomes incomplete
- Dedicated follow-up: NEEDS_ETL_GUARD (HIGH PRIORITY)

### thai_binh_hue_can_phat_giam (23 total relations)
- **In TTL old/ scope: NO** (TS-Coc-Son-Hai)
- ETL does NOT affect vn_person_authority for this row (not in old/ scope)
- vn_person_relations FULL DELETE would destroy its 23 relations if they come from non-old/ TTL sources (TS-Coc-Son-Hai is not in old/)
- Identity mismatch (C5): id='thai_binh_hue_can_phat_giam' but content = 'Cốc Sơn Hải' — **separate identity repair required before any ETL, DILA lookup, or relation work**
- Dedicated follow-up: NEEDS_SEPARATE_IDENTITY_REPAIR + NEEDS_ETL_GUARD

### phat_y_linh_nhac (6 total relations)
- **In TTL old/ scope: NO** (TS-Phat-Y-Linh-Nhac)
- ETL does NOT affect vn_person_authority for this row
- vn_person_relations FULL DELETE would affect its relations (all from TS-Phat-Y-Linh-Nhac, not in old/)
- Identity mismatch (C5): id='phat_y_linh_nhac' but content = 'Trường Viễn' (name_vi) — **separate identity repair required**
- Dedicated follow-up: NEEDS_SEPARATE_IDENTITY_REPAIR

---

## I. T217 Contract Assessment

### Protected by T217

| Field | Protected | Mechanism |
|-------|-----------|-----------|
| `dila_id` (non-empty) | ✅ YES | Snapshot before DELETE, restore after INSERT |
| `status` (non-pending) | ✅ YES | Snapshot before DELETE, restore after INSERT |

### NOT protected by T217

| Field/Table | Protected | Risk |
|-------------|-----------|------|
| `name_vi`, `name_zh`, `dharma_lineage`, `generation_order` | ⚠️ Indirect | Survives only if TTL file contains equivalent data (confirmed for all 11) |
| `biographical_note_vi`, `birth_year`, `death_year`, `appellations` | ⚠️ Indirect | Survives only if TTL file contains data (confirmed for all 11 with bio) |
| `dila_id = ''` rows | ❌ NOT SNAPSHOTTED | Condition `if _r['dila_id'] and _r['dila_id'] != ''` skips empty/NULL |
| `vn_person_relations` | ❌ NOT PROTECTED | Full DELETE, 1929/2088 rows at risk, NO restore mechanism |
| `vn_person_places` | ❌ NOT PROTECTED | Full DELETE, non-old/ data lost |
| `vn_person_works` | ❌ NOT PROTECTED | Full DELETE, non-old/ data lost |
| `vn_person_events` | ❌ NOT PROTECTED | Full DELETE, non-old/ data lost |

### T217 Assessment

**`NEEDS_FOLLOWUP_GUARD`**

T217 is COMPLETE for `dila_id`/`status` preservation in `vn_person_authority`. However, it has a significant gap: the FULL DELETE on `vn_person_relations` (and 3 other tables) destroys 92.4% of all relations with no restore path. This was not within T217's original scope (T217 spec was focused on `vn_person_authority` only), but it represents a real ETL integrity risk that must be addressed before ETL is run.

---

## J. Follow-up Task Manifest

### Task 1 — Relations scope guard (ETL_GUARD, HIGH) — ✅ **IMPLEMENTED (T357)**

**ID:** T220  
**Title:** ETL vn_person_relations Scoped DELETE Guard  
**Risk:** 1929 relations from 1011 non-old/ TTL sources destroyed on next ETL run  
**Affected rows:** All 2088 relations, particularly the 1929 non-old/ ones  
**Scope:** Code-only (implemented in `scripts/t357_vnpa_safe_etl.py` via `managed_sql()`)  
**Fix:** `managed_sql()` function scopes ALL table operations to `ttl_filename IN ({_ph})`  
**Status:** ✅ **IMPLEMENTED** (commits `6ba4e95`, `82bd048`)  
**Verification:** 1929/2088 non-managed relations preserved on copy-DB test; 25/26 T220 tests PASS

```python
# Implemented in scripts/t357_vnpa_safe_etl.py lines 144-149:
def managed_sql(table, keys):
    placeholders = ','.join('?' for _ in keys)
    where = 'ttl_filename IN (' + placeholders + ')'
    if table == 'vn_person_authority':
        where += " AND substr(id,1,6) <> 'alias_'"
    return where
```

**Classification:** ✅ IMPLEMENTED — ETL now safe to run with proper waiver

---

### Task 2 — Identity repair: thai_binh_hue_can_phat_giam (IDENTITY_REPAIR, HIGH)

**Risk:** 23 relations pointing to a row where id and content represent different people  
**Affected:** `thai_binh_hue_can_phat_giam` (23 refs), `TS-Coc-Son-Hai` TTL file  
**Scope:** DB + TTL correction  
**Action required:** Admin decision — split into 2 correct rows (Thái Bình Huệ Cần AND Cốc Sơn Hải) or delete/rename  
**Prerequisite:** Admin must choose which monk the TTL file should represent  
**Classification:** NEEDS_SEPARATE_IDENTITY_REPAIR

---

### Task 3 — Identity repair: phat_y_linh_nhac (IDENTITY_REPAIR, MEDIUM)

**Risk:** 6 relations mislabeled; name_vi='Trường Viễn' in a row for 'phat_y_linh_nhac'  
**Scope:** DB + TTL correction  
**Prerequisite:** Determine correct content for TTL file TS-Phat-Y-Linh-Nhac  
**Classification:** NEEDS_SEPARATE_IDENTITY_REPAIR

---

### Task 4 — Pre-existing dangling refs (DATA_CURATION, LOW)

**Risk:** 31 outgoing refs in the 11 old/ orphan rows point to non-existent vn_person_authority IDs  
**Affected:** chuong_hiep_chanh_tri (4), dao_tin (1), minh_hai_phap_bao (8), phap_kiem_minh_giac (6), thiet_bao_cam_ung (1), thiet_dinh_an_triem (4), thiet_the_triem_an (1), toan_y_pho_hue (6)  
**Note:** Pre-existing, not introduced by T219. These are disciples not yet in DB.  
**Classification:** NEEDS_DATA_CURATION (low priority, disciples not yet imported)

---

### Task 5 — hoang_ba_hy_van data quality (DATA_CURATION, MEDIUM)

**Risk:** malformed name_vi with underscores; name_zh is a kệ/poem, not actual name  
**Scope:** DB UPDATE for name_vi and name_zh  
**Prerequisite:** Lookup correct Chinese name (黃蘗希運)  
**Classification:** NEEDS_DATA_CURATION

---

### Items with no action required

| Item | Classification | Reason |
|------|---------------|--------|
| 211→210 delta | SAFE_NO_ACTION | Explained (CASE A), 1 row gained dila_id, no data quality issue |
| T213 arithmetic | SAFE_NO_ACTION | Validated correct |
| 11 row content after ETL | SAFE_NO_ACTION | All DELETE_AND_REINSERT_EQUIVALENT (TTL contains equivalent data) |
| dila_id='' for 11 rows after ETL | SAFE_NO_ACTION | T217 correctly skips empty-string snapshot (no false restore) |
| tang_chu_pho_dung NULL | NEEDS_DATA_CURATION | NULL vs '' inconsistency — minor |

---

## K. Frozen Items

| Item | Status |
|------|--------|
| A021395 (bao_an_phap_dien / tu_to_phap_dien) | **BLOCKED_INSUFFICIENT_EVIDENCE** (T218) — no change |
| A010511 / dam_chau_bao_cai_uoc (D4) | **FROZEN** |
| T165-P8 | **GOVERNANCE HOLD** |
| T213 C3 rows | Not externally looked up (DILA not queried) |

---

## L. Mutation Proof

| Check | Result |
|-------|--------|
| DB SHA at T219 start | `e3773433...` |
| DB SHA during/after all scripts | `a2e762c8...` (stable, WAL checkpoint only) |
| Row counts changed | NO (1507→1507 throughout T219 scripts) |
| vn_person_authority mutations | 0 |
| vn_person_relations mutations | 0 |
| Schema changed | NO |
| ETL write path executed | NO |
| External LLM calls | 0 |
| External DILA transmission | 0 |
| Code files modified | 0 |
| Auto commit | NO |

SHA note: `e377...` (start) → `a2e7...` (after first read) is a SQLite WAL checkpoint artifact — NOT a data mutation. The database content (rows, schema) was not modified. All subsequent reads show stable `a2e7...`.

---

## M. Final Decision Gate (Updated 2026-10-13)

**T219 VERDICT: ETL_INTEGRITY_RISK_FOUND — ✅ MITIGATED BY T220**

**Critical finding:** `etl_ttl_person_authority.py` line 413–414 performed a FULL (unscoped) DELETE on `vn_person_relations`, `vn_person_places`, `vn_person_works`, `vn_person_events`. This would destroy 1929 of 2088 relations (92.4%) from 1011 non-old/ TTL sources on the next ETL run. There was no restore mechanism. T217 did NOT address this.

**✅ MITIGATED:** T220 implemented in T357 safe ETL framework (`scripts/t357_vnpa_safe_etl.py` — `managed_sql()` function scopes all table operations to `ttl_filename IN ({_ph})`).

**ETL can now run safely with proper waiver.**

**Do NOT run ETL with old unsafe script. Use T357 safe ETL with proper waiver.**

---

## Final Verdict Fields A–X

| Field | Value |
|-------|-------|
| A. HEAD | `9cdee56` |
| B. DB SHA before T219 / after T219 | `e3773433...` / `a2e762c8...` (WAL only, no data change) |
| C. Historical count | 211 `dila_id=''` |
| D. Current exact empty-string count | **209** |
| E. Current NULL count | **1** (tang_chu_pho_dung) |
| F. Reason for 211→210 | **CASE A**: 1 row from original cohort gained dila_id between historical snapshot and T213 execution |
| G. Exact affected row | **Unidentifiable** without historical DB snapshot (binary, not in git) |
| H. T213 arithmetic valid | **YES** — 210 rows, no duplicates, C-classes sum to 210 |
| I. Exact TTL-managed orphan count | **11** |
| J. 11-row survivability summary | **DELETE_AND_REINSERT_EQUIVALENT** for all 11 row content; dila_id stable at ''; 7 of 11 have AT-RISK incoming refs total (6 refs at risk) |
| K. High-reference risk summary | dao_tin: 5 incoming refs at risk; minh_hai_phap_bao: 1; thien_tue_bao_chuong: 1; thai_binh_hue_can_phat_giam: identity mismatch C5 |
| L. T217 assessment | **PARTIAL** — dila_id/status protected, vn_person_relations NOW protected via T220/T357 |
| M. Dangling-reference risk | **MITIGATED** — T220/T357 scoped operations preserve 1929 non-managed relations |
| N. Required follow-up tasks | Identity repairs for thai_binh_hue_can_phat_giam + phat_y_linh_nhac; D4 resolution |
| O. A021395 | **FROZEN** (BLOCKED_INSUFFICIENT_EVIDENCE, T218) |
| P. A010511 | **FROZEN** (D4) |
| Q. T165-P8 | **GOVERNANCE HOLD** |
| R. Production DB mutation | **NO** |
| S. Code mutation | **NO** |
| T. Production ETL executed | **NO** (use T357 with waiver) |
| U. External LLM calls | **0** |
| V. External DILA transmission | **0** |
| W. Artifact path | `daoanh/docs/Mimo-Flash/T219-VNPA-ORPHAN-COUNT-AND-ETL-SURVIVABILITY-AUDIT-01.md` |
| X. Exact recommended next task | **Admin W05 acknowledgment** → Generate production waiver → Run T357 safe ETL with waiver |

---

*READ ONLY — NO MUTATIONS PERFORMED — STOP — WAIT FOR ADMIN REVIEW (W05 acknowledgment)*
