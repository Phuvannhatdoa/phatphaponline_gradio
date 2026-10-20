# M58 · Buddhist Dharma Events

**Status:** 📄 Consolidated Documentation  
**Module:** M58  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp hệ thống sự kiện Phật giáo: theo dõng các sự kiện Phật giáo (Lễ Phát tín, Lễ Vulan, Lễ Vu quán, các ngày lễ Quan Âm), quản lý lịch sự kiện, và gửi thông báo đến practitioner.

## UI/UX

- **Trang Lịch sự kiện:** `/daoanh/events/calendar`
  - Hiển thị lịch các sự kiện Phật giáo: Ngày tháng, Tên sự kiện, Mô tả
   - Bộ lọc: Theo quốc gia, theo truyền thống (Theravada/Mahayana/Vajrayana), theo tháng
   - Thêm sự kiện: Tạo sự kiện mới, sửa/sửa sự kiện

- **Trang Thông báo sự kiện:** `/daoanh/events/notifications`
  - Thông báo sự kiện: Cảnh báo sớm (1 tuần, 1 ngày, 1 giờ trước)
   - Chọn nhận: Nhận thông báo qua email, SMS, ứng dụng
   - Lịch sử: Ghi nhận lịch sử nhận thông báo

- **Trang Quản lý sự kiện:** `/daoanh/events/manage`
  - Quản lý: Duyệt sự kiện, từ chối sự kiện, chỉnh sửa quyền
   - Phân quyền: Admin, Organizer, Observer

## Dữ liệu

- **Sự kiện:** 500+ các sự kiện Phật giáo hàng năm
- **Loại sự kiện:** Lễ Phát tín, Lễ Vuлан, Lễ Vu quán, Ngày Phật tử, Ngày Quan Thế
- **Thời gian:** Theo lịch Dương/Lunar calendar
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Quản lý 500+ sự kiện Phật giáo chính xác
- [ ] Phát tin đúng 90% sớm (1 tuần trước)
- [ ] Tương thích với các nền tảng: iOS, Android, Web
- [ ] Tích hợp với Module M45 (mala counter) và M56 (âmTri)
- [ ] Bảo mật dữ liệu: Không chia sẻ thông tin sự kiện nhạy cảm

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getEventsCalendar(filter)` - Lấy lịch sự kiện
2. `addEvent(eventData)` - Thêm sự kiện mới
3. `deleteEvent(eventId)` - Xóa sự kiện
4. `getNotifications(filter)` - Lấy thông báo

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T58-dharma-events-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), calendar system, notification service