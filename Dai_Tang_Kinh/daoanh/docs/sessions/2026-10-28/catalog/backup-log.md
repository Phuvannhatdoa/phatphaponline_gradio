# T482 — Log backup trước khi tạo place_catalog

- Thời điểm: 2026-10-28
- Phương pháp: SQLite backup API (`sqlite3.Connection.backup()`), KHÔNG copy file thô.
- File đích: `data/backups/lineage_2026-10-28_catalog.db`
- Kích thước: 1.683.972.096 bytes (khớp 100% với `data/lineage.db` nguồn tại thời điểm backup)
- `PRAGMA quick_check`: `ok`
- Kiểm tra lại 1 bảng mẫu sau backup: `places_dila` COUNT = 59.167 (khớp DB nguồn)

## Dry-run trước khi ghi

```
=== DRY-RUN place_catalog (T482) ===
places_dila:            59,167
dila_place_authority:    206
overlap (trùng id):      0
TỔNG DỰ KIẾN place_catalog: 59,373  (mục tiêu đề bài: 59.373)
place_catalog đã có sẵn: 0 (bảng chưa tạo)
codex_place_name (Claude, toàn DB): 59,353
ai_place_name (Gemini, toàn DB):     50,341
namevi_map_places (name_vi hiện tại, toàn DB): 60,468
```

## Apply (ghi thật, 1 transaction)

```
=== APPLY place_catalog (T482) ===
Trước: 0 dòng
Sau:   59,373 dòng
  dila_place_authority: 206
  places_dila: 59,167
```

## Revert

```bash
python -X utf8 scripts/t482_build_place_catalog.py --revert
```
DROP TABLE `place_catalog` — bảng additive, không có FK/trigger phụ thuộc, 0 ảnh hưởng
`places_dila` / `dila_place_authority` / `namevi_map_places` / `codex_place_name` /
`ai_place_name` / `lexicon`.
