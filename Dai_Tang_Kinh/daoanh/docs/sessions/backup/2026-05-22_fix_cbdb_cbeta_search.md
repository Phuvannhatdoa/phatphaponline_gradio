# Session: Fix CBDB response format + CBETA search error handling

**Date:** 2026-05-22
**Task:** CBDB trả 200 có `cbdb_places` array; CBETA search standardize error; frontend align

## Vấn đề

1. **CBDB API**: Response format cũ dùng fields flat (`name_zh`, `admin_type`). Cần chuyển sang `cbdb_places[]` array để chuẩn bị cho multi-match.
2. **CBETA search**: Error response message `"cbeta_db_connection_failed"` không khớp spec. Cần `"cbeta_internal_error"`. Thêm `error: false` vào no-results response.
3. **Frontend CBDB block**: Dùng `cbdbData.name_zh` cũ, cần dùng `cbdbData.cbdb_places[0].name_zh`.

## Thay đổi

### Backend (`app.py`)

**CBDB lookup** (`GET /places/<place_id>/cbdb`):
- No mapping → `{"has_cbdb": false, "place_id": "...", "cbdb_places": []}`
- Has mapping → `{"has_cbdb": true, "place_id": "...", "cbdb_places": [{name_zh, admin_type, notes_zh, cbdb_addr_id}]}`
- Xoá HTTP 500 cho exception → trả luôn 200 với `error` field

**CBETA search-place + search-person**:
- `"message": "cbeta_db_connection_failed"` → `"cbeta_internal_error"`
- No-results response thêm `"error": false`

### Frontend (`admin/placevn.html`)

- CBDB render block: map `cbdbData.cbdb_places[]` thay vì fields flat
- Dùng `.map()` để render array (dù hiện tại chỉ có 1 item)

## Kết quả test

```
GET /places/PL000000000003/cbdb
→ {"has_cbdb": false, "place_id": "PL000000000003", "cbdb_places": []}

GET /places/PL000000000367/cbdb  
→ {"has_cbdb": true, "place_id": "PL000000000367", "cbdb_places": [{"name_zh":"南京",...}]}

POST /cbeta/search-place (no results)
→ {"error": false, "has_cbeta": false, "results": [], "total": 0, "message": "no_match"}
```

## Liên hệ ROADMAP

- **Nguồn liên quan:** CBDB (China Biographical Database) + CBETA (Hán tạng số)
- **Khoá ROADMAP:** Khoá 1 – Xong core Hán → Việt
- **Dòng:** "CBETA pipeline (person/place → canon_citations + snippets dịch)", "CBDB — Prosopography"

## Files changed

- `app.py` — CBDB response format + CBETA error messages
- `admin/placevn.html` — CBDB render dùng `cbdb_places` array
- `docs/sessions/2026-05-22_fix_cbdb_cbeta_search.md` — session log (new)

## Test command

```bash
curl -s "http://localhost:5000/daoanh/api/admin/places/PL000000000367/cbdb"
curl -s -X POST "http://localhost:5000/daoanh/api/admin/cbeta/search-place" -H "Content-Type: application/json" -d '{"place_name":"xyz_notfound_123"}'
```
