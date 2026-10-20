# M19 · Buddhist Mobile Integration

**Status:** 📄 Consolidated Documentation  
**Module:** M19  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp tích hợp mobile cho ứng dụng Phật học: cho phép practitioner truy cập ứng dụng qua điện thoại, nhận thông báo, và thực hành meditation di động.

## UI/UX

- **Trang Ứng dụng móvil:** `/daoanh/mobile/app`
  - Hiển thị giao diện ứng dụng được tối ưu cho màn hình nhỏ
   - Các chức năng: Meditation timer, Kinh đọc, Tracking practice

- **Trang Thông báo push:** `/daoanh/mobile/push-notifications`
  - Chọn loại thông báo: Thời gian meditation, Lễ hội, Nhật quan cá nhân
   - Thiết lập: Thời gian, nội dung, đối tượng nhận

- **Trang Offline-first:** `/daoanh/mobile/offline-first`
  - Hoạt động ngoại tuyến: Tất cả chức năng có sẵn mà không cần internet
   - Đồng bộ: Đồng bộ dữ liệu khi có internet lại

- **Trang Cài đặt:** `/daoanh/mobile/settings`
  - Chọn tính năng: Chọn tính năng hiển thị trên móvil
   - Thiết lập tài khoản: Đăng nhập/cập nhật tài khoản
   - Thông báo: Kích hoạt/dé thông báo

## Dữ liệu

- **Chức năng móvil:** 10+ chức năng tối ưu cho móvil
- **Thông báo push:** 5+ loại thông báo theo dõng
- **Hoạt động offline:** 8+ chức năng hoạt động ngoại tuyến
- **Thiết bị hỗ trợ:** iPhone, Android phones

## Acceptance criteria

- [ ] Tối ưu giao diện cho 100% màn hình móvil
- [ ] Thông báo push hoạt động đúng 90% cho các loại được chọn
- [ ] Hoạt động ngoại tuyến cho 8+ chức năng chính
- [ ] Tương thích với iPhone (iOS 12+) và Android (8.0+)
- [ ] Bảo mật dữ liệu: Mã hóa dữ liệu khi đồng bộ

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getMobileApp()` - Lấy giao diện ứng dụng móvil
2. `setupPushNotifications(options)` - Thiết lập thông báo push
3. `toggleOfflineMode()` - Chuyển đổi chế độ ngoại tuyến
4. `getMobileSettings()` - Lấy cài đặt móvil

**File path:** `docs/Mimo-Flash/M19-mobile-integration-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), mobile SDK