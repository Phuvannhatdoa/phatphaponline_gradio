# M33 · Trình theo dõi Thiền và Nhận thức cho Cử Nhân

**Spec · P1**

# M33 Hệ thống theo dõi Thiền cá nhân

Cung cấp ứng dụng theo dõi thiền cá nhân: thời gian thiền, loại thiền, mức độ tập trung, và biểu đồ tiến trình cho trình độ Cử Nhân.

## Mục đích

Giúp người dùng Cử Nhân xây dựng thói quen thiền thường xuyên, theo dõi tiến độ cá nhân, và giữ nguyên động lực qua các biểu đồ và nhắc nhở.

## UI/UX

- **Trang Thời gian thiền:** `/daoanh/mindfulness/time`
  - Hiển thị: Tổng thời gian thiền hôm/năm/tháng
  - Biểu đồ: Theo ngày, theo tuần, theo tháng
  - Thông kê: Số buổi thiền, thời gian trung bình mỗi buổi

- **Trang Loại thiền:** `/daoanh/mindfulness/type`
  - Chọn loại: Kinh thiền, Tâm tiến, Scan cơ 신체, Từ định
  - Lọc theo thời gian: 5 phút, 10 phút, 20 phút, 30 phút, hơn

- **Trang Theo dõi tiến độ:** `/daoanh/mindfulness/progress`
  - Biểu đồ tiến trình: Ngày liên tục thiền, mục tiêu hàng tuần
  - Nhắc nhở: Thiết lập nhắc nhở hàng ngày
   - Hành ký: Ghi nhận "xong ngày" để duy trì streak

## Dữ liệu

- **Sự kiện thiền:** Thời gian bắt đầu/ket thúc, loại thiền, durée
- **Thẻ đánh giá:** Mức tập trung 1-10, trạng thái tinh thần sau thiền
- **Streak:** Số ngày liên tục thiền (cập nhật mỗi ngày lúc 23:59)
- **Mục tiêu cá nhân:** Thời lượng/tháng mà user tự thiết lập

## Acceptance criteria

- [ ] Hiển thị đúng tổng thời gian thiền và số buổi
- [ ] Biểu đồ tiến độ cập nhật hàng ngày
- [ ] Nhắc nhở được thiết lập và kích hoạt đúng theo cài đặt
- [ ] Streak tính đúng (không tính lại nếu user thay đổi ngày hệ thống)
- [ ] Tự động lưu dữ liệu mỗi khi kết thúc session thiền

## File tương tự

- `docs/integration/M33-meditation-tracker.md`
- `docs/Mimo-Flash/T108-m33-meditation-tracker.md`