# M83 · Buddhist Festival Calendar

**Status:** 📄 Consolidated Documentation  
**Module:** M83  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp lịch lễ tết Phật tử: hiển thị các ngày lễ quan trọng Phật tử (Phật truyền, Vu quán, Phật tathan, etc.) và cung cấp thông tin về các lễ tết này.

## UI/UX

- **Trang Lịch lễ tết:** `/daoanh/festival/calendar`
  - Hiển thị lịch lễ tết: Tuần này, Tháng này, Năm nay
   - Bộ lọc: Theo truyền thống (Theravada/Mahayana/Vajrayana), theo quốc gia
   - Chi tiết lễ tết: Tên lễ tết, Mô tả, Cách lễ tết

- **Trang Chi tiết lễ tết:** `/daoanh/festival/detail`
  - Hiển thị chi tiết: Tên lễ tết, Ngày tháng, Cách lễ tết, Ý nghĩa, Món ăn truyền thống
   - Tương tác: Bookmark lễ tết, Share lễ tết

- **Trang Cài đặt:** `/daoanh/festival/settings`
  - Chọn truyền thống mặc định: Theravada, Mahayana, Vajrayana
   - Thiết lập ghi chú cá nhân: Ghi chú riêng cho mỗi lễ tết
   - Thông báo: Kích hoạt nhắc nhở trước khi lễ tết tới

## Dữ liệu

- **Lễ tết:** 30+ ngày lễ quan trọng Phật tử hàng năm
- **Truyền thống:** Theravada, Mahayana, Vajrayana
- **Quốc gia:** 20+ quốc gia có lễ tết Phật tử
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Hiển thị đúng 30+ ngày lễ quan trọng
- [ ] Tìm lễ tết đúng 90% qua truyền thống/quốc gia
- [ ] Bookmark/SHARE hoạt động đúng 80%
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không chia sẻ thông tin lễ tết nhạy cảm

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getFestivalCalendar(filter)` - Lấy lịch lễ tết
2. `getFestivalDetail(festivalId)` - Lấy chi tiết lễ tết
3. `getSettings()` - Lấy cài đặt lễ tết
4. `getHistory()` - Lấy lịch sử lễ tết

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T83-festival-calendar-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), festival DB, notification service