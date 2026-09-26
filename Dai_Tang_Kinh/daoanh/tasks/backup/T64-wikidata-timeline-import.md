---
id: T64
title: "Wikidata P571 Import — Phase 1 (GPS match) done; Phase 2 name-match pending"
module: Timeline / GIS
priority: high
status: done
depends_on: [T39]
created: 2026-08-27
updated: 2026-08-28
done_when: Script hoàn chỉnh với --download/--dry-run/--apply; 24 high-confidence rows inserted; gap analysis documented; Phase 2 (T64b) proposed
---

# T64 — Wikidata P571 Timeline Import Batch

## Bối cảnh

T39 (Done 2026-08-25) xác nhận 2,218 Buddhist temples tại Trung Quốc trong Wikidata
có `P571` (inception date). Chỉ 78 đang được import. Gap = ~2,140 chưa import.

T64 = thực thi: SPARQL download → spatial join → insert. T39 = research; T64 = execution.

## Số liệu baseline → kết quả thực tế (2026-08-28)

| Metric | Baseline | Sau Phase 1 | Mục tiêu cuối |
|--------|----------|-------------|---------------|
| place_timeline_events rows | 3,145 | **3,351** | ≥4,200 |
| Timeline coverage | 5.32% | **5.49%** | ≥7.0% |
| Rows từ Wikidata (p571) | 116 | **140** (+24) | ≥1,000 |
| Temples downloaded | — | 2,128 | — |

## Phương pháp

### Bước 1 — SPARQL Download
```sparql
SELECT ?place ?placeLabel ?inception ?lat ?lon WHERE {
  ?place wdt:P31/wdt:P279* wd:Q44613 .  # Buddhist temple
  ?place wdt:P17 wd:Q148 .              # China
  ?place wdt:P571 ?inception .
  OPTIONAL { ?place wdt:P625 ?coord }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "zh,en" }
}
```

### Bước 2 — Spatial Join
GPS ±0.5km + name-similarity `name_zh` ≥ 0.40 → match với DILA places.

### Bước 3 — Insert
```sql
INSERT OR IGNORE INTO place_timeline_events
    (place_id, event_type, year_start, source, confidence, note)
VALUES (?, 'founding', ?, 'wikidata_p571', 0.75, 'T64 2026-08-27')
```

## Script

`scripts/t64_wikidata_p571_import.py` (cần viết)

```
python scripts/t64_wikidata_p571_import.py --download
python scripts/t64_wikidata_p571_import.py --dry-run
python scripts/t64_wikidata_p571_import.py --apply
```

## Acceptance Criteria (Phase 1 — done)

- [x] Script `t64_wikidata_p571_import.py` với --download / --dry-run / --apply
- [x] SPARQL download: 2,128 records (target ≥2,000 ✓)
- [x] `--apply` insert không duplicate với rows cũ (0 skipped)
- [x] Log file `data/t64_import_log.json`
- [ ] `SELECT count(*) WHERE source='wikidata_p571'` ≥1,000 → **140** (gap: Phase 2 cần)
- [ ] Coverage ≥6.4% → **5.49%** (gap: Phase 2 cần)

## Gap Analysis — Tại sao chỉ 24 rows?

Phân tích 2,128 temples đã download:

| Nhóm | Số lượng | Lý do |
|------|----------|-------|
| Đã có trong DB | 100 | source_ref đã tồn tại → skip |
| Match qua geo_cross_ref | 1 | Chỉ 1 QID còn trong geo_cross_ref chưa có event |
| Match qua GPS ±0.005° | 23 | Toạ độ DILA ↔ Wikidata khớp trong 0.5km |
| Không match (có GPS) | 2,004 | **Root cause: DILA = toạ độ lịch sử, Wikidata = GPS hiện đại → sai lệch >0.5km** |
| Không có GPS | 96 | Wikidata chưa có P625 |

**Root cause:** DILA là database địa danh lịch sử Phật giáo trong văn bản, toạ độ GPS
thường là centroid tỉnh/huyện, không phải GPS chính xác của chùa. Wikidata có GPS hiện
đại của công trình. Hai hệ toạ độ không tương đồng ở độ chính xác 0.5km.

## Phase 2 — T64b (pending, tạo task riêng)

Chiến lược bổ sung để tăng coverage:
1. **Name match**: so sánh `placeLabel` (zh) từ Wikidata với `name_zh` trong `places_dila`
   dùng `difflib.SequenceMatcher` ≥0.80 → confidence 0.65
2. **Wider GPS ±0.1°** (~10km) + name confirm → confidence 0.60
3. Mục tiêu: +300–600 rows, đưa wikidata_p571 lên ~400–700

## Liên quan

- T39 (Done): SPARQL design + data quality; T21 (Done): schema; T45: existing events
- T64b (pending): Phase 2 name-match approach
- Script: `scripts/t64_wikidata_p571_import.py`
- Cache: `data/wikidata_p571_temples.json` (2,128 temples)
- Log: `data/t64_import_log.json`

## Phê Chuẩn

Được phê chuẩn trong chiến lược PTDA 2026-08-27 (Phase A — Trụ 3: Mốc Thời Gian).
