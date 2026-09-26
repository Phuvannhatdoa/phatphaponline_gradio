# T21 — Niên Đại Tab: Geo-Identity Linking Implementation

**Ngày:** 2026-08-20  
**Session:** T21 implementation (sau khi T22 BLOCKED vì `nlp_authorized=False`)

---

## Tóm Tắt

Implemented T21 Geo-Identity Linking hoàn chỉnh (trừ Giai đoạn 4 BGIS ETL):

| Giai đoạn | Nội dung | Kết quả |
|-----------|----------|---------|
| 1 | Tạo `place_timeline_events` table | ✅ Done |
| 2a | SPARQL P1188 seed | ✅ 148 rows geo_cross_ref, 72 founding years |
| 2b | Manual seed Thiếu Lâm → Q232771 | ✅ Đã có từ T28 session |
| 3 | API route thật + helper functions | ✅ Done |
| 4 | ETL BGIS/Marcus | ⏳ Pending (BGIS zip chưa download) |
| 5 | Rewrite renderTimelineTab() | ✅ Done |

---

## Thay Đổi Files

### `data/lineage.db`
- Tạo `place_timeline_events` (11 columns, index trên dila_id)
- Seed SPARQL P1188: **148 rows** trong `geo_cross_ref`
- Seed P571: **72 founding year** rows trong `place_timeline_events`

### `app.py` (thay route stub T21 pending)

Thêm các functions:
- `_fetch_wikidata_timeline(qid)` — Wikidata on-demand, cache 24h trong `_timeline_cache`
- `_get_dynasty_context(year_ce, conn)` — query DILA `time_periods` (115,921 rows)
- `_ensure_place_timeline_events_table(conn)` — CREATE TABLE IF NOT EXISTS
- `api_places_timeline(place_id)` — route thật, trả JSON đầy đủ

Response object:
```json
{
  "ok": true,
  "status": "ok",
  "dila_id": "PL000000023255",
  "cross_refs": {"wikidata_qid": "Q232771", "mapped_by": "manual"},
  "founding": {"year": 495, "label": "少林寺", "heritage": [...], "source": "wikidata", "source_ref": "Q232771·P571", "license": "CC0"},
  "dynasty_context": {"dynasty_zh": "北魏", "dynasty_vi": "Bắc Ngụy", "era_name": "..."},
  "static_events": []
}
```

Khi chưa có QID:
```json
{"ok": true, "status": "no_mapping", "message": "Chưa có ID xác minh..."}
```

### `places.html` (rewrite renderTimelineTab)

- Thay toàn bộ "T21 pending" stub bằng real render
- Hiển thị: founding year (font lớn) + dynasty context (Bắc Ngụy / Bắc Ngụy) + heritage badges
- Thêm `_renderStaticEvents()` cho BGIS/Marcus data
- Source badges: `[Wikidata · Q232771·P571]` `[DILA · time_periods]`
- Fallback no_mapping: hiển thị thông báo, không crash

---

## SPARQL Seed Chi Tiết

Query: `wdt:P1188 ?dila_id` (DILA Property Bridge)
- Wikidata trả 151 entries
- 148 có dila_id hợp lệ (prefix PL)
- 72 có P571 (founding date) được seed vào `place_timeline_events`
- 1 updated (Thiếu Lâm đã có từ manual seed)

Sample geo_cross_ref:
```
PL000000023255 → Q232771 (Thiếu Lâm Tự, manual)
PL000000000063 → Q902 (year=1971)
PL000000000074 → Q62454 (year=557)
PL000000000075 → Q551067 (year=557)
```

---

## Giai Đoạn 4 Còn Lại (BGIS ETL)

BGIS `china_bgis_fme.zip` từ Harvard Dataverse chưa download. Cần:
1. Download từ: https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/VAYEUZ
2. Verify field "Starting year" = historical founding hay modern registration
3. ETL spatial join GPS ±0.5km → `place_timeline_events`

---

## Cần Restart Server

Code trong `app.py` đã cập nhật nhưng Flask server (PID 17640, port 5000) đang chạy code cũ.

```powershell
# Restart app.py (chạy từ thư mục daoanh/)
Stop-Process -Id 17640 -Force
Start-Process python -ArgumentList "app.py" -RedirectStandardOutput "app_local.log" -RedirectStandardError "app_local.err" -NoNewWindow
```

Sau restart: test `GET http://localhost:8080/daoanh/api/places/PL000000023255/timeline`  
Expected: `{"ok":true,"status":"ok","founding":{"year":495,...}}`
