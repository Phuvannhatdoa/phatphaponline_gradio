---
id: T369
title: "Phase 4b: Import Scripts & CBETA Re-mapping (Works, CBETA Citations, Activity)"
status: pending
created: 2026-10-12
updated: 2026-10-12
parent: T367
depends_on:
  - T368  # Schema must exist first
blocked_by: []
done_when:
  - "3 import scripts created: import_person_works.py, import_person_cbeta.py, import_person_activity.py"
  - "CBETA mapping fix script: fix_cbeta_mapping.py (44 dòng '了然' sai mapping re-assigned, số liệu thực tế — không phải 158)"
  - "Dry-run test: --limit 100 shows correct row counts + no DB writes"
  - "A000035, A033489, A020703 test cases verified (8 CBETA, 6 works, 4 places each)"
  - "Verification: tests/test_t369_imports.py passes (20+ test cases)"
  - "Evidence document: docs/evidence/T369_cbeta_reassignment_before_after.tsv"
  - "Code committed"
---

## Context

**Data Source:** T366 created JSON sidecars at `data/dila_import/extracted/<dila_id>.json`
**Scope:** Import **1,063 matched sidecars** (Option A, Admin approved) — không import toàn bộ 49,487 sidecars.
**Destination:** Import into 3 new tables created by T368:
- `person_activity` — birth/death/ordained/work dates (activity_type enum: 'birth', 'death', 'ordained', 'active_at', 'work')
- `passage_entity_mention` — CBETA citations
- Entity updates: `person_activity` for works metadata (activity_type='work')

**Critical Bug Fix:** 44 dòng (số liệu thực tế từ harness report) với tên "了然" đang bị CBETA-mapped sai person_id. Phải re-assign bằng DILA cross-references.

---

## Scope

### 1. `import_person_works.py`

**Purpose:** Read `<works_in_tripitaka>` from sidecars → Insert into `person_activity` (activity_type='work')

**Logic:**
```python
def import_person_works(sidecar_dir, db_path, dry_run=True, limit=None):
    """Import works from T366 sidecars."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    count = 0
    for sidecar_file in os.listdir(sidecar_dir):
        if limit and count >= limit:
            break
        
        dila_id = sidecar_file.replace('.json', '')
        sidecar = json.load(open(os.path.join(sidecar_dir, sidecar_file)))
        
        # Get person_id from vn_person_authority
        cursor.execute('SELECT id FROM vn_person_authority WHERE dila_id = ?', (dila_id,))
        result = cursor.fetchone()
        if not result:
            continue
        person_id = result[0]
        
        # Insert works as person_activity rows
        for work in sidecar.get('works_in_tripitaka', []):
            activity_id = f"PA_{uuid()}"
            cursor.execute('''
                INSERT INTO person_activity 
                (id, person_id, activity_type, source, confidence, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (activity_id, person_id, 'work', 'DILA', 1.0, work))
            count += 1
    
    if not dry_run:
        conn.commit()
    conn.close()
    return {'imported_works': count, 'dry_run': dry_run}
```

**Test Case:**
- A000035: 6 works → 6 person_activity rows inserted ✓
- A033489: 6 works → 6 person_activity rows inserted ✓

---

### 2. `import_person_cbeta.py`

**Purpose:** Read `<cbeta_citations>` from sidecars → Insert into `passage_entity_mention` (CBETA links)

**Logic:**
```python
def import_person_cbeta(sidecar_dir, db_path, dry_run=True, limit=None):
    """Import CBETA citations from T366 sidecars."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    count = 0
    for sidecar_file in os.listdir(sidecar_dir):
        if limit and count >= limit:
            break
        
        dila_id = sidecar_file.replace('.json', '')
        sidecar = json.load(open(os.path.join(sidecar_dir, sidecar_file)))
        
        # Get person_id
        cursor.execute('SELECT id FROM vn_person_authority WHERE dila_id = ?', (dila_id,))
        result = cursor.fetchone()
        if not result:
            continue
        person_id = result[0]
        
        # Parse CBETA citations: "( CBETA T50n2060_p0457c16 ) 唐高僧傳: ..."
        for citation in sidecar.get('cbeta_citations', []):
            # Extract passage_id: regex → "T50n2060_p0457c16"
            match = re.search(r'T\d+n\d+_p[0-9a-z]+', citation)
            if not match:
                continue
            passage_id = match.group(0)
            
            pem_id = f"PEM_{uuid()}"
            cursor.execute('''
                INSERT INTO passage_entity_mention
                (id, person_id, cbeta_passage_id, mention_type, context, source, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (pem_id, person_id, passage_id, 'subject', citation, 'DILA', 1.0))
            count += 1
    
    if not dry_run:
        conn.commit()
    conn.close()
    return {'imported_cbeta': count, 'dry_run': dry_run}
```

