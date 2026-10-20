# M35 · Buddhist Calendar

**Status:** 📄 Consolidated Documentation  
**Module:** M35  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp lịch Phật giáo đầy đủ với các ngày Thánh, tiết, và các ngày quan trọng khác, giúp Cử nhân lên kế hoạch tu práctica và tham gia các kiện lễ đúng đắn.

## UI/UX

- **Trang Lịch Phật giáo:** `/daoanh/calendar/buddhist`
  - Hiển thị ngày tháng lunar, thông tin tiết/thánh hàng ngày
  - Màu sắc phân biệt: Thánh ngày (vàng), Tiết (xanh lá), Ngày thường (trắng)
  - Click ngày: Xem chi tiết lễ tiễn, kinh cần đọc

- **Trang Ngày quan trọng cá nhân:** `/daoanh/calendar/personal-dates`
  - Thêm ngày sinh nhật, ngày lễ gia đình vào lịch Phật giáo
  - Đồng bộ với Google Calendar, Apple Calendar
  - Nhắc nhở trước ngày quan trọng (1 ngày, 3 ngày, 1 tuần)

- **Trang Tìm ngày:** `/daoanh/calendar/search`
  - Tìm theo ngày, theo tên tiết, theo tên Thánh
  - Kết quả: Ngày corresponded, lý do quan trọng, Kinh cần đọc

## Dữ liệu

- **Lịch Phật giáo:** DILA calendar (366 tiết, 108 Thánh ngày chính)
- **Người dùng:** Cá nhân dates (tùy chọn đồng bộ)
- **Cảnh báo:** Thông báo trước ngày quan trọng (tùy chọn)
- **Cấp phép:** Tuân thủ quy tắc lịch (không trùng lịch)

## Acceptance criteria

- [ ] Lịch hiển thị đúng 366 ngày (năm nhuận có 29 ngày tháng 2)
- [ ] Thông báo ngày quan trọng gửi đúng theo cài đặt của user
- [ ] Đồng bộ với Google Calendar/Apple Calendar trong 5 phút
- [ ] Tìm ngày hoạt động đúng cho 100+ từ khóa Phật giáo
- [ ] Tối đa 1 thông báo/c ngày (không spam user)

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getBuddhistDate(gregorianDate)` - Chuyển đổi ngày Gregorian sang Buddhist calendar
2. `isSacredDay(date)` - Kiểm tra xem ngày có phải Thánh ngày không
3. `getUpcomingSacredDays()` - Lấy danh sách Thánh ngày sắp tới
4. `syncWithCalendar(calendarType)` - Đồng bộ với Google/Apple Calendar

**File path:** `docs/Mimo-Flash/M35-buddhist-calendar-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), DILA calendar data, Calendar API integration (Google/Apple)