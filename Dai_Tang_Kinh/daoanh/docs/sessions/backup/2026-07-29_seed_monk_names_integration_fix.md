# Session: Seed Monk Names + Integration Layer Fix

**Date**: 2026-07-29
**Tasks**: Tasks 1, 2a, 2b

## What was done

### Task 1: Seed monk names
- Wrote `scripts/seed_monk_names.py` — bulk Hán-Việt seeding for 48K people
- 3-tier lookup: lexicon → hanviet_fallback → char-by-char fallback
- Result: 46,272 / 48,673 people seeded (95%), only 335 had name_vi before
- API now shows `auto_pending: 45937`

### Task 2a: Fix integration layer
- Rewrote `scripts/build_integration_layer.py` to populate ALL 5 CBETA texts
- Uses `INSERT OR REPLACE` with passage_id matching `cbeta_content_index.id`
- Character-based reverse index for Chinese name matching (bypasses FTS5 CJK limitations)
- Results: TEXT entities 5 (was 1), passages 7,563 (was 3,917), passage_entity links 378,483 (was 5,276)

### Task 2b: passage_vi + entity summary
- Added `vi_text` column to `passage` table
- Created `/daoanh/api/entity/<entity_id>/summary` endpoint
- Groups passages by source text with CBETA catalog metadata

## API Evidence
### Thiếu Lâm Tự passage count before → after: 0 → 15
### Entity summary: A025190 (舍利): 335 passages across 5 texts

## Files changed
- `app.py` — added entity summary endpoint (line ~7230)
- `scripts/build_integration_layer.py` — full rewrite for 5 texts
- `scripts/seed_monk_names.py` — new file, bulk name seeding
- `AGENTS.md` — section 0 tasktodo protocol
- `docs/tasktodo.md` — authoritative task list
- `data/lineage.db` — DB changes (seeds, passages, links)

## Next
- Tasks 3–9 per tasktodo.md priority
