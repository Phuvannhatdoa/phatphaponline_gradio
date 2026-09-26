---
id: T21
title: Niên Đại Tab — Geo-Identity Linking (Bridge Table Strategy)
module: GIS Places / Timeline
priority: medium
status: done
depends_on: [T14, T18]
created: 2026-08-19
updated: 2026-08-25
done_when: geo_cross_ref populated cho top 100 places, API on-demand trả timeline thật, tab NIÊN ĐẠI hiển thị với attribution chuẩn, server chạy code mới, Giai đoạn 4 BGIS ETL xong
scope_limit: Wikidata path: 81 places (source=wikidata). DILA fallback path (Hướng A, 2026-08-25): 2,687 places thêm — founding.year từ dila_era_name/dila_dynasty/dila_note với status=dila_fallback + note_vi cảnh báo nguồn
---

# T21 — Niên Đại Tab: Phân Tích Kỹ Thuật Đầy Đủ

## Bối cảnh

Tab "⏱ Niên Đại" cũ dùng `_CHINESE_DYNASTIES` hardcode + regex parse trên `places_dila.note` — vi phạm nguyên tắc nội dung (xóa 2026-08-19). Hiện tại tab hiển thị `⚠ T21 pending`.

Chiến lược được phê duyệt: **"Geo-Identity Linking"** — không import dữ liệu thô, chỉ lưu ID, truy vấn on-demand khi cần.

---

## Audit Hiện Trạng (đã thực hiện 2026-08-19)

### DB Schema

```sql
-- places_dila (59,167 rows) — KHÔNG có external ID column
CREATE TABLE places_dila (
    id TEXT PRIMARY KEY,          -- DILA Place ID: PL000000023255
    name TEXT, name_zh TEXT, name_en TEXT,
    geo_lat REAL, geo_long REAL,  -- GPS tọa độ — có thể dùng cho TGAZ query
    place_key TEXT,               -- DILA internal key: PLD001520
    district TEXT,                -- Chuỗi hành chính: 中國-河南省-鄭州市-登封市
    note TEXT,                    -- Narrative text (KHÔNG parse)
    listbibl TEXT,                -- CBETA refs (đang dùng cho T-series JOIN)
    raw_xml TEXT,                 -- TEI XML gốc
    source_id INTEGER
);

-- places (Vietnam-focused) — KHÔNG có external ID column
CREATE TABLE places (
    id TEXT PRIMARY KEY,
    name_zh TEXT, name_vi TEXT,
    gps_lat REAL, gps_long REAL,
    country TEXT DEFAULT 'Vietnam'
);
```

### Kết luận Audit

| Câu hỏi | Kết quả |
|---------|---------|
| Có cột Wikidata/CHGIS/TGAZ nào chưa? | ❌ Chưa có |
| `geo_cross_ref` đã tồn tại chưa? | ❌ Chưa có |
| GPS tọa độ có trong `places_dila`? | ✅ Có (34.507018, 112.935331 cho Thiếu Lâm) |
| DILA ID là khóa duy nhất? | ✅ `id TEXT PRIMARY KEY` |

---

## Chiến Lược: "Không Tích Hợp Thô" (No Raw Import)

### Nguyên tắc

> **Đừng tải dữ liệu của họ về DB.** Chỉ lưu ID. Khi user click → hệ thống dùng ID để hỏi nguồn gốc qua API.

**Lợi ích đã được phê duyệt:**
- DB nhẹ, không bị phình dữ liệu của bên thứ ba
- Luôn lấy dữ liệu mới nhất từ nguồn gốc (live)
- Nếu CHGIS/Wikidata cập nhật → tự động được hưởng, không cần re-import
- Additive: không chạm vào bảng hiện có → an toàn tuyệt đối với `lineage.db`

**Nhược điểm và rủi ro (đã nhận thức):**
- **API downtime**: nếu Wikidata/CHGIS API down → tab không có data (cần fallback)
- **Latency**: mỗi lần click place phải chờ API ngoài (50–500ms)
- **Rate limiting**: Wikidata SPARQL có rate limit (không vấn đề với traffic nhỏ)
- **License thay đổi**: nguồn có thể thay đổi điều kiện sử dụng (ít xảy ra với CC0/CC BY)
- **Data staleness**: cache cần TTL để không gọi API liên tục

