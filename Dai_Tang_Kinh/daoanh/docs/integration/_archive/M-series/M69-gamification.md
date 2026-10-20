# M69 · Mindfulness Gamification System

**Spec · P2**

# M69 Hệ thống Gamification Thiền tập

Cung cấp hệ thống gamification cho practice thiền: hệ thống điểm, bảng xếp hạng, và thành tựu để khuyến khích practice hàng ngày theo hướng Phật giáo.

## Mục đích

Thực hiện gamification dựa trên các nguyên tắc Phật giáo: cho phép sinh viên, tăng ni ghi nhận tiến độ thiền, đạt được thành tựu (meditation streak,_duration targets), và tham gia vào các compétition Phật giáo có giám sát.

## UI/UX

- **Trang Thống kê practice:** `/daoanh/gamification/stats`
  - Hiển thị tiến độ: Số ngày liên tục (streak), tổng thời gian thiền, số lượng đoạn kinh đã đọc
  - Biểu đồ tiến độ: Đồ thị theo ngày/tuan/thang
  - Thành tựu khóa khóa: Mở khóa badge khi đạt ngưỡng

- **Trang Danh bảng xếp hạng:** `/daoanh/gamification/leaderboard`
  - Xếp hạng theo: Ngày hôm nay, Tuần này, Tháng này, Năm nay
  - Lọc: Toàn cầu, Theo nước, Theo nhà trang
  - Xuất bảng: PDF xuất bảng xếp hạng

- **Trang Thanh tắc thành tựu:** `/daoanh/gamification/badges`
  - Danh sách thành tựu có thể đạt: "30 ngày thiền liên tục", "Đọc 100 đoạn kinh", "Thiền 100 giờ"
  - Trạng thái: Đã đạt/chưa đạt, tiến độ tới mục tiêu
  - Xuất bản: Chia sẻ thành tựu lên mạng xã hội Phật tử

- **Trang Cài đặt:** `/daoanh/gamification/settings`
  - Chọn chế độ: Thông thường, Compétition, Riêng tư
  - Thiết lập mục tiêu cá nhân: Thời lượng thiền mục tiêu mỗi ngày
  - Thông báo: Kích hoạt nhắc nhở hàng ngày qua push notification

## Dữ liệu

- **Con số practice:** Ngày thiền, phút thiền, đoạn kinh đã đọc, thành tựu đã đạt
- **Thành tựu:** 50+ badge khác nhau kèm điều kiện mở khóa
- **Xếp hạng:** Top 10, Top 100, Top 1000 theo thời gian thực
- **Thông báo:** Push notification khi đạt mục tiêu, nhắc nhở thiền hàng ngày

## Acceptance criteria

- [ ] Tăng practice hàng ngày 40% qua gamification
- [ ] Khóa được 80%+ badge có sẵn cho user tích cực
- [ ] Tăng retention user 30% qua hệ thống/badge
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không chia sẻ thông tin practice với bên thứ ba

## File tương tự

- `docs/integration/M69-gamification.md`
- `docs/Mimo-Flash/T144-m69-gamification.md`