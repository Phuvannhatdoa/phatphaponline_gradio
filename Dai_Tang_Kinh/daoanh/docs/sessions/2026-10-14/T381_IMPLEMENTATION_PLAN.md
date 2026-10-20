# T381 Implementation Plan — 3-Source Dharma Lineage with Y-Fork Rendering

**Date**: 2026-10-14  
**Task**: T381 — Build Dharma Lineage (TTL + Marcus + DILA) with Y-Fork Visualization  
**Demo Case**: `minh_hai_phap_bao` (Minh Hải Pháp Bảo)  
**Philosophy**: Always drawable — no data loss, flexibility for any source combination  

---

## Architecture Overview

```
3 Independent Data Sources:
├─ dharma_lineage_ttl_vn (1,106 rows)
│  └─ Source: TTL file (Vietnam Zen masters only)
│
├─ dharma_lineage_marcus (X rows)
│  └─ Source: Marcus Binney scholarship
│
└─ dharma_lineage_dila (46,004 rows)
   └─ Source: DILA international database

Query Layer:
  /daoanh/api/monk/<id>/lineage-tree
  └─ Merge 3 sources + Y-fork logic + color-coding

Rendering:
  Frontend (VisJS graph)
  ├─ GREEN edges: Consensus or TTL baseline
  ├─ YELLOW edges: Marcus branches
  ├─ BLUE edges: DILA branches
  └─ is_divergence flag: True if sources differ
```

---

## Step-by-Step Build Plan

### Step 1: Create Database Tables (Python script)

**Script**: `scripts/t381_create_dharma_tables.py`

```python
# 1. Connect to DB
# 2. Drop existing tables (if exists)
# 3. Create dharma_lineage_ttl_vn
#    - Columns: id, teacher_id, student_id, source='TTL', relationship_type, confidence, created_at
#    - Source: Read TTL files, extract teacher-student pairs for Vietnam monks
#    - Filter: Both teacher & student in vn_person_authority with Vietnam nationality
#    - Rows expected: ~1,106
#
# 4. Create dharma_lineage_marcus
#    - Columns: id, teacher_id, student_id, source='Marcus', relationship_type, confidence, created_at
#    - Source: marcus_lineage table (current DB)
#    - Rows expected: X (to be counted)
#
# 5. Create dharma_lineage_dila
#    - Columns: id, teacher_id, student_id, source='DILA', relationship_type, confidence, created_at
#    - Source: Extract from lineage_edge_consensus where dila_asserted=1
#    - Rows expected: ~46,004
#
# 6. Create indexes: teacher_id, student_id
# 7. Verify row counts
```

**Expected Output**:
```
✅ dharma_lineage_ttl_vn: 1,106 rows
✅ dharma_lineage_marcus: X rows
✅ dharma_lineage_dila: 46,004 rows
✅ Indexes created
```

---

### Step 2: Implement Y-Fork Logic (Python function)

**Script**: `scripts/t381_yfork_logic.py`

