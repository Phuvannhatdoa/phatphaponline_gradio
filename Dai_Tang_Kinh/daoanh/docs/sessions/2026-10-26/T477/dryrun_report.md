# T477 — Dry-run gộp namevi_map_places (2026-10-26, chỉ đọc, chưa ghi DB)

| Chỉ số | Giá trị |
|---|---|
| Dòng trong namevi_map_places | 118.298 |
| Mã địa danh sau chuẩn hóa về 12 số | 60.468 |
| Mã có trong file authority | 59.152 |
| Mã ngoài authority | 1.316 (cần xem riêng) |
| Địa danh trong authority nhưng chưa có dòng nào trong namevi | 223 |
| Cặp trùng | 57.828 |
| Cặp trùng có cùng tên Hán (an toàn gộp theo số 0) | 57.828 |
| Cặp tên Hán lệch / có ký tự lỗi `????` (giữ lại) | 2 |
| Cặp tên Việt sạch khác nhau, chưa có duyệt Admin | 8.368 |
| Cặp tên Việt đã reviewed | 5 |

Kết luận: việc chuẩn hóa mã bằng cách thêm số 0 đúng cho 57.828 cặp (tên Hán khớp).
8.368 cặp cần quy tắc chọn tên Việt hoặc Admin duyệt; không gộp tự động.
Không ghi DB. Bước tiếp theo: Admin chọn quy tắc chọn tên Việt; sau đó backup và --apply.
