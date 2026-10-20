# M129 · Buddhist Counseling Techniques Expanded

**Status:** 📄 Consolidated Documentation  
**Module:** Mbuddhist  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp hệ thống counseling/therapy Phật tử: buddhist counseling techniques expanded. Kết hợp praktyка truyền thống với các công nghệ/triết lý/contemporary framework.

## UI/UX

- **Trang Tổng quan Counseling/Therapy:** `/daoanh/counseling/therapy/overview`
  - Hiển thị metrics counseling/therapy: 20+ kỹ thuật kèm full script, 10+ profile
  - Biểu đồ thống kê: Theo thời gian, theo nhóm, theo tiêu chí
  - User dashboard: Practice Dana, tài chính cá nhân, mục tiêu tài chính

- **Trang Chi tiết:** `/daoanh/counseling/therapy/detail/:id`
  - Thông tin: Kích thước, bố cục, đặc điểm
  - Phân tích: So sánh, đánh giá, đề xuất cải tiến
  - Tài liệu: Tài liệu đi kèm, tài liệu đi kèm

- **Trang Cài đặt:** `/daoanh/counseling/therapy/settings`
  - Chọn truyền thống: Theravāda, Mahāyāna, Vajrayāna
  - Thiết lập mục tiêu: Mục tiêu luyện tập hàng ngày, hàng tuần
  - Tích hợp calendar: Đối chiếu với Lịch Phật giáo (M35), rétreat schedule

## Dữ liệu

- **Metrics Counseling/Therapy:** 20+ kỹ thuật kèm full script, 10+ profile
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
1. `getCounselingtechniques() - Lấy tổng quan counseling/therapy kèm getCounselingTechniques()`
2. `getTechniqueDetails(techniqueId) - Lấy getTechniqueDetails(techniqueId)`
3. `getEthicalGuidelines() - Lấy getEthicalGuidelines()`
4. `getSettings() - Lấy cài đặt counseling/therapy`

**File path:** `docs/Mimo-Flash/Mbuddhist-buddhist-counseling-techniques-expanded-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), counseling/therapy database, getCounselingTechniques system, getTechniqueDetails system, Charting library (D3/Chart.js) cho visualization

## Mối liên hệ với các module trước

- Tích hợp kết quả từ M108 (Buddhist Counseling Techniques): counseling/therapy counseling kèm dana management kèm ethical guidelines extension kèm tech-assisted therapy
- Kết nối dữ liệu với M106 (Buddhist Psychotherapy): therapeutic techniques kèm end-of-life kèm palliative care kèm counseling/therapy kèm framework integration
- Mở rộng từ M104 (Buddhist Ethics Modern): counseling/therapy ethics kèm ethical guardrails kèm contemporary issues kèm policy documents kèm regulatory compliance
- Mở rộng từ M105 (Advanced Buddhist Psychology): 75-door consciousness kèm mental factors kèm counseling/therapy kèm consciousness expansion kèm tech-assisted practice
- Mở rộng zero-RAM principle cho counseling/therapy data tracking anony-mized, chỉ hiển thị aggregates statistics chứ không user-identifiable financial/tech history
- Mối liên hệ với M37 (Buddhist Meditation Music): counseling/therapy meditation kèm meditation app kèm mindfulness kèm audio guided meditation kèm tech delivery platform

---
