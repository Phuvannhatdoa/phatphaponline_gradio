# T274 Build Report — Option A.2 (2026-10-11)

## Status: ⏳ BLOCKED on Data Structure Clarification

**Build Date:** Oct 11, 2026  
**Option:** A.2 (2 tables riêng: dharma_lineage_base + dharma_lineage_ttl_vn)  
**Backup Used:** Oct 10 (restored)  

---

## Findings

### ✅ What Worked
1. **Database Connection:** OK (1.4GB lineage.db, 146 tables)
2. **TTL Files:** Found 1,036 TTL files in `daoanh/data/ttl/`
3. **Vietnam Monks:** Loaded 1,064 monks from `vn_person_authority`
4. **Table Creation:** Successfully created 2 new tables
   - `dharma_lineage_base` (immutable DILA edges)
   - `dharma_lineage_ttl_vn` (Vietnam TTL edges)
5. **TTL Parsing:** Parsed 99 TTL files, extracted 167 edges

### ❌ What Failed
1. **DILA Edges:** Could NOT find DILA edges source
   - Searched for tables with 'edge', 'lineage', 'link' keywords
   - No table found with 46,004 DILA edges
   - **QUESTION:** Where are DILA edges stored?

2. **TTL Edge Extraction:** Only 167 edges extracted (expected ~1,300)
   - TTL parser may not be finding correct RDF predicates
   - **QUESTION:** What RDF predicates define teacher-student in TTL files?

3. **Vietnam Filter:** 0 edges after filtering (expected 1,106)
   - Issue: vn_person_authority DILA IDs don't match TTL entity URIs
   - **QUESTION:** How to map TTL entity names → vn_person_authority records?

---

## Data Structure Questions for Admin

### Q1: DILA Edges Location
- Which table contains the 46,004 DILA edges?
- Schema: What are the column names? (teacher_id? student_id? or different names?)
- Query example to extract?

### Q2: TTL Structure
- What are the exact RDF predicates for teacher-student relationships?
  - `bkg:hasTeacher`?
  - `pth:hasTeacher`?
  - `dila:teacher_of`?
  - Other?
- Namespace prefixes used in TTL files?

### Q3: Vietnam Monk Mapping
- How to match TTL monk names → `vn_person_authority.dila_id`?
  - Parse `rdf:label` or `pth:nameVietnam`?
  - Use name similarity matching?
  - Direct ID mapping exists?

---

## Next Steps (After Clarification)

1. **Fix DILA extraction** — Once we know the source table
2. **Fix TTL parsing** — Use correct RDF predicates
3. **Fix Vietnam filtering** — Use proper monk mapping logic
4. **Re-run build script** — Insert 46,004 + 1,106 edges
5. **Verify & commit** — Row counts, no duplicates, git commit

---

## Build Script Status

**File:** `daoanh/scripts/t274_build_dharma_tables.py` (ASCII-safe, runs without errors)

**Current Output:**
```
[START] T274 Build
[TABLES] Found 146 tables
[PHASE3] Extract DILA Edges: [WARN] Could not find DILA edges table
[PHASE4] Parse TTL Files: 1,036 files found, 99 parsed, 167 edges extracted
[PHASE5] Create Tables: OK (dharma_lineage_base, dharma_lineage_ttl_vn)
[PHASE6] Insert Data: 0 rows inserted (no DILA edges found)
[PHASE7] Verify: 0 total edges
[RESULT] SUCCESS (but no data)
```

**Verification Log:** `/tmp/t274_build.log` (local)

---

## Plan Revision Needed

Current plan assumed:
- DILA edges exist in accessible table ❌ (need location)
- TTL parsing with standard predicates ❌ (need exact predicates)
- Direct Vietnam monk mapping ❌ (need mapping logic)

**Awaiting admin clarification on Q1-Q3 above to proceed.**

---

## Estimate

- With clarifications: **30 min** to fix script + re-run + verify
- Without: **blocked**

**Assigned to:** Admin (data structure details)  
**Next Agent:** Once clarifications provided, run build again
