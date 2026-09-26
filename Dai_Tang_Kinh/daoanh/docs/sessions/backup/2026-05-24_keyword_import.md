# Session: Keyword Import Tool (parse txt → preview → bulk insert)

**Date:** 2026-05-24

## Liên hệ ROADMAP

- **Nguồn liên quan:** Hạ tầng docs & automation, DILA/Marcus (keyword data nhập từ Word)
- **Khoá ROADMAP:** Khoá 1 — Xong core Hán → Việt
- **Dòng ROADMAP tương ứng:**
  - "Viết 1–2 prompt mẫu cho Opencode/LLM: Input: TTL gốc + metadata DILA/Marcus/CBETA"
  - "Chuẩn hoá authority (Person/Place) từ txt → DB"

## Mô tả task

Tạo admin tool cho phép:
1. Paste raw txt chú thích từ Word vào textarea
2. Click "Xử lý bằng Python & Xem trước" → Flask parse theo StarDict/2-line format
3. Preview bảng có thể sửa inline (keyword + value)
4. Click "Import vào keyword_map" → bulk insert vào SQLite

## Thiết kế / giải pháp

### Table mới: `keyword_map` trong `lineage.db`

```sql
CREATE TABLE keyword_map (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL,
    value TEXT NOT NULL,
    category TEXT DEFAULT 'import_ui',
    source TEXT DEFAULT 'manual',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### API endpoints (thêm vào `app.py`)

| Endpoint | Method | Input | Output |
|----------|--------|-------|--------|
| `/daoanh/api/admin/keywords/parse_txt` | POST | `{raw: "..."}` | `{items: [{keyword, value}], warnings: [...]}` |
| `/daoanh/api/admin/keywords/bulk_import` | POST | `{items: [...], category: "import_ui"}` | `{imported: N}` |

### Thuật toán parse (StarDict/2-line)
1. Split bằng `\n{2,}` (2+ newlines = block separator)
2. Mỗi block: line 1 = keyword, line 2+ = value
3. Block chỉ 1 dòng → warning + skip
4. Trim whitespace, skip rỗng

### Frontend: `admin/keyword_import.html`
- React + Tailwind + Babel standalone (giống pattern placevn.html)
- Session check redirect → login
- Textarea full-width → Parse button → Warnings box → Editable preview table → Import button
- Inline sửa: mỗi hàng có 2 `<input>` (keyword/value)
- Nút xoá hàng, nút xoá toàn bộ
- Toast message khi import thành công

## Danh sách file đã tạo/sửa

| File | Action |
|------|--------|
| `data/lineage.db` | Thêm table `keyword_map` |
| `app.py` | Thêm 2 route: `keywords_parse_txt`, `keywords_bulk_import` |
| `admin/keyword_import.html` | Tạo mới |
| `docs/sessions/2026-05-24_keyword_import.md` | Tạo mới |
| `docs/progress.md` | Cập nhật |
| `docs/db_schema.md` | Thêm `keyword_map` |

## Cách chạy / test

```bash
# 1. Restart Flask
pkill -f app.py && python /opt/.../daoanh/app.py &

# 2. Vào trình duyệt: /daoanh/admin/keyword_import.html
# 3. Paste:
#    Huyền Trang
#    602-664 (đời Đường, Tam Tạng Pháp Sư)
#
#    Mã Tổ Đạo Nhất
#    709-788 (thiền sư đời Đường)
#
# 4. Click "Xử lý bằng Python & Xem trước" → thấy bảng preview 2 dòng
# 5. Sửa inline nếu cần
# 6. Click "Import vào keyword_map" → toast "Đã import 2 bản ghi"
```

## Kết quả test

```
✅ lint PASSED
✅ test PASSED
✅ e2e PASSED
✅ e2e:runtime PASSED
```
