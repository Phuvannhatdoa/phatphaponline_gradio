# M77 · Buddhist Study Tracker

**Status:** 📄 Consolidated Documentation  
**Module:** M77  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp theo dõng học tập Phật học: theo dõng và quản lý quá trình học tập Kinh, giáo Thái, thiền định cho practitioner, bao gồm mục sách, thời gian học, và tiến độ.

## UI/UX

- **Trang Theo dõng học tập:** `/daoanh/tracking`
  - Hiển thị tiến độ: Số sách đã đọc, Thời gian học tổng, Mục sách hiện tại, Tiến độ từng mục
   - Bộ lọc: Theo sách (Kinh, Giáo Thái, Thiền), theo thời gian (ngày/tháng/năm)
   - Tiến sách: Đánh dấu mục đã đọc, xem tiến độ chi tiết

- **Trang Mục sách:** `/daoanh/tracking/modules`
  - Hiển thị mục sách: Tên mục, trạng thái (chưa bắt đầu, đang đọc, đã hoàn thành), tiến độ
   - Chức năng: Bắt đầu mục mới, chuyển sang mục tiếp theo, đánh dấu mục đã hoàn thành

- **Trang Cài đặt:** `/daoanh/tracking/settings`
  - Chọn mục sách mặc định: Mục sách được chọn thường xuyên
   - Thiết lập mục tiêu: Mục tiêu đọc sách theo ngày/tháng (ví dụ: 1 mục/ngày)
   - Thông báo: Kích hoạt nhắc nhở khi bắt đầu/mục sách mới

## Dữ liệu

- **Mục sách:** 50+ mục sách Phật giáo phổ biến
- **Thể loại:** Kinh, Giáo Thái, Thiền định
- **Thời gian theo dõng:** Hàng ngày, hàng tuần, hàng tháng
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Theo dõng 50+ mục sách chính xác
- [ ] Đánh dấu mục đọc đúng 90% qua thời gian thực
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Tích hợp với Module M47 (Bookmarks) và M73 (Scripture Search)
- [ ] Bảo mật dữ liệu: Không chia sẻ dữ liệu học tập với bên thứ ba

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getStudyTracker()` - Lấy theo dõng học tập
2. `updateModuleProgress(moduleId, progress)` - Cập nhật tiến độ mục
3. `getSettings()` - Lấy cài đặt theo dõng học tập
4. `getHistory()` - Lấy lịch sử đọc sách

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T77-study-tracker-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), sách DB, notification service