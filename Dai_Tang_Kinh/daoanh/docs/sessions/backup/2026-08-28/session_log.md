# Session Log — 2026-08-28

## Task thực hiện: T64 — Wikidata P571 Import (Phase 1)

### Script đã viết
`scripts/t64_wikidata_p571_import.py`  
Flags: `--download` / `--dry-run` / `--apply` / `--verbose`

### Kết quả

| Bước | Kết quả |
|------|---------|
| SPARQL download | 2,128 temples (target 2,218; Wikidata query trả về ít hơn) |
| Cache | `data/wikidata_p571_temples.json` |
| Method A (geo_cross_ref) | 1 match mới (少林寺 — PL000000023255, conf 0.85) |
| Method B (GPS ±0.005°) | 23 matches mới (conf 0.72) |
| Inserted | **24 rows** vào `place_timeline_events` |
| wikidata_p571 total | 116 → **140** |
| place_timeline_events total | 3,327 → **3,351** |
| Timeline coverage | 5.47% → **5.49%** |
| Log | `data/t64_import_log.json` |

### Gap Analysis

Chỉ 24/2,128 matched vì DILA dùng toạ độ lịch sử (centroid vùng), Wikidata dùng GPS hiện đại của công trình vật lý. Sai lệch >0.5km với phần lớn (2,004) temples.

- 100 temples: đã có trong DB (skip)
- 1 match: qua geo_cross_ref QID
- 23 match: GPS ±0.5km
- 2,004 không match: GPS delta > 0.5km
- 96 không có GPS Wikidata

### Phase 2 cần làm (T64b)
- Name similarity: `difflib.SequenceMatcher(name_zh)` ≥ 0.80
- GPS wider: ±0.1° + name confirm
- Target: +300–600 rows thêm

### Task file cập nhật
- `tasks/T64-wikidata-timeline-import.md` → status: done, gap analysis, Phase 2 note

### Dashboard
- Rebuild: `python scripts/build_progress_data.py`
- Kết quả: 71%, done=41, total=68

## Files changed

| File | Thay đổi |
|------|---------|
| `scripts/t64_wikidata_p571_import.py` | Tạo mới |
| `data/wikidata_p571_temples.json` | Tạo mới (cache 2,128 temples) |
| `data/t64_import_log.json` | Tạo mới |
| `tasks/T64-wikidata-timeline-import.md` | status: done, gap analysis |
| `data/progress_data.json` | Rebuild: 71%, done=41 |