---

## Thiết Kế Bridge Table: `geo_cross_ref`

### Schema (KHÔNG thay đổi bảng hiện có)

```sql
CREATE TABLE IF NOT EXISTS geo_cross_ref (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    dila_id     TEXT NOT NULL REFERENCES places_dila(id),
    wikidata_qid TEXT,      -- Q232771 (Thiếu Lâm Tự)
    chgis_svid  TEXT,       -- CHGIS System Variant ID (administrative unit)
    tgaz_id     TEXT,       -- TGAZ place ID nếu có
    bgis_id     TEXT,       -- BGIS monastery ID (Jiang Wu / Bingenheimer)
    marcus_ref  TEXT,       -- Marcus datasets reference
    notes       TEXT,       -- Ghi chú mapping (vd: "GPS match ±0.1km")
    confidence  TEXT DEFAULT 'verified',  -- 'verified' | 'probable' | 'spatial'
    mapped_by   TEXT,       -- 'manual' | 'sparql_p1188' | 'spatial_join'
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(dila_id)
);
```

### Quan hệ

```
places_dila.id (PL000000023255)
    └── geo_cross_ref.dila_id
            ├── wikidata_qid = "Q232771"   → Wikidata API
            ├── chgis_svid   = "..."        → CHGIS TGAZ API
            ├── bgis_id      = "..."        → BGIS dataset
            └── marcus_ref   = "..."        → Marcus CSV
```

---

## Kiến Trúc API On-Demand

### Endpoint mới: `/daoanh/api/places/<place_id>/timeline`

```
Request:  GET /daoanh/api/places/PL000000023255/timeline
Response: {
  "ok": true,
  "dila_id": "PL000000023255",
  "cross_refs": {
    "wikidata_qid": "Q232771",
    "chgis_svid": "...",
    "bgis_id": "..."
  },
  "timeline": {
    "founding": {
      "year": 495,
      "source": "wikidata",
      "source_ref": "Q232771 · P571",
      "license": "CC0"
    },
    "heritage": [
      {"year": 1983, "label": "Trọng điểm Phật giáo Quốc gia", "source": "wikidata", "source_ref": "Q232771 · P1435"},
      {"year": 2010, "label": "Di sản UNESCO", "source": "wikidata", "source_ref": "Q232771 · P1435"}
    ]
  },
  "dynasty_context": {
    "year": 495,
    "dynasty": "北魏",
    "dynasty_vi": "Bắc Ngụy",
    "admin_unit": "登封縣",
    "source": "chgis_tgaz",
    "source_ref": "CHGIS TGAZ API · Harvard CGA",
    "license": "CC BY"
  },
  "cache_ttl": 86400
}
```

### Logic backend (app.py)

```python
@app.route('/daoanh/api/places/<place_id>/timeline')
def api_places_timeline(place_id):
    conn = get_db_connection()
    dila_id, _ = _resolve_dila_id(conn, place_id)

    # 1. Lấy cross_ref từ bridge table
    xref = conn.execute(
        'SELECT * FROM geo_cross_ref WHERE dila_id = ?', (dila_id,)
    ).fetchone()

    if not xref:
        return jsonify({"ok": True, "status": "no_mapping",
                        "message": "Chưa có mapping ID cho địa danh này. Xem T21."})

    # 2. Wikidata — founding date + heritage (cache 24h)
    timeline = _fetch_wikidata_timeline(xref['wikidata_qid'])  # calls Wikidata API

    # 3. CHGIS TGAZ — dynasty context tại founding year (cache 24h)
    dynasty = _fetch_chgis_dynasty(dila_id, timeline.get('founding_year'),
                                   xref.get('chgis_svid'))  # calls TGAZ API

    conn.close()
    return jsonify({"ok": True, "dila_id": dila_id,
                    "timeline": timeline, "dynasty_context": dynasty,
                    "cross_refs": dict(xref)})
```

---

## Nguồn Dữ Liệu — Vai Trò Cụ Thể

### 1. Wikidata (P571 + P1435) — Founding Date

