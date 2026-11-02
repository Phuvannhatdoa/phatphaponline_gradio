
## Cập nhật 2026-11-01 (điều phối)
- Đã vá vào app.py: kiểm T166 trước khi ghi cache (REVIEW_REQUIRED không tạo dòng mới), HASH_MISMATCH trả 422 trước khi gọi AI. Commit: 0c630ce8.
- Còn mở: route chạy trong monolith app.py nhưng module gốc routes_translate.py dùng app riêng (core.py). Ca dịch hợp lệ còn lỗi 500 do write_cache (style_constitution.py). Chờ Admin chọn hướng kiến trúc (T479).
- Trạng thái: in_progress (blocked). Chưa QA lại.
