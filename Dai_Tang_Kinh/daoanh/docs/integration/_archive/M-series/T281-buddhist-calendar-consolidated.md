# T281 · Buddhist Calendar and Holy Days

> Đổi số ngày 2026-10-10: M4 (trùng số kế hoạch M-series) → T281. Nội dung không đổi.

**Status:** 📄 Consolidated Documentation  
**Module:** M4  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp lịch Phật giáo và danh sách ngày lễ: cho phép practitioner tra cứu các ngày lễ Phật giáo, nhật quan quan trọng, và ghi nhận các ngày quan trọng cá nhân trong practice của mình.

## UI/UX

- **Trang Lịch Phật:** `/daoanh/calendar`
  - Hiển thị ngày lễ Phật giáo: Phật Đản, Vu Lan, Thành đạo, Tháng tịnh…
   - Chọn ngày: Đăng ký retreat, 참석 nghi lễ, lịch personalized

- **Trang Cài đặt:** `/daoanh/calendar/settings`
  - Chọn lưu địa phương/đám mây
   - Thiết lập múi giờ: Việt Nam, Châu Âu, Châu Mỹ
   - Thông báo: Kích hoạt nhắc nhở lễ hội

- **Trang Nhật quan cá nhân:** `/daoanh/calendar/personal-dates`
  - Thêm nhật quan cá nhân: Ngày bắt đầu practice, ngày nhập môn, ngày cần nhớ
   - Xuất báo cáo: PDF kèm nhật quan part of practice

## Dữ liệu

- **Các ngày lễ chính:** 20+ ngày lễ Phật giáo được định nghĩa sẵn
- **Giai đoạn tu práctica:** 3 giai đoạn (Niem, Sat, Thau)
- **Thời gian chạy:** Tích hợp với Module M0 (base modules)
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Hiển thị đúng 20+ ngày lễ Phật giáo
- [ ] Tích hợp được với Module M0 (base modules)
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Lưu cài đặt chọn lọc: Local/Cloud tùy ý
- [ ] Bảo mật dữ liệu: Chỉ hiển thị dữ liệu cho user đã xác thực

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getBuddhistHolidays(year)` - Trả về mảng 20+ ngày lễ
2. `isHolyDay(date)` - Kiểm tra ngày có phải lễ Phật không
3. `getMeditationPhase(date)` - Trả về giai đoạn (Niem/Sat/Thau)
4. `getCalendarConfig()` - Lấy cấu hình múi giờ và lưu trữ

**File path:** `docs/Mimo-Flash/M4-buddhist-calendar-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created)