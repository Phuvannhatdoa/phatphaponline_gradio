# T91 — Fix: /daoanh/places — Category Filter + Layout

**Status:** ✅ DONE  
**Priority:** High  
**Created:** 2026-09-04

## Mô tả

Trang `/daoanh/places` có 2 lỗi:

1. **Category filter pill không hoạt động** — click "⛩ Chùa / Tự viện" (hoặc các pill khác) không hiện marker trên Leaflet map, API trả về `{"ok": true, "count": 0}`.
2. **Filter bar bị map đè lên** — `cate-filter-bar` dùng `position:absolute` nằm chồng lên map, không đọc được.

## Root Cause

### Lỗi 1 — Category filter
- `CATE_LIKES` dict trong `app.py` dùng `p.note_category LIKE ?` nhưng column `note_category` **không tồn tại** trong schema DB.
- `place_type` column tồn tại nhưng `NULL` cho toàn bộ 58,476 GPS records — không dùng được.
- `except Exception: pass` ở route `places/search` swallow `OperationalError` → API trả về count=0 không có error, khó debug.

### Lỗi 2 — Layout filter bar
- CSS dùng `position:absolute` cho `.cate-filter-bar` → nằm đè lên `<div id="map">` bên dưới → không click được và khó đọc.

## Fix

### `app.py` — CATE_LIKES dùng `name_zh` LIKE patterns
```python
# Trước (broken):
CATE_LIKES = {
    'temple_site':    ['%寺%', '%廟%', ...],
    # ... dùng p.note_category LIKE ?
}
# → OperationalError: no such column: p.note_category

# Sau (fixed):
CATE_LIKES = {
    'temple_site':   ['%寺', '%廟%', '%塔', '%庵', '%禪%', '%精舍%', '%伽藍%', '%石窟%'],
    'mountain':      ['%山', '%峰', '%嶺%', '%崖%', '%岳%', '%丘%'],
    'river_lake':    ['%江', '%河', '%湖', '%溪', '%潭%', '%海%', '%港%', '%渡%'],
    'dynasty_region':['%郡%', '%州', '%路%', '%府%', '%道%', '%縣%', '%鄉%'],
    'other':         ['%洞%', '%岩%', '%林%', '%原%', '%坡%', '%野%'],
}
# SQL condition đổi từ p.note_category LIKE ? → p.name_zh LIKE ?
```

Verification từ DB:
- 8,871 temple records có GPS coords
- 2,743 mountain records
- 2,104 river/lake records

### `places.html` — cate-filter-bar static above map
- Đổi `position:absolute` → static flex row, đặt trước `<div id="map">` trong DOM
- Map nằm dưới filter bar, không còn bị che

## Files thay đổi

- `app.py` — CATE_LIKES + SQL condition (route `/daoanh/api/places/search`, ~line 3273)
- `places.html` — cate-filter-bar layout (từ position:absolute → static)

## Rollback

```bash
git revert <commit-hash>
# hoặc
git checkout <prev-commit> -- app.py places.html
```
