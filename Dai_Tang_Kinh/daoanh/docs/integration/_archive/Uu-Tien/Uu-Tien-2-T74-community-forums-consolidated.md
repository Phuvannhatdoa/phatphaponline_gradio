# M74 · Buddhist Community Forums

**Status:** 📄 Consolidated Documentation  
**Module:** M74  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp diễn đàn cộng đồng Phật tử: cho phép practitioner thảo luận, chia sẻ kinh nghiệm práctica,提问 hỏi đáp về Phật học tại các diễn đàn được phân loại theo thể loại và khu vực.

## UI/UX

- **Trang Diễn đàn:** `/daoanh/forums`
  - Hiển thị các diễn đàn: Danh sách diễn đàn theo thể loại (Thiền, Kinh, Lễ tạc, Sống thứ) và khu vực (Khu vực địa lý, Online)
   - Thảo luận: Xem chủ đề, gửi tin nhắn mới, bình luận vào chủ đề

- **Trang Chủ đề thảo luận:** `/daoanh/forums/topics`
  - Hiển thị chủ thể: Tiêu đề, nội dung, tác giả, số lượt xem, số lượt bình luận
   - Tương tác: Phát biểu vào chủ thể, bình luận, Bookmark chủ đề

- **Trang Cài đặt diễn đàn:** `/daoanh/forums/settings`
  - Chọn thể loại diễn đàn: Hiển thị/ẩn các thể loại
   - Thiết lập quyền: Quyền đăng bài, quyền bình luận, quyền quản lý
   - Thông báo: Kích hoạt nhắc nhở khi có phản hồi mới

## Dữ liệu

- **Diễn đàn:** 50+ diễn đàn Phật tử theo thể loại và khu vực
- **Chủ đề:** 1000+ chủ đề thảo luận Phật học
- **Thành viên:** 5000+ practitioner tham gia diễn đàn
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Quản lý 50+ diễn đàn chính xác
- [ ] Chủ đề thảo luận đúng 1000+ chủ đề
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không lộ thông tin cá nhân nhạy diễn đàn
- [ ] Tích hợp Bookmark (Module M47) và Share (Module M44)

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getForums()` - Lấy danh sách diễn đàn
2. `getTopics(filter)` - Lấy danh sách chủ thể theo bộ lọc
3. `postReply(topicId, content)` - Phát biểu vào chủ thể
4. `getSettings()` - Lấy cài đặt diễn đàn

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T74-community-forums-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), forum DB, notification service