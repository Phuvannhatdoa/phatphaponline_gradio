# M65 · Buddhist Emotion Analytics

**Status:** 📄 Consolidated Documentation  
**Module:** M65  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp phân tích cảm xúc Phật học theo thời gian thực: sử dụng AI để phân tích cảm xúc từ tín hiệu biofeedback (Module M62), đoạn kinh, và session méditation, và xây dựng hồ sơ cảm xúc cá nhân theo thời gian.

## UI/UX

- **Trang Phân tích cảm xúc:** `/daoanh/analytics/emotion`
  - Input: Tín hiệu biofeedback, đoạn kinh, hoặc session méditation
   - Kết quả: Phân tích cảm xúc (thơmmmée, giận dữ, vui tươi, buồn, nỗi lo, trọng trọ), đồ graph cảm xúc qua thời gian, xu hướng cảm xúc
   - Khuyến nghị: Phương pháp điều chỉnh cảm xúc dựa trên kết quả phân tích

- **Trang Hồ sơ cảm xúc:** `/daoanh/analytics/profile`
  - Hồ sơ cá nhân: Mức độ cảm xúc trung bình, xu hướng cảm xúc qua thời gian, các phát hiện chính
   - So sánh: So sánh cảm xúc cá nhân với trung bình cộng cộng cộng cộng cộng cộng cộng cộng cộng cộng cộng cộng cộng cộng cộng cộng cộng cộng cộng cộng cộng cộng cộng cộng cộng cộng

- **Trang Cài đặt:** `/daoanh/analytics/settings`
  - Chọn nguồn dữ liệu: Biofeedback, Đoán từ kinh, Session méditation
   - Thiết lập ngưỡng cảnh báo: Cảnh báo khi cảm xúc đạt ngưỡng cao/trung bình/thấp
   - Thông báo: Kích hoạt nhắc nhở khi cảm xúc thay đổi đáng kể

## Dữ liệu

- **Mô hình cảm xúc:** Mô hình Phật học fine-tuned trên 10000+ user-session cảm xúc và tín hiệu biofeedback
- **Chỉ số:** 6 giai đoạn cảm xúc (thơmmmée, giận dữ, vui tươi, buồn, nỗi lo, trọng trọ)
- **Thời gian theo dõng:** Hàng ngày, hàng tuần, hàng tháng
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop (kết hợp với Module M62 biofeedback)

## Acceptance criteria

- [ ] Phân tích đúng 75% cảm xúc qua biofeedback và kinh
- [ ] Xây dựng hồ sơ cảm xúc cá nhân chính xác 90% qua 30 ngày
- [ ] Tăng awareness cảm xúc 25% qua analytics cá nhân
- [ ] Tích hợp với Module M53 (Lộ trình học tập cá nhân) và M63 (Phân tích cảm xúc cơ bản)
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không chia sẻ dữ liệu cảm xúc với bên thứ ba

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `analyzeEmotionAnalytics(userId, period)` - Phân tích cảm xúc analytics
2. `getEmotionProfile(userId)` - Lấy hồ sơ cảm xúc cá nhân
3. `getEmotionHistory(userId, period)` - Lấy lịch sử cảm xúc
4. `getSettings()` - Lấy cài đặt emotion analytics

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T65-emotion-analytics-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), AI model cho emotion analytics, kết hợp với Module M62 biofeedback