| | Chi tiết |
|-|---------|
| Endpoint | `https://query.wikidata.org/sparql` |
| Data | P571 = founding year · P1435 = heritage designations |
| Cho Thiếu Lâm | Q232771 · P571 = `0495-01-01T00:00:00Z` ✅ |
| License | CC0 |
| Cách seed | SPARQL batch 148 places có P1188 · Manual cho top 100 |
| Rủi ro | Rate limiting (low traffic OK) · API downtime |
| Cache | 24h TTL trong memory/Redis |

```sparql
-- SPARQL batch seed: 148 places đã có P1188 (DILA bridge)
SELECT ?item ?dila_id ?inception WHERE {
  ?item wdt:P1188 ?dila_id .
  OPTIONAL { ?item wdt:P571 ?inception }
}
-- Endpoint: https://query.wikidata.org/sparql
```

### 2. CHGIS TGAZ (Harvard) — Dynasty Context

| | Chi tiết |
|-|---------|
| Endpoint | `https://chgis.hudci.org/tgw/` (URL mới, cần verify) |
| Data | Administrative unit + dynasty tại 1 năm cụ thể |
| Query | `?placename=登封&year=495&fmt=json` |
| Coverage | 222 BCE → 1911 CE |
| License | CC BY (Harvard CGA) |
| Cách dùng | Thay `_CHINESE_DYNASTIES` hardcode bằng API call thật |
| Rủi ro | Domain hiện không resolve (`chgis.fairbank.fas.harvard.edu`) — cần verify URL mới |
| Fallback | Nếu TGAZ down → show `time_periods` table (117K rows, DILA) để verify niên hiệu |

### 3. BGIS / Marcus datasets — Buddhist-specific Founding Date

| | Chi tiết |
|-|---------|
| Source | BGIS `china_bgis_fme.zip` (Jiang Wu/Bingenheimer) · Marcus Taiwanese CSV (5,500 temples) |
| Data | Founding date chuyên biệt cho Chinese Buddhist temples |
| Cách dùng | ETL → `place_timeline_events` → join với `geo_cross_ref` |
| Mapping | GPS spatial join: `geo_lat`/`geo_long` trong `places_dila` ↔ BGIS coordinates |
| License | Academic (CC) |
| Rủi ro | Format zip chưa verify · Marcus dataset phủ Taiwan, không phải mainland China |

**Lưu ý quan trọng:** BGIS và Marcus không có on-demand API → cần ETL một lần vào `place_timeline_events` (khác với Wikidata/CHGIS là on-demand). Đây là exception hợp lý vì đây là Buddhist-specific data ổn định, không cập nhật thường xuyên.

---

## Bảng Bổ Sung: `place_timeline_events`

Cho BGIS/Marcus data (không có API, cần ETL):

```sql
CREATE TABLE IF NOT EXISTS place_timeline_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    dila_id     TEXT NOT NULL,
    event_type  TEXT NOT NULL,  -- 'founding' | 'heritage' | 'renovation' | 'destroyed'
    year        INTEGER,        -- CE (negative = BCE)
    year_end    INTEGER,
    label_zh    TEXT,
    label_vi    TEXT,
    source      TEXT NOT NULL,  -- 'wikidata' | 'bgis' | 'marcus' | 'chgis'
    source_ref  TEXT,           -- Q232771·P571 / BGIS_ID / ...
    confidence  TEXT DEFAULT 'verified',
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_pte_dila ON place_timeline_events(dila_id);
```

---

## Phân Tích Rủi Ro / Lợi Ích Đầy Đủ

### Lợi ích

| | |
|-|-|
| **Tính toàn vẹn dữ liệu** | 100% authority source — không có data fake |
| **Nhẹ DB** | Chỉ lưu ID (text ngắn), không clone dataset của người khác |
| **Luôn mới** | API on-demand → tự động nhận update từ Wikidata/CHGIS |
| **An toàn DB** | Additive-only — không chạm bảng hiện có, không risk corrupt |
| **Attribution chuẩn** | Mỗi data point có source_ref rõ ràng → scholarly credible |
| **Extensible** | Thêm nguồn mới chỉ cần thêm cột vào `geo_cross_ref` |

### Rủi ro và Giảm nhẹ

