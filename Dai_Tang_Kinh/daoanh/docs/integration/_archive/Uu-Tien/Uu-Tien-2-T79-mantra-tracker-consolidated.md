# M79 · Buddhist Mantra Tracker

**Status:** 📄 Consolidated Documentation  
**Module:** M79  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp theo dõng mắc Phật tử: dùng để theo dõng và đếm số lần récitation mắc, theo dõng tiến độ mắc qua thời gian, và cung cấp các chế độ mắc linh hoạt.

## UI/UX

- **Trang Theo dõng mắc:** `/daoanh/mantra/tracking`
  - Chế độ mắc: Mắc Phật tỵ, Mắc tên Phật, Mắc chú기도
   - Hiển thị số mắc: Số lần mắc hiện tại, Thời lượng mắc, Tiến độ qua thời gian
   - Chức năng: Tăng số mắc, Reset mắc, Lưu trạng thái

- **Trang Lịch sử mắc:** `/daoanh/mantra/history`
  - Lịch sử: Các session mắc trước, thống kê qua thời gian (ngày/tháng/năm)
   - Phân tích: Phần trăm mắc hoàn thành, xu hướng số mắc

- **Trang Cài đặt:** `/daoanh/mantra/settings`
  - Chọn chế độ mắc: Mặc định, Linh hoạt, Chỉ định
   - Thiết lập ngưỡng cảnh báo: Cảnh báo khi mắc đạt ngưỡng (ví dụ: 108, 54, 27 lần)
   - Thông báo: Kích hoạt nhắc nhở khi bắt đầu mắc mới

## Dữ liệu

- **Chế độ mắc:** 3 chế độ chính (Phật tỵ, Tên Phật, chú기도)
- **Ngưỡng cảnh báo:** Có thể tùy chỉnh (mặc định 108, 54, 27)
- **Thời lượng thực:** Theo dõng thời lượng mắc qua thời gian
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Theo dõng đúng 108+lần mắc chính xác
- [ ] Phát hiện đúng ngưỡng cảnh báo qua thời gian thực
- [ ] Lịch sử mắc đúng 80% qua 30 ngày
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không lưu trữ số liệu mắc nhạy cảm

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getMantraTracker()` - Lấy theo dõng mắc
2. `incrementMantra()` - Tăng số mắc
3. `resetMantra()` - Reset số mắc
4. `getSettings()` - Lấy cài đặt theo dõng mắc

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T79-mantra-tracker-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), mantra DB, notification service