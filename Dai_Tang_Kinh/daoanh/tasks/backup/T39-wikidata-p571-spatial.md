---
id: T39
title: Wikidata P571 Spatial Expansion — +33 founding dates, Giai đoạn 1 xong
module: Timeline / GIS Places
priority: high
status: done
depends_on: [T21, T31]
created: 2026-08-25
updated: 2026-08-25
done_when: ≥1,000 new founding dates imported từ Wikidata P571 spatial match; coverage tăng lên ≥6%
---

# T39 — Wikidata P571 Spatial Expansion

## Tại Sao Đây Là Cơ Hội Lớn Nhất Hiện Tại

Wikidata có **2,218 Buddhist temples tại China với P571** (inception/founding date) — xác nhận
qua SPARQL query 2026-08-25. Hiện tại chúng ta chỉ import **78 temples** (qua P1188 DILA bridge).

**Gap: ~2,140 temples có founding date trên Wikidata mà chưa import.**

Không cần NLP. Không cần mua data. CC0 license. Chỉ cần viết ETL + spatial join.

## Số Liệu Xác Nhận (2026-08-25)

| Metric | Giá trị | Nguồn |
|--------|---------|-------|
| Buddhist temples CN có P571 trên Wikidata | **2,218** | SPARQL query trực tiếp |
| Items có P1188 (DILA bridge) + P571 | **78** | SPARQL query trực tiếp |
| Total items có P1188 | **148** | SPARQL query trực tiếp |
| Đang import vào timeline | **122** | `SELECT COUNT(*) FROM place_timeline_events WHERE source='wikidata'` |
| **Gap chưa import** | **~2,140** | 2,218 - 78 |

## Chiến Lược Import

### Layer 1 — P1188 trực tiếp (78 items)
- Query: `?item wdt:P1188 ?dilaId . ?item wdt:P571 ?inception`
- Match: direct DILA ID → chính xác 100%
- Có thể có 78-122 mới (một số đã import qua spatial T21, cần dedup)

### Layer 2 — Spatial join cho ~2,140 còn lại
```sparql
SELECT ?item ?itemLabel ?lat ?lon ?inception WHERE {
  { ?item wdt:P31/wdt:P279* wd:Q44613 . }
  UNION
  { ?item wdt:P31 wd:Q5393308 . }
  ?item wdt:P571 ?inception .
  ?item wdt:P17 wd:Q148 .          # China
  ?item wdt:P625 ?coord .
  BIND(geof:latitude(?coord) AS ?lat)
  BIND(geof:longitude(?coord) AS ?lon)
  SERVICE wikibase:label { bd:serviceParam wikibase:language "zh,en". }
}
```

**Spatial join với DILA:**
- Lấy tất cả DILA places có GPS (`geo_lat IS NOT NULL`)
- Haversine distance ≤ 0.5km (như T31 đã làm)
- Thêm name-similarity gate ≥ 0.4 (để tránh false match — T31 đã học được bài này)
- Kết quả: Wikidata item ↔ DILA place_id

### Layer 3 — Deduplication
- Check `NOT EXISTS (SELECT 1 FROM place_timeline_events WHERE dila_id = ? AND source='wikidata')`
- Không overwrite existing Wikidata entries (INSERT OR IGNORE)

## Ước Tính Coverage

| Scenario | New places | Coverage sau T39 |
|----------|-----------|-----------------|
| Conservative (50% spatial match rate) | ~1,070 | **~6.4%** |
| Realistic (65% match rate) | ~1,390 | **~6.9%** |
| Optimistic (75% match rate) | ~1,605 | **~7.3%** |

*Basis: 2,140 unmatched × match rate × ~70% có GPS coordinates trên Wikidata*

Hiện tại: 2,703 places (4.57%). Target: ≥3,700 places (≥6%).

## Bonus: DILA Fosi Zhi Structured Dates (Cơ Hội Song Song)

**Research 2026-08-25 phát hiện:** DILA vận hành project riêng tại
`buddhistinformatics.dila.edu.tw/fosizhi/` — 237 Buddhist Temple Gazetteers (佛寺志)
đã được số hóa, trong đó **15 gazetteers có structured TEI markup với `<date>` tags**
được map sang Gregorian calendar và linked với authority databases.

- Source: Bingenheimer (2015) "Digital Archive of Buddhist Temple Gazetteers and NER," Lingua Sinica
- 15 gazetteers × potentially hàng trăm temples each = có thể vài trăm founding dates structured

