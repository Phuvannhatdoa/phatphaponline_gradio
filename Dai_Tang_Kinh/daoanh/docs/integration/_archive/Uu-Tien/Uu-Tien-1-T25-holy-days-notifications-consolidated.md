# M25 · Buddhist Holy Days Notifications

**Status:** 📄 Consolidated Documentation  
**Module:** M25  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp thông báo ngày lễ Phật giáo: thông báo các ngày lễ quan trọng, đếm ngược đến ngày lễ, và ghi nhận ghi nhận ngày lễ đã qua.

## UI/UX

- **Trang Thông báo lễ hội:** `/daoanh/holy-days/notifications`
  - Hiển thị: Ngày lễ sắp tới, Đếm ngược ngày lễ, Ghi nhận lễ đã qua
   - Chọn loại thông báo: Thông báo mới, Thông báo hàng tuần, Thông báo hàng tháng

- **Trang Thêm ngày lễ:** `/daoanh/holy-days/add`
  - Thêm ngày lễ cá nhân: Ngày quan trọng cá nhân, Ngày nhập môn, Ngày kết kỷ
   - Xuất báo cáo: Xuất báo cáo ngày lễ cá nhân ra file PDF

- **Trang Lịch sử:** `/daoanh/holy-days/history`
  - Lịch sử ghi nhận: Ghi nhận lễ đã qua qua các năm
   - Thống kê: Số lần ghi nhận, xu hướng qua thời gian

- **Trang Cài đặt:** `/daoanh/holy-days/settings`
  - Chọn loại thông báo: Thông báo lễ quan trọng, thông báo cá nhân
   - Thiết lập múi giờ: Việt Nam, Châu Âu, Châu Mỹ
   - Thông báo: Kích hoạt lịch sử ghi nhận

## Dữ liệu

- **Lễ quan trọng:** 20+ lễ Phật quan trọng theo mặc định
- **Thông báo:** 3 loại thông báo (mới, hàng tuần, hàng tháng)
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop
- **Thời gian:** Cập nhật tự động mỗi ngày lúc 6 giờ sáng

## Acceptance criteria

- [ ] Hiển thị đúng 20+ lễ quan trọng Phật giáo
- [ ] Thông báo đúng 90% so với thời gian thực tế
- [ ] Đếm ngược ngày lễ đúng 100% trường hợp
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không chia sẻ lịch sử ghi nhận với bên thứ ba

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getHolyDaysNotifications()` - Lấy thông báo lễ quan trọng
2. `addHolyDay(id, date, type)` - Thêm ngày lễ cá nhân
3. `getHolyDayHistory()` - Lấy lịch sử ghi nhận lễ
4. `getSettings()` - Lấy cài đặt thông báo

**File path:** `docs/Mimo-Flash/M25-holy-days-notifications-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), hệ thống calendar

---