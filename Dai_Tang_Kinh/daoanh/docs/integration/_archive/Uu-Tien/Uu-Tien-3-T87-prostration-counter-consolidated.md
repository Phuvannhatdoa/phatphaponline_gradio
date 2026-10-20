# M87 · Buddhist Prostration Counter

**Status:** 📄 Consolidated Documentation  
**Module:** M87  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp bộ đếm hạ plong Phật tử: dùng để đếm số lượng hạ plong, cung cấp các chế độ đếm linh hoạt và theo dõng số liệu qua thời gian.

## UI/UX

- **Trang Bộ đếm hạ plong:** `/daoanh/prostration/counter`
  - Chế độ đếm: Đếm hạ plong, Đếm session, Đếm pratica khác
   - Hiển thị số đếm: Số lượng hạ plong hiện tại, Số lượt reset, Thời lượng pratica
   - Chức năng: Tăng/giảm số đếm, Reset số đếm, Lưu trạng thái

- **Trang Lịch sử hạ plong:** `/daoanh/prostration/history`
  - Lịch sử: Các session hạ plong trước, thống kê qua thời gian (ngày/tháng/năm)
   - Phân tích: Phần trăm session hoàn thành, xu hướng số lượng hạ plong

- **Trang Cài đặt:** `/daoanh/prostration/settings`
  - Chọn chế độ đếm: Mặc định, Linh hoạt, Chỉ định
   - Thiết lập ngưỡng cảnh báo: Cảnh báo khi hạ plong đạt ngưỡng (ví dụ: 108 lần)
   - Thông báo: Kích hoạt nhắc nhở khi bắt đầu pratica mới

## Dữ liệu

- **Chế độ đếm:** 3 chế độ chính (hạ plong, session, praktyka khác)
- **Ngưỡng cảnh báo:** Có thể tùy chỉnh (mặc định 108, 54, 27)
- **Thời lượng thực:** Theo dõng thời lượng pratica qua thời gian
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Đếm đúng 108+lần hạ plong chính xác
- [ ] Phát hiện ngưỡng cảnh báo đúng 90% qua thời gian thực
- [ ] Lịch sử hạ plong đúng 80% qua 30 ngày
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không lưu trữ số liệu práctica nhạy cảm

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getProstrationCounter()` - Lấy bộ đếm hạ plong
2. `incrementProstration()` - Tăng số lượng hạ plong
3. `resetProstration()` - Reset số lượng hạ plong
4. `getSettings()` - Lấy cài đặt bộ đếm

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T87-prostration-counter-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), counter DB, notification service