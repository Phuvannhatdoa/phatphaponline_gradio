# Session: Fix CBETA search 500 Internal Server Error

**Date:** 2026-05-22
**Task:** Sửa lỗi 500 ở `POST /daoanh/api/admin/cbeta/search-place`

## Vấn đề

Frontend click "Tra" CBETA → console báo `500 (INTERNAL SERVER ERROR)`.

## Nguyên nhân gốc

2 lỗi trong handler `cbeta_search_place`:

### 1. Column `text_id` không tồn tại

Handler query `SELECT ... text_id FROM cbeta_place_mentions` nhưng schema thực tế dùng `cbeta_text_sigla` (TEXT), không có `text_id`.

```sql
-- Schema actual
cbeta_place_mentions: ... cbeta_text_sigla TEXT, dila_place_id TEXT, ...
-- Handler cũ query
SELECT ... text_id FROM cbeta_place_mentions  -- SQLite error: no such column
```

### 2. Vòng lặp join không cần thiết

Handler mở `get_cbeta_conn()` cho mỗi row để JOIN `cbeta_texts` lấy sigla — trong khi sigla đã có sẵn trong `cbeta_place_mentions.cbeta_text_sigla`.

### 3. Không có fallback khi không tìm thấy

Handler chỉ trả `{"success": True, "results": [...]}` — nếu bảng mentions rỗng (0 annotated mentions trong file test), không có `has_cbeta: false` response rõ ràng.

## Sửa chữa

### File: `app.py`

**`cbeta_search_place` (line 786):**
- `text_id` → `cbeta_text_sigla AS sigla` (dùng thẳng sigla từ mentions table)
- Bỏ vòng lặp join `cbeta_texts`; thay bằng `SELECT title_zh FROM cbeta_texts WHERE sigla = ?` chỉ 1 lần nếu cần title
- Chấp nhận cả `query` lẫn `place_name` trong request body
- Empty query → trả 200 `{"has_cbeta": false, "results": [], "total": 0}`
- Thêm **LIKE fallback** sau FTS: vì FTS5 unicode61 không xử lý CJK multi-char tốt, fallback `LIKE` trên `cbeta_content_index.content_zh`
- FTS exception được catch riêng (log warning, không gây 500)
- Exception handler log `traceback` vào `app.logger.error`

**`cbeta_search_person` (line 859):**
- Sửa tương tự: `text_id` → `cbeta_text_sigla`, LIKE fallback, `has_cbeta` response, FTS try/catch

### Kết quả test

```
Test 1: {} → {"has_cbeta": false, "results": [], "total": 0} (200)
Test 2: {"query": "Thắng Cảnh Quan"} → {"has_cbeta": false, "results": [], "total": 0} (200)
Test 3: {"place_name": "釋迦文"} → {"has_cbeta": true, "results": [1 item, type: "like"]} (200)
Test 4: {"place_name": "佛", "limit": 3} → {"has_cbeta": true, "results": [3 items, types: "fts"/"like"]} (200)
```

## Liên hệ ROADMAP

- **Nguồn liên quan:** CBETA (Hán tạng số)
- **Khoá ROADMAP:** Khoá 1 – Xong core Hán → Việt
- **Dòng ROADMAP:** "CBETA — Corpus kinh văn Hán: ... Xây xong pipeline CBETA→DILA (person trước, place sau)"

## Files changed

- `app.py` — 2 handlers fixed (search-place + search-person)
- `docs/sessions/2026-05-22_fix_cbeta_search_500.md` — session log (new)

## Test command

```bash
curl -X POST http://localhost:5000/daoanh/api/admin/cbeta/search-place \
  -H 'Content-Type: application/json' \
  -d '{"place_name": "釋迦文"}'
```