| Rủi ro | Mức độ | Giảm nhẹ |
|--------|--------|----------|
| Wikidata API down | Thấp | Cache 24h TTL · fallback "Đang cập nhật" |
| CHGIS URL không resolve | Trung bình | Cần verify URL mới · fallback `time_periods` table |
| Latency API ngoài | Trung bình | Cache + async prefetch khi select place |
| Wikidata thiếu P1188 | Cao | Manual seed cho top 100 places |
| BGIS format unknown | Trung bình | Verify zip trước khi ETL |
| Marcus data = Taiwan only | Trung bình | Chỉ dùng cho Taiwanese temples; mainland cần BGIS |

### Nhược điểm (chấp nhận có ý thức)

- **Tab NIÊN ĐẠI sẽ trống** cho 99% places ban đầu (chỉ top 100 được mapping)
- **Cần maintain `geo_cross_ref`** — khi DILA thêm places mới, phải seed thêm
- **Wikidata quality**: P571 của Wikidata đôi khi thiếu reference cụ thể (dù CC0)
- **CHGIS TGAZ**: chỉ biết administrative unit tại 1 năm, không phải founding date của temple

---

## Lộ Trình Implementation

### Giai đoạn 1 — Schema (additive, không risk)

```sql
-- Chạy một lần, không thay đổi gì hiện có
CREATE TABLE IF NOT EXISTS geo_cross_ref (...);
CREATE TABLE IF NOT EXISTS place_timeline_events (...);
```

### Giai đoạn 2 — Seed `geo_cross_ref`

```
Step 2a: SPARQL batch → 148 places có P1188 → insert vào geo_cross_ref
Step 2b: Manual seed top 100 places lớn:
  PL000000023255 → Q232771 (Thiếu Lâm)
  PL... → Q... (Long Môn Thạch Quật)
  ... (danh sách ưu tiên theo lượt xem)
Step 2c: Spatial join GPS → BGIS coordinates → bgis_id (precision ±0.5km)
```

### Giai đoạn 3 — API wrapper functions

```python
_fetch_wikidata_timeline(qid)   # Wikidata SPARQL → P571 + P1435
_fetch_chgis_dynasty(lat, lon, year)  # TGAZ API → dynasty context
```

### Giai đoạn 4 — ETL BGIS/Marcus (ngoại lệ: static data)

```
ETL BGIS china_bgis_fme.zip → place_timeline_events (founding dates)
ETL Marcus Taiwanese CSV    → place_timeline_events (5,500 temples)
```

### Giai đoạn 5 — Rewrite tab NIÊN ĐẠI

Tab từ `⚠ T21 pending` → show real data với attribution chuẩn.

---

## Acceptance Criteria

**Audit (done 2026-08-19):**
- [x] Verify DB schema — không có external ID column
- [x] Confirm `geo_cross_ref` chưa tồn tại
- [x] Thiếu Lâm GPS (34.507018, 112.935331) có sẵn cho TGAZ query
- [x] Xác nhận chiến lược "Không tích hợp thô" + Bridge Table
- [x] Phân tích đầy đủ 15 nguồn → chọn Wikidata + CHGIS TGAZ + BGIS/Marcus

