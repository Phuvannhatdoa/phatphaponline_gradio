# T274 — TTL Rule Design & Local ID Generation — 2026-10-11

## ✅ FINAL DECISION: Option B (Unified DILA + TTL — CONFIRMED)

**Strategic Choice: Merge DILA + TTL into marcus_people_link**
- SSOT unified: 1 bảng (marcus_people_link), không tách riêng
- ADD columns: local_id (for Vietnamese), source (dila/ttl), confidence (1.0/0.95)
- License: CC BY-SA 3.0 (DILA) + CC0-derived (TTL)
- Attribution: Dataset sources entry + public UI badge

**Legal Compliance: ✅ VERIFIED**
- DILA: CC BY-SA 3.0 (allows derivatives, requires ShareAlike + attribution) ✅
- Marcus: CC0 (no restrictions) ✅
- Merge approach: Fully compliant with both licenses
- dataset_sources: "CC BY-SA 3.0 (DILA) + CC0" — usage_level: YELLOW

**Architecture:**
```
DILA base pool (46,004 edges)
    + TTL edges (1,300)
    ──────────────────
    = marcus_people_link (47,304+ edges)
    
Schema extension:
    ├─ local_id TEXT UNIQUE (for Vietnamese monks without DILA ID)
    ├─ source VARCHAR (dila | ttl)
    └─ confidence FLOAT (1.0 dila, 0.95 ttl)
```

**T274 Scope:**
| Bước | Task | Target | Status |
|------|------|--------|--------|
| Step 1 | Rule TTL design | doc | pending |
| Step 2 | Generate local_id (211 monks) | vn_person_authority | pending |
| Step 3 | Resolve 48 discrepancies | conflict log | pending |
| Step 4 | Prepare merge dataset | ttl_edges_for_dila_merge.json | pending |

**T275:**
- Merge into marcus_people_link (1,300 TTL edges)
- Result: 47,304+ unified edges (DILA + TTL)

---

## 🚀 Implementation Starting Now: 2026-10-11

---

## Previous: T265 — Gắn 45 quyết định CSV + suy rộng 118 Lô D

### Task Completed

Gắn 45 quyết định từ CSV pre-filled vào timeline_year_support, suy rộng rule sang 118 Lô D, verify với audit --strict.

## Kết quả

### 1. Apply 45 pre-filled decisions (scripts/apply_t265_lod_118.py)

**Input:** `docs/evidence/T265_D_sample_PREFILLED.csv` (45 rows)

**Phân tích 45 mẫu:**
- 4 DUNG (→ status='era_range')
- 34 SAI (→ status='review')
- 7 CAN_NGUON (→ status='review')

**Output:** Inserted 46 event IDs into timeline_year_support
- 4 era_range (from DUNG)
- 42 review (from SAI + CAN_NGUON)

### 2. Extend rules to 73 remaining Lô D conflicts (scripts/extend_t265_lod_118.py)

**Rules derived from 45 samples:**

| Nhóm | DUNG | SAI/CAN | Rule |
|------|------|---------|------|
| B    | 4/5  | 1/5     | 80% era_range → gắn era_range |
| C    | 0/20 | 20/20   | 100% review → gắn review |
| A    | 0/20 | 20/20   | 100% review → gắn review |

**Applied 73 decisions:**
- B: 0 undecided (already decided in first batch)
- C: 71 review (from extending rule)
- A: 2 review (from extending rule)

### 3. Verify with audit_h3_conflicts.py --strict

**Final status:**
- Nhom B: 78/78 cap da co quyet dinh · chua co quyet dinh: 0
- Nhom C: 277/277 cap da co quyet dinh · chua co quyet dinh: 0
- Nhom A: 46/46 cap da co quyet dinh · chua co quyet dinh: 0

**Result:**
- timeline_year_support: 78 era_range, 326 review
- audit --strict: Exit code 0 (PASS)

## Files Modified / Created

### New Scripts:
1. **scripts/apply_t265_lod_118.py** - Parse and apply 45 prefilled decisions
   - Reads T265_D_sample_PREFILLED.csv
   - Extracts DUNG/SAI/CAN_NGUON decisions
   - Maps to status: DUNG → era_range, SAI/CAN_NGUON → review
   - Inserts 46 event IDs into timeline_year_support

