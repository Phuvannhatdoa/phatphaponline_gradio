---
id: BUG-013
title: "Unified endpoint trả null cho DILA geo/name — places table không được fallback"
module: GIS / Places / Unified API
priority: P1
status: done
depends_on: []
created: 2026-09-09
updated: 2026-09-09
done_when:
  - /api/entity/<PL-short-id>/unified trả name_zh, gps, country_vi, district_vi_computed đúng
  - Panel cột trái hiển thị COUNTRY, DISTRICT, GEO, MÔ TẢ DILA cho các địa danh short ID
  - Không ảnh hưởng các entity dùng long DILA ID (PL000000000001)
---

## Triệu chứng

Click marker chùa (ví dụ PL056722 "Sen Hoa Am") → panel cột trái hiển thị:
- COUNTRY —
- DISTRICT —
- GEO —
- Tên Hán — (tất cả null)

Nhưng marker có GPS đúng và `/api/places/PL056722` trả về đầy đủ data.

## Root cause

`entity_unified()` (app.py line ~13127) query `places_dila WHERE id='PL056722'` — KHÔNG có kết quả
vì `places_dila` dùng DILA long IDs (`PL000000000001`), còn PL056722 là short local ID chỉ
tồn tại trong bảng `places`.

- **`places_dila`**: 59k+ rows, ID format `PL000000000001` (DILA canonical)
- **`places`**: 58k+ rows, ID format `PL056722` (app local ID)
- **`entity_source_ids`** cho PL056722: source='DILA', source_entity_id='PL056722' (short ID)
  → khi unified query `places_dila WHERE id='PL056722'` → empty → tất cả DILA fields null

Phạm vi: toàn bộ 58,476 places có GPS (places table) đều có khả năng bị lỗi này nếu
entity_source_ids.source_entity_id dùng short ID.

## Fix

`app.py` — trong `entity_unified()`, sau khi query `places_dila` trả empty, thêm fallback
query `places WHERE id = dila_id`:

```python
_places_fb = None
if not dila_detail:
    _pf = conn.execute(
        "SELECT name_zh, gps_lat, gps_long, province FROM places WHERE id = ?",
        (dila_id,)
    ).fetchone()
    if _pf and (_pf['gps_lat'] or _pf['name_zh']):
        _places_fb = _pf
```

Sau đó dùng `_places_fb` để fill `name_zh`, `gps`, `district_raw` khi `dila_detail` là None.
`parse_dila_district(province)` xử lý `'中國-河南省-鄭州市-鞏義市'` → `country_vi='Trung Quốc'`,
`district_vi_computed='thành phố Củng Nghĩa...'`.

File: `daoanh/app.py` lines ~13127-13165

## Acceptance criteria checklist

- [x] `/api/entity/PL056722/unified` trả `name_zh='慈雲寺'`, `gps='34.712045,113.099581'`, `country_vi='Trung Quốc'`
- [x] Panel cột trái hiển thị COUNTRY=Trung Quốc, DISTRICT=thành phố Củng Nghĩa..., GEO=34.712045 113.099581
- [x] Test 3 địa danh short ID khác (PL023255, PL001000) → đều có name_zh, gps, country_vi đúng
- [x] Panel hiển thị MÔ TẢ DILA (note) + category badge + nút Tạm Dịch AI cho PL056722
- [x] Admin xác nhận DONE (2026-09-09)