**Test Case:**
- A000035: 8 CBETA citations → 8 passage_entity_mention rows inserted ✓
- A000035 passage IDs correctly extracted (e.g., "T50n2060_p0457c16") ✓

---

### 3. `import_person_activity.py`

**Purpose:** Read `<birth_death_dates>`, `<places_of_origin>` from sidecars → Insert into `person_activity`

**Logic:**
```python
def import_person_activity(sidecar_dir, db_path, dry_run=True, limit=None):
    """Import birth/death/ordained events from T366 sidecars."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    count = 0
    for sidecar_file in os.listdir(sidecar_dir):
        if limit and count >= limit:
            break
        
        dila_id = sidecar_file.replace('.json', '')
        sidecar = json.load(open(os.path.join(sidecar_dir, sidecar_file)))
        
        # Get person_id and place_ids
        cursor.execute('SELECT id FROM vn_person_authority WHERE dila_id = ?', (dila_id,))
        result = cursor.fetchone()
        if not result:
            continue
        person_id = result[0]
        
        # Import birth/death/ordained
        dates = sidecar.get('birth_death_dates', {})
        for activity_type in ['birth', 'death', 'ordained']:
            if activity_type in dates:
                pa_id = f"PA_{uuid()}"
                year = dates[activity_type].get('year')
                place_name = dates[activity_type].get('place')
                
                place_id = None
                if place_name:
                    cursor.execute('SELECT id FROM places WHERE name_zh = ?', (place_name,))
                    result = cursor.fetchone()
                    if result:
                        place_id = result[0]
                
                cursor.execute('''
                    INSERT INTO person_activity
                    (id, person_id, place_id, activity_type, year_start, source, confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (pa_id, person_id, place_id, activity_type, year, 'DILA', 0.8))
                count += 1
        
        # Import places_of_origin
        for place_name in sidecar.get('places_of_origin', []):
            cursor.execute('SELECT id FROM places WHERE name_zh = ?', (place_name,))
            result = cursor.fetchone()
            if result:
                place_id = result[0]
                pa_id = f"PA_{uuid()}"
                cursor.execute('''
                    INSERT INTO person_activity
                    (id, person_id, place_id, activity_type, source, confidence)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (pa_id, person_id, place_id, 'active_at', 'DILA', 0.8))
                count += 1
    
    if not dry_run:
        conn.commit()
    conn.close()
    return {'imported_activities': count, 'dry_run': dry_run}
```

**Test Case:**
- A000035: 4 places_of_origin → 4 person_activity (active_at) rows ✓

---

### 4. `fix_cbeta_mapping.py` — CRITICAL BUG FIX

**Problem:** 44 dòng (số liệu thực tế theo harness report, không phải 158) với tên "了然" đang bị mapped sai vào cùng một person_id trong DB. Cần re-assign thành các monk riêng biệt với CBETA mapping đúng.

**Solution:** Use DILA cross-references (dynasty, dates, lineage) to disambiguate and re-assign:

```python
def fix_cbeta_mapping(db_path, dry_run=True):
    """Re-assign CBETA citations for 158 '了然' monks."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Find all "了然" monks in DILA
    cursor.execute('''
        SELECT dila_id, person_id FROM vn_person_authority 
        WHERE name_zh LIKE '%了然%'
    ''')
    monks = cursor.fetchall()
    
    before_count = 0
    after_count = 0
    
    for dila_id, current_person_id in monks:
        # Get DILA metadata
        cursor.execute('''
            SELECT id FROM vn_person_authority 
            WHERE dila_id = ? AND id != ?
        ''', (dila_id, current_person_id))
        correct_person_ids = [r[0] for r in cursor.fetchall()]
        
        if not correct_person_ids:
            continue
        
        # Re-assign CBETA citations from first person_id to correct person_ids
        cursor.execute('''
            SELECT COUNT(*) FROM passage_entity_mention 
            WHERE person_id = ? AND cbeta_passage_id LIKE ?
        ''', (current_person_id, f'%{dila_id}%'))
        before_count += cursor.fetchone()[0]
        
        # Update CBETA mappings
        for correct_person_id in correct_person_ids:
            # Complex logic: split CBETA citations by era/context
            # (Simplified: assign first half to first person_id, second half to second, etc.)
            cursor.execute('''
                UPDATE passage_entity_mention 
                SET person_id = ? 
                WHERE person_id = ? AND ...
            ''')  # Details elided
            after_count += 1
    
    if not dry_run:
        conn.commit()
    conn.close()
    
    return {
        'before': before_count,
        'after': after_count,
        'monks_fixed': len(monks),
        'dry_run': dry_run
    }
```

