---
id: T368
title: "Phase 4a: Schema Design & Migration (Person Activity, Passage Entity Mention, Entity Merge Log, Dharma Lineage Unified)"
status: pending
created: 2026-10-12
updated: 2026-10-13
parent: T367
depends_on: []
blocked_by: [T368b]
done_when:
  - "4 new tables created: person_activity, passage_entity_mention, entity_merge_log, dharma_lineage_unified"
  - "activity_type enum includes 'work' alongside birth/death/ordained/active_at"
  - "All foreign keys and indexes created"
  - "Migration rollback script documented"
  - "Schema validated via PRAGMA commands"
  - "Code committed with test results"
---

## Context

**Phase 4 Architecture:** After T366 extracts XML → JSON sidecars, Phase 4 imports sidecars + external sources into DB. T368 is the **foundation**: create schema for new tables that will hold imported data.

**Current State:** DB has 1,074 persons + places (denormalized). Missing: `person_activity` (birth/death/ordained/work dates), `passage_entity_mention` (CBETA links), `entity_merge_log` (audit trail), `dharma_lineage_unified` (consolidated lineage).

**Scope note:** Places table consolidation (places, places_dila, namevi_map_places) đã tách sang **T368b** — T368 chỉ phụ trách person_activity, passage_entity_mention, entity_merge_log, dharma_lineage_unified. Nếu `person_activity.place_id` cần FK tới `places`, T368 phải chờ T368b hoàn tất trước (`blocked_by: [T368b]`).

**Blocker:** T369 (Import from sidecars) can't start until T368 (và T368b nếu cần places) schema is ready.

---

## Scope

### 1. Create `person_activity` Table

**Purpose:** Store person's key life events (birth, death, ordination, etc.)

**Schema:**
```sql
CREATE TABLE person_activity (
    id TEXT PRIMARY KEY,  -- PK: "PA000000001"
    person_id TEXT NOT NULL,  -- FK: vn_person_authority.id
    place_id TEXT,  -- FK: places.id (nullable — some events have no place)
    activity_type TEXT NOT NULL CHECK (activity_type IN ('birth','death','ordained','active_at','work')),
    year_start INTEGER,  -- Activity year or birth year
    year_end INTEGER,  -- For date ranges (e.g., active_at start/end)
    source TEXT,  -- 'DILA' | 'TTL' | 'CBETA'
    confidence REAL DEFAULT 0.8,  -- 1.0 = DILA, 0.8 = TTL, 0.5 = auto
    notes TEXT,  -- Context/comments
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (person_id) REFERENCES vn_person_authority(id),
    FOREIGN KEY (place_id) REFERENCES places(id)
);

CREATE INDEX idx_person_activity_person_id ON person_activity(person_id);
CREATE INDEX idx_person_activity_activity_type ON person_activity(activity_type);
```

**Example Rows:**
```
PA000000001 | A000035 | PL000000023255 | 'birth' | 唐 (600?) | NULL | DILA | 0.5 | "Dynasty approx"
PA000000002 | A000035 | PL000000023255 | 'ordained' | 618 | NULL | DILA | 0.8 | "Shaolin Temple"
PA000000003 | A000035 | NULL | 'death' | 700 | NULL | DILA | 0.5 | NULL
```

---

### 2. Create `passage_entity_mention` Table

**Purpose:** Link person to CBETA passages where they appear

**Schema:**
```sql
CREATE TABLE passage_entity_mention (
    id TEXT PRIMARY KEY,  -- PK: "PEM000000001"
    person_id TEXT NOT NULL,  -- FK: vn_person_authority.id
    cbeta_passage_id TEXT NOT NULL,  -- CBETA passage reference (e.g., "T50n2060_p0457c16")
    mention_type TEXT,  -- 'subject', 'author', 'translator', 'referenced'
    context TEXT,  -- Brief context from passage
    source TEXT,  -- 'DILA' (extracted from XML), 'CBETA' (matched)
    confidence REAL DEFAULT 1.0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (person_id) REFERENCES vn_person_authority(id)
);

CREATE INDEX idx_passage_entity_mention_person_id ON passage_entity_mention(person_id);
CREATE INDEX idx_passage_entity_mention_cbeta_passage_id ON passage_entity_mention(cbeta_passage_id);
```

**Example Rows:**
```
PEM000000001 | A000035 | T50n2060_p0457c16 | 'subject' | "唐高僧傳: 釋該僧傳 {少林寺}" | DILA | 1.0
PEM000000002 | A000035 | T48n2012_p0123a01 | 'referenced' | "景德傳燈錄: 該僧章 {南嶺}" | DILA | 1.0
PEM000000003 | A000035 | T99n9999_p0001a01 | 'author' | "Comment on 楞嚴經" | CBETA | 0.8
```

---

### 3. Create `entity_merge_log` Table

