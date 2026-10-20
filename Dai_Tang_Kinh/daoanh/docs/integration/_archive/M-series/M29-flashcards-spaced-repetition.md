# M29 · Flashcards và spaced repetition cho Cử Nhân

**Spec · P1**

# M29 Hệ thống thẻ lưu ý và hồi đàm dựa trên khoảng thời gian

Cung cấp hệ thống thẻFlashcard và cơ chế spaced repetition (lặp lại dựa trên khoảng thời gian) giúp Cử Nhân ghi nhớ các từ Kinh, câu ngữ, và các niệm quan trọng hiệu quả hơn.

## Mục đích

Tận dụng hiệu quả cơ chế ghi nhớ con người để lưu trữ dài hạn các nội dung Phật giáo: từ Hán-Pali, câu kinh, niệm cotidien.

## UI/UX

- **Trang Flashcard:** `/daoanh/flashcards/browse`
  - Hiển thị thẻ hiện tại: Về mặt trước (từ/Hán), Về mặt sau (nghĩa/Việt)
  - Nút "Biết / Không biết": Phản hồi để tính spaced repetition
  - Trượt trái/phải: Next card, Previous card

- **Trang Cài đặt spaced repetition:** `/daoanh/flashcards/settings`
  - Chọn thuật toán: SM-2, SM-3, hoặc tùy chỉnh
  - Thiết lập tần suất review: 10 thẻ/ngày, 20 thẻ/ngày
  - Chọn chủ đề: Từ Kinh, Câu ngữ, Niệm định

- **Trang Theo dõi tiến độ:** `/daoanh/flashcards/progress`
  - Biểu đồ: Số thẻ đã học, số thẻ nhớ lại, tỷ lệ thành công
  - Lịch sử: Thẻ đã vượt qua, thẻ cần review lại
  - Xuất báo cáo: Số từ đã ghi nhớ dài hạn

## Dữ liệu

- **Thẻ Flashcard:** 500+ thẻ cơ bản (từ Kinh phổ biến, câu ngữ, niệm)
- **Thuật toán:** SM-2 (mặc định), tùy chỉnh theo preference user
- **Lịch review:** Tự động tính khoảng thời gian tiếp theo dựa trên phản hồi user
- **Nhóm chủ đề:** Từ vựng Kinh, Câu hiệu, Niệm định hàng ngày

## Acceptance criteria

- [ ] Thuật toán spaced repetition tính đúng khoảng thời gian dựa trên phản hồi (Biết/Chưa biết)
- [ ] Hiển thị đúng 20 thẻ mỗi trang, swipe mượt mà
- [ ] Tỷ lệ nhớ lại sau 30 ngày > 70% cho user tu luyện đều đặn
- [ ] User có thể thêm thẻ tùy chỉnh (từ Kinh của chính mình)
- [ ] Tải danh sách thẻ ban đầu dưới 2s

## File tương tự

- `docs/integration/M29-flashcards-spaced-repetition.md`
- `docs/Mimo-Flash/T104-m29-flashcards-spaced-repetition.md`