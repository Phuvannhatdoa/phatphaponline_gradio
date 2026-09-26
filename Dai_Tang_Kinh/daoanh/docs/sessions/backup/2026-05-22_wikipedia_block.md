# Session: Wikipedia integration — sidebar block + cache DB + CC BY-SA

**Date:** 2026-05-22
**Task:** Thêm block Wikipedia (CC BY-SA) cho mỗi địa danh, fetch tự động từ tên Việt DILA, cache vào DB.

## Thiết kế

### DB — bảng mới `place_wiki_snapshots`

```sql
CREATE TABLE place_wiki_snapshots (
  place_id TEXT PRIMARY KEY,
  wiki_title TEXT,
  wiki_url TEXT,
  snippet TEXT,
  full_text TEXT,
  source TEXT DEFAULT 'wikipedia',
  license TEXT DEFAULT 'CC BY-SA 4.0',
  created_at TEXT,
  updated_at TEXT
);
```

### Backend — `POST /daoanh/api/admin/wiki/fetch`

**Input:** `{place_id, name_vi, name_zh}`

**Logic:**
1. Kiểm tra cache → nếu có return ngay
2. Gọi Wikipedia API (vi.wikipedia.org) với `name_vi` + User-Agent header
3. Nếu tìm thấy → lấy snippet + full extract (intro paragraph)
4. Nếu không tìm thấy tiếng Việt → thử zh.wikipedia với `name_zh`
5. Save snapshot vào DB (upsert)
6. Response luôn 200

**Response:**
- `has_wiki: true` → `{has_wiki, wiki_title, wiki_url, snippet, cached_at}`
- `has_wiki: false` → `{has_wiki: false}`
- `missing_place_id` → `{has_wiki: false, error: "missing_place_id"}`

### Frontend — `admin/placevn.html`

- State: `wikiData` (null/loading/has_wiki/no_wiki), `wikiLoading`
- Nút "Tra Wikipedia" khi chưa fetch
- Loading → "Đang tra Wikipedia..."
- Có kết quả → title (link), snippet, cached_at, **disclaimer**
- Không kết quả → "Không tìm thấy" + nút thử lại
- Disclaimer cuối mỗi block: "Tham khảo từ Wikipedia (CC BY-SA). Text chính thức cho GIS: bản dịch riêng trong DB Đạo Ảnh."

### Các item 1 & 2 (CBDB/CBETA API) — đã xong session trước

Không thay đổi gì thêm.

## Kết quả test

```
POST /wiki/fetch {"name_vi":"Chùa Thiếu Lâm","name_zh":"少林寺"}
→ {"has_wiki":true, "wiki_title":"Chùa Thiếu Lâm", "wiki_url":"https://vi.wikipedia.org/wiki/Chùa_Thiếu_Lâm", ...}

POST /wiki/fetch (cached)
→ {"has_wiki":true, "cached_at":"2026-05-22 15:54:10", ...}

POST /wiki/fetch {"name_vi":"xyz_notfound_12345"}
→ {"has_wiki":false}

POST /wiki/fetch {"name_vi":"test"} (missing place_id)
→ {"has_wiki":false, "error":"missing_place_id"}
```

## Liên hệ ROADMAP

- **Nguồn liên quan:** Wikipedia (tham khảo đa ngữ) — mới thêm vào "Nguồn tiềm năng"
- **Khoá ROADMAP:** Khoá 1 – Xong core Hán → Việt
- **Lưu ý:** Wikipedia là tham khảo phụ (CC BY-SA). Text chính thức GIS là bản dịch riêng của Đạo Ảnh.

## Files changed

- `app.py` — + route `POST /wiki/fetch` (~80 dòng)
- `admin/placevn.html` — + sidebar block Wikipedia + state + handler
- `data/lineage.db` — + bảng `place_wiki_snapshots`
- `docs/roadmap.md` — thêm Wikipedia vào bảng "Nguồn tiềm năng"
- `docs/progress.md` — cập nhật tiến độ
- `docs/db_schema.md` — (cập nhật nếu cần)
- `docs/sessions/2026-05-22_wikipedia_block.md` — session log (new)

## Test command

```bash
curl -s -X POST "http://localhost:5000/daoanh/api/admin/wiki/fetch" \
  -H "Content-Type: application/json" \
  -d '{"place_id":"PL123","name_vi":"Chùa Thiếu Lâm","name_zh":"少林寺"}'
```
