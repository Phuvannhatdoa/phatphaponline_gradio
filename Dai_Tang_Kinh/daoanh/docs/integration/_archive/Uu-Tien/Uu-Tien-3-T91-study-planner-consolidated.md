# M91 · Buddhist Study Planner

**Status:** 📄 Consolidated Documentation  
**Module:** M91  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp kế hoạch học tập Phật tử: tạo kế hoạch học tập cá nhân, theo dõng tiến độ và cung cấp các gợi ý học tập dựa trên tiến độ và mục tiêu.

## UI/UX

- **Trang Kế hoạch học tập:** `/daoanh/study-plan`
  - Input: Mục sách (Kinh, Giáo Thái, Thiền), Thời gian có sẵn (ngày/tháng), Mục tiêu học tập
   - Kết quả: Kế hoạch học tập (ngày/tuần/tháng), danh sách việc cần làm, tiến độ dự đoán

- **Trang Theo dõng kế hoạch:** `/daoanh/study-plan-tracking`
  - Theo dõng: Tiến độ thực tế so với kế hoạch, phát hiện trễ (behind schedule)
   - Phản hồi: Điều chỉnh kế hoạch, đánh giá kế hoạch (1-5 sao)

- **Trang Cài đặt:** `/daoanh/study-plan/settings`
  - Chọn kế hoạch mặc định: Kế hoạch thường xuyên dùng
   - Thiết lập mục tiêu cá nhân: Mục tiêu học tập theo định nghĩa riêng
   - Thông báo: Kích hoạt nhắc nhở khi đến giờ học tập

## Dữ liệu

- **Kế hoạch:** 50+ kế hoạch học tập Phật tử được sẵn
- **Mục sách:** Kinh, Giáo Thái, Thiền định
- **Thời gian theo dõng:** Hàng ngày, hàng tuần, hàng tháng
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Tạo kế hoạch đúng 80% phù hợp với mục tiêu và thời gian
- [ ] Theo dõng tiến độ đúng 75% qua 30 ngày
- [ ] Tích hợp với Module M77 (Study Tracker) và M73 (Scripture Search)
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không chia sẻ kế hoạch học tập với bên thứ ba

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getStudyPlan(userId, preferences)` - Lấy kế hoạch học tập
2. `updatePlanProgress(userId, progress)` - Cập nhật tiến độ kế hoạch
3. `getPlanHistory(userId, period)` - Lấy lịch sử kế hoạch
4. `getSettings()` - Lấy cài đặt kế hoạch học tập

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T91-study-planner-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), kế hoạch học tập logic, DB