```python
def merge_sources(student_id, teacher_id=None):
    """
    Merge 3 sources for a given student or teacher-student pair.
    Returns: {color, style, is_divergence, sources, confidence}
    """
    
    # Query all 3 tables for this relationship
    ttl_has = query_ttl(student_id, teacher_id)
    marcus_has = query_marcus(student_id, teacher_id)
    dila_has = query_dila(student_id, teacher_id)
    
    sources = []
    if ttl_has: sources.append('TTL')
    if marcus_has: sources.append('Marcus')
    if dila_has: sources.append('DILA')
    
    # Decision logic
    if len(sources) == 3:
        # All 3 sources have same relationship
        return {
            'color': '#22c55e',  # GREEN
            'style': 'solid',
            'is_divergence': False,
            'sources': sources,
            'confidence': 0.95,
            'label': 'TTL ✓ Marcus ✓ DILA ✓'
        }
    
    elif 'TTL' in sources and (marcus_has or dila_has):
        # TTL confirmed + at least 1 other
        return {
            'color': '#22c55e',  # GREEN
            'style': 'solid',
            'is_divergence': False,
            'sources': sources,
            'confidence': 0.90,
            'label': f"TTL ✓ ({'+'.join([s for s in sources if s != 'TTL'])})"
        }
    
    elif marcus_has and dila_has:
        # Marcus + DILA agree, TTL silent
        return {
            'color': '#a855f7',  # PURPLE
            'style': 'solid',
            'is_divergence': False,
            'sources': sources,
            'confidence': 0.85,
            'label': 'Marcus ✓ DILA ✓'
        }
    
    elif 'TTL' in sources:
        # Only TTL
        return {
            'color': '#22c55e',  # GREEN
            'style': 'solid',
            'is_divergence': False,
            'sources': sources,
            'confidence': 0.92,
            'label': 'TTL ✓'
        }
    
    elif marcus_has:
        # Only Marcus (Y-fork branch)
        return {
            'color': '#eab308',  # YELLOW
            'style': 'dashed',
            'is_divergence': True,
            'sources': sources,
            'confidence': marcus_confidence,
            'label': '⚠️ Marcus only'
        }
    
    elif dila_has:
        # Only DILA (Y-fork branch)
        return {
            'color': '#3b82f6',  # BLUE
            'style': 'dashed',
            'is_divergence': True,
            'sources': sources,
            'confidence': dila_confidence,
            'label': '⚠️ DILA only'
        }
```

---

### Step 3: Update API Endpoint

**File**: `app.py` — `/daoanh/api/monk/<id>/lineage-tree`

**Changes**:
```python
# Old: Query from lineage_edge_consensus (single source)
# New: Query from dharma_lineage_ttl_vn + dharma_lineage_marcus + dharma_lineage_dila

# BFS logic (same as before, but sources now merged):
for each edge (teacher → student):
    edge_info = merge_sources(student, teacher)
    edge.color = edge_info['color']
    edge.style = edge_info['style']
    edge.is_divergence = edge_info['is_divergence']
    edge.sources = edge_info['sources']
    edge.label = edge_info['label']

# Add tree_status:
response['tree_status'] = {
    'has_divergence': any(e['is_divergence'] for e in edges),
    'divergence_count': len([e for e in edges if e['is_divergence']]),
    'warning': 'Y-Fork detected: sources diverge' if has_divergence else None
}
```

---

### Step 4: Frontend Rendering Updates

**File**: `static/js/lineage-tree.js` or similar

**Changes**:
```javascript
// 1. Update edge colors
edge.color = response.edges[i].color;
edge.dashes = response.edges[i].style === 'dashed' ? [5, 5] : false;
edge.label = response.edges[i].label;

// 2. Add legend dynamically
if (response.tree_status.has_divergence) {
    showLegend({
        'GREEN': 'Consensus (TTL or all 3 sources)',
        'YELLOW': 'Marcus branch',
        'BLUE': 'DILA branch',
        'PURPLE': 'Marcus + DILA agree'
    });
    showWarning('⚠️ Y-Fork detected: Sources diverge');
}

// 3. Render detail panel with source breakdown
showDetailPanel({
    'primary_teachers': green_edges,
    'alternative_teachers': yellow_blue_edges,
    'source_breakdown': {
        'TTL': ttl_count,
        'Marcus': marcus_count,
        'DILA': dila_count
    }
});
```

---

### Step 5: Test with Demo Case (`minh_hai_phap_bao`)

**Test Steps**:

1. **Query teachers**:
   ```sql
   SELECT * FROM dharma_lineage_ttl_vn WHERE student_id='minh_hai_phap_bao';
   SELECT * FROM dharma_lineage_marcus WHERE student_id='minh_hai_phap_bao';
   SELECT * FROM dharma_lineage_dila WHERE student_id='minh_hai_phap_bao';
   ```
   Expected: All 3 have Thạch Liêm → GREEN trunk

