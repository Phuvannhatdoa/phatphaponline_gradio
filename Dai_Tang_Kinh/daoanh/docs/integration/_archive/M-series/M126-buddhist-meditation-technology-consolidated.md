# M126 · Buddhist Meditation Technology

**Status:** 📄 Consolidated Documentation  
**Module:** Mbuddhist  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp hệ thống tech/meditation Phật tử: buddhist meditation technology. Kết hợp praktyка truyền thống với các công nghệ/triết lý/contemporary framework.

## UI/UX

- **Trang Tổng quan Tech/Meditation:** `/daoanh/tech/meditation/overview`
  - Hiển thị metrics tech/meditation: 20+ technique méditation, 10+ thiết bị
  - Biểu đồ thống kê: Theo thời gian, theo nhóm, theo tiêu chí
  - User dashboard: Practice Dana, tài chính cá nhân, mục tiêu tài chính

- **Trang Chi tiết:** `/daoanh/tech/meditation/detail/:id`
  - Thông tin: Kích thước, bố cục, đặc điểm
  - Phân tích: So sánh, đánh giá, đề xuất cải tiến
  - Tài liệu: Tài liệu đi kèm, tài liệu đi kèm

- **Trang Cài đặt:** `/daoanh/tech/meditation/settings`
  - Chọn truyền thống: Theravāda, Mahāyāna, Vajrayāna
  - Thiết lập mục tiêu: Mục tiêu luyện tập hàng ngày, hàng tuần
  - Tích hợp calendar: Đối chiếu với Lịch Phật giáo (M35), rétreat schedule

## Dữ liệu

- **Metrics Tech/Meditation:** 20+ technique méditation, 10+ thiết bị
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
1. `getMeditationlibrary() - Lấy tổng quan tech/meditation kèm getMeditationLibrary()`
2. `getRitualScripts() - Lấy getRitualScripts()`
3. `getEthicalGuidelines() - Lấy getEthicalGuidelines()`
4. `getSettings() - Lấy cài đặt tech/meditation`

**File path:** `docs/Mimo-Flash/Mbuddhist-buddhist-meditation-technology-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), tech/meditation database, getMeditationLibrary system, getRitualScripts system, Charting library (D3/Chart.js) cho visualization

## Mối liên hệ với các module trước

- Tích hợp kết quả từ M108 (Buddhist Counseling Techniques): tech/meditation counseling kèm dana management kèm ethical guidelines extension kèm tech-assisted therapy
- Kết nối dữ liệu với M106 (Buddhist Psychotherapy): therapeutic techniques kèm end-of-life kèm palliative care kèm tech/meditation kèm framework integration
- Mở rộng từ M104 (Buddhist Ethics Modern): tech/meditation ethics kèm ethical guardrails kèm contemporary issues kèm policy documents kèm regulatory compliance
- Mở rộng từ M105 (Advanced Buddhist Psychology): 75-door consciousness kèm mental factors kèm tech/meditation kèm consciousness expansion kèm tech-assisted practice
- Mở rộng zero-RAM principle cho tech/meditation data tracking anony-mized, chỉ hiển thị aggregates statistics chứ không user-identifiable financial/tech history
- Mối liên hệ với M37 (Buddhist Meditation Music): tech/meditation meditation kèm meditation app kèm mindfulness kèm audio guided meditation kèm tech delivery platform

---
