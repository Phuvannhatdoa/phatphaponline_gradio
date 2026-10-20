# M16 · Buddhist Social Media Integration

**Status:** 📄 Consolidated Documentation  
**Module:** M16  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp tích hợp mạng xã hội cho cộng đồng Phật tử: chia sẻ nội dung Phật học, kết bạn cùng práctica, và theo dõng hoạt động cộng đồng lên mạng xã hội.

## UI/UX

- **Trang Chia sẻ nội dung:** `/daoanh/social/share`
  - Input: Đoạn Kinh, giáo Thái, hoặc hình ảnh cần chia sẻ
   - Chọn nền tảng: Facebook, Twitter, Instagram, Telegram
   - Kết quả: Link chia sẻ, preview nội dung, số lượt xem

- **Trang Kết bạn:** `/daoanh/social/friends`
  - Hiển thị người dùng có thể kết bạn: Tên,.avatar,brief info
   - Hành động: Gửi yêu cầu kết bạn, xem hồ sơ

- **Trang Theo dõng hoạt động:** `/daoanh/social/activity`
  - Hiển thị hoạt động gần đây: Bài đăng, retreat, nghi lễ
   - Theo dõng: Ai đã theo dõng, like, comment

- **Trang Cài đặt:** `/daoanh/social/settings`
  - Chọn nền tảng kết nối: Kết nối Facebook, Twitter, Instagram, v.v.
   - Thiết lập quyền chia sẻ: Công khai, bạn bè, riêng tư
   - Thông báo: Kích hoạt thông báo mới

## Dữ liệu

- **Nền tảng hỗ trợ:** Facebook, Twitter, Instagram, Telegram
- **Loại nội dung:** 10+ loại nội dung Phật học có thể chia sẻ
- **Hoạt động:** 1000+ hoạt động gần đây được ghi nhận
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Chia sẻ nội dung đúng 80% lên nền tảng đã chọn
- [ ] Kết bạn hiển thị đúng 75% người dùng có sẵn
- [ ] Theo dõng hoạt động đúng 85% cho hoạt động đã tổ chức
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không chia sẻ thông tin cá nhân với bên thứ ba ngoài nền tảng mạng xã hội

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `shareContent(content, platform)` - Chia sẻ nội dung lên nền tảng
2. `getFriendsList()` - Lấy danh sách bạn có thể kết nối
3. `getRecentActivity()` - Lấy hoạt động gần đây
4. `getSocialSettings()` - Lấy cài đặt mạng xã hội

**File path:** `docs/Mimo-Flash/M16-social-media-integration-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), API kết nối mạng xã hội