# M58 · Tích hợp Thiết bị phát được (Wearable Integration) cho Cử Nhân

**Spec · P1**

# M58 Tích hợp Thiết bị phát được

Cung cấp tích hợp thiết bị phát được (Apple Watch, Fitbit, tương tự) cho trình độ Cử nhân: theo dõi nhịp tim, chất lượng giấc ngủ, và nhắc nhở tu pratica.

## Mục đích

Tận dụng thiết bị phát được để theo dõi các chỉ số sinh học liên quan đến tu pratica: nhịp tim trong thiền, chất lượng giấc ngủ, và cung cấp nhắc nhở dựa trên dữ liệu sinh học.

## UI/UX

- **Trang kết nối thiết bị:** `/daoanh/wearable/connect`
  - Danh sách thiết bị hỗ trợ: Apple Watch, Fitbit, Garmin, Xiaomi
  - Kết nối: Bluetooth, Wi-Fi
  - Trạng thái: Đang kết nối, Ngắt kết nối

- **Trang Dữ liệu thiền:** `/daoanh/wearable/session`
  - Hiển thị: Thời gian thiền, nhịp tim trung bình, calories burned
  - Biểu đồ: Thời gian thiền theo ngày/tuần/tháng
  - Nhạc điệu: Phát nhạc nền dựa trên nhịp tim

- **Trang Cài đặt:** `/daoanh/wearable/settings`
  - Chọn thiết bị: Apple Watch, Fitbit, Garmin, Xiaomi
  - Thiết lập ngưỡng nhắc nhở: Nhịp tim dưới X phut, giấc ngủ dưới Y giờ
  - Tùy chọn: Chuyển đổi giữa các thiết bị

## Dữ liệu

- **Dữ liệu cảm biến:** Nhịp tim, SpO2, chất lượng giấc ngủ, calories burned
- **Sự kiện thiền:** Thời gian bắt đầu/ket thúc, duración
- **Thông báo:** Thông báo nhịp tim bất thường, nhắc nhở thiền

## Acceptance criteria

- [ ] Tích hợp với Apple Watch, Fitbit hoạt động đúng 90% trường hợp
- [ ] Hiển thị đúng nhịp tim và dữ liệu cảm biến
- [ ] Cảnh báo nhịp tim bất thường hoạt động đúng
- [ ] Tương thích với iOS, Android
- [ ] Tự động lưu dữ liệu mỗi khi kết thúc session thiền

## File tương tự

- `docs/integration/M58-wearable-integration.md`
- `docs/Mimo-Flash/T133-m58-wearable-integration.md`