# Session: T21 — Phân Tích Kỹ Thuật Geo-Identity Linking

**Date:** 2026-08-19  
**Module:** GIS Places / Tab NIÊN ĐẠI  
**Scope:** Research + Technical spec, không có code change

---

## Tóm tắt

Hoàn thành phần research và viết phân tích kỹ thuật đầy đủ cho T21 (Niên Đại / Place Timeline).

Chiến lược được phê duyệt: **Geo-Identity Linking (Bridge Table)** — chỉ lưu external ID trong bảng `geo_cross_ref`, truy vấn on-demand qua API, không import dữ liệu thô.

---

## DB Audit (thực hiện session này)

```
Database: daoanh/data/lineage.db
places_dila: 59,167 rows, 18 columns — KHÔNG có external ID column nào
places: table riêng, 15 columns — cũng không có external ID
geo_cross_ref: CHƯA TỒN TẠI (cần tạo)
Thiếu Lâm Tự (PL000000023255): geo_lat=34.507018, geo_long=112.935331
```

Kết luận audit: `places_dila` là một bảng thuần DILA — hoàn toàn không có liên kết sang bất kỳ hệ thống bên ngoài nào. Thiết kế `geo_cross_ref` là bắt buộc, không phải optional.

---

## Kết quả research nguồn dữ liệu

### Confirmed: Wikidata P571 ✅
- Q232771 (Thiếu Lâm Tự) · P571 = `0495-01-01T00:00:00Z`
- 148 places đã có P1188 (DILA ID bridge) trong Wikidata → có thể batch SPARQL
- License: CC0

### Confirmed: Wikidata P1188 = DILA bridge ✅
- `wdt:P1188 ?dila_id` — cho phép tìm tất cả Wikidata items có DILA ID
- Chỉ 148/59,167 places (~0.25%) — phần lớn cần manual seed

### Confirmed: CHGIS TGAZ = dynasty context ✅
- Harvard REST API: `year + location` → administrative unit + dynasty (222 BCE–1911 CE)
- Thay thế `_CHINESE_DYNASTIES` hardcode bằng data thật
- Cần verify URL mới (domain cũ `chgis.fairbank.fas.harvard.edu` không resolve)

### Confirmed: DILA Time Authority ≠ place timeline ✅
- `time_periods` table = 117K rows niên hiệu/era/emperor/dynasty = bộ chuyển đổi lịch
- Không có link nào giữa `time_periods` và `place_id`
- Kết luận: DILA Time Authority KHÔNG giải quyết được place timeline

### Confirmed: BDRC ≠ Chinese Buddhist temples ✅
- BDRC (Buddhist Digital Resource Center) tập trung Tibetan Buddhism
- Chinese Chan temples (Thiếu Lâm, v.v.) không có trong BDRC
- `bdo:placeEvent` chỉ hữu ích cho Tibetan monasteries

### Confirmed: BGIS + Marcus datasets ✅ (cần ETL)
- BGIS (Jiang Wu + Marcus Bingenheimer): relational DB Chinese Buddhist monasteries + founding dates
- Marcus Taiwanese: 5,500 temples CSV georeferenced + dated
- Không có on-demand API → cần ETL một lần vào `place_timeline_events`

---

## Schema `geo_cross_ref` (thiết kế)

```sql
CREATE TABLE geo_cross_ref (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    dila_id     TEXT NOT NULL REFERENCES places_dila(id),
    wikidata_qid TEXT,      -- Q232771
    chgis_svid  TEXT,       -- CHGIS admin unit ID
    tgaz_id     TEXT,       -- TGAZ place ID
    bgis_id     TEXT,       -- BGIS monastery ID
    marcus_ref  TEXT,       -- Marcus CSV reference
    confidence  TEXT DEFAULT 'verified',  -- verified | probable | spatial
    mapped_by   TEXT,       -- manual | sparql_p1188 | spatial_join
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(dila_id)
);
```

---

## Quan hệ giữa các bảng

```
places_dila (59,167 rows)
    id = PL000000023255
    geo_lat = 34.507018
    geo_long = 112.935331
         │
         └── geo_cross_ref.dila_id [1:1]
                  ├── wikidata_qid = "Q232771" ──► Wikidata API (P571, P1435)
                  ├── chgis_svid   = "..."     ──► CHGIS TGAZ API (dynasty)
                  ├── bgis_id      = "..."     ──┐
                  └── marcus_ref   = "..."     ──┤ → place_timeline_events (ETL, static)
                                                └─┘
```

---

## Files thay đổi (session này + session trước liên quan)

| File | Thay đổi |
|------|---------|
| `tasks/T21-nien-dai-timeline-research.md` | ✅ Full technical spec viết xong (audit + schema + API design + risk analysis) |
| `docs/trusted-sources.md` | ✅ 15 nguồn uy tín trong 3 nhóm (Data/Academic/Technology) |
| `daoanh/CLAUDE.md` | ✅ Rule #3 mới: 3-step research protocol bắt buộc |
| `docs/tasktodo.md` | ✅ T21 section cập nhật đầy đủ trạng thái research + blockers |
| `app.py` | ✅ (session trước) Xóa `_CHINESE_DYNASTIES` + `api_places_timeline` pending stub |
| `places.html` | ✅ (session trước) `renderTimelineTab` → pending notice + research directions |

---

## Không thay đổi code / DB

Session này là research + spec thuần túy. Không có:
- CREATE TABLE
- ALTER TABLE
- INSERT INTO
- Sửa `app.py` hoặc `places.html` (đã làm session trước)

---

## Blockers để implementation

1. **CHGIS TGAZ URL**: `chgis.fairbank.fas.harvard.edu` không resolve. Cần tìm URL mới hoặc mirror trước khi code `_fetch_chgis_dynasty()`.

2. **BGIS zip format**: `china_bgis_fme.zip` chưa download. Cần mở xem schema trước khi viết ETL.

3. **Manual seed priority list**: Cần người có kiến thức địa danh Phật giáo để prioritize 100 places lớn nhất cần seed trước.

4. **Wikidata coverage thấp**: Chỉ 148/59,167 places có P1188 (~0.25%). Phần còn lại cần manual/spatial matching — effort lớn.

---

## Bước tiếp theo (T21 implementation — session sau)

```
Session sau:
  1. Verify CHGIS TGAZ URL mới (search Harvard CGA portal)
  2. Download + inspect BGIS zip format
  3. CREATE TABLE geo_cross_ref (additive, safe — không động bảng cũ)
  4. SPARQL script batch seed 148 places có P1188
  5. Manual seed Thiếu Lâm: dila_id=PL000000023255, wikidata_qid=Q232771
  6. _fetch_wikidata_timeline(qid) → P571 + P1435
  7. _fetch_chgis_dynasty(lat, lon, year) → dynasty context
  8. Rewrite renderTimelineTab() trong places.html
```
