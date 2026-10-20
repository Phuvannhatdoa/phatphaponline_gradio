# M80 · Buddhist Incense Management

**Status:** 📄 Consolidated Documentation  
**Module:** M80  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp quản lý hương đồ Phật tử: theo dõng và quản lý bài hương, loại hương, và lịch sử sử dụng hương trong pratica méditation và nghi tạc.

## UI/UX

- **Trang Quản lý hương:** `/daoanh/incense/management`
  - Hiển thị loại hương: Tên hương, nguồn gốc, loại (Bạch hổ, Hồng hất, Kỳ quicker, và các loại khác)
   - Chức năng: Thêm loại hương mới, sửa loại hương, xóa loại hương

- **Trang Lịch sử hương:** `/daoanh/incense/history`
  - Lịch sử: Các session sử dụng hương trước, thống kê qua thời gian (ngày/tháng/năm)
   - Phân tích: Loại hương được sử dụng nhiều nhất, xu hướng sử dụng hương

- **Trang Cài đặt:** `/daoanh/incense/settings`
  - Chọn loại hương mặc định: Loại hương được sử dụng thường xuyên
   - Thiết lập ngưỡng cảnh báo: Cảnh báo khi hết hương (cấu hình số lượng còn lại)
   - Thông báo: Kích hoạt nhắc nhở khi đến thời điểm补充 hương

## Dữ liệu

- **Loại hương:** 20+ loại hương Phật tử phổ biến
- **Nguồn gốc:** Thiên nhiên, Nhân tạo
- **Thời gian theo dõng:** Hàng ngày, hàng tuần, hàng tháng
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Quản lý 20+ loại hương chính xác
- [ ] Theo dõng sử dụng đúng 80% qua thời gian thực
- [ ] Cảnh báo hết hương đúng 90% trước khi hết
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không lộ thông tin loại hương nhạy cảm

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getIncenseManagement()` - Lấy quản lý hương
2. `addIncense(incenseData)` - Thêm loại hương mới
3. `updateIncense(incenseId, data)` - Cập nhật loại hương
4. `getSettings()` - Lấy cài đặt hương

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T80-incense-management-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), incense DB, notification service