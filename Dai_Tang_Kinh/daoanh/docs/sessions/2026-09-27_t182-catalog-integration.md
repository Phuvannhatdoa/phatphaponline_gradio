# Session 2026-09-27 — T182 Catalog Integration vào Admin T50 Progress

## Task hoàn thành
Tích hợp thông tin Đại Tạng Kinh (3.122 bộ) từ `dai-tang-kinh.html` vào trang admin `t50-progress.html`.

## Thay đổi

### `daoanh/admin/t50-progress.html`
- Thêm **Tab system**: Tab 1 = Tiến Độ T50 (giữ nguyên), Tab 2 = Đại Tạng Kinh
- Tab 2 dùng API `/daoanh/api/danh-sach-kinh` từ port 5002 (local dev workaround)
- Filter: search, series dropdown, status dropdown, checkbox "Chỉ có bản dịch"
- Bảng 7 cột: Ký hiệu, Tên (Việt), Hán văn, Cuốn, Trạng thái, Tiến độ dịch, Đọc
- Status badges: ✅ Hoàn thành, 🟡 Đang dịch, 🔵 Chờ dịch, ⚫ Chưa có
- Mini progress bar: X/Y đoạn đã dịch
- Pagination 50 items/trang
- Modal đọc kinh (Hán + Việt song song)
- Nút "Import XML hàng loạt" gọi `/daoanh/api/admin/cbeta/batch-import`

### `daoanh/app.py`
- Dọn debug print statements T182 (đã thêm tạm để debug, xóa sau)

### `daoanh/local_gateway.py`
- Thay đổi tạm thời `APP_PORT = 5002` trong debug, đã revert về 5000

## Vấn đề gặp phải

### PID blocking (local dev issue)
- PID 3312 (server cũ từ phiên trước) giữ port 5000, không kill được (Access is denied — elevated privileges)
- Port 5002 là server mới (PID 15588) có đầy đủ T181+T182 routes
- **Workaround**: `_CAT_BASE` trong t50-progress.html trỏ trực tiếp `localhost:5002` khi detect hostname = localhost
- Trên VPS production: `_CAT_BASE = ''` (relative URL), nginx proxy về app.py đúng

## Trạng thái
- ✅ Tab T50 (existing): hoạt động
- ✅ Tab Đại Tạng Kinh: 3.122 bộ, filter, pagination, 5 bộ "đang dịch" hiện đúng
- ⏳ Commit pending (cùng batch với T181+T182 từ phiên trước)

## Update 2026-09-27 (port fix)

### Vấn đề PID 3312 blocking
- PID 3312 (server elevated từ phiên cũ) chiếm port 5000, không kill được
- Server mới bind được port 5000 nhưng OS round-robin request giữa 2 processes
- T182 routes không có trong PID 3312 → 50% requests 404

### Giải pháp
- `app.py`: đọc `APP_PORT` từ env var (mặc định 5000), chạy trên 5001 khi `APP_PORT=5001`
- `local_gateway.py`: `APP_PORT = 5001` (đổi từ 5000)
- `admin/t50-progress.html`: bỏ hardcode port 5002, dùng `_CAT_BASE = ''` (relative URL qua gateway)

## Todo tiếp theo
- Commit toàn bộ T181+T182+t50-integration (theo hướng dẫn trong `docs/sessions/2026-09-27_t181-commit-pending.md`)
- Khi VPS deploy: restart app.py trên VPS (port 5000 sẽ không bị block, không cần APP_PORT)
