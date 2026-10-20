# M42 · Buddhist Lunar-Solar Reconciliation

**Status:** 📄 Consolidated Documentation  
**Module:** M42  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp hệ thống thống nhất lịch âm-dự chính xác cho Phật giáo: chuyển đổi giữa lịch âm, lịch dự, và lịch Tân trân Vật gia, đảm bảo ngày lễ và các ngày quan trọng được celebra đúng ngày.

## UI/UX

- **Trang Chuyển đổi lịch:** `/daoanh/calendar/convert`
  - Input: Ngày âm, ngày dự, hoặc ngày Tân trân Vật gia
   - Kết quả: Đúng tương đương giữa ba loại lịch, ngày lễ tiếp theo

- **Trang Lễ hội theo lịch:** `/daoanh/calendar/holidays`
  - Hiển thị lễ theo lịch âm, dự, Tân trân Vật gia
   - Chức năng: Đếm ngược đến lễ, ghi nhận lễ đã qua

- **Trang Cài đặt:** `/daoanh/calendar/settings-lunar`
  - Chọn loại lịch mặc định: Âm, Dự, Tân trân Vật gia
   - Thiết lập múi giờ, cañ đúng chuyển đổi
   - Thông báo: Kích hoạt nhắc nhở dựa trên lịch theo lựa chọn

## Dữ liệu

- **Hệ thống lịch:** Lịch âm, Lịch dự, Tân trân Vật gia
- **Quy đổi:** Các công thức chuyển đổi chính xác centuries-tested
- **Lễ quan trọng:** 20+ lễ Phật quan trọng tính trên ba loại lịch
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Chuyển đổi lịch chính xác 100% cho các ngày quan trọng
- [ ] Hiển thị lễ đúng 95% trên ba loại lịch
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Tính ngày lễ kế tiếp đúng 100% trường hợp
- [ ] Bảo mật dữ liệu: Không lưu trữ dữ liệu cá nhân liên quan đến lịch

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `convertLunarToSolar(lunarDate)` - Chuyển đổi lịch âm sang dự
2. `convertSolarToLunar(solarDate)` - Chuyển đổi lịch dự sang âm
3. `getNextHoliday(lunarDate)` - Lấy ngày lễ kế tiếp
4. `getCalendarSettings()` - Lấy cài đặt calendrier

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T42-lunar-solar-reconciliation-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), lunar-solar conversion algorithms