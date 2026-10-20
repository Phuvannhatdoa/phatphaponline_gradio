# M78 · Buddhist Prayer Beads Counter

**Status:** 📄 Consolidated Documentation  
**Module:** M78  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp Bộ tánh Phật tử đếm: dùng để đếm số lần récitation, méditation, hoặc các práctica Phật giáo khác. Cung cấp các chế độ đếm linh hoạt và theo dõng số liệu qua thời gian.

## UI/UX

- **Trang Bộ tánh đếm:** `/daoanh/mala/counter`
  - Chế độ đếm: Đếm récitation, Đếm méditation, Đếm практика khác
   - Hiển thị số đếm: Số lần đếm hiện tại, Số lượt reset, Thời lượng praktyка
   - Chức năng: Tăng/giảm số đếm, Reset số đếm, Lưu trạng thái

- **Trang Lịch sử đếm:** `/daoanh/mala/history`
  - Lịch sử: Các session đếm trước, thống kê qua thời gian (ngày/tháng/năm)
   - Phân tích: Phần trăm praktyka hoàn thành, xu hướng số đếm

- **Trang Cài đặt:** `/daoanh/mala/settings`
  - Chọn chế độ đếm: Mặc định, Linh hoạt, Chỉ định
   - Thiết lập ngưỡng cảnh báo: Cảnh báo khi đếm đạt ngưỡng (ví dụ: 108 lần)
   - Thông báo: Kích hoạt nhắc nhở khi bắt đầu pratica mới

## Dữ liệu

- **Chế độ đếm:** 3 chế độ chính (récitation, méditation, prácticas khác)
- **Ngưỡng cảnh báo:** Có thể tùy chỉnh (mặc định 108, 54, 27)
- **Thời lượng thực:** Theo dõng thời lượng praktyka qua thời gian
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Đếm đúng 108+lần prácticas chính xác
- [ ] Phát hiện đúng ngưỡng cảnh báo qua thời gian thực
- [ ] Lịch sử đếm đúng 80% qua 30 ngày
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không lưu trữ số liệu practices nhạy cảm

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getMalaCounter()` - Lấy bộ tánh đếm
2. `incrementCounter()` - Tăng số đếm
3. `resetCounter()` - Reset số đếm
4. `getSettings()` - Lấy cài đặt bộ tánh

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T78-prayer-beads-counter-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), counter DB, notification service