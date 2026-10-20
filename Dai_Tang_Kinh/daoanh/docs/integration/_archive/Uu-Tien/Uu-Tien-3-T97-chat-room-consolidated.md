# M97 · Buddhist Chat Room

**Status:** 📄 Consolidated Documentation  
**Module:** M97  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp phòng chat Phật tử: cho phép practitioner chat trực tiếp, thảo luận về Phật học, và chia sẻ kinh nghiệm práctica tại các phòng chat được phân loại theo thể loại và khu vực.

## UI/UX

- **Trang Phòng chat:** `/daoanh/chat-room`
  - Hiển thị các phòng chat: Danh sách phòng chat theo thể loại (Kinh, Thiền, Lễ tạc, Sống thứ) và khu vực (Khu vực địa lý, Online)
   - Thảo luận: Tin nhắn trực tiếp, bình luận, phản ứng (emoji)

- **Trang Tạo phòng chat:** `/daoanh/chat-room/create`
  - Tạo phòng chat mới: Nhập tên phòng, chọn thể loại, chọn khu vực
   - Chức năng: Lưu phòng chat, chia sẻ phòng chat

- **Trang Cài đặt chat:** `/daoanh/chat-room/settings`
  - Chọn phòng mặc định: Phòng chat thường xuyên tham gia
   - Thiết lập quyền: Quyền gửi tin nhắn, quyền bình luận, quyền quản lý
   - Thông báo: Kích hoạt nhắc nhở khi có tin nhắn mới

## Dữ liệu

- **Phòng chat:** 30+ phòng chat Phật tử theo thể loại và khu vực
- **Thành viên:** 5000+ practitioner tham gia phòng chat
- **Thể loại:** Kinh, Thiền, Lễ tạc, Sống thứ
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Quản lý 30+ phòng chat chính xác
- [ ] Hiển thị thành viên đúng 5000+ practitioner
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không lộ thông tin cá nhân nhạy diễn phòng chat
- [ ] Tích hợp với Module M91 (Study Planner) và M74 (Community Forums)

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getChatRooms()` - Lấy danh sách phòng chat
2. `createChatRoom(roomData)` - Tạo phòng chat mới
3. `getSettings()` - Lấy cài đặt phòng chat
4. `getHistory()` - Lấy lịch sử tin nhắn

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T97-chat-room-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), chat room DB, notification service