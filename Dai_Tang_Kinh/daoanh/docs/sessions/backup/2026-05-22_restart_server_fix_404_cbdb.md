# Session: Restart Flask Server — Fix CBDB 404

**Date:** 2026-05-22
**Task:** Khắc phục lỗi 404 ở `/daoanh/api/admin/places/PL000000000003/cbdb`

## Vấn đề

Frontend gọi `GET /daoanh/api/admin/places/PL000000000003/cbdb` nhận HTTP 404.

## Điều tra

1. **Route `cbdb_place_lookup` đã tồn tại** trong `app.py:693` (commit `35db888` May 21).
2. **Server process cũ**: `ps aux` cho thấy server (PID 3696267) khởi động **May 20** — trước khi commit chứa CBDB route được merge. Flask đang chạy code cũ không có route.
3. **Response `has_cbdb: false` đã đúng**: Khi không có mapping (PL000000000003 = 界關, chưa có trong `place_cbdb_map`), route trả 200 với `{"has_cbdb": false}` — không cần sửa.
4. **10 mapping đã tồn tại** trong `place_cbdb_map` (長安, 洛陽, 敦煌, 開封, 涼州, 南京, 揚州, 廣州, 成都, 西域).

## Giải pháp

Restart server để nạp code mới:

```bash
fuser -k 5000/tcp && nohup python3 app.py > flask.log 2>&1 &
```

## Kết quả test

```json
GET /daoanh/api/admin/places/PL000000000003/cbdb
→ 200 {"has_cbdb": false}

GET /daoanh/api/admin/places/PL000000012849/cbdb  (長安)
→ 200 {"has_cbdb": true, "name_zh": "長安", "cbdb_addr_id": 1217, "admin_type": "Xian"}

GET /daoanh/api/admin/cbeta/stats
→ 200 {"texts": 1, "paragraphs": 3917, "fts_entries": 3917, "files_imported": 1}
```

Tất cả endpoints hoạt động. Server mới PID 4102566, khởi động 08:12.

## Liên hệ ROADMAP

- **Nguồn liên quan:** CBDB (China Biographical Database)
- **Khoá ROADMAP:** Khoá 1 – Xong core Hán → Việt (hạ tầng CBDB cho place)
- **Dòng ROADMAP:** "*CBDB — Prosopography toàn Trung Hoa: ... chỉ giữ mapping ID (person ↔ CBDB ID) và link ra CBDB*"

## Files changed

- `docs/sessions/2026-05-22_restart_server_fix_404_cbdb.md` — session log (new)
- Không có thay đổi code (chỉ restart process)

## Test

✅ `curl localhost:5000/.../cbdb` — 200
✅ `curl localhost:5000/.../cbeta/stats` — 200
✅ `ps aux` — server process mới
