# Session: Link Marcus Term Glossaries to DILA People/Works (Task 4)

**Date**: 2026-07-29
**Tasks**: Task 4

## What was done

### Task 4: Link Marcus term glossaries ↔ DILA people/works

**Problem**: `marcus_reference` table was empty (0 rows). `entity.marcus_id` was NULL for all 167K entities. Marcus glossary data was not linked to DILA entities.

**Solution**: ETL script to populate both.

### ETL Script
- Wrote `scripts/link_marcus_entities.py`
- Reads `marcus_nodes_mapped.json` (18,127 nodes with DILA IDs + enriched metadata)
- Step 1: Populates `marcus_reference` table with all node data (label, label_vi, birth/death years)
- Step 2: Sets `entity.marcus_id` = dila_id for all matching entities

### Results
- **18,127** rows in `marcus_reference` (was 0)
- **18,121** entities now have `marcus_id` set
- **6** Marcus nodes without matching DILA entities (minor — likely test/obsolete entries)

### API Changes
- Updated `GET /daoanh/api/entity/<id>` — now includes `marcus` sub-object with label, label_vi, birth/death from `marcus_reference` when available
- New endpoint: `GET /daoanh/api/entity/<id>/marcus` — full Marcus data including:
  - Glossary reference entry
  - Teachers list (who taught this person)
  - Students list (who this person taught)
  - Edge count

### Example
```
GET /daoanh/api/entity/A000005/marcus
→ Label: 鑑堂一 / 鑑堂
→ Teachers: [幻敏]
→ Students: [明滿, 明福, 明訓, 明微, 明燦]
→ Total edges: 7
```

## Files changed
- `scripts/link_marcus_entities.py` — new ETL script
- `app.py` — entity info now includes Marcus data + new /marcus endpoint
- `data/lineage.db` — marcus_reference populated, entity.marcus_id set

## Next
- Task 5: TTL VN → authority Person VN
