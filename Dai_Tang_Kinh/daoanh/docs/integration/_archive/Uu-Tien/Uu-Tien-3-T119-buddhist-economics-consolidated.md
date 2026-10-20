# M119 · Buddhist Economics & Wealth

**Status:** 📄 Consolidated Documentation  
**Module:** M119  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp khung Kinh tế Phật tử: hướng dẫn practitioner quản lý dana, tư duy phong phú và áp dụng đạo đức Phật tử vào tài chính, doanh nghiệp và phát triển bền vững.

## UI/UX

- **Trang Tổng quan Kinh tế:** `/daoanh/economics/overview`
  - Hiển thị metrics kinh tế: Dana lưu trữ, đầu tư bền vững, doanh nghiệp đạo đức
  - Biểu đồ tài chính: Lưu trữ, chi tiêu, đầu tư kèm tiêu chuẩn đạo đức
  - User dashboard: Practice Dana, tài chính cá nhân, mục tiêu tài chính

- **Trang Tư duy phong phú:** `/daoanh/economics/mindset`
  - Hiển thị tư duy: Phong phú chi tiết, hại là được dục Tâm lý, Nỗi lo hàng xóm
  - Bài viết kinh tế Phật tử: Bài viết từ thầy tọt, giáo viên kinh tế Phật tử
  - Tạp chí tư duy: Nhật ký tư duy hàng ngày, bài tập tư duy

- **Trang Đầu tư Bền vững:** `/daoanh/economics/sustainable`
  - Dự án đầu tư: Dự án eco-friendly, xã hội hữu ích,_RETURN on impact
  - Quản lý Dana: Phân bổ Dana, báo cáo kê sách, compliance kiểm soát
  - Công cụ đầu tư: KPIs kèm ethical guardrails

- **Trang Doanh nghiệp đạo đức:** `/daoanh/economics/ethical-business`
  - Mẫu bắt đầu: Quy tắc kinh doanh đạo đức, chính sách Sila
  - Đánh giá tác động: Đầu ra xã hội, môi trường,_RETURN measurement
  - Hợp rule tuân thủ: Luật pháp, đạo đức Phật tử, báo cáo transparency

## Dữ liệu

- **Metrics kinh tế:** 20+ chỉ số kèm tiêu chuẩn đạo đức
- **Dự án đầu tư:** 15+ dự án kèm RETURN on impact kèm ethical score
- **Tư duy phong phú:** 30+ bài viết kèm mindfulness kèm practical exercise
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Metrics hiển thị đúng 20+ chỉ số kèm tiêu chuẩn đạo đức
- [ ] Dự án đầu tư hiển thị đúng 15+ dự án kèm RETURN on impact kèm ethical score
- [ ] Tư duy phong phú hiển thị đúng 30+ bài viết kèm mindfulness kèm practical exercise
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Hệ thống quản lý Dana kèm 95% compliance kiểm soát
- [ ] Báo cáo transparency hoạt động đúng 90% cho các cáo tài chính

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getEconomicsOverview()` - Lấy tổng quan metrics kèm 20+ chỉ số kèm tiêu chuẩn đạo đức
2. `getSustainableInvestment(projectId)` - Lấy dự án đầu tư kèm RETURN on impact kèm ethical score
3. `getMindsetResources()` - Lấy 30+ bài viết kèm mindfulness kèm practical exercise
4. `getSettings()` - Lấy cài đặt kinh tế Phật tử

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T119-buddhist-economics-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), Economics database (20+ chỉ số kèm tiêu chuẩn đạo đức), Investment database (15+ dự án kèm RETURN on impact kèm ethical score), Mindset library (30+ bài viết kèm mindfulness kèm practical exercise), Dana management system (compliance kiểm soát kèm 95% uptime)

## Mối liên hệ với các module trước

- Tích hợp kết quả từ M108 (Buddhist Counseling Techniques): economic counseling kèm financial therapy kèm dana management kèm dana tracking kèm ethical guidelines
- Kết nối dữ liệu với M104 (Buddhist Ethics Modern): economic ethics kèm ethical guardrails kèm business ethics kèm transparency kèm compliance
- Mở rộng từ M109 (Buddhist Chaplaincy): chaplaincy financial counseling kèm end-of-life financial kèm dana distribution kèm estate planning kèm bereavement financial support
- Mở rộng từ M110 (Buddhist Engaged Social Work): social economics kèm community development kèm resource allocation kèm social enterprise kèm impact measurement
- Mở rộng zero-RAM principle cho dana data tracking anony-mized, chỉ hiển thị aggregates statistics chứ không dana-owner-identifiable financial history
- Mối liên hệ với M37 (Buddhist Meditation Money): dana offering kèm meditation kèm ritual offering kèm temple support kèm monastery maintenance

---