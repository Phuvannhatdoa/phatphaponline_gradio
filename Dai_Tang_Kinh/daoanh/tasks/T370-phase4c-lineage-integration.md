---
id: T370
title: "Phase 4c: Lineage Integration & Merge Strategy (DILA + TTL + Vietnamese)"
status: pending
created: 2026-10-12
updated: 2026-10-12
parent: T367
depends_on:
  - T368  # Schema ready
  - T369  # CBETA fixed, data integrity verified
blocked_by: []
done_when:
  - "dharma_lineage_base + dharma_lineage_ttl_vn consolidated"
  - "211 VNPA orphans linked to DILA via TTL mapping"
  - "entity_merge_log populated for ambiguous monks (same name)"
  - "Lineage integrity verified: 0 cycles, 0 unresolved parents"
  - "Vietnamese coverage % calculated before/after"
  - "docs/SSOT_merge_strategy.md documented (merge rules)"
  - "Verification: tests/test_t370_lineage_integrity.py passes"
  - "Evidence: docs/evidence/T370_lineage_audit.tsv"
  - "Code committed"
---

## Context

**Three Lineage Sources:**
1. **dharma_lineage_base** (23,014 edges — số liệu thực tế, không phải 46,004) — DILA, immutable reference pool
2. **dharma_lineage_ttl_vn** (784 edges — số liệu thực tế, không phải 1,106) — TTL Vietnam subset (via T274)
3. **Vietnamese monks without DILA mapping** (211 orphans) — Need linking

**Goal:** Consolidate all 3 sources into unified lineage graph with no conflicts, cycles, or orphans.

**Ghi chú:** Mismatches không khớp (ví dụ các dòng "了然" không match được) sẽ được
ghi vào `entity_merge_log` để chờ Admin review thủ công, không tự động merge
khi chưa xác minh.

---

## Scope

### 1. Consolidate `dharma_lineage_base` + `dharma_lineage_ttl_vn`

**Current State:** 2 separate tables
**Target State:** 1 unified table `dharma_lineage_unified` with source tagging

**Script:** `consolidate_lineage.py`

```python
def consolidate_lineage(db_path, dry_run=True):
    """Consolidate DILA + TTL edges into unified table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create unified table (or insert if already exists)
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
        
        # Insert DILA edges (if not duplicate)
        cursor.execute('''
            INSERT OR IGNORE INTO dharma_lineage_unified 
            (id, teacher_id, student_id, source, confidence)
            SELECT id, teacher_id, student_id, 'DILA', confidence 
            FROM dharma_lineage_base
        ''')
        
        dila_count = cursor.rowcount
        
        # Insert TTL edges (if not duplicate)
        cursor.execute('''
            INSERT OR IGNORE INTO dharma_lineage_unified 
            (id, teacher_id, student_id, source, confidence)
            SELECT id, teacher_id, student_id, 'TTL_VN', confidence 
            FROM dharma_lineage_ttl_vn
        ''')
        
        ttl_count = cursor.rowcount
        
        # Check for conflicts (same edge from both sources with different confidence)
        cursor.execute('''
            SELECT teacher_id, student_id, COUNT(*) as conflict_count
            FROM dharma_lineage_unified
            WHERE (teacher_id, student_id) IN (
                SELECT teacher_id, student_id FROM dharma_lineage_unified
                GROUP BY teacher_id, student_id HAVING COUNT(DISTINCT source) > 1
            )
            GROUP BY teacher_id, student_id
        ''')
        conflicts = cursor.fetchall()
        
        if not dry_run:
            conn.commit()
        
        return {
            'dila_inserted': dila_count,
            'ttl_inserted': ttl_count,
            'conflicts': len(conflicts),
            'dry_run': dry_run
        }
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()
```

---

### 2. Link VNPA Orphans to DILA

**Problem:** 211 monks in `vn_person_authority` have no DILA mapping (no `dila_id`)

**Solution:** Use TTL cross-reference table to match Vietnamese name ↔ DILA ID

**Script:** `link_vnpa_to_dila.py`

