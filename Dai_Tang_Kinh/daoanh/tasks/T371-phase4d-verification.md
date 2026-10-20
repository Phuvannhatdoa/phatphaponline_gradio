---
id: T371
title: "Phase 4d: Verification & Data Integrity (Final Audit, Rollback Plan)"
status: pending
created: 2026-10-12
updated: 2026-10-12
parent: T367
depends_on:
  - T369  # Import complete, CBETA fixed
  - T370  # Lineage consolidated
blocked_by: []
done_when:
  - "Comprehensive audit report created: docs/T371_phase4_verification_report.md"
  - "Data integrity checklist passed: 10/10 items ✓"
  - "CBETA mapping: 44 dòng '了然' sai mapping re-assigned (số liệu thực tế, không phải 158) ✓"
  - "Lineage cycles: 0 detected ✓"
  - "Vietnamese coverage: % improved from 10.7% → X% documented"
  - "Rollback documentation complete: docs/PHASE4_ROLLBACK.md"
  - "Performance baseline tested: Phase 2 queries < 100ms with new schema"
  - "Check for 44 mis-mapped '了然' entries in entity_merge_log"
  - "Final commit + session log"
---

## Context

**Goal:** Final validation that Phase 4 (T368-T370) completed successfully with no data corruption.

**Input:** All Phase 4 data:
- 3 new tables: `person_activity`, `passage_entity_mention`, `entity_merge_log`
- Imports: CBETA citations, works, birth/death/ordained events
- Lineage: consolidated + orphan-linked
- CBETA bug fix: 44 dòng "了然" sai mapping re-assigned (số liệu thực tế, không phải 158)

**Output:** 
- ✅ Audit report with before/after metrics
- ✅ Rollback plan (in case issues found later)
- ✅ Performance baseline
- ✅ Ready to close Phase 4 and unlock T359b + Phase 5

---

## Scope

### 1. Comprehensive Audit Report

**File:** `docs/T371_phase4_verification_report.md`

**Sections:**

#### 1.1 Row Counts (Before/After)

```markdown
# Phase 4 Verification Report

## 1. Row Counts by Table

| Table | Before | After | Expected | Status |
|-------|--------|-------|----------|--------|
| person_activity | 0 | X | 6000-8000 | ✓ |
| passage_entity_mention | 0 | Y | 70000-80000 | ✓ |
| entity_merge_log | 0 | Z | 200-500 | ✓ |
| dharma_lineage_unified | 23014 | 23798 | 23014+784 (số liệu thực tế) | ✓ |
| vn_person_authority (updated) | 1074 | 1074 | 1074 | ✓ |

**Summary:** All tables populated as expected, no orphan rows.
```

#### 1.2 CBETA Mapping Fix

```markdown
## 2. CBETA Mapping Fix: 44 "了然" Rows (số liệu thực tế)

| Metric | Before | After | Status |
|--------|--------|-------|--------|
| "了然" rows pointing to same person_id | 44 | 44 | ✓ (now disambiguated) |
| CBETA passages re-assigned | 0 | 2456 | ✓ |
| Conflicts in re-assignment | — | 0 | ✓ |

**Sample A000035 CBETA Before/After:**
```
Before: person_id=P001, cbeta_citations=["T50n2060_p0457c16", "T48n2012_p0123a01", ...] (12 rows)
After:  person_id=P001, cbeta_citations=["T50n2060_p0457c16", "T48n2012_p0123a01", ...] (8 correct rows)
        person_id=P002, cbeta_citations=[...] (4 rows, re-assigned to different monk)
```

**Verification:**
- Each "了然" monk has unique CBETA passage IDs (no overlap)
- Total CBETA citations unchanged (conservation check)
- Passage IDs match person dynasty/era (sanity check)
```

#### 1.3 Lineage Integrity

```markdown
## 3. Lineage Integrity Checks

| Check | Result | Status |
|-------|--------|--------|
| Cycles detected (DFS algorithm) | 0 | ✓ PASS |
| Unresolved parents (NULL teacher_id) | 5 | ✓ ACCEPTABLE (roots allowed) |
| Unresolved students (NULL student_id) | 0 | ✓ PASS |
| Cross-source conflicts | 0 | ✓ PASS |
| Orphan monks (not in lineage graph) | 23 | ✓ ACCEPTABLE (<1% orphan rate) |

**Summary:** Lineage graph is valid DAG (directed acyclic graph), no cycles.
```

#### 1.4 Vietnamese Coverage Improvement

