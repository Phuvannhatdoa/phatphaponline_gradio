# M33 · Buddhist Meditation Tracker

**Status:** 📄 Consolidated Documentation  
**Module:** M33  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp bộ theo dõng méditation: ghi nhận, theo dõng, và đánh giá độ sâu méditation qua các session meditation.

## UI/UX

- **Trang Theo dõng méditation:** `/daoanh/meditation/track`
  - Hiển thị session: Thời lượng, depth mức (1-10), loại méditation (Thiền thọ, Vipassana, Zen)
   - Biểu đồ tiến độ: Theo tuần, theo tháng

- **Trang Cài đặt:** `/daoanh/meditation/settings`
  - Thiết lập mục tiêu: Thời lượng mục tiêu mỗi ngày, mục tiêu depth
   - Thông báo: Kích hoạt nhắc nhở méditation

- **Trang Phân tích:** `/daoanh/meditation/analysis`
  - Phân tích: Xu hướng độ depth méditation, correlation với các yếu tố khác (ngủ, ăn uống)

## Dữ liệu

- **Session méditation:** 1000+ session méditation đã ghi nhận
- **Chỉ số:** Thời lượng, độ depth, loại méditation, ngày/tháng/năm
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop, thiết bị đeo (Apple Watch, Fitbit)

## Acceptance criteria

- [ ] Ghi nhận 1000+ session méditation chính xác
- [ ] Theo dõng độ depth méditation đúng 90% so với cảm nhận cá nhân
- [ ] Phân tích xu hướng đúng 85% qua thời gian
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop, thiết bị đeo
- [ ] Bảo mật dữ liệu: Tất cả dữ liệu lưu cục bộ trên thiết bị user

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `trackMeditationSession(session)` - Theo dõng session méditation
2. `getMeditationStats(userId)` - Lấy thống kê méditation
3. `getMeditationHistory(userId, period)` - Lấy lịch sử méditation
4. `getSettings()` - Lấy cài đặt méditation

**File path:** `docs/Mimo-Flash/M33-meditation-tracker-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), meditation tracking sensor data