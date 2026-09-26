# Session: Replace CBETA search with DILA-based snippet loading

**Date:** 2026-05-22
**Task:** Thay thế CBETA search bằng snippet từ DILA listbibl

## Vấn đề

Block "NGUỒN CBETA" có ô search + nút Tra, cần user gõ tên Hán. DILA đã có sẵn list citation chính xác trong `listbibl` (e.g., `( CBETA T50n2060_p0457c16 ) 唐高僧傳: 釋玄奘傳 {少林寺}`). Cần dùng list này làm authority thay vì search.

## Giải pháp

### Backend: `GET /daoanh/api/admin/cbeta/snippet?id=T50n2060_p0457c16`

Route mới parse CBETA citation ID → map sang XML local → extract context snippet.

| Case | Response |
|------|----------|
| File chưa import | `{"success": false, "error": "not_imported", "sigla": "T50n2060"}` |
| Page không tìm thấy | `{"success": false, "error": "page_not_found", "page": "p0457c16"}` |
| Thành công | `{"success": true, "sigla": "T51n2076", "snippet": "…text…", "title": "Taishō Tripiṭaka"}` |
| ID không hợp lệ | `{"success": false, "error": "invalid_id"}` |

**Cách parse CBETA ID:**
- `T50n2060_p0457c16` → sigla=`T50n2060`, canon=`T`, vol=`50`, page=`p0457c16`
- XML path: `data/cbeta/xml-p5a/T/T50/T50n2060.xml`
- Tìm `<pb n="0457c16">`, lấy context từ `<p>` elements xung quanh (~800 chars)

### Frontend: `admin/placevn.html`

- Xoá hoàn toàn search input + nút Tra
- Xoá `handleCbetaSearch` + `cbetaInputRef` + state cũ
- Thêm state mới: `cbetaSnippets: {[id]: {loading, data, error}}`, `cbetaParsedIds`
- `knowledgeData` trả thêm `cbetaIds`: parse `listbibl` với regex `/CBETA\s+([A-Z]\d+n\d+_\w+)/g`
- `useEffect`: khi `cbetaIds` thay đổi, gọi `GET /cbeta/snippet` cho từng ID
- Render: mỗi citation → icon amber + raw text + snippet (loading / not_imported / page_not_found / success)

## Kết quả test

```
GET /cbeta/snippet?id=T50n2060_p0457c16
→ 200 {"error": "not_imported", "sigla": "T50n2060", ...}

GET /cbeta/snippet?id=T51n2076_p0197a
→ 200 {"success": true, "snippet": "…", "sigla": "T51n2076", ...}

GET /cbeta/snippet
→ 400 {"error": "missing_id", ...}
```

## Liên hệ ROADMAP

- **Nguồn liên quan:** CBETA (Hán tạng số) — Khoá 1
- **Thay đổi kiến trúc:** CBETA block không còn search độc lập, dựa hoàn toàn vào `listbibl` của DILA.

## Files changed

- `app.py` — +1 route `GET /cbeta/snippet` (~100 dòng)
- `admin/placevn.html` — xoá search block, thêm snippet loading + render (~80 dòng thay thế)
- `docs/sessions/2026-05-22_replace_cbeta_search_with_snippet.md` — session log (new)

## Test command

```bash
curl -s "http://localhost:5000/daoanh/api/admin/cbeta/snippet?id=T51n2076_p0197a"
```
