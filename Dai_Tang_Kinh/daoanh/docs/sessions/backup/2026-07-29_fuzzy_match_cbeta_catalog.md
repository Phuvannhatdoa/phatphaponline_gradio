# Session: Fuzzy Match CBETA Catalog ↔ Places (Task 3)

**Date**: 2026-07-29
**Tasks**: Task 3

## What was done

### Task 3: Fuzzy matching title_zh ↔ place using RapidFuzz
- **Problem**: Place detail API used `LIKE '%name_zh%'` to match places against CBETA catalog titles — brittle, no variant handling
- **Solution**: ETL script + pre-computed table + API improvements

### ETL Script
- Wrote `scripts/fuzzy_match_cbeta_catalog.py`
- Uses RapidFuzz `fuzz.partial_ratio` (C-optimized Levenshtein)
- For each of 36,731 distinct Chinese place names, finds top-5 matching catalog titles (3,122 entries) with score >= 60

### Results
- **64,281** fuzzy matches inserted in 165s (222 names/s)
- **20,211** places now have fuzzy catalog matches
- **5,388** are high-confidence (score >= 80)

### API Changes
- New endpoint: `POST /daoanh/api/admin/cbeta/fuzzy-match-place`
  - Search by `place_id` or `place_name`
  - Returns ranked matches with scores + catalog metadata
- Updated `GET /daoanh/api/places/<id>` detail endpoint:
  - Priority: (1) exact LIKE match, (2) fuzzy table (score >= 70), (3) VI name search
  - Adds `text_info_match` field (`exact`/`fuzzy`/`like`)

### Example
```
POST /daoanh/api/admin/cbeta/fuzzy-match-place
{"place_id":"PL011817"}  → 阿育王寺 matches 阿育王經 (score=85.7), 阿育王傳 (85.7), etc.
```

## Files changed
- `scripts/fuzzy_match_cbeta_catalog.py` — new ETL script
- `app.py` — new fuzzy endpoint + updated place detail API
- `data/lineage.db` — new `cbeta_catalog_place_fuzzy` table with 64K rows

## Next
- Task 4: Link Marcus term_glossaries to DILA people/works
- Or Task 9: Fix dashboard stats API 404
