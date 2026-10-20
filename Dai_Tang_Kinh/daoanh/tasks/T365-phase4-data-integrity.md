---
id: T365
title: "Phase 4 Planning: Data Integrity & Schema Rebuild (Weeks 9-12)"
status: pending
created: 2026-10-12
updated: 2026-10-12
parent: null
former_ids: []
done_when:
  - "places tables consolidated (places_dila + places_pending → single places table with source)"
  - "person_activity table created (for activeAt, birthplace, deathplace)"
  - "passage_entity_mention table created (for CBETA passage links)"
  - "entity_merge_log + audit trail implemented"
  - "SSOT merge strategy documented with examples"
  - "CBETA mapping fix: 44 dòng '了然' sai mapping re-assigned to correct dila_id (số liệu thực tế từ harness report, không phải 158)"
  - "Works import: author links assigned to correct persons"
  - "T359b (Fix 4-6) can proceed after Phase 4 complete"
note: >
  Option A (Admin approved): Import 1,063 people from vn_person_authority
  (matched sidecars) — không import toàn bộ 49,487 sidecar. Phase 4 chạy
  độc lập, không phụ thuộc T364.
---

## Context

Phases 1-3 improve code quality.
Phase 4 fixes data integrity issues discovered in architecture audit.

Current problems:
- **Issue #2:** Denormalized schema (places + places_dila + places_pending)
- **Issue #4:** Missing entity tables (person_activity, passage_entity_mention)
- **Issue #5:** CBETA mapping broken (7 "了然" monks, only 2 imported correctly)
- **Issue #8:** Works/activeAt incomplete (0 rows for most persons)

---

## Scope

### 1. Schema Consolidation & Normalization

**Before:**
```
places
places_dila
places_pending
places_vps
namevi_map_places
place_cbdb_map
...
```

**After:**
```
places (canonical)
├── id, name_zh, name_vi, source (DILA|VPS|PENDING|etc)
├── status (draft|verified|active)
└── confidence, created_at, updated_at

places_audit (for tracking changes)
├── change_id, place_id, field_name, old_value, new_value
└── changed_by, changed_at
```

### 2. New Entity Tables

**person_activity** (for activeAt, birthplace, deathplace):
```sql
CREATE TABLE person_activity (
    id INTEGER PRIMARY KEY,
    person_id TEXT,
    place_id TEXT,
    activity_type TEXT (ordained|taught|died|born|active),
    year_start INTEGER, year_end INTEGER,
    source TEXT (DILA|TTL|CBETA|etc),
    confidence REAL,
    FOREIGN KEY (person_id) REFERENCES people(id),
    FOREIGN KEY (place_id) REFERENCES places(id)
);
```

**passage_entity_mention** (for CBETA passage links):
```sql
CREATE TABLE passage_entity_mention (
    passage_id TEXT,
    entity_id TEXT,
    entity_type TEXT (person|place|work),
    context TEXT (excerpt from passage),
    mention_type TEXT (author|subject|place),
    FOREIGN KEY (passage_id) REFERENCES cbeta_ref_passages(passage_id)
);
```

### 3. CBETA & Works Mapping Fix

**Problem:** 44 rows (số liệu thực tế theo harness report, không phải 158) with name "了然" mapped to A015841/A040005 instead of correct monks
- A000035 (該僧 from XML) = 0 rows
- A015841 = 22 rows (wrong!)
- A040005 = 22 rows (wrong!)

**Solution:**
- Audit: Verify CBETA source data (sigla, context)
- Re-assign: Map to correct dila_id based on:
  - Year/dynasty context (when available)
  - Passage context (who is mentioned where)
  - TTL data (Vietnamese records as reference)
- Verify: No data loss, audit trail maintained

### 4. Entity Merge Strategy (SSOT)

Document "Single Source of Truth" merge logic:
```
For persons with same name:
  1. Check DILA context (dates, places, teachers)
  2. Check TTL data (Vietnamese nationality/lineage)
  3. Check CBETA mentions (signatures, passages)
  4. If ambiguous: Flag for manual review (add to entity_merge_log)
  5. Record decision in entity_merge_log with confidence score

For places:
  1. Use DILA as primary
  2. Add VPS/local modifications as source="VPS"
  3. Tag uncertain places as status="draft"
```

---

## Deliverables

- Schema consolidation script (migration SQL)
- person_activity table + data backfill
- passage_entity_mention table + CBETA linking
- entity_merge_log + audit trail
- CBETA mapping audit + re-assignment script
- docs/DATA_INTEGRITY_STRATEGY.md (SSOT merge rules)
- Verification scripts (before/after data validation)

---

## Timeline: 4 weeks (Phase 4)

### Breakdown:
- Week 1: Schema design + approval
- Week 2: Migration (places consolidation)
- Week 3: CBETA/Works mapping fix + person_activity backfill
- Week 4: Verification + edge cases

---

## UNBLOCKS

After Phase 4 complete:
- ✅ T359b (Fix 4-6) can proceed
  - Fix 4: CBETA citations load correctly
  - Fix 5: Works display correctly
  - Fix 6: ActiveAt places display correctly
- ✅ Lô 1 remaining tasks (data-dependent)

---

## Dependencies

- Depends on: không phụ thuộc T364 — Phase 4 chạy độc lập (Option A, Admin approved)
- Blocks: T359b, Lô 1 remaining tasks
