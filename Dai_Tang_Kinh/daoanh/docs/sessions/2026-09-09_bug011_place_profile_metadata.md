# Session 2026-09-09 — BUG-011 Place Profile Metadata Not Loading

**Task:** BUG-011 (MAP_MARKER_PLACE_PROFILE_METADATA_NOT_LOADING_001)  
**Files changed:** `app.py`, `places.html`  
**Status:** IMPLEMENTED / READY_FOR_ADMIN_TEST

---

## Root Cause Analysis

### Data verified (PL000000023255 = Thiếu Lâm Tự)

| Source | Field | Value |
|--------|-------|-------|
| `places_dila` | `id` | PL000000023255 |
| `places_dila` | `geo_lat / geo_long` | 34.507018 / 112.935331 |
| `places_dila` | `district` | 中國-河南省-鄭州市-登封市 |
| `places_dila` | `note_category` | 寺廟、佛塔、佛教文化地點 |
| `places_dila` | `note` | 始建於495年… (143 chars, no HTML) |
| `namevi_map_places` | `dila_id` | PL000000023255 |
| `namevi_map_places` | `name_vi` | Thiếu Lâm Tự |
| `namevi_map_places` | `district_vi` | Thành Phố 登封, Thành Phố 鄭州, Tỉnh Hà Nam, Trung Quốc |
| `entity` | `entity_id` | PL000000023255 |
| `entity_hub` | entity_id='PL000000023255' | NOT FOUND (entity_hub uses INTEGER PK) |
| `entity_source_ids` | DILA for PL000000023255 | hub_int_id=181597, source_entity_id='PL000000023255' |

### Code path trace

1. Click marker → `selectItem('PL000000023255', lat, lng)`
2. Fetch `GET /daoanh/api/entity/PL000000023255/unified`
3. In `entity_unified`:
   - `entity_hub WHERE entity_id = 'PL000000023255'` → NOT FOUND (entity_hub.entity_id = INTEGER 100001-N, not text)
   - Fallback: `entity WHERE entity_id = 'PL000000023255'` → FOUND
   - `entity_source_ids WHERE source_entity_id = 'PL000000023255'` → hub_int_id = 181597
   - `entity_source_ids WHERE entity_id = 181597` → DILA source found
   - `places_dila WHERE id = 'PL000000023255'` → FOUND with GPS/note/category
4. Response: `{ok:true, sources:{dila:{active:true, gps:'34.507018,112.935331', note:'...', note_category:'...'}}}`
5. Frontend unified path: `if (src.dila)` → renders GPS/district/note/category

### Why bug may occur

**Primary root cause (defensive fix):** For some `places_pending` entities that have:
- Entry in `entity` table (via entity_type='PLACE')
- But NO entry in `entity_source_ids` (entity_source_ids coverage = 167K of 59K DILA + ~108K persons)

When `entity_source_ids` empty → `source_map = {}` → `'DILA' not in source_map` → `sources['dila'] = {active: False}`. Unified returns `ok:true` (entity found) but no DILA data.

**Secondary issues fixed:**
- `dilaId` element not reset at selectItem start → shows stale DILA ID from previous marker
- No race guard → rapid clicks could leave stale response in panel
- `name_vi` missing from `sources['dila']` response → showGlobalDilaStrip uses stale fallback
- HTML tags in DILA note not stripped in unified path (safe via textContent but cleaner without)

---

## Changes

### app.py — `entity_unified` (~line 13082-13141)

**Old code:**
```python
if 'DILA' in source_map:
    dila_id = source_map['DILA']['source_entity_id']
    ...
    sources['dila'] = { "active": True, ... }
else:
    sources['dila'] = {"active": False}
```

**New code:**
```python
_dila_source_id = None
if 'DILA' in source_map:
    _dila_source_id = source_map['DILA']['source_entity_id']
elif str(entity_id).startswith('PL'):
    # For place entities, entity_id IS the DILA ID when entity_source_ids incomplete
    _dila_source_id = entity_id
if _dila_source_id:
    dila_id = _dila_source_id
    # ... lookup places_dila + namevi_map_places
    # + strip HTML from note
    # + add name_vi to response
    sources['dila'] = { "active": True, "name_vi": ..., ... }
else:
    sources['dila'] = {"active": False}
```

### places.html — `selectItem` (~line 1044-1070, 1106-1110, 1232-1234)

1. **`_selectToken` variable** (line ~862): `let _selectToken = 0;`
2. **Token capture** (line ~1047): `const _myToken = ++_selectToken;`
3. **`dilaId` reset** (line ~1062): Added `document.getElementById('dilaId').innerText = '—';` in initial reset block
4. **Stale guard (unified path)** (line ~1106): `if (_myToken !== _selectToken) return;` before unified DOM update
5. **Stale guard (legacy path)** (line ~1234): `if (_myToken !== _selectToken) return;` before legacy DOM update

---

## Verification

```
DB verify: places_dila PL000000023255 → geo_lat=34.507018, geo_long=112.935331, note_category='寺廟...' ✓
DB verify: namevi_map_places PL000000023255 → name_vi='Thiếu Lâm Tự', district_vi='...' ✓
parse_dila_district('中國-河南省-鄭州市-登封市') → country_vi='Trung Quốc', district_vi='thành phố Đăng Phong...' ✓
JS syntax check: OK (1 block, 0 fail) ✓
Python ast.parse app.py: OK ✓
```

Expected render after fix:
- `rawGeo` = "34.507018 112.935331"
- `rawDistrict` = "thành phố Đăng Phong, thành phố Trịnh Châu, tỉnh Hà Nam"
- `dilaNoteBlock` = visible with note text
- `dilaCategoryBadge` = "寺廟、佛塔、佛教文化地點"
- `dilaId` = "PL000000023255"

---

## Acceptance test (cho Admin)

1. Khởi động server: `python app.py`, `python local_gateway.py`
2. Mở `http://localhost:8080/daoanh/places.html`
3. Search "Thiếu Lâm Tự" → click marker
4. Kiểm tra panel trái:
   - GPS: "34.507018 112.935331"
   - District: có địa chỉ hành chính (không phải '—')
   - Mô Tả DILA: visible với nội dung "始建於495年..."
   - Category badge: "寺廟、佛塔、佛教文化地點" (không ẩn)
   - DILA ID: "PL000000023255"
5. Click marker khác → panel thay đổi đúng (không hiện dữ liệu cũ)
6. Click liên tiếp nhiều marker → panel cuối cùng hiển thị marker cuối, không bị ghi đè

**KHÔNG mark Done** cho đến khi Admin confirm.