2. **Query students**:
   ```sql
   SELECT * FROM dharma_lineage_ttl_vn WHERE teacher_id='minh_hai_phap_bao';
   SELECT * FROM dharma_lineage_marcus WHERE teacher_id='minh_hai_phap_bao';
   SELECT * FROM dharma_lineage_dila WHERE teacher_id='minh_hai_phap_bao';
   ```
   Expected: Divergence → Y-fork (TTL=Thiệt Diệu, Marcus adds Thiệt Mẫn, DILA adds Thiệt Thọ)

3. **API call**:
   ```bash
   curl "http://127.0.0.1:8080/daoanh/api/monk/minh_hai_phap_bao/lineage-tree?up=1&down=2"
   ```
   Expected: JSON with color-coded edges + is_divergence flags

4. **Visual check**:
   - Open http://127.0.0.1:8080/daoanh/lineage/minh_hai_phap_bao
   - Verify GREEN trunk (teacher)
   - Verify Y-fork branches (students)
   - Check legend + warning

---

### Step 6: Verification Checklist

- [ ] Database: 3 tables created, rows counted
- [ ] Y-fork logic: All scenarios tested (consensus, divergence, partial)
- [ ] API: Returns color + is_divergence + sources for each edge
- [ ] Frontend: Colors render correctly, legend shows
- [ ] Demo case: minh_hai_phap_bao visualizes correctly
- [ ] No data loss: All 3 sources preserved
- [ ] PRAGMA quick_check: OK
- [ ] Performance: Query time < 1s for typical trees

---

### Step 7: Documentation & Commit

**Files to update**:
- Task file: T381-build-dharma-lineage-3sources.md
- Session log: T381_EXECUTION_LOG.md
- ROLLBACK.md: Add T381 entry
- Dashboard: http://localhost:8080/dashboard/dashboard_process.html

**Commit message**:
```
T381: Build 3-source dharma lineage with Y-fork rendering

- Create dharma_lineage_ttl_vn (1,106 rows from TTL)
- Create dharma_lineage_marcus (X rows from Marcus)
- Create dharma_lineage_dila (46,004 rows from DILA)
- Implement Y-fork merge logic (consensus → GREEN, divergence → branches)
- Update /daoanh/api/monk/<id>/lineage-tree for 3-source queries
- Add color-coding (GREEN/YELLOW/BLUE) to frontend
- Test with minh_hai_phap_bao demo case
- Verify no data loss, all sources preserved
- Always drawable: consensus + divergence + partial agreement

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
```

---

## Timeline Estimate

| Phase | Time | Notes |
|-------|------|-------|
| Step 1 (DB tables) | 30 min | Create 3 tables, indexes, verify counts |
| Step 2 (Y-fork logic) | 45 min | Implement merge_sources() function |
| Step 3 (API update) | 30 min | Modify /lineage-tree endpoint |
| Step 4 (Frontend) | 45 min | Update VisJS rendering + legend |
| Step 5 (Test demo) | 15 min | Test minh_hai_phap_bao |
| Step 6 (Verify) | 20 min | PRAGMA check, performance test |
| Step 7 (Commit) | 10 min | Docs + git commit |
| **TOTAL** | **~3.5 hours** | |

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Large data transfer (46K DILA rows) | Use generator/iterator in extraction |
| Query performance (3 table joins) | Indexes on teacher_id + student_id |
| Data inconsistency (conflicting PKs) | Validate IDs exist in vn_person_authority |
| Frontend not updated (shows old colors) | Clear browser cache, hard refresh |
| Missing sources (silent failures) | Log each table insert count |

---

## Next Steps (After T381)

1. Admin reviews demo case visualization
2. Admin approves Y-fork rendering
3. Consider T382+ (conflict resolution UI, dharma transmission confirmation)
4. Consider full-tree visualization optimization (performance for 1.5K+ nodes)

---

## Attribution

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
