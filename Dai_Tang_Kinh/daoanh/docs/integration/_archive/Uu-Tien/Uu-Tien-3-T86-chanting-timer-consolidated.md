# M86 · Buddhist Chanting Timer

**Status:** 📄 Consolidated Documentation  
**Module:** M86  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp đồng hồ âm Chánh cho pratica méditation: dùng để đếm thời lượng chanting, cung cấp các chế độ thời gian linh hoạt và theo dõng lịch sử chanting qua thời gian.

## UI/UX

- **Trang Đồng hồ âm Chánh:** `/dao chanting/timer`
  - Chế độ đồng hồ: Đếm ngược, Đếm lên, Đồng hồ dừng
   - Chọn thời lượng: Tùy chọn thời gian (5 phút, 15 phút, 30 phút, 60 phút, tùy chỉnh)
   - Hiển thị thời gian: Thời lượng còn lại/đã trôi qua, lưu lượng chanting

- **Trang Lịch sử chanting:** `/dao chanting/history`
  - Lịch sử: Các session chanting trước, thống kê qua thời gian (ngày/tháng/năm)
   - Phân tích: Thời lượng chanting trung bình, xu hướng thời lượng

- **Trang Cài đặt:** `/dao chanting/settings`
  - Chọn chế độ mặc định: Chế độ thường xuyên dùng
   - Thiết lập thời lượng mặc định: Thời lượng thường xuyên dùng
   - Thông báo: Kích hoạt nhắc nhở khi kết thúc chanting

## Dữ liệu

- **Chế độ đồng hồ:** 3 chế độ chính (đếm ngược, đếm lên, đồng hồ dừng)
- **Thời lượng:** Tùy chọn 5min, 15min, 30min, 60min, tùy chỉnh
- **Thời gian thực:** Theo dõng thời lượng chanting qua thời gian
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Đồng hồ chính xác 100% qua thời gian thực
- [ ] Phát hiện kết thúc đúng 90% qua chế độ cảnh báo
- [ ] Lịch sử chanting đúng 80% qua 30 ngày
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không lưu trữ lịch sử chanting nhạy cảm

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getChantingTimer()` - Lấy đồng hồ âm Chánh
2. `startTimer(mode, duration)` - Bắt đầu đồng hồ
3. `stopTimer()` - Dừng đồng hồ
4. `getSettings()` - Lấy cài đặt đồng hồ

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T86-chanting-timer-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), đồng hồ logic, DB