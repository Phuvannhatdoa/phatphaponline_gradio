# M82 · Buddhist Temple Manager

**Status:** 📄 Consolidated Documentation  
**Module:** M82  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp quản lý nhà trang Phật tử: quản lý thông tin nhà trang, hoạt động, nhân sự, và tài chính cho các nhà trang Phật tử.

## UI/UX

- **Trang Thông tin nhà trang:** `/daoanh/temple/info`
  - Hiển thị thông tin: Tên nhà trang, Địa chỉ, Sơ đồ, Giờ mở cửa, Thông tin liên hệ
   - Chức năng: Sửa thông tin nhà trang, thêm ảnh nhà trang

- **Trang Hoạt động:** `/daoanh/temple/activities`
  - Hiển thị hoạt động: Các hoạt động thường niên, các sự kiện sắp tới, tin tức nhà trang
   - Chức năng: Đăng bài hoạt động, sửa/sửa hoạt động, xóa hoạt động

- **Trang Nhân sự:** `/daoanh/temple/staff`
  - Hiển thị nhân sự: Tên, chức vụ, hình ảnh, vai trò
   - Chức năng: Thêm nhân sự, sửa nhân sự, xóa nhân sự

- **Trang Tài chính:** `/daoanh/temple/finances`
  - Hiển thị tài chính: Thu nhập, chi expenditures, báo cáo tài chính
   - Chức năng: Thêm giao dịch, sửa giao dịch, xuất báo cáo tài chính PDF

## Dữ liệu

- **Thông tin nhà trang:** 1000+ nhà trang Phật tử có sẵn
- **Hoạt động:** 500+ hoạt động/niện niên
- **Nhân sự:** 1000+ nhân sự nhà trang
- **Tài chính:** Giao dịch tài chính hàng ngày

## Acceptance criteria

- [ ] Quản lý 1000+ nhà trang chính xác
- [ ] Hiển thị hoạt động đúng 500+ hoạt động
- [ ] Tài chính giao dịch đúng 100% qua thời gian thực
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không lộ thông tin nhà trang nhạy cảm

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getTempleInfo()` - Lấy thông tin nhà trang
2. `getActivities(filter)` - Lấy danh sách hoạt động
3. `getStaff()` - Lấy danh sách nhân sự
4. `getFinances(filter)` - Lấy thông tin tài chính

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T82-temple-manager-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), temple DB, notification service