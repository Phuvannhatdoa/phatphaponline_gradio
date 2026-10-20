# M81 · Buddhist Prayer Times

**Status:** 📄 Consolidated Documentation  
**Module:** M81  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp giờ vàng Phật tử: tính toán và hiển thị giờ vàng (thời gian meditation, prayer, và prática Phật giáo khác) theo từng ngày, dựa trên địa lý và truyền thống Phật tử.

## UI/UX

- **Trang Giờ vàng:** `/daoanh/prayer-times`
  - Hiển thị giờ vàng hôm nay: Giờ thiền sáng, Giờ thiền trưa, Giờ thiền chiều, Giờ lễ tạc
   - Địa lý: Tự động xác định địa lý qua vị trí GPS, hoặc chọn thủ công
   - Tùy chọn: Chọn truyền thống (Theravada/Mahayana/Vajrayana), xem chi tiết giờ vàng

- **Trang Lịch giờ vàng:** `/daoanh/prayer-times/calendar`
  - Hiển thị lịch giờ vàng: Tuần này, Tháng này, Năm nay
   - Bộ lọc: Theo truyền thống, theo địa lý
   - Thêm ghi chú: Ghi chú riêng cho mỗi giờ vàng

- **Trang Cài đặt:** `/daoanh/prayer-times/settings`
  - Chọn truyền thống mặc định: Theravada, Mahayana, Vajrayana
   - Thiết lập địa lý: Vị trí mặc định, cài đặt địa lý khác
   - Thông báo: Kích hoạt nhắc nhở khi nào giờ vàng sắp tới

## Dữ liệu

- **Giờ vàng:** 4 giờ vàng chính mỗi ngày (sáng, trưa, chiều, lễ tạc)
- **Truyền thống:** Theravada, Mahayana, Vajrayana (mỗi truyền thống có giờ vàng khác nhau)
- **Địa lý:** Tự động qua GPS, hoặc chọn thủ công qua bản đồ
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Tính toán đúng giờ vàng theo truyền thống và địa lý
- [ ] Tự động xác định vị trí GPS trong 10s
- [ ] Nhắc nhở đúng 90% trước khi giờ vàng sắp tới
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không gửi vị trí GPS về máy chủ bên ngoài không cần thiết

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getPrayerTimes()` - Lấy giờ vàng
2. `getCalendar(filter)` - Lấy lịch giờ vàng
3. `getSettings()` - Lấy cài đặt giờ vàng
4. `getHistory()` - Lấy lịch sử giờ vàng

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T81-prayer-times-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), thời gian tính toán, vị trí GPS