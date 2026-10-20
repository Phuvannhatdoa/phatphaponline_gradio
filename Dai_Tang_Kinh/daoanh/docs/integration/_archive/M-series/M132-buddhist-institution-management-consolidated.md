# M132 · Buddhist Institution Management

**Status:** 📄 Consolidated Documentation  
**Module:** Mbuddhist  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp hệ thống institution/management Phật tử: buddhist institution management. Kết hợp praktyка truyền thống với các công nghệ/triết lý/contemporary framework.

## UI/UX

- **Trang Tổng quan Institution/Management:** `/daoanh/institution/management/overview`
  - Hiển thị metrics institution/management: 15+ chỉ số, 10+ dự án bền vững
  - Biểu đồ thống kê: Theo thời gian, theo nhóm, theo tiêu chí
  - User dashboard: Practice Dana, tài chính cá nhân, mục tiêu tài chính

- **Trang Chi tiết:** `/daoanh/institution/management/detail/:id`
  - Thông tin: Kích thước, bố cục, đặc điểm
  - Phân tích: So sánh, đánh giá, đề xuất cải tiến
  - Tài liệu: Tài liệu đi kèm, tài liệu đi kèm

- **Trang Cài đặt:** `/daoanh/institution/management/settings`
  - Chọn truyền thống: Theravāda, Mahāyāna, Vajrayāna
  - Thiết lập mục tiêu: Mục tiêu luyện tập hàng ngày, hàng tuần
  - Tích hợp calendar: Đối chiếu với Lịch Phật giáo (M35), rétreat schedule

## Dữ liệu

- **Metrics Institution/Management:** 15+ chỉ số, 10+ dự án bền vững
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Hiển thị đúng metrics kèm tiêu chuẩn
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Tích hợp calendar Lịch Phật giáo hoạt động đúng cho 90+ holidays/festivals
- [ ] Bộ lọc truyền thống hiển thị đúng 3 truyền thống kèm đặc điểm riêng
- [ ] Báo cáo transparency hoạt động đúng 90% cho các cáo tài chính
- [ ] Buddhist ethical principles hiển thị đúng 10+ principles kèm guidelines

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getEconomicsoverview() - Lấy tổng quan institution/management kèm getEconomicsOverview()`
2. `getSustainableProjects(projectId) - Lấy getSustainableProjects(projectId)`
3. `getGreenMindsetResources() - Lấy getGreenMindsetResources()`
4. `getSettings() - Lấy cài đặt institution/management`

**File path:** `docs/Mimo-Flash/Mbuddhist-buddhist-institution-management-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), institution/management database, getEconomicsOverview system, getSustainableProjects system, Charting library (D3/Chart.js) cho visualization

## Mối liên hệ với các module trước

- Tích hợp kết quả từ M108 (Buddhist Counseling Techniques): institution/management counseling kèm dana management kèm ethical guidelines extension kèm tech-assisted therapy
- Kết nối dữ liệu với M106 (Buddhist Psychotherapy): therapeutic techniques kèm end-of-life kèm palliative care kèm institution/management kèm framework integration
- Mở rộng từ M104 (Buddhist Ethics Modern): institution/management ethics kèm ethical guardrails kèm contemporary issues kèm policy documents kèm regulatory compliance
- Mở rộng từ M105 (Advanced Buddhist Psychology): 75-door consciousness kèm mental factors kèm institution/management kèm consciousness expansion kèm tech-assisted practice
- Mở rộng zero-RAM principle cho institution/management data tracking anony-mized, chỉ hiển thị aggregates statistics chứ không user-identifiable financial/tech history
- Mối liên hệ với M37 (Buddhist Meditation Music): institution/management meditation kèm meditation app kèm mindfulness kèm audio guided meditation kèm tech delivery platform

---