```python
def link_vnpa_to_dila(db_path, dry_run=True):
    """Link orphan Vietnamese monks to DILA via TTL mapping."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Find orphans (no dila_id)
    cursor.execute('''
        SELECT id, name_vi FROM vn_person_authority 
        WHERE dila_id IS NULL
    ''')
    orphans = cursor.fetchall()
    
    linked_count = 0
    unlinked = []
    
    for orphan_id, name_vi in orphans:
        # Look for matching name in TTL mapping table
        # (Assumes TTL provides mappings like: vietnamese_name → dila_id)
        cursor.execute('''
            SELECT dila_id FROM ttl_vietnam_mappings 
            WHERE name_vi = ?
        ''', (name_vi,))
        
        result = cursor.fetchone()
        if result:
            dila_id = result[0]
            
            # Update orphan with dila_id
            cursor.execute('''
                UPDATE vn_person_authority 
                SET dila_id = ? 
                WHERE id = ?
            ''', (dila_id, orphan_id))
            
            linked_count += 1
            
            # Create merge_log entry (documenting the link)
            cursor.execute('''
                INSERT INTO entity_merge_log 
                (id, entity_type, entity_ids, decision, reason, created_by)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                f"EML_{uuid()}",
                'person',
                json.dumps([orphan_id, dila_id]),
                'keep_separate',
                f"Linked Vietnamese orphan to DILA via TTL mapping",
                'auto'
            ))
        else:
            unlinked.append((orphan_id, name_vi))
    
    if not dry_run:
        conn.commit()
    
    return {
        'orphans_found': len(orphans),
        'linked': linked_count,
        'unlinked': len(unlinked),
        'unlinked_list': unlinked,
        'dry_run': dry_run
    }
```

**Expected Result:** 211 orphans → ~180-190 linked (some names too generic to match)

---

### 3. Document Merge Strategy

**File:** `docs/SSOT_merge_strategy.md`

**Rules for ambiguous monks (same name, different eras):**

```markdown
# Single Source of Truth (SSOT) Merge Strategy

## Disambiguation Rules

When multiple monks have the same name (e.g., 5 "了然" monks from different dynasties):

1. **Primary Key:** (name_zh, dynasty, century)
2. **Cross-Reference:** DILA ID, TTL ID, CBETA passage IDs
3. **Confidence Scoring:**
   - DILA mapping (same name + dynasty + dates match): 1.0
   - TTL mapping (same name + lineage match): 0.8
   - CBETA passage context: 0.6

## Conflict Resolution

### Case 1: Same Edge from DILA + TTL
- Use DILA as primary source
- Keep TTL as secondary (confidence 0.8 vs 1.0)
- Log in entity_merge_log

### Case 2: Name collision (multiple monks, same name)
- Create separate entries for each (differentiate by dila_id)
- Link ambiguous ones via entity_merge_log
- UI shows disambiguation note: "(唐代)" "(宋代)" etc.

### Case 3: Missing DILA ID (orphan Vietnamese monk)
- Try TTL mapping table
- If matched: update dila_id, log in entity_merge_log
- If unmatched: keep as separate Vietnamese entry (status='pending')

## Entity Merge Log Schema

```json
{
  "id": "EML000000001",
  "entity_type": "person",
  "entity_ids": ["A000035", "VN000123"],  // IDs being merged/linked
  "decision": "keep_separate",  // 'merge' | 'keep_separate' | 'disambiguate'
  "reason": "Two different dynasties (唐 vs 宋)",
  "created_by": "admin",  // or 'auto'
  "created_at": "2026-10-12T14:30:00Z"
}
```

## Lineage Integrity Checks

1. **No cycles:** Verify no A→B→C→A paths
2. **No unresolved parents:** Every student should have a teacher (or be root)
3. **Cross-source consistency:** DILA edges should not conflict with TTL edges
```

---

### 4. Lineage Integrity Verification

**Script:** `verify_lineage_integrity.py`

