# M121 · Buddhist Environmental Ethics

**Status:** 📄 Consolidated Documentation  
**Module:** M121  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp khung đạo đức Môi trường Phật tử: hướng dẫn practitioner áp dụng đạo đức Phật tử vào bảo vệ môi trường, thay đổi khí hậu, và sống xanh bền vững.

## UI/UX

- **Trang Tổng quan Môi trường:** `/daoanh/environment/overview`
  - Hiển thị metrics môi trường: Carbon footprint, biodiversity loss, pollution levels
  - Biểu đồ tình trạng: Thay đổi khí hậu, woody coverage, air quality
  - User action: Cá nhân, cộng đồng, Institutional initiatives

- **Trang Tư duy Xanh:** `/daoanh/environment/green-mindset`
  - Hiển thị tư duy: Giảm thiểu rác rưởi, Tái sử dụng, Tái chế
  - Bài viết môi trường Phật tử: Bài viết từ thầy tọt, giáo viên môi trường Phật tử
  - Tạp chí xanh: Nhật kỹ xanh hàng ngày, bài tập môi trường

- **Trang Dự án Bền vững:** `/daoanh/environment/sustainable-projects`
  - Dự án: Restore ecosystem, tái định cư,renewable energy
  - Quản lý dana: Phân bổ dana, báo cáo kê sách, compliance kiểm soát
  - KPIs: Đo lường tác động môi trường, social benefit measurement

- **Trang Cài đặt:** `/daoanh/environment/settings`
  - Chọn tác động: Local, regional, global
  - Thiết lập mục tiêu: Giảm thiểu 10% carbon, tăng 20% biodiversity
  - Tích hợp activism: Kết nối với environmental activism, cộng đồng projects

## Dữ liệu

- **Metrics môi trường:** 15+ chỉ số kèm dữ liệu thực tế
- **Dự án bền vững:** 10+ dự án kèm impacto measurement kèm social benefit
- **Bài viết môi trường:** 20+ bài viết kèm mindfulness kèm practical exercise
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Metrics hiển thị đúng 15+ chỉ số kèm dữ liệu thực tế
- [ ] Dự án bền vững hiển thị đúng 10+ dự án kèm impacto measurement kèm social benefit
- [ ] Tư duy xanh hiển thị đúng 20+ bài viết kèm mindfulness kèm practical exercise
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Hệ thống quản lý dana kèm 95% compliance kiểm soát
- [ ] Báo cáo tác động kèm 90% accuracy đo lường tác động môi trường

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getEnvironmentOverview()` - Lấy tổng quan metrics kèm 15+ chỉ số kèm dữ liệu thực tế
2. `getSustainableProjects(projectId)` - Lấy dự án bền vững kèm impacto measurement kèm social benefit
3. `getGreenMindsetResources()` - Lấy 20+ bài viết kèm mindfulness kèm practical exercise
4. `getSettings()` - Lấy cài đặt đạo đức môi trường

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T121-buddhist-environmental-ethics-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), Environment database (15+ chỉ số kèm dữ liệu thực tế), Sustainable projects database (10+ dự án kèm impacto measurement kèm social benefit), Mindset library (20+ bài viết kèm mindfulness kèm practical exercise), Environmental activism system (kèm connection với cộng đồng projects)

## Mối liên hệ với các module trước

- Tích hợp kết quả từ M108 (Buddhist Counseling Techniques): environmental counseling kèm eco-psychology kèm dana management kèm environmental action kèm ethical guidelines
- Kết nối dữ liệu với M104 (Buddhist Ethics Modern): environmental ethics kèm ethical guardrails kèm contemporary issues kèm policy documents kèm regulatory compliance
- Mở rộng từ M119 (Buddhist Economics): environmental economics kèm carbon footprint kèm renewable energy kèm sustainable finance kèm impact measurement
- Mở rộng từ M120 (Buddhist Bioethics): environmental health kèm medical connection kèm pollution health effects kèm ethical framework kèm bioethics integration
- Mở rộng zero-RAM principle cho environmental data tracking anony-mized, chỉ hiển thị aggregates statistics chứ không user-identifiable environmental footprint history
- Mối liên hệ với M37 (Buddhist Meditation Nature): nature meditation kèm environmental awareness kèm mindfulness kèm connection với đất nước kèm ritual connection với earth

---