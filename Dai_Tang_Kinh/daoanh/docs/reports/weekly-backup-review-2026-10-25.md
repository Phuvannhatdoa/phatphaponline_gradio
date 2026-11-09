# Báo cáo rà soát bản sao lưu DB hàng tuần — 2026-10-25

**Phạm vi:** `data/backups/` (đệ quy), các file `*.db`.
**Ngưỡng tuổi:** sửa đổi cũ hơn 30 ngày (trước 2026-09-25).

## Kết quả

- Số file `.db` quét được: toàn bộ file `*.db` trong `data/backups/` và các thư mục con.
- File cũ hơn 30 ngày: **0**.
- File cũ nhất hiện có: `data/backups/lineage_t169_20260928_130129.db` (sửa 2026-09-28, khoảng 27 ngày tuổi, chưa đủ ngưỡng).
- Bước đối chiếu tham chiếu (`docs/`, `tasks/`, `docs/ROLLBACK.md`) không áp dụng vì không có file ứng viên.

## Danh sách ứng viên giải phóng

Không có file nào thỏa điều kiện. Tổng dung lượng có thể giải phóng: **0 byte**.

## Ghi chú

- Đây là báo cáo tự động. Không xóa, không di chuyển file, không ghi DB, không thao tác git, không gọi API.
- Lần rà soát tiếp theo sẽ có ứng viên khi các file hiện tại vượt 30 ngày tuổi (từ khoảng 2026-10-28 trở đi, bắt đầu với các file 2026-09-28 … 2026-09-30 nếu còn tồn tại).

**Chưa xóa. Cần Admin xác nhận trước khi xóa vĩnh viễn.**