**Test Case:**
- Before: 44 dòng "了然" → single person_id (sai mapping)
- After: 44 dòng "了然" → individual person_ids with correct CBETA citations ✓

---

## Testing

### Dry-Run Test
```bash
cd daoanh

# Test imports with --limit 100
python -X utf8 scripts/import_person_works.py --limit 100 --dry-run
# Expected output: imported_works: ~600, dry_run: True

python -X utf8 scripts/import_person_cbeta.py --limit 100 --dry-run
# Expected output: imported_cbeta: ~800, dry_run: True

python -X utf8 scripts/import_person_activity.py --limit 100 --dry-run
# Expected output: imported_activities: ~400, dry_run: True

python -X utf8 scripts/fix_cbeta_mapping.py --dry-run
# Expected output: before: X, after: Y, monks_fixed: 44, dry_run: True
```

### Unit Tests
**File:** `daoanh/tests/test_t369_imports.py`

```python
import pytest
import json
import os

def test_import_person_works():
    """Test works import."""
    result = import_person_works('data/dila_import/extracted', 'data/lineage.db', dry_run=True, limit=50)
    assert result['imported_works'] > 0
    assert result['dry_run'] == True

def test_import_person_cbeta():
    """Test CBETA import."""
    result = import_person_cbeta('data/dila_import/extracted', 'data/lineage.db', dry_run=True, limit=50)
    assert result['imported_cbeta'] > 0
    
    # Verify A000035 has 8 CBETA rows
    cursor.execute('SELECT COUNT(*) FROM passage_entity_mention WHERE person_id = ?', (person_id_a000035,))
    count = cursor.fetchone()[0]
    assert count == 8

def test_import_person_activity():
    """Test activity import."""
    result = import_person_activity('data/dila_import/extracted', 'data/lineage.db', dry_run=True, limit=50)
    assert result['imported_activities'] > 0

def test_cbeta_mapping_fix():
    """Test CBETA '了然' mapping fix."""
    result = fix_cbeta_mapping('data/lineage.db', dry_run=True)
    assert result['monks_fixed'] == 44  # số liệu thực tế theo harness report
    assert result['after'] > result['before']
```

### Evidence Document
**File:** `daoanh/docs/evidence/T369_cbeta_reassignment_before_after.tsv`

```
dila_id	name_zh	before_cbeta_count	after_cbeta_count	before_person_id	after_person_ids
A000035	了然	12	8	P001	P001
A000036	了然	10	5	P001	P002
A000037	了然	14	7	P001	P003
...
```

---

## Deliverables

1. ✓ `daoanh/scripts/import_person_works.py`
2. ✓ `daoanh/scripts/import_person_cbeta.py`
3. ✓ `daoanh/scripts/import_person_activity.py`
4. ✓ `daoanh/scripts/fix_cbeta_mapping.py`
5. ✓ `daoanh/tests/test_t369_imports.py` (20+ test cases)
6. ✓ `daoanh/docs/evidence/T369_cbeta_reassignment_before_after.tsv`
7. ✓ `daoanh/docs/sessions/2026-10-12/T369_import_report.md`

---

## Timeline

- **Scripts:** 6 hours (4 import scripts + bug fix)
- **Testing & verification:** 4 hours (dry-run, unit tests, edge cases)
- **Documentation:** 2 hours
- **Total:** 12 hours (10 working days at 1-1.5 hrs/day)

---

## Dependencies & Unblocks

**Depends on:** T368 (schema ready)  
**Unblocks:** T359b (Fix 4-6 CBETA/works in UI) + T370 (lineage integration can proceed with working CBETA data)

---

## Critical Notes

⚠️ **CBETA Mapping Fix:** The 44 "了然" rows bug (số liệu thực tế theo harness report, không phải 158) is a real data integrity issue. All CBETA citations for "了然" must be re-assigned to correct person_ids before Phase 4 completes.

⚠️ **Dry-run Only:** Don't commit to DB until Admin approves. All tests use `dry_run=True` to verify logic without DB writes.

⚠️ **Data Loss:** If this import runs with errors, could corrupt DB. Must test thoroughly before actual `--no-dry-run` commit.

---

**Ready for daoanh-debugger implementation?** ✓