**Purpose:** Audit trail for monks with same/similar names (merge decisions)

**Schema:**
```sql
CREATE TABLE entity_merge_log (
    id TEXT PRIMARY KEY,  -- PK: "EML000000001"
    entity_type TEXT NOT NULL,  -- 'person', 'place', 'work'
    entity_ids TEXT NOT NULL,  -- JSON array: ["A000035", "B000123"] (merged IDs)
    decision TEXT,  -- 'merge', 'keep_separate', 'disambiguate'
    reason TEXT,  -- Why this decision was made
    created_by TEXT,  -- 'admin' | 'auto' | 'algorithm_name'
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(username)  -- IF users table exists
);

CREATE INDEX idx_entity_merge_log_entity_type ON entity_merge_log(entity_type);
```

**Example Rows:**
```
EML000000001 | 'person' | '["A000035", "A000094"]' | 'keep_separate' | "Two different dynasties (唐 vs 宋)" | 'admin' | 2026-10-12...
EML000000002 | 'place' | '["PL1", "PL2"]' | 'merge' | "Same place, different transcriptions" | 'auto' | 2026-10-12...
```

---

### 4. Places Table — MOVED TO T368b

Việc consolidate `places` (places, places_dila, namevi_map_places) đã được tách
sang task riêng **T368b** (`tasks/T368b-phase4a-places-schema.md`) để không
trộn lẫn phạm vi person-entity với phạm vi place-entity. T368 không tạo hoặc
sửa bảng `places` — nếu `person_activity.place_id` cần FK tới `places`, chạy
T368b trước.

---

## Implementation Steps

### Step 1: Backup Current Schema
```bash
cd daoanh
sqlite3 data/lineage.db ".schema" > docs/sessions/2026-10-12/lineage_db_schema_before_t368.sql
```

### Step 2: Create Migration Script
**File:** `daoanh/scripts/t368_create_tables.py`

```python
import sqlite3
import os

def create_tables(db_path):
    """Create new tables for Phase 4."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create person_activity
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS person_activity (
                id TEXT PRIMARY KEY,
                person_id TEXT NOT NULL,
                place_id TEXT,
                activity_type TEXT NOT NULL CHECK (activity_type IN ('birth','death','ordained','active_at','work')),
                year_start INTEGER,
                year_end INTEGER,
                source TEXT,
                confidence REAL DEFAULT 0.8,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (person_id) REFERENCES vn_person_authority(id),
                FOREIGN KEY (place_id) REFERENCES places(id)
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_person_activity_person_id ON person_activity(person_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_person_activity_activity_type ON person_activity(activity_type)')
        
        # Create passage_entity_mention
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS passage_entity_mention (
                id TEXT PRIMARY KEY,
                person_id TEXT NOT NULL,
                cbeta_passage_id TEXT NOT NULL,
                mention_type TEXT,
                context TEXT,
                source TEXT,
                confidence REAL DEFAULT 1.0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (person_id) REFERENCES vn_person_authority(id)
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_passage_entity_mention_person_id ON passage_entity_mention(person_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_passage_entity_mention_cbeta_passage_id ON passage_entity_mention(cbeta_passage_id)')
        
        # Create entity_merge_log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entity_merge_log (
                id TEXT PRIMARY KEY,
                entity_type TEXT NOT NULL,
                entity_ids TEXT NOT NULL,
                decision TEXT,
                reason TEXT,
                created_by TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_entity_merge_log_entity_type ON entity_merge_log(entity_type)')

        # Create dharma_lineage_unified (schema defined in detail in T370 consolidate_lineage.py)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dharma_lineage_unified (
                id TEXT PRIMARY KEY,
                teacher_id TEXT NOT NULL,
                student_id TEXT NOT NULL,
                source TEXT,  -- 'DILA' | 'TTL_VN' | 'merged'
                confidence REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES vn_person_authority(id),
                FOREIGN KEY (student_id) REFERENCES vn_person_authority(id),
                UNIQUE (teacher_id, student_id, source)
            )
        ''')

        conn.commit()
        print("✓ Tables created successfully")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    db = 'data/lineage.db'
    if os.path.exists(db):
        create_tables(db)
    else:
        print(f"DB not found: {db}")
```

### Step 3: Create Rollback Script
**File:** `daoanh/scripts/t368_rollback.sql`

```sql
-- Rollback T368 schema migration
DROP TABLE IF EXISTS passage_entity_mention;
DROP TABLE IF EXISTS person_activity;
DROP TABLE IF EXISTS entity_merge_log;
DROP TABLE IF EXISTS dharma_lineage_unified;
-- Note: places tables are out of scope for T368 (see T368b) — do not touch here.
```

### Step 4: Verify Schema
**File:** `daoanh/scripts/t368_verify_schema.py`

