# M26 · Hệ thống quản lý giờ lên viện/thiền cho Tiến sĩ

**Spec · P2**

# M24 Quản lý lịch trình tu prática và giờ thiền

Cung cấp hệ thống quản lý lịch trình chi tiết cho chùa, tự viện: giờ lên viện, giờ thiền, giờ ăn trưa, và lịch các kiện lễ quan trọng.

## Mục đích

Tối ưu hóa quy trình vận hành chùa, đảm bảo các buổi thiền và tu práctica diễn ra đúng giờ, có lịch trình rõ ràng cho các phương tu và khách du lịch.

## UI/UX

- **Trang Lịch chùa:** `/daoanh/temple/schedule`
  - **Hàng ngày:** Giờ lên viện (5:00), Giờ thiền trưa (10:00), Giờ ăn trưa (12:00), Giờ thiền buổi chiều (16:00)
  - **Tuần:** Lịch các tiết, Thánh ngày, Các kiện lễ tiễn theo lunar calendar
  - **Tháng:** Lịch các hội Phật, Hội theo chủ nghĩa Phật giáo lớn

- **Trang Cài đặt lịch:** `/daoanh/temple/settings`
  - Thiết lập giờ cho mỗi hoạt động (tùy chỉnh cho từng chùa)
  - Lập lịch lại khi có thay đổi (kịch bản, tiết tấu)
  - Cảnh báo nếu chập chùng lịch (ví dụ: giờ thiền trùng giờ ăn)

- **Trang Thông báo:** `/daoanh/temple/alerts`
  - Thông báo khi có thay đổi lịch (nhắn tin cho tất cả monks, volunteers)
  - Xem lịch lịch sử: lịch đã thay đổi trước đây, ai thay đổi, lúc nào

## Dữ liệu

- **Lunar calendar:** DILA lunar calendar (29/30 ngày/tháng, 12 tháng/năm)
- **Lịch sửa:** Giờ hoạt động chùa (54 lịch hoạt động phổ biến)
- **Nhắc nhở:** Push notification, Email 30 phút trước mỗi hoạt động
- **Người dùng:** Monks (thầy tọt), volunteers (khách tu prática), Tourists (khách du lịch)

## Acceptance criteria

- [ ] Lịch hiển thị đúng theo lunar calendar (366 ngày/năm)
- [ ] Thiết lập giờ hoạt động tùy chỉnh cho từng chùa
- [ ] Nhắc nhở gửi đúng 30 phút trước giờ hoạt động
- [ ] Cảnh báo chập chùng lịch hoạt động đúng
- [ ] Tích hợp với hệ thốngpush notification có thể bật/tắt

## File tương tự

- `docs/integration/M26-temple-schedule-management.md`
- `docs/Mimo-Flash/T101-m26-temple-schedule-management.md`