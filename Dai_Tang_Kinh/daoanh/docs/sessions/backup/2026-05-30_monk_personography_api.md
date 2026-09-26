# Session: monk_dict + monk_name_index + ETL + API — Personography for Đạo Ảnh

**Date:** 2026-05-30
**Task:** `feat: monk personography — schema, ETL, API, test`

## Liên hệ ROADMAP

- **Nguồn liên quan:** DILA Authority (Person) + CBETA (Hán tạng số)
- **Khoá ROADMAP:** Khoá 1 – Xong core Hán → Việt
- **Dòng ROADMAP tương ứng:**
  - "DILA Authority (Person/Place/Time): Authority Phật học cho nhân vật & địa danh trong Phật điển Hán"
  - "Hoàn thiện mapping DILA ↔ people/places, nối với CBETA (canon_citations) và Marcus SNA"

## Tóm tắt

Tạo 2 bảng `monk_dict` và `monk_name_index` trong lineage.db để phục vụ personography mapping cho Đạo Ảnh. Viết ETL script sync `monk_dict → monk_name_index` với normalize (bỏ dấu + lowercase). Triển khai 3 API endpoints cho tra cứu nhân vật. Test với 2 record mẫu (玄奘/Huyền Trang, 菩提達磨/Bồ Đề Đạt Ma).

## Thiết kế / Giải pháp

### Database

**Bảng `monk_dict`** — master authority cho nhân vật Phật giáo:
- `id` (PK), `dila_id` (UNIQUE), `han_name`, `vn_name`, `pinyin`
- `alt_han_names` (JSON array), `vn_aliases` (JSON array)
- `era`, `dynasty`, `role_main`, `role_alt`, `biography`, `refs` (JSON)
- `source`, `status` (pending/approved/rejected), `created_at`, `updated_at`

**Bảng `monk_name_index`** — search index với normalized:
- `id` (PK), `monk_id` (FK → monk_dict.id)
- `lang` (zh/vi/pinyin/san/other), `name_form`, `name_type` (official/alias)
- `normalized` (bỏ dấu + lowercase)
- Index trên `(monk_id)` và `(normalized)`
- `INSERT OR IGNORE` tránh duplicate

### ETL — `scripts/sync_monk_names.py`

- Đọc tất cả `monk_dict WHERE status='approved'`
- Xoá index cũ → insert lại đầy đủ
- Với mỗi monk:
  - `han_name` → `(zh, official)`
  - `vn_name` → `(vi, official)`
  - `pinyin` → `(pinyin, official)`
  - `alt_han_names[]` → `(zh, alias)`
  - `vn_aliases[]` → `(vi, alias)`
- Normalize: NFD decomposition → remove combining marks → đ→d, Đ→d → lowercase → trim

### API — 3 endpoints trong `app.py`

| Endpoint | Vị trí | Mô tả |
|----------|--------|-------|
| `GET /daoanh/api/monk/<dila_id>` | ~6972 | Full profile với danh sách names |
| `GET /daoanh/api/monk/<dila_id>?view=tooltip` | ~6972 | Rút gọn (han_name, vn_name, pinyin, dynasty, role) |
| `GET /daoanh/api/monk/search?q=<query>&limit=20` | ~7016 | Prefix search trên `normalized`, join với `monk_dict`, group theo monk |

### Test data

| DILA ID | Han | Việt | Names indexed |
|---------|-----|------|---------------|
| A000294 | 玄奘 | Huyền Trang | 15 (zh+vi+pinyin) |
| A001361 | 菩提達磨 | Bồ Đề Đạt Ma | 22 (zh+vi+pinyin) |

## Files changed

| File | Change |
|------|--------|
| `data/lineage.db` | + bảng `monk_dict`, + bảng `monk_name_index`, + test records |
| `scripts/sync_monk_names.py` | Mới — ETL script |
| `app.py` | + 3 routes: `/daoanh/api/monk/<id>`, `/daoanh/api/monk/search` |
| `docs/db_schema.md` | Cập nhật schema |
| `docs/pipelines.md` | Cập nhật pipeline mới |

## Test commands

```bash
# ETL
python3 scripts/sync_monk_names.py

# API — full profile
curl -s http://localhost:5000/daoanh/api/monk/A000294 | python3 -m json.tool

# API — tooltip
curl -s 'http://localhost:5000/daoanh/api/monk/A001361?view=tooltip' | python3 -m json.tool

# API — search by Chinese
curl -s 'http://localhost:5000/daoanh/api/monk/search?q=玄奘' | python3 -m json.tool

# API — search by normalized Vietnamese
curl -s 'http://localhost:5000/daoanh/api/monk/search?q=huyen' | python3 -m json.tool

# Pipeline
npm run pipeline
```

## Test results

```
❯ python3 scripts/sync_monk_names.py
  [1] 玄奘: 15 names indexed
  [2] 菩提達磨: 22 names indexed
✅ Done: 2 monks, 37 names indexed

❯ API tests (5 endpoints)
✅ GET /daoanh/api/monk/A000294 → 200, full profile + 15 names
✅ GET /daoanh/api/monk/A001361?view=tooltip → 200, 6 fields
✅ GET /daoanh/api/monk/search?q=玄奘 → 200, 1 result (matched: zh)
✅ GET /daoanh/api/monk/search?q=dat → 200, 1 result (matched: vi alias)
✅ GET /daoanh/api/monk/search?q=bodhi → 200, 1 result (matched: pinyin)
```

## Kết luận

Pipeline personography mapping hoạt động đúng spec. Sẵn sàng cho:
- Seed thêm dữ liệu từ `people` table hoặc `persons.json` (48K+ records)
- Tích hợp frontend (tooltip trên map, search box)
- Mở rộng API (thêm bộ lọc dynasty, role, sorting)
