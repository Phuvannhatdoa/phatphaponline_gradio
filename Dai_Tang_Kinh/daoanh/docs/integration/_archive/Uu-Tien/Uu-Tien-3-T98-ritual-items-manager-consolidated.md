# M98 · Buddhist Ritual Items Manager

**Status:** 📄 Consolidated Documentation  
**Module:** M98  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp quản lý đồ cụ ritual Phật tử: quản lý đồ cụ ritual (phật tỵ, Glocken, quả cúng, và các đồ cụ khác) cho nhà trang và practitioner, bao gồm thông tin đồ cụ, trạng thái, và lịch sử sử dụng.

## UI/UX

- **Trang Quản lý đồ cụ:** `/daoanh/ritual-items`
  - Hiển thị đồ cụ: Tên đồ cụ, loại đồ cụ, trạng thái (có sẵn, đang sử dụng, cần sửa chữa), địa chỉ lưu trữ
   - Chức năng: Thêm đồ cụ mới, sửa đồ cụ, xóa đồ cụ, thay đổi trạng thái

- **Trang Lịch sử sử dụng:** `/daoanh/ritual-items/history`
  - Lịch sử: Các lần sử dụng đồ cụ trước, thống kê qua thời gian (ngày/tháng/năm)
   - Phân tích: Đồ cụ được sử dụng nhiều nhất, xu hướng sử dụng đồ cụ

- **Trang Cài đặt:** `/daoanh/ritual-items/settings`
  - Chọn đồ cụ mặc định: Đồ cụ được sử dụng thường xuyên
   - Thiết lập ngưỡng cảnh báo: Cảnh báo khi đồ cụ cần sửa chữa (cấu hình thời gian/số lượng)
   - Thông báo: Kích hoạt nhắc nhở khi đến thời điểm kiểm tra/đ sửa đồ cụ

## Dữ liệu

- **Đồ cụ:** 50+ đồ cụ ritual Phật tử phổ biến
- **Thể loại:** Phật tỵ, Glocken, Quả cúng, Cây thuốc thuốc, và các đồ cụ khác
- **Thời gian theo dõng:** Hàng ngày, hàng tuần, hàng tháng
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Quản lý 50+ đồ cụ chính xác
- [ ] Theo dõng sử dụng đúng 80% qua thời gian thực
- [ ] Cảnh báo sửa chữa đúng 90% trước khi đồ cụ bị hư hỏng
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không lộ thông tin đồ cụ nhạy cảm

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getRitualItems()` - Lấy danh sách đồ cụ
2. `updateRitualItem(itemId, data)` - Cập nhật đồ cụ
3. `getSettings()` - Lấy cài đặt đồ cụ
4. `getHistory()` - Lấy lịch sử sử dụng đồ cụ

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T98-ritual-items-manager-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), ritual items DB, notification service