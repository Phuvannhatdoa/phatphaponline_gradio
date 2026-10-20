# M45 · Đếm mạch기도 và Thời gian Thiền cho Cử Nhân

**Spec · P1**

# M45 Trình theo dõi Đếm mạch기도

Cung cấp bộ đếm mạch기도 và thời gian thiền chuyên用于 cho trình độ Cử Nhân: đếm số buổi기도, thời lượng, và theo dõi tiến độ hàng ngày.

## Mục đích

Giúp người dùng Cử nhân duy trì practice mạch기도 hàng ngày, theo dõi thời lượng tổng thể, và thiết lập mục tiêu thực현 được.

## UI/UX

- **Trang Đếm mạch기도:** `/daoanh/mala/counter`
  - Hiển thị: Số mạch đã hoàn tất hôm/năm
  - Nút "Mạch mới": Bắt đầu mạch mới, reset số liệu
  - Thiết lập mục tiêu: 108 mạch (số mạch truyền thống), 50 mạch, tùy chỉnh

- **Trang Thời gian thiền:** `/daoanh/mala/timer`
  - Đếm ngược: Thời lượng mạch (3 phút, 5 phút, 10 phút, tùy chỉnh)
  - Phát âm thanh bông khi kết thúc
  - Hiển thị thời gian đã trôi qua

- **Trang Tiến độ:** `/daoanh/mala/progress`
  - Biểu đồ: Số mạch hôm/tháng/năm
  - Thống kê: Thời gian tổng thể, thời gian trung bình mỗi mạch
  - Mục tiêu: Đạt % mục tiêu đã thiết lập

## Dữ liệu

- **Sự kiện mạch:** Thời gian bắt đầu/ket thúc, số mạch ngày, mục tiêu
- **Mục tiêu:** Số mạch định kỳ (108, 50, tùy chỉnh)
- **Thời lượng:** Tổng thời gian mạch, thời gian trung bình
- **Streak:** Số ngày liên tục thực hiện mạch

## Acceptance criteria

- [ ] Đếm mạch hoạt động đúng và lưu trữ số liệu hằng ngày
- [ ] Thiết lập mục tiêu tùy chỉnh hoạt động đúng
- [ ] Phát âm thanh bông khi kết thúc mạch
- [ ] Biểu đồ tiến độ cập nhật hàng ngày
- [ ] Streak tính đúng (không tính lại nếu thay đổi ngày hệ thống)

## File tương tự

- `docs/integration/M45-mala-counter.md`
- `docs/Mimo-Flash/T120-m45-mala-counter.md`