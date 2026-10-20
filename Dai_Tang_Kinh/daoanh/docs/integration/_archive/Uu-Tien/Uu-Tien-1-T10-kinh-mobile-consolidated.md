# M10 · Buddhist Mobile Kinh Responsive Display

**Status:** 📄 Consolidated Documentation  
**Module:** M10  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp giao diện Kinh phản ứng cho mobile: cho phép practitioner đọc Kinh trên điện thoại với định dạng tối ưu, tỷ lệ phù hợp và các tính năng nhỏ gọn.

## UI/UX

- **Trang Đọc Kinh trên mobile:** `/daoanh/kinh/mobile`
  - Hiển thị đoạn Kinh: Văn bản lớn, đoạn ngắn, tương contraste cao
   - Điều chỉnh: Kích thước chữ, khoảng cách dòng,背景 màu

- **Trang Cài đặt hiển thị:** `/daoanh/kinh/mobile-settings`
  - Chọn phong cách: Trình độ học trò, Trình độ tiến sĩ, Trình độ chuyên gia
   - Thiết lập ngưỡng: Kích thước chữ tối thiểu, nền tối/ sáng
   - Thông báo: Kích hoạt chế độ đọc đêm

- **Trang Quick access:** `/daoanh/kinh/quick-access`
  - Tự động mở Kinh lên mỗi buổi sáng
   - Chọn đoạn Kinh ngẫu nhiên hàng ngày
   - Thống kê: Số lần đọc mỗi ngày

## Dữ liệu

- **Đoạn Kinh:** 500+ đoạn Kinh phổ biến cho mobile display
- **Phong cách:** 3 phong cách hiển thị (học trò, tiến sĩ, chuyên gia)
- **Thiết bị hỗ trợ:** iPhone, Android phones, tablets
- **Thời lượng:** Tự động mỗi buổi sáng, hoặc khi user mở ứng dụng

## Acceptance criteria

- [ ] Hiển thị đúng 500+ đoạn Kinh trên mobile
- [ ] Tăng tốc độ đọc 30% qua giao diện tối ưu mobile
- [ ] Tương thích với iPhone Safari, Android Chrome, Tablet browsers
- [ ] Chế độ đọc đêm hoạt động đúng 100% trường hợp
- [ ] Bảo mật dữ liệu: Không gửi lịch sử đọc về server bên ngoài

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `displayKinhMobile(segment)` - Hiển thị đoạn Kinh trên mobile
2. `getMobileSettings()` - Lấy cài đặt hiển thị mobile
3. `toggleNightMode()` - Chuyển đổi chế độ đọc đêm
4. `getDailyKinh()` - Lấy đoạn Kinh ngẫu nhiên hàng ngày

**File path:** `docs/Mimo-Flash/M10-kinh-mobile-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created)