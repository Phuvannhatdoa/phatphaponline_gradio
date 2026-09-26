# Session: CBETA Catalog VN — License Tracking for GIS Places

**Date:** 2026-05-29
**Task:** `feat: cbeta_catalog_vn — license tracking for GIS places`

## Summary

Created `cbeta_catalog_vn` table in `lineage.db` to track source/license attribution for Đại Chánh Tân Tu catalog (Nguyễn Minh Tiến), and wired it into the Đạo Ảnh GIS place detail API + frontend.

## Design / Solution

### Database
- New table `cbeta_catalog_vn` with 20+ columns mirroring the .doc structure + 6 license columns:
  - `source_name`, `source_full_title`, `source_url`
  - `license_name`, `license_url`, `source_note`
- Default license: `CC BY-SA 4.0 – dùng cho mục đích học thuật`

### Import Pipeline
- `src_python/db/import_cbeta_catalog_vn.py`:
  - Uses `catdoc` (only reliable extractor for .doc binary files)
  - Reuses `parse_muc_luc.py`'s `while`-index scanning pattern
  - Parses 5-line record blocks (● Tên, ● Niên đại, ● Dịch giả, ● Số thứ tự+trang+sh, ● Tên Hoa)
  - Strips ● bullet character
  - Result: **3,122 records** (correct count)

### API
- `app.py:2389-2413` (`api_places_detail`):
  - After loading place detail, queries `cbeta_catalog_vn` using `name_zh` fuzzy match
  - Attaches result as `text_info` object (title, dynasty, translator, location refs, source, license)

### Frontend
- `places.html:149-155` (`selectItem`):
  - New `#licenseBlock` div (hidden by default) below bio
  - Shows `source_full_title`, `license_name`, `source_note` when `text_info` is present

### GIS Marker Cluster (also in this session)
- `places.html:294-297`: Migrated to `L.markerClusterGroup` with `markerMap` for performance
- Backend limit raised from 100 → 50,000 in `app.py`

## Files Changed

| File | Change |
|------|--------|
| `src_python/db/import_cbeta_catalog_vn.py` | **New** — schema + import script (3122 records) |
| `app.py` | Added `cbeta_catalog_vn` query to `api_places_detail` |
| `places.html` | Added `#licenseBlock` UI + populate in `selectItem` |

## Test Commands

```bash
# Verify import
sqlite3 data/lineage.db "SELECT COUNT(*) FROM cbeta_catalog_vn; SELECT title_vi, license_name FROM cbeta_catalog_vn LIMIT 5;"

# Test API
curl -s http://localhost:5000/daoanh/api/places/PL000061 | python3 -m json.tool | grep -E 'license|text_info'

# Pipeline
npm run pipeline
```

## Result

- ✅ 3,122 records imported with full license attribution
- ✅ API returns `text_info` with license for matching places
- ✅ UI shows NGUỒN & GIẤY PHÉP block when data available
- ✅ All pipeline tests passed
