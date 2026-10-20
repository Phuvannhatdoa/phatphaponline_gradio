# M39 · Ghi chú và Đoạn trích cho Cử Nhân

**Spec · P1**

# M39 Hỗ trợ Ghi chú đoạn trích Kinh

Cung cấp khả năng ghi chú, đoạn trích, và đánh dấu các đoạn Kinh quan trọng cho trình độ Cử Nhân: lưu ý cá nhân, đánh dấu favorites, và chia sẻ với cộng đồng.

## Mục đích

Đỗ người dùng Cử Nhân có thể lưu trữ các đoạn kinh có ý nghĩa, ghi nhận nhận định cá nhân, và xây dựng bộ sưu tập đoạn trích riêng của mình.

## UI/UX

- **Trang Đoạn trích:** `/daoanh/quotes/browse`
  - Hiển thị Đoạn trích ngẫu nhiên, Theo chủ đề (Tâm lý, Luật, Sutra)
  - Nút "Lưu ý thích", "Đọc thêm", "Phím tắt"
  - Thể loại: Từ Kinh, Câu chữ, Niệm định

- **Trang Ghi chú cá nhân:** `/daoanh/notes/my-notes`
  - Danh sách tất cả ghi chú của user
  - Sửa/xóa ghi chú
  - Thẻ: #tâm lý, #tu_thuân, #sutra, v.v.

- **Trang Chi tiết đoạn trích:** `/daoanh/quotes/detail/:id`
  - Đoạn trích gốc, Ghi chú thêm, Ai tạo
  - Phản hồi: Like/Dislike, Số lượt lưu

## Dữ liệu

- **Ghi chú:** Nội dung, thời gian tạo, thẻ, owner
- **Đoạn trích:** Nguồn (Kinh, trang), nội dung gốc, tác giả
- **Thẻ:** Free-form tags do user define

## Acceptance criteria

- [ ] Lưu trữ đúng 100+ Đoạn trích cho mỗi user
- [ ] Tìm kiếm theo thẻ hoạt động đúng 90% trường hợp
- [ ] Ghi chú có thể sửa/xóa bởi owner duy nhất
- [ ] Phản hồi Like/Dislike hiển thị đúng số lượng
- [ ] Tương thích với màn hình thiết bị: điện thoại, tablet, desktop

## File tương tự

- `docs/integration/M39-quotes-notes.md`
- `docs/Mimo-Flash/T114-m39-quotes-notes.md`