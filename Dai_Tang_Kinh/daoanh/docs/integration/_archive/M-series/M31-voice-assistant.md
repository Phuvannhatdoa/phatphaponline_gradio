# M31 · Tích hợp Voice Assistant cho Cử Nhân

**Spec · P1**

# M31 Hỗ trợ trợ lý giọng nói (Voice Assistant)

Tích hợp Voice Assistant (Siri, Google Assistant, tương tự) cho trình độ Cử Nhân: lệnh giọng nói để tra cứu kinh, tìm monk, và kiểm soát ứng dụng mà không cần tay.

## Mục đích

Cung cấp trải nghiệm hands-free (thông qua giọng nói) cho người dùng Cử Nhân, cho phép tra cứu kinh, monk, và kiểm soát các chức năng ứng dụng bằng lệnh giọng nói tự nhiên.

## UI/UX

- **Lệnh giọng nói được hỗ trợ:**
  - "Tra cứu Kinh đầu ngày"
  - "Tìm thầy tọt Thiền mập"
  - "Đọc Kinh vào giờ 6 sáng"
  - "Nhắc nhở tiết Canicules"
  - "Chỉ số practice của tôi hôm nay"

- **Trang Phản hồi voice:** `/daoanh/voice/feedback`
  - Hiển thị: Lệnh đã nhận, kết quả, xác nhận
  - Tùy chọn: Sửa lại, thêm ngữ cảnh

- **Trang Cài đặt voice:** `/daoanh/voice/settings`
  - Chọn trợ lý: Siri, Google Assistant, Bixby
  - Chọn giọng đọc: Việt Nam, English, Pali
  - Đặt ngưỡng cảm nhận giọng nói

## Dữ liệu

- **Voice API:** Google Speech-to-Text, VinoSpeech (offline-first)
- **Command library:** 50+ lệnh Phật học phổ biến
- **Context awareness:** Hiểu ngữ cảnh lịch tu práctica, ngày Thánh
- **User profile:** Lưu lịch sử lệnh, 선호语言

## Acceptance criteria

- [ ] Nhận diện lệnh giỌ đúng 90%+ cho 100 lệnh Phật học mẫu
- [ ] Phản hồi dưới 2s cho câu lệnh đơn giản
- [ ] Tương thích với iOS Siri, Android Google Assistant
- [ ] Hoạt động offline cho 80% lệnh phổ biến (không cần internet)
- [ ] Tiếng Việt được hỗ trợ đầy đủ (Không bị đọc sai dấu)

## File tương tự

- `docs/integration/M31-voice-assistant.md`
- `docs/Mimo-Flash/T116-m31-voice-assistant.md`