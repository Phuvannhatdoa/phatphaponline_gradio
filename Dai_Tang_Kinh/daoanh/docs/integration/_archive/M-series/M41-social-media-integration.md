# M41 · Tích hợp Mạng xã hội cho Cử Nhân

**Spec · P1**

# M41 Tích hợp chia sẻ lên Mạng xã hội

Cung cấp khả năng chia sẻ nội dung Kinh, đoạn trích, và tiến độ tu práctica lên mạng xã hội phổ biến: Facebook, Twitter, Instagram, và các nền tảng khác.

## Mục đích

Đỗ người dùng Cử nhân dễ dàng chia sẻ giá trị của kinh Phật giáo, truyền bá thông điệp, và kết nối với cộng đồng Phật tử trên các nền tảng mạng xã hội.

## UI/UX

- **Nút chia sẻ:** Hiển thị trên trang Kinh, Đoạn trích, Trang progress
  - Các biểu tượng: Facebook, Twitter, LinkedIn, Copy link
  - Pre-fill nội dung: Tiêu đề đoạn trích, Phần trích dẫn, Hashtag chủ đề (#PhậtHọc, #Thiền, #KinhĐá)

- **Trang Xem thống kê chia sẻ:** `/daoanh/social/stats`
  - Tổng chia sẻ: Tổng lượt, tăng trưởng theo thời gian
  - Nền tảng: Phân bố theo Facebook, Twitter,...
  - Phản ứng: số like/share/share được từ chia sẻ

- **Trang Cài đặt chia sẻ:** `/daoanh/social/settings`
  - Chọn nền tảng: Kích/tắt Facebook, Twitter, LinkedIn
  - Tùy chọn nội dung: Tiêu đề, Đoạn trích, Hashtag tự định nghĩa
  - Quyền truy cập: Phát phép ứng dụng truy cập hồ sơ, bài đăng

## Dữ liệu

- **Nền tảng:** Facebook Share API, Twitter Web Intent, LinkedIn Post API
- **Nội dung mặc định:** Tiêu đề Đoạn trích, Liên kết nguồn, Hashtag tự động (#Buddhism, #Quotes)
- **Phân tích:** Số lượng chia sẻ, tăng trưởng theo tuần/tháng

## Acceptance criteria

- [ ] Nút chia sẻ hiển thị đúng trên 3 màn hình: điện thoại, tablet, desktop
- [ ] Nội dung pre-fill đúng 100% cho 50 trial share
- [ ] Chia sẻ đến Facebook/Twitter thành công cho 90% trial
- [ ] Quyền truy cập được cấp phép và có thể thu hồi
- [ ] Hiển thị thống kê chia sẻ đúng (tổng lượt, nền tảng)

## File tương tự

- `docs/integration/M41-social-media-integration.md`
- `docs/Mimo-Flash/T116-m41-social-media-integration.md`