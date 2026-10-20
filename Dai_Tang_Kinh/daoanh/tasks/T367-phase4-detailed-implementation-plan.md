---
id: T367
title: "Phase 4 Detailed Implementation Plan (Parallel with T366)"
status: pending
created: 2026-10-12
updated: 2026-10-12
parent: T365
depends_on: []
blocked_by: []
done_when:
  - "Phase 4 breakdown into 4 sub-phases (T368-T371) created"
  - "Dependencies mapped: T368 → T369 → T370 → T371"
  - "Timeline: Parallel with T366 (Oct 12 - Nov 9)"
  - "daoanh-debugger + daoanh-qa + harness workflow approved"
  - "Dashboard updated with Phase 4 progress tracking"
---

## Context

**User Decision (Oct 12):** Run Phase 4 (T365) in PARALLEL with T366 to guarantee 100% data coverage.

**Rationale:** 
- T366 extracts XML → sidecars (2-3 hours)
- Phase 4 imports sidecars + external sources (4 weeks)
- Together: 85-90% (XML) + 10-15% (lineage/cross-refs) = **100%**

**Challenge:** T365 currently lists as single 4-week block. Need to break into parallel sub-phases to avoid bottlenecks.

---

## Phase 4 Breakdown (5 Weeks Total)

### Week 1 (Oct 12-18): Foundation & Schema
**T368 — Phase 4a: Schema Design & Migration**
- Create new tables:
  - `person_activity` (activeAt, birth, death, ordained dates)
  - `passage_entity_mention` (CBETA passage links)
  - `entity_merge_log` (audit trail)
- Create consolidated places table (merge places_dila + places_pending)
- Migration scripts + rollback plan
- **Duration:** 3 days
- **Dependency:** None (can start immediately)

### Week 2-3 (Oct 19-Nov 1): Data Import from Sidecars
**T369 — Phase 4b: Import Scripts & CBETA Re-mapping**
- Write `import_person_works.py` (from T366 sidecars)
- Write `import_person_cbeta.py` (from T366 sidecars)
- Write `import_person_activity.py` (birth/death/ordained places)
- Fix CBETA mapping bug: 44 "了然" monks re-assigned to correct DILA IDs
- Test with --dry-run on sample data
- **Duration:** 10 days
- **Dependency:** T368 (schema ready)
- **Unblocks:** T359b (Fix 4-6) once complete

### Week 3-4 (Oct 26-Nov 8): Lineage & Cross-References
**T370 — Phase 4c: Lineage Integration & Merge Strategy**
- Consolidate dharma_lineage_base + dharma_lineage_ttl_vn
- Link Vietnamese monks to DILA IDs (from TTL)
- Create entity_merge_log for ambiguous monks (same name)
- Document SSOT (Single Source of Truth) merge rules
- Cross-validate lineage: no cycles, no orphans
- **Duration:** 10 days (parallel with T369)
- **Dependency:** T368 (schema ready), T369 (data imported)

### Week 4-5 (Nov 1-9): Verification & Closure
**T371 — Phase 4d: Verification & Data Integrity**
- Run comprehensive audit:
  - Row counts: expected vs actual
  - CBETA mapping: 44 re-assigned ✓
  - Lineage cycles: 0 ✓
  - Vietnamese name coverage: % improvement
- Test Phase 2 (performance) with new schema
- Create rollback documentation
- **Duration:** 5 days
- **Dependency:** T369 + T370 complete

---

## Critical Path (Parallel Execution)

```
T366 (Oct 12-13, 2-3 hours)
  ↓ [sidecars ready]
  
T368 (Oct 12-18) ────────────→ T369 (Oct 19-Nov 1) ┐
                                                     → T370 (Oct 26-Nov 8)
                                                     ↓
                                                   T371 (Nov 1-9)
                                                   
RESULT (Nov 9): 100% coverage (85% XML + 15% lineage/cross-refs)
```

---

## Sub-Task Details

### T368 — Schema Design & Migration
**File:** `daoanh/tasks/T368-phase4a-schema-migration.md`

**Deliverables:**
- `scripts/t368_create_tables.py` (DDL for new tables)
- `scripts/t368_migrate_places.py` (places consolidation)
- `docs/T368_schema_design.md` (ER diagram, foreign keys)
- Migration test: `tests/test_t368_schema_migration.py`
- Rollback script: `scripts/t368_rollback.sql`

**Scope:**
- Create `person_activity` table (id, person_id, place_id, activity_type, year_start, year_end, source, confidence)
- Create `passage_entity_mention` table (passage_id, entity_id, entity_type, mention_type, context)
- Create `entity_merge_log` table (id, entity_type, entity_ids, decision, reason, created_by, created_at)
- Consolidate places: places_dila + places_pending → places (canonical)
- Add indexes on foreign keys

**QA:**
- Verify schema: `PRAGMA table_info(person_activity)` returns all columns ✓
- Verify indexes: `PRAGMA index_list(person_activity)` ✓
- Rollback test: apply migration, run rollback, verify schema reverted ✓

---

