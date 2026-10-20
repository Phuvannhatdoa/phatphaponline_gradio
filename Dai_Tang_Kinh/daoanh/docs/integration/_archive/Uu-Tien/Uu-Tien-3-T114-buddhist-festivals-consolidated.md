# M114 · Buddhist Festivals & Holy Days

**Status:** 📄 Consolidated Documentation  
**Module:** M114  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp hệ thống Lễ Phật giáo và Ngày 성일: quản lý các ngày lễ, tiết, thánh quan quan trọng, và cung cấp hướng dẫn cho practitioner tham gia lễ đúng giáo pháp.

## UI/UX

- **Trang Lễ Phật giáo:** `/daoanh/festivals/calendar`
  - Hiển thị các lễ quan trọng: 100+ ngày lễ kèm thông tin
  - Bộ lọc theo truyền thống: Theravāda, Mahāyāna, Vajrayāna
  - User calendar: Đồng bộ cá nhân, nhắc nhở, lịch practice cá nhân

- **Trang Chi tiết Lễ:** `/daoanh/festivals/detail/:id`
  - Thông lễ: Lịch sử, ý nghĩa, ritual procedures
  - Cách thực hành: Cách offering, chanting, meditation kèm từng lễ
  - Tham chiếu: Kinh đoạn trích, luận pháp kèm liên quan

- **Trang Tham gia:** `/daoanh/festivals/participation`
  - Đăng ký tham gia: Đăng ký retreat, ceremony, offering
  - Lịch trình chi tiết: Thời gian, địa điểm,.prepare requirements
   - Phản hồi: Đánh giá experience, ghi nhận insight

- **Trang Cài đặt:** `/daoanh/festivals/settings`
  - Chọn truyền thống: Theravāda, Mahāyāna, Vajrayāna
  - Thiết lập nhắc nhở: Cách ngày lễ, ngày practice cá nhân
  - Đồng bộ calendar: Google Calendar, Apple Calendar integration

## Dữ liệu

- **100+ ngày lễ:** Kèm thông tin kèm truyền thống
- **30+ ritual procedures:** Kèm bước ritual kèm lời nguyện kèm offering items
- **10+ truyền thống:** Kèm đặc điểm riêng kèm cách celebración
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Lễ hiển thị đúng 100+ ngày quan trọng kèm thông tin truyền thống
- [ ] Ritual procedures hiển thị đúng 30+ bước ritual kèm lời nguyện kèm offering items
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Đồng bộ calendar Google/Apple hoạt động đúng 95% trường hợp
- [ ] Lọc truyền thống hiển thị đúng 3 truyền thống kèm đặc điểm riêng
- [ ] Hệ thống nhắc nhở hoạt động đúng 90% cho các ngày lễ sắp tới

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getFestivalCalendar()` - Lấy calendar 100+ ngày lễ quan trọng kèm thông tin truyền thống
2. `getRitualProcedures(festivalId)` - Lấy ritual procedures kèm bước ritual kèm lời nguyện kèm offering items
3. `getTraditionSettings()` - Lấy cài đặt truyền thống kèm đặc điểm riêng
4. `getCalendarSync()` - Đồng bộ calendar kèm Google/Apple integration

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T114-buddhist-festivals-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), Festival database (100+ ngày lễ kèm thông tin kèm truyền thống), Ritual procedures system (30+ bước ritual kèm lời nguyện kèm offering items), Calendar integration (Google/Apple Calendar API), Multi-tradition support (Theravāda, Mahāyāna, Vajrayāna)

## Mối liên hệ với các module trước

- Tích hợp kết quả từ M35 (Buddhist Calendar): Buddhist calendar foundation kèm 366 days, 108 Thánh ngày chính kèm festival dates kèm ritual schedules
- Kết nối dữ liệu với M112 (Buddhist Pilgrimage): festival dates kèm pilgrimage timing kèm optimal travel dates kèm retreat schedules
- Mở rộng từ M109 (Buddhist Chaplaincy): festival chaplaincy support kèm end-of-life care kèm ceremonial support kèm family guidance
- Mở rộng từ M110 (Buddhist Engaged Social Work): festival engaged social work kèm community events kèm cultural preservation kèm community participation
- Mở rộng zero-RAM principle cho festival data caching, chỉ hiển thị aggregates statistics chứ không user-identifiable festival participation history
- Mối liên hệ với M37 (Buddhist Meditation Music): festival music kèm ceremonial chanting kèm ritual soundtrack kèm audio guided meditation cho lễ

---