# M88 · Buddhist Malas Counter

**Status:** 📄 Consolidated Documentation  
**Module:** M88  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp bộ đếm mala Phật tử: dùng để đếm số lượng mala (108 quả), theo dõng tiến độ prática, và cung cấp các chế độ đếm linh hoạt.

## UI/UX

- **Trang Bộ đếm mala:** `/daoanh/mala/counter`
  - Chế độ đếm: Đếm mala, Đếm session, Đếm práctica khác
   - Hiển thị số đếm: Số lượng quả mala hiện tại, Số lượt reset, Thời lượng pratica
   - Chức năng: Tăng/giảm số đếm, Reset số đếm, Lưu trạng thái

- **Trang Lịch sử mala:** `/daoanh/mala/history`
  - Lịch sử: Các session mala trước, thống kê qua thời gian (ngày/tháng/năm)
   - Phân tích: Phần trăm session hoàn thành, xu hướng số lượng mala

- **Trang Cài đặt:** `/daoanh/mala/settings`
  - Chọn chế độ đếm: Mặc định, Linh hoạt, Chỉ định
   - Thiết lập ngưỡng cảnh báo: Cảnh báo khi đếm đạt ngưỡng (ví dụ: 108 quả)
   - Thông báo: Kích hoạt nhắc nhở khi bắt đầu pratica mới

## Dữ liệu

- **Chế độ đếm:** 3 chế độ chính (mala, session, praktyka khác)
- **Ngưỡng cảnh báo:** Có thể tùy chỉnh (mặc định 108, 54, 27)
- **Thời lượng thực:** Theo dõng thời lượng pratica qua thời gian
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Đếm đúng 108+lần mala chính xác
- [ ] Phát hiện ngưỡng cảnh báo đúng 90% qua thời gian thực
- [ ] Lịch sử mala đúng 80% qua 30 ngày
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không lưu trữ số liệu práctica nhạy cảm

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getMalaCounter()` - Lấy bộ đếm mala
2. `incrementMala()` - Tăng số lượng mala
3. `resetMala()` - Reset số lượng mala
4. `getSettings()` - Lấy cài đặt bộ đếm

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T88-malas-counter-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), counter DB, notification service