# M44 · Buddhist Bookmarks

**Status:** 📄 Consolidated Documentation  
**Module:** M44  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp hệ thống bookmarks cho văn bản Phật học: cho phép practitioner lưu trữ và quản lý các đoạn Kinh, giáo Thái, hoặc các đoạn văn quan tâm tại một nơi duy nhất.

## UI/UX

- **Trang Bookmarks:** `/daoanh/bookmarks`
  - Hiển thị danh sách bookmarks: Tên, đoạn văn, nguồn, ngày lưu
   - Chức năng: Thêm/bookmark, xóa bookmark, sắp xếp

- **Trang Bookmark theo thể loại:** `/daoanh/bookmarks/category`
  - Phân thể loại: Kinh, Giáo Thái, Tâm lý, Triết lý
   - Quản lý: Gán/bookmark vào thể loại, bỏ thể loại

- **Trang Cài đặt:** `/daoanh/bookmarks/settings`
  - Chọn cách hiển thị: Grid view, List view
   - Thiết lập đồng bộ: Đồng bộ bookmarks qua đám mây
   - Thông báo: Kích hoạt nhắc nhở khi thêm bookmark mới

## Dữ liệu

- **Số bookmarks:** 1000+ bookmarks Phật học
- **Thể loại:** 10+ thể loại bookmarks
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop
- **Đồng bộ:** Cloud sync cho 100% bookmarks

## Acceptance criteria

- [ ] Quản lý 1000+ bookmarks chính xác
- [ ] Phân thể loại đúng 90% tự động
- [ ] Đồng bộ cloud đúng 100% cho bookmarks
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không chia sẻ bookmarks nhạy cảm với bên thứ ba

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `addBookmark(segment, category)` - Thêm bookmark
2. `getBookmarks(filter)` - Lấy danh sách bookmarks
3. `deleteBookmark(id)` - Xóa bookmark
4. `getSettings()` - Lấy cài đặt bookmarks

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T44-bookmarks-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), bookmarks DB