# M99 · Integrated Dharma Dashboard 2.0

**Spec · P2**

# M99 Tổng kết Lưới đà Phật giáo 2.0

Cung cấp Lưới đà Phật giáo tích hợp 2.0: giao diện tổng kết tất cả các module M50–M100, cho phép practitioner quản lý mọi khía cạnh practice của mình tại một nơi duy nhất.

## Mục đích

Thực hiện dashboard tích hợp 2.0: cho phép practitioner xem toàn cảnh practice của mình: meditation progress, analytics, retreat schedules, Dharma readings, và các chỉ số khác tất cả trong giao diện duy nhất, tùy chỉnh layout theo sở thích.

## UI/UX

- **Trang Dashboard chính:** `/daoanh/dashboard/integrated`
  - Widget layout tùy chỉnh: Kéo-thả các widget (Meditation tracker, Analytics, Retreat schedule, Dharma readings)
   - Hiển thị tổng quan: Tình trạng exercise hôm nay, upcoming retreats, breakthrough insights
   - Tốc truy cập nhanh: Quick access đến các module phổ biến

- **Trang Tùy chỉnh widgets:** `/daoanh/dashboard/widgets`
  - Chọn widget muốn hiển thị: Meditation, Analytics, Retreat, Dharma, Knowledge graph,...
   - Thiết lập kích thước: Kích thước widget (Nhỏ, Trung bình, Lớn)
   - Lưu bố cục: Lưu bố cục dashboard cá nhân

- **Trang Cài đặt toàn cục:** `/daoanh/dashboard/settings`
  - Chọn giao diện: Giao diện sáng, tối, tùy chỉnh
   - Thiết lập thông báo: Thông báo meditation, retreat, nieuwe insights
   - Tích hợp tài khoản: Kết nối các thiết bị cảm biến, tài khoản mạng xã hội Phật tử

## Dữ liệu

- **Widget hỗ trợ:** 20+ widget khác nhau từ các module M50–M100
- **Tổng quan practice:** Tổng hợp dữ liệu từ tất cả practice history
- **Tùy chọn layout:** 10+ bố cục dashboard được định nghĩa sẵn
- **Thời gian tải:** < 3s cho dashboard hoàn chỉnh

## Acceptance criteria

- [ ] Hiển thị được 80% widget từ modules M50–M100
- [ ] Tùy chỉnh layout thành công 90% trường hợp
- [ ] Tăng lợi dụng tính năng 40% qua dashboard tích hợp
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Chỉ hiển thị dữ liệu cho user đã xác thực

## File tương tự

- `docs/integration/M99-integrated-dharma-dashboard.md`
- `docs/Mimo-Flash/T175-m99-integrated-dharma-dashboard.md`