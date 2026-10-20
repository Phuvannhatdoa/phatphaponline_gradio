# M133 · Buddhist Interfaith Dialogue

**Status:** 📄 Consolidated Documentation  
**Module:** Mbuddhist  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp hệ thống comparative/dialogue Phật tử: buddhist interfaith dialogue. Kết hợp praktyка truyền thống với các công nghệ/triết lý/contemporary framework.

## UI/UX

- **Trang Tổng quan Comparative/Dialogue:** `/daoanh/comparative/dialogue/overview`
  - Hiển thị metrics comparative/dialogue: 10+ chủ đề so sánh kèm quan điểm Phật giáo kèm tradición khác, 30+ quan điểm công khai kèm tham chiếu nguồn
  - Biểu đồ thống kê: Theo thời gian, theo nhóm, theo tiêu chí
  - User dashboard: Practice Dana, tài chính cá nhân, mục tiêu tài chính

- **Trang Chi tiết:** `/daoanh/comparative/dialogue/detail/:id`
  - Thông tin: Kích thước, bố cục, đặc điểm
  - Phân tích: So sánh, đánh giá, đề xuất cải tiến
  - Tài liệu: Tài liệu đi kèm, tài liệu đi kèm

- **Trang Cài đặt:** `/daoanh/comparative/dialogue/settings`
  - Chọn truyền thống: Theravāda, Mahāyāna, Vajrayāna
  - Thiết lập mục tiêu: Mục tiêu luyện tập hàng ngày, hàng tuần
  - Tích hợp calendar: Đối chiếu với Lịch Phật giáo (M35), rétreat schedule

## Dữ liệu

- **Metrics Comparative/Dialogue:** 10+ chủ đề so sánh kèm quan điểm Phật giáo kèm tradición khác, 30+ quan điểm công khai kèm tham chiếu nguồn
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
1. `getComparisonphilosophy() - Lấy tổng quan comparative/dialogue kèm getComparisonPhilosophy(topic)`
2. `getComparisonMethod(method) - Lấy getComparisonMethod(method)`
3. `getDialogueGuide(topic) - Lấy getDialogueGuide(topic)`
4. `getSettings() - Lấy cài đặt comparative/dialogue`

**File path:** `docs/Mimo-Flash/Mbuddhist-buddhist-interfaith-dialogue-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), comparative/dialogue database, getComparisonPhilosophy system, getComparisonMethod system, Charting library (D3/Chart.js) cho visualization

## Mối liên hệ với các module trước

- Tích hợp kết quả từ M108 (Buddhist Counseling Techniques): comparative/dialogue counseling kèm dana management kèm ethical guidelines extension kèm tech-assisted therapy
- Kết nối dữ liệu với M106 (Buddhist Psychotherapy): therapeutic techniques kèm end-of-life kèm palliative care kèm comparative/dialogue kèm framework integration
- Mở rộng từ M104 (Buddhist Ethics Modern): comparative/dialogue ethics kèm ethical guardrails kèm contemporary issues kèm policy documents kèm regulatory compliance
- Mở rộng từ M105 (Advanced Buddhist Psychology): 75-door consciousness kèm mental factors kèm comparative/dialogue kèm consciousness expansion kèm tech-assisted practice
- Mở rộng zero-RAM principle cho comparative/dialogue data tracking anony-mized, chỉ hiển thị aggregates statistics chứ không user-identifiable financial/tech history
- Mối liên hệ với M37 (Buddhist Meditation Music): comparative/dialogue meditation kèm meditation app kèm mindfulness kèm audio guided meditation kèm tech delivery platform

---
