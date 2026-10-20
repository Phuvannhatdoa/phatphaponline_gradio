# M67 · Buddhist AI Chatbot

**Status:** 📄 Consolidated Documentation  
**Module:** M67  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp chatbot AI Phật giáo: sử dụng ngôn ngữ tự nhiên (NLP) để trả lời câu hỏi về Phật học, cung cấp lời khuyên thiền, và hướng dẫn pratica cho practitioner tại mọi lúc mọi nơi.

## UI/UX

- **Trang Chatbot:** `/daoanh/chatbot`
  - Giao diện chat: Hiển thị tin nhắn trước/cả hai, nhập tin nhắn mới
   - Tối ưu cho mobile: Chuyển sang chế độ ngang/dọc tùy thích
   - Tìm kiếm: Tìm câu hỏi trước đã có trong lịch sử chat

- **Trang Câu hỏi thường gặp:** `/daoanh/chatbot/faq`
  - Danh sách câu hỏi: 100+ câu hỏi Phật giáo phổ biến
   - Tìm kiếm: Tìm câu hỏi qua từ khóa
   - Phản hồi: Đánh giá câu trả lời (1-5 sao)

- **Trang Cài đặt chatbot:** `/daoanh/chatbot/settings`
  - Chọn ngôn ngữ: Tiếng Việt, English, Tiếng Trung, các ngôn ngữ khác
   - Chọn giọng đọc: M masculine, feminine, trung lập
   - Thiết lập chủ đề: Chủ đề Phật giáo, Thiền, Kinh, Lễ tạc

## Dữ liệu

- **Câu hỏi:** 500+ câu hỏi Phật giáo đã được training
- **Mô hình NLP:** Mô hình ngôn ngữ fine-tuned cho Phật học (fine-tuned trên 10000+ conversation)
- **Ngôn ngữ:** Tiếng Việt, English, Tiếng Trung (khả năng đa ngôn ngữ)
- **Thời gian phản hồi:** < 2s cho mỗi câu hỏi

## Acceptance criteria

- [ ] Trả lời đúng 80% câu hỏi Phật giáo cơ bản
- [ ] Thời gian phản hồi < 2s cho mỗi câu hỏi
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Tích hợp với Module M63 (Phân tích cảm xúc) và M68 (Lời khuyên trì tu)
- [ ] Bảo mật dữ liệu: Không lưu trữ tin nhắn nhạy cảm lâu dài

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getChatbotResponse(message)` - Lấy câu trả lời từ chatbot
2. `getChatHistory(userId)` - Lấy lịch sử chat
3. `getSettings()` - Lấy cài đặt chatbot
4. `addFAQ(question, answer)` - Thêm câu hỏi thường gặp mới

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T67-chatbot-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), NLP model cho Phật học, chat interface