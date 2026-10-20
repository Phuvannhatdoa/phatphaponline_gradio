# M31 · Buddhist Voice Assistant

**Status:** 📄 Consolidated Documentation  
**Module:** M31  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp trợ lý giọng lệnh Phật giáo: giọng lệnh hướng dẫn meditation, đọc Kinh, và trả lời câu hỏi Phật học hands-free.

## UI/UX

- **Trang trợ lý giỸ lệnh:** `/daoanh/voice-assistant`
  - Giọng lệnh: Giọng Việt tự nhiên, tốc độ điều chỉnh (0.5x, 1x, 1.5x, 2x)
   - Chức năng: Hướng dẫn meditation, đọc Kinh, trả lời câu hỏi Phật học

- **Trang Cài đặt giỸ lệnh:** `/daoanh/voice-assistant/settings`
  - Chọn giọng: Việt Nam, English, Pali
   - Thiết lập tốc độ, tiếng thức từ
   - Thông báo: Kích hoạt chế độ hands-free

- **Trang Lịch sử:** `/daoanh/voice-assistant/history`
  - Lịch sử lệnh: Ghi nhận các lệnh đã thực hiện
   - Phản hồi: Đánh giá hiệu quả giỸ lệnh

## Dữ liệu

- **Giọng lệnh:** Tiếng Việt tự nhiên (chất lượng studio), English, Pali
- **Chức năng:** 50+ lệnh Phật học phổ biến
- **Thời gian phản hồi:** < 1s từ lệnh đến phản hồi
- **Thiết bị hỗ trợ:** Điện thoại, Đồng hồ thông minh, Smart speaker

## Acceptance criteria

- [ ] Nhận diện giỸ lệnh đúng 95% cho lệnh Phật học phổ biến
- [ ] Thời gian phản hồi < 1s từ lệnh đến phản hồi
- [ ] Tăng tỷ lệ méditation hàng ngày 20% qua giỸ lệnh hands-free
- [ ] Tương thích với các thiết bị: Điện thoại, Đồng hồ thông minh, Smart speaker
- [ ] Bảo mật dữ liệu: Không lưu trữ lệnh nhạy cảm dài hạn

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `processVoiceCommand(command)` - Xử lý lệnh giỸ
2. `getAssistantResponse(command)` - Lấy phản hồi từ giỸ lệnh
3. `getAssistantSettings()` - Lấy cài đặt giỸ lệnh
4. `getHistory()` - Lấy lịch sử lệnh

**File path:** `docs/Mimo-Flash/M31-voice-assistant-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), voice recognition SDK, TTS engine