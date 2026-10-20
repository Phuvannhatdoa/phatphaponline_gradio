# Session 2026-09-30 — Changes Log

## Feature — Cột TTLLocal trong namevimap.html

**Files sửa:** `daoanh/admin/namevimap.html` + `daoanh/app.py`
**Backup:** `docs/sessions/2026-09-30/namevimap.html.bak`

### Mục đích
Cho admin thấy ngay trong bảng Name Vi Map: với mỗi DILA ID, có tên thiền sư trong TTL chưa.
Ví dụ: `A000005 - 鑑堂 - Giám Đường` → cột TTLLocal show `✅ Giám Đường` nếu đã có file TTL có `dila_id=A000005`.

### app.py — API mới
Route: `GET /daoanh/api/admin/ttl-local-names`
- Đọc `vn_person_authority.{dila_id, name_vi}` (ưu tiên 1)
- Đọc `ttl_master.{dila_id, name_vi}` (ưu tiên 2, fill ID còn thiếu)
- Trả `{ok, map: {dila_id: name_vi, ...}, total}`
- Client load 1 lần on-init, lookup O(1) cho mọi row

### namevimap.html — HTML + JS
- CSS: `.ttl-local-yes` (xanh lá) + `.ttl-local-no` (muted)
- State: `var _ttlLocalMap = {}`
- Hàm `loadTtlLocalNames()` — fetch + populate map, gọi trong `init()` (non-await, song song)
- Hàm `ttlLocalCell(dilaId)` — trả HTML cell với tên TTL hoặc "—"
- **Tab 1 (Queue)**: thêm `<th>TTLLocal</th>` + cell trong `loadQueue()` + `searchNames()`; colspan 7→8
- **Tab 2 (TTL Stats)**: thêm `<th>TTLLocal</th>` + cell trong `loadTtlList()`; colspan 8→9

### Trạng thái
- Code complete.
- API 404 (server chưa restart) → graceful fallback: tất cả cells hiện "—", không crash.
- Sau khi admin restart server: cells tự điền tên từ TTL.

## Feature — Nút lọc TTLLocal trong namevimap.html Tab 1

**Files sửa:** `daoanh/admin/namevimap.html` + (backend đã sẵn trong `daoanh/app.py`)

### Mục đích
Cho admin lọc nhanh: chỉ xem 1038 vị đã có TTL, hoặc chỉ xem vị chưa có.

### namevimap.html — HTML + JS (session này)
- CSS: `.ttll-btn` + `.ttll-btn.active` (amber gold style)
- State: `let ttlLocalFilter = 'all'`
- Hàm `setTtlLocalFilter(f, btn)` — set state + active class + gọi `loadQueue(1)`
- HTML row mới giữa filter-btn và bảng:
  `🗂 Tất cả | ✅ Có TTL (N) | ○ Chưa TTL (M)` — N/M cập nhật live từ API
- `loadQueue()`: URL thêm `&ttl_local=${ttlLocalFilter}`; khi nhận response: update `#ttl-has-count` + `#ttl-no-count`

### app.py — đã sẵn (session trước)
- `admin_namevi_queue` đọc param `ttl_local=all|has|no`
- Trả thêm `ttl_has_count` + `ttl_no_count` mỗi request
- Dùng `_TTL_SUBQ` (UNION vn_person_authority + ttl_master) tránh SQLite 999-param limit

### Trạng thái
- Code complete.
- Cần restart server để test thực tế.