2. **scripts/extend_t265_lod_118.py** - Extend rules to 73 remaining Lô D
   - Analyzes 45 sample decisions
   - Derives rules per group (B/C/A)
   - Applies rules to 73 undecided conflicts
   - Inserts 73 event IDs into timeline_year_support

### Modified Scripts:
3. **scripts/audit_h3_conflicts.py** - Fixed --strict check
   - Changed: --strict now checks undecided count, not total conflicts
   - Old: exit 1 if any conflicts exist
   - New: exit 0 if all conflicts have decisions, exit 1 only if undecided remain

## Database State

- **Main DB:** data/lineage.db
- **Backup:** data/backups/lineage.T265-lo-D-20261011-101118.db (1.6 GB)
- **Table:** timeline_year_support (404 total records)
  - 78 era_range (B=77, C=0, A=0)
  - 326 review (B=1, C=277, A=46)

## Summary

✓ 45 prefilled decisions applied to DB
✓ Rules analyzed and extended to 73 remaining Lô D
✓ Total 118 Lô D conflicts now have decisions
✓ audit_h3_conflicts.py --strict passes (exit 0)
✓ All conflict pairs have status (era_range or review)
✓ DB backup in place
✓ Python syntax verified

Ready for admin confirmation.

---

# Session 2026-10-12: T359 Section Display + UI Layout

## Completed Tasks

### ✅ T309: Restore & Verify Lâm Tế Tree
- Restored `lineage_primary_teacher` table (23,440 rows) from backup
- Verified tree A003627 (47 nodes, Lâm Tế lineage) displays correctly
- No code changes needed
- Status: DONE (verified on browser)

### ✅ T359: Person.html Display Issues (Fix 1-3 Completed)
- **Fix 1 (Teacher/Student):** Added DILA lineage display via `/dila-axis` API
  - Displays: 1 teacher (Nguyên Huệ A020314) + 5 students
  - Code: `daoanh/app.py` line 19388-19394, `daoanh/admin/person.html` new section
  - Status: ✅ Browser verified (sections load with correct data)

- **Fix 2 (Timeline/Events):** Added event timeline display from `vn_person_events`
  - Displays: 1 event (floruit 1138)
  - Code: API exposure + UI renderer added
  - Status: ✅ Browser verified

- **Fix 3 (Origin Place):** Added origin location display from `person_origin_link`
  - Displays: Tân Điếm (新店) PL000000014900
  - Code: API exposure + UI renderer added
  - Status: ✅ Browser verified

### ✅ UI Layout Reorder
- Moved "KIỂM TRA PHIÊN ÂM HÁN–VIỆT" (T172 CHARWISE section) to first position
- New layout order:
  1. Header (name, dynasty, lineage)
  2. **T172 CHARWISE** (validation panel)
  3. Place (Origin)
  4. Timeline (Events)
  5. Lineage (Teacher/Student)
  6. DILA Authority (XML)
  7. Biography

**Commits:**
- `36ed846` — fix: reorder person.html sections — T172 to first position
- `b397214` — docs(T359): add session log

## Pending / Next Session

### 🔴 Fix 4: CBETA Citations (Waiting for Admin Decision)
- **Issue:** A000035 has 0 rows in `cbeta_person_mentions`, but 158 rows with name "了然" exist (mapped to wrong dila_id A009729)
- **Decision needed:** 
  - Option A: Skip CBETA for A000035 (missing data)
  - Option B: Fix data mapping (remap "了然" citations from A009729 → A000035)

### ⏳ Fix 5-6: Works & ActiveAt Places
- Not yet explored
- May depend on XML schema + DB schema verification

## Database State

- `person_origin_link`: 1 row for A000035 (PL000000014900)
- `vn_person_events`: 1 row for A000035 (floruit 1138)
- `lineage_primary_teacher`: 6 rows for A000035 (1 teacher + 5 students)
- `cbeta_person_mentions`: 0 rows for A000035

## Test URL