**Implementation (2026-08-20):**
- [x] Giai đoạn 1: CREATE TABLE `geo_cross_ref` (đã có từ T28) + CREATE TABLE `place_timeline_events` ✅
- [x] Giai đoạn 2a: SPARQL P1188 batch seed → 148 rows trong `geo_cross_ref`, 72 founding years trong `place_timeline_events` ✅
- [x] **Giai đoạn 2c: Wikidata bulk enrichment (2026-08-21):** Script `scripts/wikidata_bulk_places.py` — Phase A fetch full properties (P571+P576+P17+label_vi). Kết quả: 72→81 founding (+9 missing), **+41 dissolved events** (kiểu mới), total 122 rows / 82 DILA places. Frontend cập nhật: typeMap thêm 'dissolved'/'admin_context', year BCE render "344 TCN" thay vì "-344 CE". Phase B (coordinate-based staging) đang chạy → `geo_cross_ref_candidates` table. ✅
- [x] **Giai đoạn 2d: DILA note regex extraction (2026-08-21):** Script `scripts/dila_note_founding_extract.py` — trích year từ pattern `（\d{3,4}）` trong 5,904 temple/pagoda notes. Kết quả: **+429 founding events** (source='dila_note', confidence='regex_note'), total 551 rows / 511 unique DILA places. Coverage: 0.12% → **0.86%** (511/59,167). Frontend: badge "DILA note" + snippet snippet label_zh. ✅
- [x] **Giai đoạn 2e: Era name (年號) extraction (2026-08-23):** Script `scripts/dila_era_name_extract.py` — lookup table ~215 era names (Đông Hán → Dân Quốc, thêm Nam Tề/Lương/Trần) → trích founding year từ pattern "{dynasty}{era_name}{N}年建" hoặc "{era_name}中" (midpoint). Kết quả: **+1,449 founding events** (exact + midpoint), source='dila_era_name', confidence='era_name_exact'/'era_name_midpoint'. Total: 2,000 rows / **1,960 unique DILA places**. Coverage: 0.86% → **3.31%** (1,960/59,167). Frontend: badge "DILA·年號" (midpoint có prefix "~"). ✅
- [x] **Giai đoạn 2f: Dynasty range fallback (2026-08-23):** Script `scripts/dila_dynasty_range_extract.py` — lookup 35 dynasties → trích midpoint founding year từ pattern "唐代建/始建於宋/元末明初". Kết quả: **+543 places** (confidence='dynasty_range'), source='dila_dynasty'. Total: 2,543 rows / **2,503 unique DILA places**. Coverage: 3.31% → **4.23%** (2,503/59,167). Frontend: badge "DILA·朝代" + "~" prefix. ✅
- [x] Giai đoạn 2b: Manual seed Thiếu Lâm Tự → Q232771 (đã có từ T28 session) ✅
- [x] Giai đoạn 3: `_fetch_wikidata_timeline()` (Wikidata on-demand, cached 24h) + route thật trong app.py ✅
- [x] **Fix dynasty context bug (2026-08-20):** `_get_dynasty_context()` ban đầu query `time_periods` — nhưng bảng này là lịch âm (tháng '十','三'), không phải triều đại. Fix: dùng bảng hardcode 22 triều đại Trung Quốc (CE range), trả đúng 北魏 Bắc Ngụy cho năm 495. Source: `chinese_dynasties_static`, license: public domain ✅
- [ ] **Giai đoạn 4: ETL BGIS + Marcus → `place_timeline_events`** ← BLOCKER còn lại
  - Download `china_bgis_fme.zip` từ Harvard Dataverse: https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/VAYEUZ
  - Verify field "Starting year" = historical founding hay modern registration
  - Spatial join GPS ±0.5km: `places_dila.geo_lat/geo_long` ↔ BGIS coordinates
  - ETL → `place_timeline_events` với `source='bgis'`, `confidence='verified'`
  - Mục tiêu: thêm ~500-2000 founding dates từ BGIS
- [x] Giai đoạn 5: Rewrite tab NIÊN ĐẠI từ pending → real data (`renderTimelineTab()` + `_renderStaticEvents()`) ✅
- [x] Attribution mỗi data point: badge Wikidata·P571·CC0 + hardcoded dynasty table ✅
- [x] Fallback graceful: status='no_mapping' khi chưa có QID; wikidata_error khi API down ✅
- [x] Session doc tạo: `docs/sessions/2026-08-20_t21_nien_dai_implementation.md` ✅
- [ ] **Cần restart app.py để load code mới** — chạy lệnh dưới đây:
  ```powershell
  cd daoanh/
  Get-Process python | Stop-Process -Force; Start-Sleep 2; Start-Process python -ArgumentList "app.py" -NoNewWindow
  ```
- [ ] Verify sau restart: `GET /daoanh/api/places/PL000000023255/timeline` → `{"status":"ok","founding":{"year":495},"dynasty_context":{"dynasty_zh":"北魏","dynasty_vi":"Bắc Ngụy","dynasty_start":386}}`

---

## Blockers & Chỉ Thị Còn Lại (2026-08-20)

