# Session: DILA Integration Layer Phase 2 (LIKE Fallback + placevn Integration)

**Date:** 2026-05-23

## Mô tả task

Phase 2 của DILA Integration Layer:
1. **LIKE fallback API**: Thêm `?mode=like` vào endpoint `/daoanh/api/entity/<id>/passages` — khi mode=like, bypass PASSAGE_ENTITY, query LIKE trên raw_text bằng alias_zh.
2. **placevn.html integration**: Thêm section "Đại Tạng dẫn chứng" trong sidebar phải của placevn.html, auto-fetch 5 passages khi chọn địa danh, có nút LIKE fallback và link đến test_entity.html.

## Liên hệ ROADMAP

- **Khoá ROADMAP:** Khoá 5 — DILA Integration Layer
- **Nguồn liên quan:** DILA (Person/Place), CBETA (text corpus)

## Thiết kế / giải pháp

### API LIKE mode

```
GET /daoanh/api/entity/<entity_id>/passages?mode=like&limit=5

→ Lấy alias_zh từ ENTITY table
→ Query: SELECT FROM passage WHERE raw_text LIKE '%alias_zh%'
→ Trả về kết quả + mode='like' trong response
```

Khi mode=linked (default): dùng PASSAGE_ENTITY (pre-built links).
Khi mode=like: LIKE search runtime, useful cho những entity không có pre-built links.

### placevn.html integration

- Auto-fetch (useEffect) khi selectedId thay đổi
- Hiển thị 5 passages đầu trong section "Đại Tạng dẫn chứng"
- Nút "LIKE" để chuyển sang LIKE mode
- Nếu không có data linked mode, hiện nút "Thử tìm bằng LIKE"
- Link "Xem tất cả N đoạn" → test_entity.html?id=PL...

## File đã sửa

| File | Trạng thái | Mô tả |
|------|-----------|-------|
| `app.py` (lines 4090-4150) | MODIFIED | Thêm mode=like vào entity_passages route |
| `admin/placevn.html` | MODIFIED | Thêm state, useEffect, handler, section mới |
| `docs/sessions/2026-05-23_dila_integration_layer_phase2.md` | NEW | Session log này |
| `docs/progress.md` | UPDATED | Cập nhật Phase 2 status |

## Cách test

### 1. LIKE API
```bash
# Linked mode (default)
curl "http://localhost:5000/daoanh/api/entity/PL000000/passages?limit=2"

# LIKE mode
curl "http://localhost:5000/daoanh/api/entity/PL000000/passages?limit=2&mode=like"
```

### 2. placevn.html
Mở browser → `/daoanh/admin/` → chọn địa danh → scroll xuống section "Đại Tạng dẫn chứng"

## Kết quả test

| Test | Result |
|------|--------|
| API linked mode | ✅ 200, returns passages from PASSAGE_ENTITY |
| API LIKE mode | ✅ 200, returns passages from LIKE match |
| API LIKE mode with short alias | ✅ 200, has_data=false, note |
| Python syntax check | ✅ OK |
| Tester agent | _pending_ |
