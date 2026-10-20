# M61 · Buddhist Augmented Reality Dharma

**Status:** 📄 Consolidated Documentation  
**Module:** M61  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp trải nghiệm augmented reality (AR) cho Phật học: sử dụng AR để hiển thị các phật tỵ, tháp, và các biểu tượng Phật giáo trong môi trường thực tế, giúp practitioner trực quan hóa và cảm nhận triết lý Phật tử.

## UI/UX

- **Trang AR Dharma:** `/daoanh/ar/dharma`
  - Hiển thị phật tỵ/tháp: Quét mã QR hoặc chọn tượng Phật
   - Tương tác: Quay camera, phóng/thu nhỏ, xoay xoay tượng Phật trong không gian thực tế
   - Thông tin: Hiển thị tên, lịch sử, triết lý khi click vào tượng Phật

- **Trang AR Lễ tạc:** `/daoanh/ar/rituals`
  - Hiển thị các nghi lễ AR: Thiền hướng dẫn, Đäch hợp, Phật tỵ quang
   - Tương tác: Theo dõng các bước nghi lễ qua AR, ghi nhận tiến độ

- **Trang Cài đặt AR:** `/daoanh/ar/settings`
  - Chọn tượng/thể loại: Phật Gautama, Quan Thế, Bồ Tát, các phật tộc
   - Điều chỉnh: Kích thước, màu sắc, hiệu ứng ánh sáng
   - Thông báo: Kích hoạt tự động khi quét mã QR

## Dữ liệu

- **Tượng Phật:** 100+ tượng Phật có thể hiển thị qua AR
- **Thể loại:** Triết lý Phật giáo, Lễ tạc, Thiền định
- **Thiết bị hỗ trợ:** iOS (ARKit), Android (ARCore), desktop (WebXR)
- **Tốc độ:** Hiển thị tượng Phật trong 2s sau khi quét mã QR

## Acceptance criteria

- [ ] Hiển thị tượng Phật đúng 90% qua AR
- [ ] Tương thích với iOS (ARKit), Android (ARCore), desktop (WebXR)
- [ ] Hiển thị thông tin trong 2s sau khi click
- [ ] Tối ưu cho thiết bị di động: Khử nhiễu ảnh, giữ 60fps
- [ ] Bảo mật dữ liệu: Không gửi ảnh camera về máy chủ bên ngoài

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `initARDharma(options)` - Khởi tạo AR Dharma
2. `getARObjects()` - Lấy danh tượng Phật qua AR
3. `getARSettings()` - Lấy cài đặt AR
4. `getHistory()` - Lấy lịch sử AR session

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T61-augmented-reality-dharma-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), AR SDK (ARKit/ARCore), 3D models Phật giáo