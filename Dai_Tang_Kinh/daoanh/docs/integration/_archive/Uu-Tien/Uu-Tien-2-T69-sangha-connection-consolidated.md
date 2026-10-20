# M69 · Buddhist Sangha Connection

**Status:** 📄 Consolidated Documentation  
**Module:** M69  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp kết nối Sống để cộng đồng Tăng added: giúp practitioner tìm kiếm, kết nối, và exercise cùng các practitioner cùng khu vực hoặc cùng truyền thống Phật học.

## UI/UX

- **Trang Tìm kiếm practitioner:** `/daoanh/sangha/search`
  - Tìm kiếm theo: Quốc gia, Tình tại, Truyền thống (Theravada/Mahayana/Vajrayana), Tên practitioner
   - Kết quả: Danh sách practitioner khớp, thông tin cơ bản (tên, avatar, truyền thống)

- **Trang Kết nối:** `/daoanh/sangha/connect`
  - Gửi yêu cầu kết nối: Yêu cầu kết nối, chấp nhận/ Từ chối kết nối
   - Danh sách kết bạn: Xem các request kết nối, quản lý kết bạn

- **Trang Sự kiện cộng đồng:** `/daoanh/sangha/events`
  - Hiển thị sự kiện: Các sự kiện Phật tử tại khu vực, online sự kiện
   - Đăng ký: Đăng ký tham gia, hủy đăng ký

## Dữ liệu

- **Practitioner:** 10000+ practitioner đăng ký
- **Khu vực:** 50+ quốc gia, 200+ thành phố
- **Truyền thống:** Theravada, Mahayana, Vajrayana
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Tìm practitioner đúng 80% qua tiêu chí tìm kiếm
- [ ] Gửi/ấp nhận kết nối trong 24s
- [ ] Hiển thị đúng 10000+ practitioner theo đúng khu vực/ truyền thống
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không lộ thông tin cá nhân nhạy cảm cho người không kết nối

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `searchSangha(filter)` - Tìm practitioner theo tiêu chí
2. `sendConnectionRequest(targetId)` - Gửi yêu cầu kết nối
3. `getConnectionRequests()` - Lấy danh sách request kết nối
4. `getSettings()` - Lấy cài đặt Sangha Connection

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T69-sangha-connection-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), practitioner DB, location service