# M25 · Thông báo Thánh ngày và Lịch tiết cho Cử Nhân

**Spec · P1**

# M25 Hệ thống thông báo Thánh ngày Phật giáo

Cung cấp thông báo tự động cho các ngày Thánh, tiết, và các ngày quan trọng trong lịch Phật giáo, giúp người dùng không错过 các kiện lễ, tu práctica đặc biệt.

## Mục đích

Đồng bộ lịch Phật giáo với lịch trình cá nhân, gửi nhắc nhở qua ứng dụng, email, hoặc push notification để người dùng tham gia các kiện lễ, tu práctica theo đúng традиция.

## UI/UX

- **Trang Lịch Thánh ngày:** `/daoanh/calendar/holy-days`
  - Hiển thị toàn bộ lịch năm (365/366 ngày)
  - Màu sắc phân biệt: Thánh ngày (vàng), Tiết (xanh), Ngày thường (trắng)
  - Click vào ngày: Xem thông tin tiết, Lễ tiễn, Cách tham gia

- **Trang Cài đặt nhắc nhở:** `/daoanh/calendar/settings`
  - Chọn các loại thông báo: Email, SMS, Push notification
  - Chọn ngày: Tất cả Thánh ngày, Các tiết quan trọng, Chỉ ngày chủ Nhật
  - Thiết lập thời gian提前提醒: 1 ngày, 3 ngày, 1 tuần trước

- **Trang Lịch cá nhân:** `/daoanh/calendar/personal`
  - Lịch riêng của user: Những ngày user đã lưu ý
  - Nhập ngày lễ gia đình, sinh nhật Hồ regularly
  - Đồng bộ với Google Calendar, Apple Calendar

## Dữ liệu

- **Lịch Phật giáo:** DILA calendar (366 tiết, 108 Thánh ngày chính)
- **Cờ kênh:** Email, SMS, Push notification (tùy chọn user)
- **Thông báo:** Tiêu đề, nội dung ngắn, link đến tiết/Kinh cần đọc
- **Cấp phép:** Tuân thủ quy tắc gửi thông báo (không spam, tối đa 1/c ngày)

## Acceptance criteria

- [ ] Lịch hiển thị đúng 366 ngày (năm nhuận có 29 ngày tháng 2)
- [ ] Thông báo gửi đúng theo cài đặt của user (không gửi nếu tắt)
- [ ] Đồng bộ với Google Calendar/Apple Calendar trong 5 phút
- [ ] Tốc độ tải lịch năm < 2s
- [ ] Tối đa 1 thông báo/c ngày (không spam user)

## File tương tự

- `docs/integration/M25-holy-days-notifications.md`
- `docs/Mimo-Flash/T100-m25-holy-days-notifications.md`