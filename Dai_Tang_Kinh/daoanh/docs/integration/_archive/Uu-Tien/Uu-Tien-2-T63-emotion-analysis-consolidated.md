# M63 · Buddhist Emotion Analysis

**Status:** 📄 Consolidated Documentation  
**Module:** M63  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp phân tích cảm xúc Phật học: sử dụng AI để phân tích cảm xúc từ đoạn kinh, đánh giá trạng thái tâm lý (thơmmmée, giận dữ, vui tươi, và s...) và đề xuất các phương pháp điều chỉnh.

## UI/UX

- **Trang Phân tích cảm xúc:** `/daoanh/emotion/analyze`
  - Input: Đoạn kinh, hoặc ghi âm méditation cá nhân
   - Kết quả: Phân tích cảm xúc (thơmmmée, giận dữ, vui tươi, buồn), đồ graph cảm xúc qua thời gian, mức độ mạnh mẽ
   - Khuyến nghị: Phương pháp điều chỉnh cảm xúc dựa trên kết quả

- **Trang Theo dõng cảm xúc:** `/daoanh/emotion/tracking`
  - Lịch sử cảm xúc: Các session đã phân tích, xu hướng cảm xúc qua thời gian
   - Biểu đồ xu hướng: Đồ graph cảm xúc hàng ngày/hàng tuần/hàng tháng
   - Phản hồi: Đánh giá độ chính xác dự đoán cảm xúc (1-5 sao)

- **Trang Cài đặt:** `/daoanh/emotion/settings`
  - Chọn mô hình dự đoán: Mô hình cảm xúc, Mô hình lịch sử, Kết hợp cả hai
   - Thiết lập ngưỡng cảnh báo: Cảnh báo khi cảm xúc đạt ngưỡng cao/trung bình/thấp
   - Thông báo: Kích hoạt nhắc nhở khi cảm xúc thay đổi đáng kể

## Dữ liệu

- **Mô hình cảm xúc:** Mô hình Phật học fine-tuned trên 10000+ user-session cảm xúc
- **Giai đoạn cảm xúc:** Thơmmmée, Giận dữ, Vui tươi, Buồn, Trọng trọ, Nỗi lo
- **Chỉ số chính xác:** 75%+ độ chính xác phân tích cảm xúc
- **Thời gian cập nhật:** Mỗi session tự động phân tích

## Acceptance criteria

- [ ] Phân tích đúng 75% cảm xúc đoạn kinh
- [ ] Tăng awareness cảm xúc 20% qua khuyến nghị AI
- [ ] Tích hợp với Module M53 (Lộ trình học tập cá nhân) và M68 (Lời khuyên trì tu)
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không chia sẻ dữ liệu cảm xúc với bên thứ ba

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `analyzeEmotion(text)` - Phân tích cảm xúc đoạn văn
2. `getEmotionHistory(userId, period)` - Lấy lịch sử cảm xúc
3. `getRecommendations(emotion)` - Lấy khuyến nghị điều chỉnh cảm xúc
4. `getSettings()` - Lấy cài đặt phân tích cảm xúc

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T63-emotion-analysis-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), AI model cho cảm xúc, DB theo dõng cảm xúc