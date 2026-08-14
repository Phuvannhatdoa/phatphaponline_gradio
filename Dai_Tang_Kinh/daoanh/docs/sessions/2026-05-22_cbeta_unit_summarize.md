# Session: Cải tiến block Nguồn dẫn Đại Tạng Kinh — [Chi tiết] + han_text + LLM summary

**Date:** 2026-05-22
**Task:** Thay nút [Chi tiết] cho mỗi citation CBETA, load on-demand full unit text + LLM tóm tắt

## Thiết kế

### Backend: 2 routes mới

**1. `GET /daoanh/api/admin/cbeta/unit?id=X77n1524_p0484c06`**

| Case | Response |
|------|----------|
| File chưa import | `{"has_local": false, "message": "CBETA X77n1524 chưa được import"}` |
| File có, tìm thấy div | `{"has_local": true, "id", "sigla", "work", "section", "han_text"}` |
| File có, page not found | `{"has_local": false, "error": "page_not_found"}` |

Tái sử dụng logic `cbeta_snippet` (parse ID → parent_map → enclosing `<cb:div>`). Khác biệt:
- Trả `han_text` (full unit text, truncate 50000 chars)
- Trả `work` (từ DB cbeta_texts) + `section` (từ `<head>` trong div)
- Ko trả `preview`/`has_full` (frontend tự xử lý preview via `slice(0,300)`)
- Ko auto-fetch — chỉ load khi user click [Chi tiết]

**2. `POST /daoanh/api/admin/llm/summarize`**

Body: `{"han_text": "...", "place_name": "Thiếu Lâm Tự"}`

Pipeline:
1. Gemini 2.0 Flash (prompt: "Tóm tắt 3-5 câu về địa danh X")
2. Fallback: GoogleTranslator (deep-translator)
3. Last fallback: trả 500 ký tự raw

Response: `{"summary_vi": "...", "provider": "gemini-2.0-flash|google-translate|fallback"}`

### Frontend: thay đổi kiến trúc

**Xoá:**
- `cbetaSnippets` state (auto-fetch all on mount)
- `cbetaExpanded` state
- `cbetaParsedIds` state
- `useEffect` auto-fetch snippets (lines 751-772)

**Thêm:**
- `cbetaUnits: {[id]: {loading, unit, summary, error}}` state
- `cbetaUnitExpanded: {[id]: boolean}` state
- `handleLoadCbetaUnit(id, placeName)` — async function:
  1. Set loading=true
  2. Fetch `GET /cbeta/unit?id=...`
  3. If `has_local` → set unit → fetch `POST /llm/summarize` → set summary
  4. Error → set error message

**Render thay đổi:**
- Label: "Nguồn CBETA" → "NGUỒN DẪN ĐẠI TẠNG KINH (DILA)"
- Mỗi citation: raw text + [Chi tiết] button
- Click [Chi tiết] → loading → show panel:
  - `☸ work — section`
  - han_text (300 chars preview / full, [Xem đầy đủ] toggle)
  - "Tóm tắt tiếng Việt (LLM)" + provider badge
- Hết citation là CBETA Online link

## Kết quả test

```
GET /cbeta/unit?id=T51n2076_p0204c
→ has_local=true, work="Taishō Tripiṭaka", section="七佛天竺祖師", han_text=50000 chars

GET /cbeta/unit?id=X77n1524_p0484c06
→ has_local=false, message="CBETA X77n1524 chưa được import"

POST /llm/summarize
→ summary_vi="Chùa Thiếu Lâm được thành lập...", provider="google-translate"
  (Gemini rate-limited, fallback GoogleTranslator)
```

## Liên hệ ROADMAP

- **Nguồn liên quan:** CBETA (Hán tạng số) — Khoá 1
- **Dòng ROADMAP:** "CBETA pipeline (person/place → canon_citations + snippets dịch)"
- **Vị trí:** Đây là cải tiến UI/UX cho tính năng snippet đã có — thêm on-demand loading + LLM summary. Chưa chạm pipeline dịch Canon.

## Files changed

- `app.py` — +2 routes (`/cbeta/unit`, `/llm/summarize`) ~130 dòng
- `admin/placevn.html` — xoá auto-fetch states/effects, thêm lazy-load button + han_text panel + LLM summary render
- `docs/sessions/2026-05-22_cbeta_unit_summarize.md` — session log (new)

## Test command

```bash
curl -s "http://localhost:5000/daoanh/api/admin/cbeta/unit?id=T51n2076_p0204c" | python3 -m json.tool
curl -s -X POST "http://localhost:5000/daoanh/api/admin/llm/summarize" -H "Content-Type: application/json" -d '{"han_text":"少林寺者，後魏孝文帝所立也。","place_name":"Thiếu Lâm Tự"}'
```