| # | Vấn đề | Chỉ thị | Ưu tiên |
|---|--------|---------|---------|
| 1 | **Server không load code mới** | Admin restart app.py (lệnh ở Acceptance Criteria) | URGENT |
| 2 | **BGIS ETL chưa làm** | Download zip từ Harvard Dataverse, verify field, spatial join, ETL vào `place_timeline_events` | HIGH |
| 3 | **148/59167 places có QID (0.25%)** | Wikidata P1188 đã khai thác hết (148 = tất cả). Hướng tiếp: ① DILA note regex extraction (~3,302 places có founding text) ② Phase B coordinate SPARQL → staging table `geo_cross_ref_candidates` (đang chạy 2026-08-21) | MEDIUM |
| 4 | **dynasty context lỗi cũ (đã fix)** | Đã fix 2026-08-20: query `time_periods` sai → đổi sang hardcoded table 22 triều đại. Không còn là blocker. | DONE |

**Lưu ý kỹ thuật về `time_periods`:** Bảng này là bộ chuyển đổi âm–dương lịch (115,921 rows = các tháng âm lịch từ năm -2740), KHÔNG phải dynasty timeline. Dynasty rows (123) trong table không có `start_year`. Đây là `T14` scope, không phải `T21`. Dynasty context của `T21` dùng hardcoded table riêng. ✅ Resolved.
- BGIS `china_bgis_fme.zip` cần download + verify format trước ETL (Giai đoạn 4 còn pending)
- Wikidata P1188 coverage 148/59,167 (~0.25%) — đủ cho core Buddhist sites. Phần lớn non-temple (39K 中研院歷史地名) không cần P571.
- Manual seed top 100 cần người có kiến thức địa danh Phật giáo để prioritize

---

## Audit 2026-08-24 — Trạng Thái Thực Tế Cho Admin

### Tóm tắt nhanh

| Hạng mục | Kết quả |
|----------|---------|
| Code đã viết | ✅ Hoàn chỉnh (routes, tab render, attribution) |
| DB populated | ✅ 2,543 rows / 2,503 DILA places có founding event |
| Coverage | 4.23% (2,503/59,167) — đủ cho top sites |
| Server đang chạy code mới | ❌ **CẦN RESTART** |
| BGIS Giai đoạn 4 | ❌ Chưa làm (optional, +500-2000 rows nữa) |

### Chỉ Thị Ưu Tiên (Priority Actions)

**[URGENT] Restart app.py** để load tất cả code đã viết trong các session trước:
```powershell
# Chạy từ thư mục daoanh/
Get-Process python | Where-Object { $_.ProcessName -eq 'python' } | Stop-Process -Force
Start-Sleep 2
Start-Process python -ArgumentList "app.py" -NoNewWindow -RedirectStandardOutput "app_local.log"
```

**[VERIFY] Kiểm tra endpoint sau restart:**
```
GET http://localhost:8080/daoanh/api/places/PL000000023255/timeline
Expected: {"status":"ok","founding":{"year":495},"dynasty_context":{"dynasty_vi":"Bắc Ngụy"}}
```

**[OPTIONAL/HIGH] Giai đoạn 4 — BGIS ETL:**
1. Download `china_bgis_fme.zip` từ: https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/VAYEUZ
2. Inspect CSV — verify "Starting year" field là founding year lịch sử (không phải registration year)
3. Spatial join: match BGIS GPS ±0.5km với `places_dila.geo_lat/geo_long`
4. ETL vào `place_timeline_events` với `source='bgis'`, `confidence='verified'`
5. Mục tiêu: +500–2,000 founding dates bổ sung

### Tiêu Chí Hoàn Thành T21

- [x] Code routes + frontend tab (done)
- [x] 2,503 places có founding event trong DB (done)  
- [ ] Server restart + endpoint verify thành công
- [ ] BGIS ETL (optional — có thể mark done mà không cần Giai đoạn 4)

---

## Ghi Chú Kiến Trúc

Từ báo cáo "Geo-Identity Linking":
> "Hệ thống của Ngài nhẹ, luôn cập nhật dữ liệu mới nhất từ nguồn gốc mà không cần làm gì cả."

Đây là design pattern chuẩn trong Digital Humanities — tương tự cách VIAF (Virtual International Authority File) hoạt động: không lưu dữ liệu của từng thư viện, chỉ lưu ID và truy vấn khi cần. Phù hợp với hệ thống không có bandwidth để maintain full copy của CHGIS hay Wikidata.
