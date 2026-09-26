# Session 2026-08-25 — T39 Place CBETA Bibl ETL

## Tóm tắt
Tích hợp `<listBibl>` từ DILA Place Authority XML thành nguồn Person↔Place thứ 4 trong hệ thống.
Từ 2 nhân vật → 148 nhân vật cho Thiếu Lâm Tự (2 curated + 1 Wikidata + 20 CBETA Bibl + 125 Bio).

## Files đã thay đổi

| File | Loại thay đổi | Ghi chú |
|---|---|---|
| `scripts/import_place_person_bibl.py` | NEW | ETL script T39 |
| `tasks/T39-place-cbeta-bibl-etl.md` | NEW | Task file T39 |
| `app.py` | EDIT | Thêm Source 4 `bibl_persons` vào `api_places_persons()` |
| `places.html` | EDIT | Render section "DILA CBETA Bibl" trong tab Nhân Vật |
| `data/lineage.db` | SCHEMA+DATA | Bảng mới `place_person_bibl` (13,933 rows) |
| `docs/sessions/2026-08-25/t39_etl.log` | NEW | ETL run log |

## Backup trước khi sửa
- `docs/sessions/2026-08-25/app.py.bak`
- `docs/sessions/2026-08-25/places.html.bak`

## Để rollback
```powershell
# Rollback code (không ảnh hưởng DB):
Copy-Item docs/sessions/2026-08-25/app.py.bak app.py
Copy-Item docs/sessions/2026-08-25/places.html.bak places.html

# Rollback DB (xóa bảng mới):
# sqlite3 data/lineage.db "DROP TABLE IF EXISTS place_person_bibl;"
```

## Số liệu ETL
- XML: 117,620 places → 59,166 trong DB → 11,937 có bibl → 14,428 bibl entries parsed
- Match rate: 60.7% (6,272 exact + 2,493 strip-prefix 釋/尼)
- Kết quả: 8,513 links có person_id, 5,915 unmatched (person_name_raw giữ lại để review sau)

## API test (verified)
```
GET /daoanh/api/places/PL000000023255/persons
→ status: ok
→ persons: 2 | wikidata_persons: 1 | bibl_persons: 20 | bio_persons: 125
```

## Vấn đề phát hiện
- `鳩摩羅什`, `釋智顗`, `竺佛圖澄`: unmatched vì tên biến thể trong DB — không phải lỗi logic
- Thiên Thai Sơn (PL000000010234): bibl=0 — place đó không có bibl entries trong XML; bio=200 vẫn hoạt động
- "宋高僧傳序並釋義淨" (47x): parse noise từ tên sách dài — không ảnh hưởng data đúng vì CJK ratio check loại phần lớn
