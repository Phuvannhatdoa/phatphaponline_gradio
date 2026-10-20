# M71 · Buddhist Retreat Management

**Status:** 📄 Consolidated Documentation  
**Module:** M71  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp quản lý retreat Phật học: lập kế hoạch, theo dõng, và quản lý retreat thiền định, rút lui, và các retreat Phật giáo khác.

## UI/UX

- **Trang Lập kế hoạch retreat:** `/daoanh/retreat/planning`
  - Input: Loại retreat (thiền định, rút lui, Pure Land), Thời gian (số ngày), Địa điểm (khu vực, nhà trang), Số lượng practitioner
   - Kết quả: L kế hoạch retreat kèm danh sách việc cần chuẩn bị, ngân dự toán

- **Trang Theo dõng retreat:** `/daoanh/retreat/monitoring`
  - Theo dõng tiến độ: Thời gian còn lại, số practitioner tham gia, các session đã thực hiện
   - Biểu đồ: Phần trăm retreat đã hoàn thành, xu hướng practitioner

- **Trang Quản lý retreat:** `/daoanh/retreat/management`
  - Quản lý: Duyệt retreat, chỉnh sửa retreat, hủy retreat
   - Phân quyền: Admin, Organizer, Practitioner

## Dữ liệu

- **Retreat:** 100+ retreat Phật giáo đã được quản lý
- **Loại retreat:** Thiền định, Rút lui, Pure Land, Vipassana
- **Thời gian:** Từ 1 ngày đến 30 ngày
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Quản lý 100+ retreat chính xác
- [ ] Tính kế hoạch retreat trong 10 phút cho retreat mới
- [ ] Theo dõng tiến độ đúng 90% qua thời gian thực
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không lộ thông tin retreat nhạy cảm

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `createRetreat(retreatData)` - Tạo retreat mới
2. `getRetreatStatus(retreatId)` - Lấy trạng thái retreat
3. `updateRetreat(retreatId, data)` - Cập nhật retreat
4. `getRetreatHistory()` - Lấy lịch sử retreat

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T71-retreat-management-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), retreat DB, scheduling system