### T369 — Import Scripts & CBETA Re-mapping
**File:** `daoanh/tasks/T369-phase4b-import-from-sidecars.md`

**Deliverables:**
- `scripts/import_person_works.py` (from T366 sidecars)
- `scripts/import_person_cbeta.py` (from T366 sidecars)
- `scripts/import_person_activity.py` (from T366 sidecars + TTL)
- `scripts/fix_cbeta_mapping.py` (44 "了然" re-assignment)
- Evidence: `docs/evidence/T369_cbeta_reassignment_before_after.tsv`
- Verification: `tests/test_t369_imports.py` (20+ test cases)

**Scope:**
- Read from `data/dila_import/extracted/<dila_id>.json` (T366 output)
- Parse works, CBETA, timeline from sidecars
- Insert into person_activity, passage_entity_mention
- CBETA bug fix: 44 rows with wrong person_id → correct person_id
- Verify no data loss: sidecar count = DB rows

**Test Cases:**
- A000035: 8 CBETA citations → 8 passage_entity_mention rows ✓
- A033489: 6 works → 6 person_activity rows ✓
- CBETA mapping: "了然" A000035 gets correct 8 citations ✓

---

### T370 — Lineage Integration
**File:** `daoanh/tasks/T370-phase4c-lineage-integration.md`

**Deliverables:**
- `scripts/consolidate_lineage.py` (merge DILA + TTL edges)
- `scripts/link_vnpa_to_dila.py` (Vietnamese monks → DILA IDs)
- `docs/SSOT_merge_strategy.md` (merge rules for ambiguous monks)
- `docs/evidence/T370_lineage_audit.tsv` (cycles, orphans, coverage)
- Verification: `tests/test_t370_lineage_integrity.py` (cycle detection, uniqueness)

**Scope:**
- Consolidate dharma_lineage_base + dharma_lineage_ttl_vn
- Link VNPA orphans (211 without DILA ID) to DILA via TTL mapping
- Create entity_merge_log for same-name monks
- Verify: no cycles, no unresolved parents, 100% lineage coverage

**Test Cases:**
- Cycle detection: find any A→B→C→A paths (should be 0) ✓
- Orphan detection: find monks with NULL teacher (should be rare) ✓
- Vietnamese coverage: % of monks with Vietnamese names (track improvement) ✓

---

### T371 — Verification & Closure
**File:** `daoanh/tasks/T371-phase4d-verification.md`

**Deliverables:**
- Comprehensive audit report: `docs/T371_phase4_verification_report.md`
- Data integrity checklist: before/after metrics
- Rollback documentation: `docs/PHASE4_ROLLBACK.md`
- Performance baseline: query times before/after (Phase 2 readiness)

**Verification Checklist:**
- ✓ Row counts: person_activity = X, passage_entity_mention = Y
- ✓ CBETA mapping: 44 "了然" fixed
- ✓ Lineage cycles: 0
- ✓ Vietnamese coverage: improved from 10.7% → X%
- ✓ Rollback tested: can revert all changes
- ✓ Phase 2 performance: queries < 100ms with new schema

---

## Timeline & Dependencies

```
Week 1 (Oct 12-18):
├─ T366: Extract XML → sidecars (2-3 hours, Oct 12)
└─ T368: Schema migration (3 days, Oct 12-18) ✓ INDEPENDENT

Week 2 (Oct 19-25):
└─ T369: Import + CBETA fix (starts Oct 19, depends on T368)
   └─ Unblocks T359b (Fix 4-6) when complete

Week 3 (Oct 26-Nov 1):
├─ T369: (continues)
└─ T370: Lineage integration (starts Oct 26, depends on T368+T369)

Week 4-5 (Nov 1-9):
└─ T371: Verification (starts Nov 1, depends on T369+T370)

FINAL (Nov 9): All Phase 4 complete → 100% coverage
```

---

## Parallel Execution Benefits

| Phase | Duration | Critical Path Impact | Benefit |
|-------|----------|----------------------|---------|
| **T366** | 2-3 hours | Creates sidecars (blocks T369) | Starts Phase 4 |
| **T368** | 3 days | Independent (can run immediately) | **Parallel savings: 3 days** |
| **T369** | 10 days | Depends on T368 (Oct 19 start) | Feeds T370 |
| **T370** | 10 days | Parallel with T369 | **Parallel savings: 5 days** |
| **T371** | 5 days | Depends on T369+T370 | Final validation |

**Total time: 4 weeks (vs 5-6 weeks if sequential)**

---

## Unblocks

After Phase 4 complete (Nov 9):
- ✅ **T359b (person.html Fix 4-6)** — can proceed (CBETA/works/places fully imported)
- ✅ **Phase 5+ Tasks** — remaining Lô 1 work
- ✅ **100% Data Coverage** for all 48,803 monks

---

## Approval & Next Steps

1. **Approve Phase 4 breakdown** (T368-T371)
2. **Create sub-tasks** in tasktodo.md
3. **Assign to daoanh-debugger + daoanh-qa**
4. **Start T366 + T368 immediately** (Oct 12)
5. **Update Dashboard** with Phase 4 progress tracking

---

**Ready to proceed?** 🚀