```python
def verify_lineage_integrity(db_path):
    """Verify lineage has no cycles, orphans, or conflicts."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    checks = {}
    
    # 1. Cycle detection (DFS)
    def has_cycle():
        cursor.execute('SELECT DISTINCT teacher_id, student_id FROM dharma_lineage_unified')
        edges = cursor.fetchall()
        
        graph = {}
        for teacher, student in edges:
            if teacher not in graph:
                graph[teacher] = []
            graph[teacher].append(student)
        
        visited = set()
        rec_stack = set()
        
        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.remove(node)
            return False
        
        for node in graph:
            if node not in visited:
                if dfs(node):
                    return True
        return False
    
    checks['has_cycle'] = has_cycle()
    
    # 2. Orphan detection
    cursor.execute('''
        SELECT COUNT(*) FROM vn_person_authority 
        WHERE id NOT IN (
            SELECT DISTINCT teacher_id FROM dharma_lineage_unified
            UNION
            SELECT DISTINCT student_id FROM dharma_lineage_unified
        )
    ''')
    orphans = cursor.fetchone()[0]
    checks['orphans_count'] = orphans
    
    # 3. Conflict detection (same edge from multiple sources)
    cursor.execute('''
        SELECT teacher_id, student_id, COUNT(DISTINCT source)
        FROM dharma_lineage_unified
        GROUP BY teacher_id, student_id
        HAVING COUNT(DISTINCT source) > 1
    ''')
    conflicts = len(cursor.fetchall())
    checks['conflicts_count'] = conflicts
    
    # 4. Row counts
    cursor.execute('SELECT COUNT(*) FROM dharma_lineage_unified')
    checks['total_edges'] = cursor.fetchone()[0]
    
    conn.close()
    
    return checks
```

---

## Testing

### Dry-Run Test
```bash
cd daoanh

# Consolidate lineage
python -X utf8 scripts/consolidate_lineage.py --dry-run
# Expected: dila_inserted: 23014, ttl_inserted: 784, conflicts: <10 (số liệu thực tế)

# Link orphans
python -X utf8 scripts/link_vnpa_to_dila.py --dry-run
# Expected: orphans_found: 211, linked: ~180-190

# Verify integrity
python -X utf8 scripts/verify_lineage_integrity.py
# Expected: has_cycle: False, orphans_count: ~20-30, conflicts: 0
```

### Unit Tests
**File:** `daoanh/tests/test_t370_lineage_integrity.py`

```python
def test_consolidate_lineage():
    """Test lineage consolidation."""
    result = consolidate_lineage('data/lineage.db', dry_run=True)
    assert result['dila_inserted'] >= 23000  # số liệu thực tế: 23,014
    assert result['ttl_inserted'] >= 700     # số liệu thực tế: 784

def test_no_cycles():
    """Verify lineage has no cycles."""
    checks = verify_lineage_integrity('data/lineage.db')
    assert checks['has_cycle'] == False

def test_orphan_linking():
    """Test orphan Vietnamese monks get linked to DILA."""
    result = link_vnpa_to_dila('data/lineage.db', dry_run=True)
    assert result['orphans_found'] == 211
    assert result['linked'] > 100  # At least 50% should link

def test_no_conflicts():
    """Verify no conflicts between DILA and TTL edges."""
    checks = verify_lineage_integrity('data/lineage.db')
    assert checks['conflicts_count'] == 0
```

---

## Deliverables

1. ✓ `daoanh/scripts/consolidate_lineage.py`
2. ✓ `daoanh/scripts/link_vnpa_to_dila.py`
3. ✓ `daoanh/scripts/verify_lineage_integrity.py`
4. ✓ `daoanh/docs/SSOT_merge_strategy.md` (detailed merge rules)
5. ✓ `daoanh/tests/test_t370_lineage_integrity.py` (20+ test cases)
6. ✓ `daoanh/docs/evidence/T370_lineage_audit.tsv` (before/after counts)
7. ✓ `daoanh/docs/sessions/2026-10-12/T370_lineage_report.md`

---

## Timeline

- **Scripts:** 8 hours (3 scripts + cycle detection algorithm)
- **Testing & verification:** 4 hours (dry-run, unit tests, conflict resolution)
- **Documentation:** 2 hours
- **Total:** 14 hours (10-12 working days)

---

## Dependencies & Unblocks

**Depends on:** T368 (schema), T369 (CBETA integrity)  
**Unblocks:** T371 (final verification), complete lineage graph

---

## Critical Notes

⚠️ **Cycle Detection:** Complex algorithm (DFS). Must test with sample data first.

⚠️ **Orphan Linking:** May fail to link some orphans if Vietnamese names are too generic or not in TTL mapping. Flag unlinked for manual review.

⚠️ **Data Consistency:** After linking, VNPA orphans get dila_id. Any downstream code assuming `dila_id IS NULL` will break.

---

**Ready for daoanh-debugger implementation?** ✓