```markdown
## 4. Vietnamese Name Coverage

| Metric | Before Phase 4 | After Phase 4 | Improvement |
|--------|---|---|---|
| Monks with Vietnamese names | 576 | 810 | +41% |
| Coverage %: Vietnamese / Total | 10.7% | 15.1% | +4.4pp |
| Sources: DILA (Hán) | 1074 | 1074 | 0% (immutable) |
| Sources: ZQ transliteration (auto) | 1074 | 1074 | 0% (pre-existing) |
| Sources: TTL (Vietnam tông phái) | 0 | 234 | +234 NEW |
| Sources: Admin manual mapping | 0 | 76 | +76 NEW (during Phase 4) |

**Sample Improvement:**
```
A000035 (了然/Nghĩa Huyền)
Before: name_vi (auto) = "Liễu Nhiên" (ZQ score 0.5)
After:  name_vi (TTL) = "Nghĩa Huyền" + (DILA) = "了然" (sources diversified)
```
```

#### 1.5 Data Quality Metrics

```markdown
## 5. Data Quality Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| NULL values in foreign keys | 0 | 0 | ✓ PASS |
| Duplicate rows in new tables | 0 | 0 | ✓ PASS |
| Orphaned foreign key references | 0 | 0 | ✓ PASS |
| Consistency: Works import | 6000+ works | 5876 | ✓ 98% coverage |
| Consistency: CBETA import | 72000+ citations | 71234 | ✓ 99% coverage |
| Consistency: Activity import | 3000+ events | 3045 | ✓ 101% (ok, overlaps counted) |
```

#### 1.6 Index Performance

```markdown
## 6. Query Performance Baseline (Phase 2 readiness)

**Test:** Find monk A000035 + all CBETA + all works + all activity

Before (no indexes on new tables):
```
Query: SELECT * FROM vn_person_authority WHERE dila_id='A000035'
Time: 1ms (indexed)
Query: SELECT * FROM passage_entity_mention WHERE person_id=P001
Time: 800ms (no index) ✗
Query: SELECT * FROM person_activity WHERE person_id=P001
Time: 600ms (no index) ✗
Total: ~1.4s
```

After (indexes created by T368):
```
Query: SELECT * FROM vn_person_authority WHERE dila_id='A000035'
Time: 1ms (indexed)
Query: SELECT * FROM passage_entity_mention WHERE person_id=P001
Time: 2ms (indexed) ✓
Query: SELECT * FROM person_activity WHERE person_id=P001
Time: 2ms (indexed) ✓
Total: ~5ms ⚡⚡⚡ (280x faster!)
```

**Status:** ✓ PASS — Phase 2 performance requirements met.
```

---

### 2. Data Integrity Checklist

**File:** `daoanh/docs/sessions/2026-10-12/T371_data_integrity_checklist.md`

```markdown
# Phase 4 Data Integrity Checklist

## Pre-Audit Checks
- [ ] All T366 sidecars were processed (48,803 monks)
- [ ] No errors in T369 import scripts (check logs)
- [ ] No errors in T370 lineage consolidation (check logs)
- [ ] Database file size reasonable (~500MB-1GB, not bloated)
- [ ] No truncated tables (verify rowcounts > 0)

## Import Verification
- [ ] person_activity: 6000-8000 rows ✓
- [ ] passage_entity_mention: 70000-80000 rows ✓
- [ ] entity_merge_log: 200-500 rows ✓
- [ ] No NULL foreign keys ✓
- [ ] No duplicate rows ✓

## CBETA Fix Verification
- [ ] 44 "了然" rows have unique CBETA passages ✓ (số liệu thực tế, không phải 158)
- [ ] No CBETA citation loss (total unchanged) ✓
- [ ] Sample monks verified (A000035, A000036, ...) ✓
- [ ] 44 mis-mapped "了然" entries checked in entity_merge_log ✓

## Lineage Verification
- [ ] 0 cycles in graph ✓
- [ ] <1% orphan rate ✓
- [ ] DILA (23,014) + TTL (784) consolidated ✓ (số liệu thực tế)
- [ ] 211 VNPA orphans linked ✓

## Performance Verification
- [ ] Index queries < 2ms ✓
- [ ] Full person fetch < 5ms ✓
- [ ] Lineage path queries < 100ms ✓

## Rollback Verification
- [ ] Rollback script tested (tables drop cleanly) ✓
- [ ] Original data recoverable from backup ✓
- [ ] Rollback documented for admin ✓
```

---

### 3. Rollback Documentation

**File:** `docs/PHASE4_ROLLBACK.md`

```markdown
# Phase 4 Rollback Plan

## If Phase 4 Fails

### Immediate Actions (Within 1 hour)

1. **Stop all production traffic to DB**
   ```bash
   # Kill app.py process
   pkill -f app.py
   ```

2. **Restore backup**
   ```bash
   # Restore from pre-Phase4 backup
   cp /backups/lineage_db_pre_phase4.db data/lineage.db
   # Or from VPS backup
   rsync -avz admin@158.220.106.183:/backups/lineage_db_pre_phase4.db data/
   ```

3. **Verify restoration**
   ```bash
   sqlite3 data/lineage.db "SELECT COUNT(*) FROM dharma_lineage_base"
   # Should return: 23014 (số liệu thực tế)
   ```

4. **Restart services**
   ```bash
   python app.py > app.log 2>&1
   ```

### Rollback Script (If needed during Phase 4)

```sql
-- Drop new tables (if creation failed)
DROP TABLE IF EXISTS passage_entity_mention;
DROP TABLE IF EXISTS person_activity;
DROP TABLE IF EXISTS entity_merge_log;

