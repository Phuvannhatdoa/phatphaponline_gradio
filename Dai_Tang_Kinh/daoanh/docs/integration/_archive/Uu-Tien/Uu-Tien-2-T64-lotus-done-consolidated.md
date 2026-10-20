# M64 · Buddhist Lotus Done

**Status:** 📄 Consolidated Documentation  
**Module:** M64  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp hệ thống theo dõng hoàn thành práctica: sử dụng biểu tượng Sen (Lotus Done) để đánh dấu các session méditation đã hoàn thành, theo dõng tiến độ qua thời gian, và khuyến khích practitioner duy trì prática thường xuyên.

## UI/UX

- **Trang Theo dõng Sen:** `/daoanh/lotus/tracking`
  - Hiển thị session méditation: Tên session, thời lượng, ngày tháng, biểu tượng Sen trạng thái
   - Tiến độ: Phần trăm session hoàn thành qua ngày/tháng/năm
   - Thống kê: Biểu đồ tiến độ, streak (tần suất liên tục práctica)

- **Trang Cài đặt Sen:** `/daoanh/lotus/settings`
  - Chọn kiểu biểu tượng: Sen đầy, Sen nửa, Sen rỗng
   - Thiết lập mục tiêu: Mục tiêu session méditation theo ngày/tháng (ví dụ: 10 session/ngày)
   - Thông báo: Kích hoạt nhắc nhở khi đạt mục tiêu

- **Trang Phần thưởng:** `/daoanh/lotus/rewards`
  - Hiểm phần thưởng: Xem phần thưởng đã đạt, phần thưởng đang chờ
   - Loại phần thưởng: Badges (huy hiệu), kinh (Kinh tặng), các sản phẩm Phật giáo
   - Phát tán: Phần thưởng qua blockchain (tùy chọn)

## Dữ liệu

- **Session méditation:** 1000+ session đã theo dõng
- **Mục tiêu:** Mỗi ngày/tháng theo định nghĩa practitioner
- **Biểu tượng Sen:** 3 trạng thái (đầy, nửa, rỗng)
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Theo dõng đúng 1000+ session méditation chính xác
- [ ] Cập nhật streak (tần suất liên tục) đúng 90% qua thời gian
- [ ] Khuyến khích practitioner duy trì pratica: Tăng 20% session méditation qua biểu tượng Sen
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không chia sẻ tiến độ pratica với bên thứ ba

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `trackLotusSession(sessionData)` - Theo dõng session méditation
2. `getLotusProgress()` - Lấy tiến độ Sen
3. `getSettings()` - Lấy cài đặt Lotus Done
4. `getRewards()` - Lấy phần thưởng

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T64-lotus-done-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), DB theo dõng session, notification service