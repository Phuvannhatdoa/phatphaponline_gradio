# M90 · Buddhist Meditation Timer

**Status:** 📄 Consolidated Documentation  
**Module:** M90  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp đồng hồ méditation Phật tử: dùng để đếm thời lượng méditation, cung cấp các chế độ thời gian linh hoạt và theo dõng lịch sử méditation qua thời gian.

## UI/UX

- **Trang Đồng hồ méditation:** `/daoanh/meditation/timer`
  - Chế độ đồng hồ: Đếm ngược, Đếm lên, Đồng hồ dừng
   - Chọn thời lượng: Tùy chọn thời gian (5 phút, 15 phút, 30 phút, 60 phút, tùy chỉnh)
   - Hiển thị thời gian: Thời lượng còn lại/đã trôi qua, lưu lượng méditation

- **Trang Lịch sử méditation:** `/daoanh/meditation/history`
  - Lịch sử: Các session méditation trước, thống kê qua thời gian (ngày/tháng/năm)
   - Phân tích: Thời lượng méditation trung bình, xu hướng thời lượng

- **Trang Cài đặt:** `/daoanh/meditation/settings`
  - Chọn chế độ mặc định: Chế độ thường xuyên dùng
   - Thiết lập thời lượng mặc định: Thời lượng thường xuyên dùng
   - Thông báo: Kích hoạt nhắc nhở khi kết thúc méditation

## Dữ liệu

- **Chế độ đồng hồ:** 3 chế độ chính (đếm ngược, đếm lên, đồng hồ dừng)
- **Thời lượng:** Tùy chọn 5min, 15min, 30min, 60min, tùy chỉnh
- **Thời gian thực:** Theo dõng thời lượng méditation qua thời gian
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Đồng hồ chính xác 100% qua thời gian thực
- [ ] Phát hiện kết thúc đúng 90% qua chế độ cảnh báo
- [ ] Lịch sử méditation đúng 80% qua 30 ngày
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không lưu trữ lịch sử méditation nhạy cảm

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getMeditationTimer()` - Lấy đồng hồ méditation
2. `startTimer(mode, duration)` - Bắt đầu đồng hồ
3. `stopTimer()` - Dừng đồng hồ
4. `getSettings()` - Lấy cài đặt đồng hồ

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T90-meditation-timer-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), đồng hồ logic, DB