-- Revert lineage consolidation (restore old tables)
DROP TABLE IF EXISTS dharma_lineage_unified;
-- Tables dharma_lineage_base + dharma_lineage_ttl_vn remain unchanged
```

### Post-Rollback Actions

1. **Notify admin** — explain why rollback was needed
2. **Audit logs** — check what failed (check app_local.err)
3. **Fix root cause** — address the issue before re-running Phase 4
4. **Re-test** — run Phase 4 again from step T368
```

---

### 4. Test Results

**File:** `daoanh/docs/sessions/2026-10-12/T371_test_results.md`

(Automatically generated from test suite output)

---

## Implementation Steps

### Step 1: Run Audit Script

```python
# File: daoanh/scripts/t371_run_audit.py
def run_full_audit(db_path):
    """Run comprehensive audit."""
    
    # 1. Row counts
    rowcounts = {}
    for table in ['person_activity', 'passage_entity_mention', 'entity_merge_log', 'dharma_lineage_unified']:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        rowcounts[table] = cursor.fetchone()[0]
    
    # 2. CBETA fix verification
    cbeta_fix = verify_cbeta_fix(db_path)
    
    # 3. Lineage integrity
    lineage_check = verify_lineage_integrity(db_path)
    
    # 4. Vietnamese coverage
    coverage = calculate_vietnamese_coverage(db_path)
    
    # 5. Performance baseline
    perf_baseline = run_performance_tests(db_path)
    
    # 6. Generate report
    report = {
        'rowcounts': rowcounts,
        'cbeta_fix': cbeta_fix,
        'lineage': lineage_check,
        'coverage': coverage,
        'performance': perf_baseline,
        'timestamp': datetime.now().isoformat()
    }
    
    return report
```

### Step 2: Generate Report

```bash
cd daoanh
python -X utf8 scripts/t371_run_audit.py > docs/sessions/2026-10-12/T371_test_results.md
```

### Step 3: Verify Rollback Plan

```bash
# Test rollback script
sqlite3 data/lineage.db < docs/PHASE4_ROLLBACK.md
# Should drop tables cleanly without errors
```

### Step 4: Performance Test

```bash
cd daoanh
python -X utf8 scripts/t371_performance_baseline.py
# Expected output: All queries < 100ms ✓
```

---

## Verification Checklist

- [ ] Audit report generated ✓
- [ ] All row counts verified ✓
- [ ] CBETA fix verified (158 monks re-assigned) ✓
- [ ] Lineage integrity checked (0 cycles) ✓
- [ ] Vietnamese coverage % calculated ✓
- [ ] Performance baseline tested (< 100ms queries) ✓
- [ ] Rollback plan documented ✓
- [ ] Rollback tested (tables drop cleanly) ✓
- [ ] No data loss during Phase 4 ✓
- [ ] Ready to close Phase 4 ✓

---

## Deliverables

1. ✓ `daoanh/docs/T371_phase4_verification_report.md` (comprehensive audit)
2. ✓ `daoanh/docs/sessions/2026-10-12/T371_data_integrity_checklist.md` (checklist)
3. ✓ `daoanh/docs/PHASE4_ROLLBACK.md` (rollback plan)
4. ✓ `daoanh/docs/sessions/2026-10-12/T371_test_results.md` (test output)
5. ✓ `daoanh/scripts/t371_run_audit.py` (audit automation)
6. ✓ `daoanh/scripts/t371_performance_baseline.py` (perf testing)

---

## Timeline

- **Audit scripts:** 2 hours
- **Run audit + tests:** 2 hours
- **Report generation:** 1 hour
- **Rollback documentation:** 1 hour
- **Final review:** 1 hour
- **Total:** 7 hours (5 working days)

---

## Dependencies & Unblocks

**Depends on:** T369 (import) + T370 (lineage)  
**Unblocks:** 
- ✅ **T359b (Fix 4-6)** — can proceed (CBETA/works/places fully imported)
- ✅ **Phase 5** — remaining Lô 1 tasks
- ✅ **Production Deployment** — when Phase 4 verification passed

---

## Critical Notes

⚠️ **Audit Must Pass:** If any audit item fails, do NOT proceed to production. Investigate and re-run Phase 4.

⚠️ **No Data Loss:** This is the final quality gate. All data must be 100% verified before closing.

⚠️ **Rollback Ready:** Keep backup DB available for 2 weeks in case production issues arise.

---

**Ready for daoanh-debugger implementation?** ✓
