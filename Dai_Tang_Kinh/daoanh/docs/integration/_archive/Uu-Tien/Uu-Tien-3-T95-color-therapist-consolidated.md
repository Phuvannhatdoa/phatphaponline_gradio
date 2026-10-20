# M95 · Buddhist Colour Therapist

**Status:** 📄 Consolidated Documentation  
**Module:** M95  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp trị liệu màu sắc Phật tử: sử dụng chữa trị qua màu sắc để cải thiện trạng thái cảm xúc, tâm lý, và hỗ trợ pratica méditation dựa trên 심리 trị liệu qua màu sắc Phật tử.

## UI/UX

- **Trang Trị liệu màu sắc:** `/daoanh/color/therapy`
  - Input: Trạng thái cảm xúc hiện tại (thơmmmée, giận dữ, vui tươi, buồn), hoặc chọn màu sắc muốn ứng dụng
   - Kết quả: Khuyến nghị màu sắc (màu sắc cho cảm xúc cụ thể), bài thiền màu sắc, bài tập yoga màu sắc
   - Thực hiện: Hiển thị màu sắc trên màn hình, phát âm thanh binaural màu sắc

- **Trang Phân tích màu sắc:** `/daoanh/color/analysis`
  - Phân tích màu sắc: Xu hướng màu sắc qua thời gian, phát hiện thay đổi màu sắc
   - So sánh: So sánh màu sắc hiện tại với màu sắc trước đó

- **Trang Cài đặt:** `/daoanh/color/settings`
  - Chọn phương pháp: Tự động (qua cảm xúc), Thủ công (chọn màu)
   - Thiết lập ngưỡng cảnh báo: Cảnh báo khi trạng thái cảm xúc thay đổi đáng kể
   - Thông báo: Kích hoạt nhắc nhở khi màu sắc cần thay đổi

## Dữ liệu

- **Màu sắc:** 10+ màu sắc Phật tử chính (Trắng, Vàng, Xanh lá, Xanh dương, Hồng, Tím, Vàng chanh, Đỏ thắm, Xám, Ngọc)
- **Thời gian thực:** Cập nhật mỗi khi có tín hiệu cảm xúc mới
- **Thiết bị hỗ trợ:** Điện thoại, tablet (hiển thị màu), hoặc thiết bị chiếu màu (tù chọn)
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Trị liệu đúng 75% trạng thái cảm xúc qua màu sắc
- [ ] Phân tích đúng 80% xu hướng màu sắc qua thời gian
- [ ] Tích hợp với Module M63 (Emotion Analysis) và M68 (Mini Guidance)
- [ ] Tương thích với thiết bị hiển thị màu và chiếu màu (tù chọn)
- [ ] Bảo mật dữ liệu: Không gửi tín hiệu cảm xúc về máy chủ bên ngoài

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `colorTherapy(emotion)` - Trị liệu màu sắc cho cảm xúc
2. `getColorAnalysis()` - Phân tích màu sắc qua thời gian
3. `getSettings()` - Lấy cài đặt trị liệu màu sắc
4. `getHistory()` - Lấy lịch sử trị liệu màu sắc

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T95-color-therapist-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), AI trị liệu màu sắc, kết hợp với Module M63 emotion analysis