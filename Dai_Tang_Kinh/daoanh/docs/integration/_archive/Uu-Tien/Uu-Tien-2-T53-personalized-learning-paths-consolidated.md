# M53 · Buddhist Personalized Learning Paths

**Status:** 📄 Consolidated Documentation  
**Module:** M53  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp con đường học tập cá nhân Phật học: dựa trên trạng thái học tập, mục tiêu, và lịch trình, AI đề xuất lộ trình học tập cá nhân phù hợp cho từng giai đoạn (sơ cấp, nâng cao, chuyên sâu).

## UI/UX

- **Trang Lộ trình học tập:** `/daoanh/learning-path/personalized`
  - Input: Trạng thái học tập hiện tại, mục tiêu (Sơ cấp, Nâng cao, Chuyên sâu), Thời gian có sẵn
   - Output: Lộ trình đề xuất (7 ngày, 30 ngày, 90 ngày), các bước thực hiện
   - Xem tiến độ: So sánh thực tế vs dự đoán, điều chỉnh lộ trình

- **Trang Theo dõng dự đoán:** `/daoanh/learning-path/tracking`
  - Lịch sử dự đoán: Các lộ trình đã đề xuất, kết quả thực tế
   - Độ chính xác: Tỷ lệ dự đoán đúng so với kết quả thực tế
   - Phản hồi: Đánh giá lộ trình dự đoán (1-5 sao)

- **Trang Cài đặt dự đoán:** `/daoanh/learning-path/settings`
  - Chọn mô hình dự đoán: Mô hình cảm xúc, Mô hình lịch sử, Kết hợp cả hai
   - Thiết lập mục tiêu cá nhân: Mục tiêu học tập theo tiêu chí riêng
   - Thông báo: Kích hoạt nhắc nhở khi tiến độ đạt ngưỡng dự đoán

## Dữ liệu

- **Mô hình dự đoán:** Mô hình Phật học fine-tuned trên 10000+ user-session
- **Giai đoạn:** Sơ cấp (Beginner), Nâng cao (Intermediate), Chuyên sâu (Advanced)
- **Chỉ số chính xác:** 75%+ độ chính xác dự đoán lộ trình đúng
- **Thời gian cập nhật:** Mỗi ngày tự động tính toán lại lộ trình

## Acceptance criteria

- [ ] Dự đoán đúng 75% lộ trình học tập theo đúng giai đoạn
- [ ] Tăng tỷ lệ hoàn thành lộ trình 30% qua khuyến nghị AI
- [ ] Tích hợp với Module M65 (Phân tích cảm xúc) và M68 (Lời khuyên trì tu)
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không chia sẻ dữ liệu cá nhân với bên thứ ba

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getLearningPath(userId)` - Lấy lộ trình học tập cá nhân
2. `updateProgress(userId, progress)` - Cập nhật tiến độ học tập
3. `getPathHistory(userId, period)` - Lấy lịch sử lộ trình
4. `getSettings()` - Lấy cài đặt lộ trình

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T53-personalized-learning-paths-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), AI model cho lộ trình học tập, DB theo dõng tiến độ