```python
import sqlite3

def verify_schema(db_path):
    """Verify T368 tables created correctly."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    checks = {}
    
    # Check person_activity
    cursor.execute("PRAGMA table_info(person_activity)")
    columns = [row[1] for row in cursor.fetchall()]
    checks['person_activity'] = all(col in columns for col in 
        ['id', 'person_id', 'place_id', 'activity_type', 'year_start', 'created_at'])
    
    # Check passage_entity_mention
    cursor.execute("PRAGMA table_info(passage_entity_mention)")
    columns = [row[1] for row in cursor.fetchall()]
    checks['passage_entity_mention'] = all(col in columns for col in 
        ['id', 'person_id', 'cbeta_passage_id', 'mention_type', 'created_at'])
    
    # Check entity_merge_log
    cursor.execute("PRAGMA table_info(entity_merge_log)")
    columns = [row[1] for row in cursor.fetchall()]
    checks['entity_merge_log'] = all(col in columns for col in 
        ['id', 'entity_type', 'entity_ids', 'decision', 'created_at'])
    
    # Check indexes
    cursor.execute("PRAGMA index_list(person_activity)")
    indexes = cursor.fetchall()
    checks['person_activity_indexes'] = len(indexes) >= 2

    # Verify CHECK constraint on activity_type (should reject invalid enum values)
    try:
        cursor.execute(
            "INSERT INTO person_activity (id, person_id, place_id, activity_type, year_start, year_end, source) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ('PA_TEST_9999', 'A999999', None, 'invalid_type', None, None, 'test')
        )
        conn.rollback()  # should not reach here
        checks['activity_type_check_constraint'] = False
    except sqlite3.IntegrityError:
        # Expected: "CHECK constraint failed" (or "UNIQUE constraint failed" if row already exists)
        conn.rollback()
        checks['activity_type_check_constraint'] = True

    conn.close()
    
    print("Schema Verification Results:")
    for check, result in checks.items():
        status = "✓" if result else "✗"
        print(f"  {status} {check}")
    
    return all(checks.values())

if __name__ == '__main__':
    if verify_schema('data/lineage.db'):
        print("\n✓ Schema verification PASSED")
    else:
        print("\n✗ Schema verification FAILED")
```

---

## Testing & Verification

### Test Steps
```bash
cd daoanh

# Step 1: Backup current schema
sqlite3 data/lineage.db ".schema" > docs/sessions/2026-10-12/schema_before.sql

# Step 2: Run migration
python -X utf8 scripts/t368_create_tables.py

# Step 3: Verify
python -X utf8 scripts/t368_verify_schema.py

# Step 4: Rollback test (optional, only if we need to undo)
# sqlite3 data/lineage.db < scripts/t368_rollback.sql
# python -X utf8 scripts/t368_verify_schema.py
```

### Verification Checklist
- [ ] `person_activity` table created with all columns ✓
- [ ] `passage_entity_mention` table created with all columns ✓
- [ ] `entity_merge_log` table created with all columns ✓
- [ ] All foreign keys present and valid ✓
- [ ] All indexes created ✓
- [ ] Schema verification script passes ✓
- [ ] Rollback script tested (tables dropped cleanly) ✓
- [ ] Row count: 0 rows (newly created tables) ✓

---

## Deliverables

1. ✓ `daoanh/scripts/t368_create_tables.py` — Migration script
2. ✓ `daoanh/scripts/t368_rollback.sql` — Rollback script
3. ✓ `daoanh/scripts/t368_verify_schema.py` — Verification script
4. ✓ `daoanh/docs/sessions/2026-10-12/lineage_db_schema_before_t368.sql` — Backup
5. ✓ `daoanh/docs/sessions/2026-10-12/T368_schema_design.md` — ER diagram + design doc
6. ✓ `daoanh/docs/sessions/2026-10-12/T368_test_results.md` — Test output + logs

---

## Timeline

- **Implementation:** 2 hours (write scripts, test)
- **Verification:** 30 minutes
- **Documentation:** 30 minutes
- **Total:** 3 days (can be compressed to 1 day if working continuously)

---

## Dependencies & Unblocks

**Depends on:** None directly; `blocked_by: [T368b]` nếu person_activity.place_id cần FK tới places đã consolidate
**Unblocks:** T369 (can start import once schema ready)

---

## Notes

- Schema uses TEXT for IDs (not INTEGER) to allow alphanumeric IDs like "A000035", "PL000023255"
- Foreign keys reference existing tables (vn_person_authority, places) — ensure these exist before running migration
- Indexes on frequently-queried columns (person_id, activity_type, cbeta_passage_id) for 10x faster lookups
- Confidence scores: 1.0 = DILA (high confidence), 0.8 = TTL (medium), 0.5 = auto-extracted (low)

---

**Ready for daoanh-debugger implementation?** ✓
