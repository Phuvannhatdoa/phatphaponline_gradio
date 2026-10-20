# M112 · Buddhist Pilgrimage & Sacred Sites

**Status:** 📄 Consolidated Documentation  
**Module:** M112  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp hệ thống Lữ hành Phật tử và Địa danh 성지: quản lý các sitio sacro, tracks pilgrimage routes, và cung cấp hướng dẫn cho practitioner thực hành lữ hành đúng giáo pháp.

## UI/UX

- **Trang Tổng quan Lữ hành:** `/daoanh/pilgrimage/overview`
  - Hiển thị routes pilgrimage phổ biến: 8 major routes kèm distance, duration, highlights
  - Trạng thái hôm nay: Current practice, streak tracking, next destination
  - User progress: Completed routes, favorite sites, personal reflections

- **Trang Chi tiết Sítio:** `/daoanh/pilgrimage/site/:id`
  - Thông tin sítio: Lịch sử, importancia,Hours operating, amenities
  - Thực tiễn ritual: Morning chanting, midday meditation, evening offerings
  - Tương thích: Accessibility info, transport options, accommodation

- **Trang Lên kế hoạch Lữ hành:** `/daoanh/pilgrimage/planning`
  - Route planner: Start → Destination → Optional stops kèm distance, time estimates
  - Packing list: Essential items, ritual items, weather-appropriate clothing
  - Budget estimation: Dana expectations, accommodation costs, transport fees

- **Trang Cài đặt:** `/daoanh/pilgrimage/settings`
  - Chọn tradition: Theravāda route, Mahāyāna circuit, Vajrayāna pilgrimage
  - Thiết lập mục tiêu: Distance per day, sites per week, spiritual goals
  - Tích hợp calendar: Đối chiếu với Lịch Phật giáo (M35), rétreat schedule

## Dữ liệu

- **8 major pilgrimage routes:** Kèm distance (km), duration (days), highlights (sacred sites)
- **100+ sacred sites:** Kèm history, rituals, accessibility, accommodation options
- **Route planner algorithms:** Distance optimization, time estimation, spiritual priority weighting
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop, optional GPS tracking device

## Acceptance criteria

- [ ] Hiển thị đúng 8 major pilgrimage routes kèm distance, duration, highlights
- [ ] Trang chi tiết sítio hiển thị đúng 100+ sacred sites kèm history, rituals, amenities
- [ ] Trình planner routes hoạt động đúng cho 50+ combinations start/stop
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Tích hợp calendar Lịch Phật giáo (M35) hoạt động đúng cho 90+ holidays/festivals
- [ ] Budget estimation accuracy cao hơn 80% so với 실제 experience practitioner

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getPilgrimageOverview()` - Lấy tổng quan 8 major pilgrimage routes kèm distance/duration/highlights
2. `getSiteDetails(siteId)` - Lấy chi tiết sacred site kèm history/rituals/amenities
3. `planPilgrimage(start, destination, options)` - Lên kế hoạch lữ hành kèm route planner algorithms
4. `getSettings()` - Lấy cài đặt lữ hành và pilgrimage

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T112-buddhist-pilgrimage-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), Pilgrimage database (8 major routes kèm distance/duration/highlights, 100+ sacred sites kèm history/rituals/amenities), Route planner algorithms (distance optimization, time estimation), Calendar integration (Buddhist calendar M35 holidays/festivals), User progress tracking system

## Mối liên hệ với các module trước

- Tích hợp kết quả từ M109 (Buddhist Chaplaincy): pilgrimage rituals kèm chaplaincy support kèm end-of-life care along routes kèm safety considerations
- Kết nối dữ liệu với M110 (Buddhist Engaged Social Work): pilgrimage for social change kèm community engagement kèm ethical advocacy along sacred routes
- Mở rộng từ M7 (GIS Maps): sacred site mapping kèm geographic coordinates kèm temple locations kèm pilgrimage route visualization kèm spatial analysis
- Mở rộng từ M35 (Buddhist Calendar): calendar integration kèm festival dates kèm ritual schedules kèm pilgrimage timing optimization
- Mở rộng zero-RAM principle cho GPS tracking data anony-mized, chỉ hiển thị aggregates statistics chứ không user-identifiable location history
- Mối liên hệ với M37 (Buddhist Meditation Music): chanting music kèm pilgrimage ceremonies kèm ritual timing kèm ambient sound recommendations

---