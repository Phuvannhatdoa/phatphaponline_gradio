# M96 · Dharma Law & Ethics AI Advisory

**Spec · P2**

# M96 Pháp lý & Tài dham Thông báo AI

Cung cấp nhà tư vấn Pháp lý & Tài dham AI: cung cấp chỉ pháp lý và tư vấn tài dham Phật giáo cho các tình huống pháp lý, đạo đức, và đạo vấn đời hiện đại.

## Mục đích

Thực hiện AI advisory cho Pháp lý & Tài dham Phật giáo: cho phép practitioner hỏi đáp về các tình huống pháp lý, đạo đức Phật giáo, và nhận được câu trả lời dựa trên của Phật giáo, Luật quốc gia, và đạo đức học hiện đại.

## UI/UX

- **Trang Tư vấn AI:** `/daoanh/law-ethics/advisory`
  - Input: Tình huống pháp lý/đạo đức, Mức độ phức tạp (Cơ bản, Nâng cao, Chuyên môn)
   - Output: Câu trả lời Pháp lý & Tài dham Phật giáo, Các đề nghị thực hành, 
   - Nguồn: Luật quốc gia, Phật giáo, Đạo đức học

- **Trang Xác minh nguồn:** `/daoanh/law-ethics/verify`
  - Xác minh nguồn pháp lý: Kiểm tra nguồn gốc câu trả lời (Phật giáo/Luật quốc gia/Đạo đức học)
   - Xem lịch sử: Lịch sử câu hỏi và câu trả lời

- **Trang Phản hồi:** `/daoanh/law-ethics/feedback`
  - Đánh giá câu trả lời: Chính xác/Sai chính xác/Không phù hợp
   - Cập nhật mô hình: Đào tạo lại mô hình từ phản hồi của người dùng

## Dữ liệu

- **Mô hình advisory:** Mô hình Phật giáo & Luật fine-tuned trên 50000+ tình huống Pháp lý & Tài dham
- **Nguồn dữ liệu:** Luật pháp quốc gia, Sách Phật giáo, Tạp chí đạo đức học
- **Thuật ngữ pháp lý:** 10000+ thuật ngữ pháp lý Phật giáo và quốc gia
- **Độ tin cậy:** 80% câu trả lời dựa trên nguồn uy tín

## Acceptance criteria

- [ ] Câu trả lời chính xác 80% cho các tình huống Pháp lý & Tài dham phổ biến
- [ ] Giữ gìn đúng giá trị Phật giáo trong câu trả lời
- [ ] Hỗ trợ 3+ lĩnh vực Pháp lý: Gia đình, Tài sản, Trương起诉
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không lưu trữ thông tin cá nhạy trong dài hạn

## File tương tự

- `docs/integration/M96-law-ethics-advisory.md`
- `docs/Mimo-Flash/T172-m96-law-ethics-advisory.md`