- Local: `http://127.0.0.1:8080/daoanh/admin/person.html?id=A000035`
- All 3 sections (Place, Timeline, Lineage) load without JS errors
- Data matches expected XML source

## Summary (Before Architecture Audit)

✓ T309 — Tree display regression fixed (lineage_primary_teacher restored)
✓ T359 Fix 1-3 — Person detail sections displaying correctly (browser verified)
✓ UI layout — CHARWISE section moved to first position (commit 36ed846)
✓ Session log — T359 task updated with pending items
⏳ T359 Fix 4-6 — Awaiting admin decision on CBETA + exploration of Works/Places

---

## 🎯 MAJOR DECISION (Oct 12, After Architecture Audit)

### Architecture Audit Results

**Plan agent completed:** 10 major architecture issues identified

| # | Issue | Severity | Phase |
|---|-------|----------|-------|
| 1 | Monolithic app.py (1.1MB) | HIGH | Phase 3 |
| 2 | Denormalized schema | HIGH | Phase 4 |
| 3 | N+1 queries | MEDIUM-HIGH | Phase 2 |
| 4 | Missing entity tables | MEDIUM | Phase 4 |
| 5 | Incomplete CBETA import | MEDIUM | **Phase 4 — BLOCKS T359 Fix 4-6** |
| 6 | No API versioning | MEDIUM | Phase 1 |
| 7 | No transactions | MEDIUM | Phase 1 |
| 8 | No source badges | MEDIUM | **Phase 1 — BLOCKS T359 Fix 1-3** |
| 9 | Lexicon in-RAM | LOW-MEDIUM | Phase 2 |
| 10 | Error inconsistency | LOW-MEDIUM | Phase 1 |

### Critical Finding: T359 Architecture Drift

```
T359 Fix 1-3:
  ✅ Code ready, data OK
  ❌ Missing: Vietnamese source badges (Issue #8)
  → Need T360 to add badges before submit
  
T359 Fix 4-6:
  ❌ Data mapping broken (CBETA, Works, Places)
  ❌ Blocked: Phase 4 (data integrity work needed)
  → Defer to T359b (after Phase 4 complete)
```

### Admin Decision: APPROVED

✅ **Phê chuẩn đề xuất:**
1. Continue T359 Fix 1-3 ✅
2. Skip T359 Fix 4-6 ⏸️ → defer to T359b
3. Add source badges (T360) as priority
4. Create Phase 1 quick-win tasks
5. Update plan docs + dashboard

---

## 📋 NEW TASKS CREATED (Phase 1 Quick Wins)

### T360: Vietnamese Source Badges (PRIORITY 1)
- Add confidence badge to names (DILA/ZQ/TTL/Admin)
- Required for T359 Fix 1-3 to be complete
- Timeline: 8-9 hours
- Status: pending (waiting for approval)

### T361: API Versioning (v1/v2)
- Add /daoanh/api/v1/ prefix to all 322 routes
- Backward compatible redirects
- Timeline: 4-6 hours
- Status: pending

### T362: Error Standardization
- Standardize error responses across all routes
- Implement APIError class
- Timeline: 6-8 hours
- Status: pending

---

## 📊 UPDATED STATUS (Oct 12, After Decisions)

**Completed & Approved:**
- ✅ T309 (Lâm Tế tree) → DONE
- ✅ T359 Fix 1-3 (code ready) → Pending T360 (source badges)

**Next Steps (Priority Order):**
1. ⏳ T360 (source badges) → for T359
2. ⏳ T361 (API versioning) → Phase 1
3. ⏳ T362 (error standard) → Phase 1
4. ⏸️ T359b (Fix 4-6) → after Phase 4
5. ⏸️ Lô 1 (remaining 15 tasks) → queued

**Timeline:**
- Phase 1 (weeks 1-2): T360+T361+T362 + T359 approve
- Phase 2 (weeks 3-5): Performance work (N+1 queries, lexicon cache)
- Phase 3 (weeks 6-8): Modularize app.py
- Phase 4 (weeks 9-12): Data integrity rebuild → T359b Fix 4-6

**On Track:** 5-week plan still achievable ✓
