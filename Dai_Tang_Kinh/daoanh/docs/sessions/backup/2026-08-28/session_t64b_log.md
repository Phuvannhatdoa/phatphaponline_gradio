# Session Log — 2026-08-28 (T64b)

## Task: T64b — Wikidata P571 Phase 2 Name Match

### Root Cause Discovery

Sau T64 Phase 1 (24 GPS matches), phân tích 2,028 unmatched temples cho thấy:
- Wikidata labels: **giản thể** (龙, 灵, 马...)
- DILA name_zh: **phồn thể** (龍, 靈, 馬...)
- 47 Wikidata temples có 龙 → 0 match DILA (vì DILA chỉ có 龍)

Giải pháp: `opencc s2t` convert trước khi so sánh.

### Script viết

`scripts/t64b_wikidata_name_match.py`

Logic:
1. Convert Wikidata label: giản thể → phồn thể (opencc s2t)
2. Exact match với DILA name_zh
3. 1 hit: nếu có GPS cả hai bên mà >50km → SKIP (false positive)
4. N hits: GPS disambiguate → chọn gần nhất <50km
5. Dedup: (dila_id, year) → giữ conf cao nhất

### Kết quả

| Bước | Số |
|------|---|
| Candidates sau s2t convert | 33 |
| GPS conflict >50km → skipped | 12 |
| Ambiguous no GPS → skipped | 15 |
| Inserted | **6** |
| False positives | 0 |

wikidata_p571: 140 → **146**  
place_timeline_events: 3,351 → **3,357**  
Timeline coverage: 5.49% → **5.50%**

### Rollback

```sql
DELETE FROM place_timeline_events
WHERE source='wikidata_p571' AND created_at >= '2026-08-28T18:00:00'
```

(Xem `data/t64b_import_log.json` để lấy timestamp chính xác)

### Files changed

| File | Thay đổi |
|------|---------|
| `scripts/t64b_wikidata_name_match.py` | Tạo mới |
| `tasks/T64b-wikidata-name-match.md` | Tạo mới |
| `data/t64b_import_log.json` | Tạo mới |
| `data/progress_data.json` | Rebuild: 71%, done=47/78 |