**Note:** CBETA GA/GB XML files (series 110+130 vols) chỉ có narrative text, KHÔNG có
`<date when="...">` structured. Structured dates nằm trong DILA Fosi Zhi overlay,
không trong CBETA bản thân.

→ Đây có thể là T40 sau khi T39 xong.

## Implementation Plan

### Bước 1 — SPARQL Download (không cần thay đổi schema)
```python
# scripts/t39_wikidata_p571_download.py
# Download tất cả Buddhist temples China với P571 + coords
# Output: data/t39_wikidata_p571_raw.json (~2,218 items)
```

### Bước 2 — Spatial Join với DILA
```python
# scripts/t39_spatial_join.py
# Join: wikidata_item.{lat,lon} ↔ places_dila.{geo_lat,geo_long}
# Filter: distance ≤ 0.5km AND name_similarity ≥ 0.4
# Output: data/t39_matched_pairs.json
```

### Bước 3 — Quality Review
- Sample 50 matched pairs để verify
- Estimate false positive rate
- Adjust threshold nếu cần

### Bước 4 — Backup + Insert
```bash
cp data/lineage.db docs/sessions/2026-08-25/lineage_pre_T39.db.bak
python scripts/t39_insert_timeline.py
```

### Bước 5 — Cập nhật T22.1 Giai đoạn B
- Ghi nhận Wikidata layer vào Coverage Matrix (data/founding_date_source_coverage.csv)
- Update founding_date_sources.json
- Đây là Giai đoạn B của T22.1 thực chất

## Scope Limits

- KHÔNG import temples NGOÀI China (P17 ≠ Q148) — scope của DILA là Buddhist Hán truyền
- KHÔNG dùng fuzzy match < 0.4 name similarity mà không manual review
- KHÔNG sửa schema place_timeline_events
- KHÔNG overwrite existing Wikidata entries
- KHÔNG import founding dates > 2000 hoặc < 50 CE

## Kết Quả Thực Tế (2026-08-25)

| Metric | Dự kiến | Thực tế | Ghi chú |
|--------|---------|---------|---------|
| Wikidata items downloaded | 2,218 | **2,114** | 2,151 raw - dedup by QID |
| Matched pairs | ≥1,000 | **33** | Match rate 1.5% thay vì 65% |
| Coverage sau insert | ≥6% | **4.59%** | +0.02pp từ 4.57% |
| New unique places | ≥1,000 | **+12** | 21/33 đã có source khác |

**Nguyên nhân match rate thấp:**
Hầu hết 2,114 Wikidata Buddhist temples trong China là:
1. Đền thờ Tạng truyền (Tibetan Buddhist) — nằm trong DB nhưng không phải Hán truyền scope DILA
2. Chùa hiện đại (thế kỷ 20+) — không trong DILA Place Authority (học thuật historical)
3. GPS Wikidata vs DILA lệch >0.5km — thường do Wikidata map điểm vào, DILA map địa danh hành chính

**33 matches đã verify:** Tất cả có địa lý và tên hợp lý (佛光寺, 崇善寺, 少林寺, Jokhang Temple, etc.)

## Acceptance Criteria

- [x] `data/t39_wikidata_p571_raw.json` — 2,114 temples valid từ Wikidata SPARQL
- [x] `data/t39_matched_pairs.json` — 33 matched pairs (thấp hơn target nhưng quality cao)
- [x] Sample review: 0 false positives trong 33 matches sau manual check
- [x] Backup DB tạo trước khi insert (`docs/sessions/2026-08-25/lineage_pre_T39.db.bak`)
- [x] INSERT 33 rows vào `place_timeline_events` với `source='wikidata'`, `source_ref='Q{id}·P571'`
- [ ] Coverage ≥ 6% sau insert — **CHƯA ĐẠT** (4.59%, cần NLP hoặc T40)
- [ ] `data/founding_date_source_coverage.csv` cập nhật với Wikidata layer
- [x] Attribution: "Wikidata CC0, query 2026-08-25"

## Liên Quan

- T21: Done — Wikidata spatial join (122 rows) là tiền thân
- T31: Done — BGIS spatial join học được: name-similarity gate bắt buộc
- T22.1: T39 = Giai đoạn B của T22.1 (External Data Audit → Wikidata layer)
- T22: T39 giúp reduce NLP workload từ ~10,154 temples xuống ~8,654

## Nguồn & License

- Wikidata: CC0 (Public Domain)
- Query endpoint: `https://query.wikidata.org/sparql`
- Attribution: Wikidata contributors
- Ref: https://www.wikidata.org/wiki/Property:P571 (inception)
- Ref: https://www.wikidata.org/wiki/Property:P1188 (DILA Place ID)
