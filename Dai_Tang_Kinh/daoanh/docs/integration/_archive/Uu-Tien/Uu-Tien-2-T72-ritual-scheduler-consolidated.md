# M72 · Buddhist Ritual Scheduler

**Status:** 📄 Consolidated Documentation  
**Module:** M72  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp lịch trình nghi tạc Phật học: lập lịch, theo dõng, và quản lý các nghi tạc Phật giáo hàng ngày, hàng tuần, và các dịp lễ tết quan trọng.

## UI/UX

- **Trang Lịch nghi tạc:** `/daoanh/rituals/scheduler`
  - Hiển thị lịch nghi tắc: Ngày tháng, Tên nghi tạc, Thời gian, Trạng thái (chưa thực hiện, đang thực hiện, đã hoàn thành)
   - Tạo nghi tāc mới: Nhập tên nghi tạc, thời gian, lặp lại (hàng ngày, hàng tuần)
   - Thay đổi trạng thái: Đánh dấu đã thực hiện/ chưa thực hiện

- **Trang Loại nghi tāc:** `/daoanh/rituals/types`
  - Hiển thị loại nghi tāc: Phật tỵ, Vu quán, Thiền hướng dẫn, Lễ đắc giới, các nghi tạc khác
   - Thêm loại nghi tāc mới: Định nghĩa loại nghi tāc mới, thêm vào hệ thống

- **Trang Cài đặt:** `/daoanh/rituals/settings`
  - Chọn loại nghi tāc mặc định: Nhóm nghi tāc được chọn thường xuyên
   - Thiết lập nhắc nhở: Cảnh báo trước khi nghi tạc (15 phút, 1 tiếng, 1 ngày)
   - Thông báo: Kích hoạt tự động khi bắt đầu ngày mới

## Dữ liệu

- **Loại nghi tāc:** 30+ loại nghi tạc Phật giáo phổ biến
- **Thời gian lặp lại:** Hàng ngày, hàng tuần, hàng tháng, năm
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop
- **Nhắc nhở:** Tự động mỗi lần nghi tạc sắp tới

## Acceptance criteria

- [ ] Quản lý 30+ loại nghi tạc chính xác
- [ ] Tạo nghi tạc mới trong 2 phút
- [ ] Nhắc nhở đúng 90% trước khi nghi tạc
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không lộ thông tin nghi tạc nhạy cảm

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getRitualScheduler()` - Lấy lịch nghi tạc
2. `addRitual(ritualData)` - Thêm nghi tạc mới
3. `updateRitualStatus(ritualId, status)` - Cập nhật trạng thái nghi tạc
4. `getSettings()` - Lấy cài đặt nghi tạc

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T72-ritual-scheduler-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), ritual DB, notification service