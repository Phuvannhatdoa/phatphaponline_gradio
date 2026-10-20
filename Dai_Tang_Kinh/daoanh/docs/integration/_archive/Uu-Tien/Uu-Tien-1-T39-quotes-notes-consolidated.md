# M39 · Quotes & Notes

**Status:** 📄 Consolidated Documentation  
**Module:** M39  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp khả năng ghi chú, đoạn trích, và đánh dấu các đoạn Kinh quan trọng cho trình độ Cử Nhân: lưu ý cá nhân, đánh dấu favorites, và chia sẻ với cộng đồng.

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

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getQuotesBrowse()` - Lấy đoạn trích ngẫu nhiên
2. `addNote(content, tags)` - Thêm ghi chú mới
3. `getMyNotes()` - Lấy danh sách ghi chú của user
4. `likeDislikeQuote(quoteId, action)` - Like/Dislike đoạn trích

**File path:** `docs/Mimo-Flash/M39-quotes-notes-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), User authentication, Tag storage system, Like/dislike counter