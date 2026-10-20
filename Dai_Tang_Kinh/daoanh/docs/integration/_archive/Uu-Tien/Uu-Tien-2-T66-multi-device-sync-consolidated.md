# M66 · Buddhist Multi-Device Sync

**Status:** 📄 Consolidated Documentation  
**Module:** M66  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp đồng bộ đa thiết bị cho pratica méditation: đảm bảo dữ liệu practitioner (session méditation, tiến độ, cảm xúc, settings) đồng bộ mượt mà giữa điện thoại, tablet, và desktop.

## UI/UX

- **Trang Trạng thái đồng bộ:** `/daoanh/sync/status`
  - Hiển thị tình trạng: Tất cả thiết bị đồng bộ, Thiết bị nào đang đồng bộ, Thiết bị nào bị lỗi
   - Chi tiết: Danh sách thiết bị, lúc đồng bộ lần cuối, dữ liệu nào đang bị đồng bộ

- **Trang Cài đặt đồng bộ:** `/daoanh/sync/settings`
  - Chọn dữ liệu đồng bộ: Session méditation, Tiến độ, Cảm xúc, Settings
   - Tần suất đồng bộ: Tự động mỗi 5 phút, mỗi 30 phút, mỗi 1 giờ, thủ công
   - Xử lý xung đột: Sử dụng timestamp mới nhất, hỏi người dùng khi có xung đột

- **Trang Quản lý thiết bị:** `/daoanh/sync/devices`
  - Danh sách thiết bị: Tên thiết bị, phiên bản OS, trạng thái kết nối
   - Xóa thiết bị: Loại bỏ thiết bị khỏi danh sách đồng bộ
   - Đặt thiết bị chính: Xác định thiết bị chính làm nguồn chân lý (source of truth)

## Dữ liệu

- **Thiết bị:** 3 thiết bị tối đa (điện thoại, tablet, desktop)
- **Dữ liệu đồng bộ:** Session méditation, Tiến độ, Cảm xúc, Settings (100% đồng bộ)
- **Tần suất:** Tự động mỗi 5 phút (cấu hình được)
- **Xử lý xung đột:** Timestamp mới nhất là nguồn chân lý

## Acceptance criteria

- [ ] Đồng bộ dữ liệu đúng 100% giữa 3 thiết bị
- [ ] Phát hiện xung đột trong 1s và xử lý tự động
- [ ] Tương thích với iOS, Android, Web desktop
- [ ] Tự động đồng bộ mỗi 5 phút (cấu hình được)
- [ ] Bảo mật dữ liệu: Mã hóa End-to-End khi đồng bộ

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `syncData(userId, dataType)` - Đồng bộ dữ liệu theo kiểu
2. `getSyncStatus()` - Lấy tình trạng đồng bộ
3. `resolveConflict(dataId)` - Giải quyết xung đột đồng bộ
4. `getSettings()` - Lấy cài đặt đồng bộ

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T66-multi-device-sync-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), cloud sync service, encryption