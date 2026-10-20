# M96 · Buddhist Sound Healing

**Status:** 📄 Consolidated Documentation  
**Module:** M96  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp chữa trị bằng âm liệu Phật tử: sử dụng âm liệu (bells, bowls, chanting) để hỗ trợ thư giãn, méditation, và chữa trị căng thẳng dựa trên lý do Phật tử.

## UI/UX

- **Trang Chữa trị âm liệu:** `/daoanh/sound-healing`
  - Chọn liệu: Bells Phật, Singing bowls, Chanting, Binaural beats
   - Thiết lập: Tần số, Âm lượng, Thời lượng
   - Kết quả: Xu trình chữa trị, đồ biểu đồ sóng âm, mức độ thư giãn

- **Trang Lịch sử chữa trị:** `/daoanh/sound-healing/history`
  - Lịch sử: Các session chữa trị trước, thống kê qua thời gian (ngày/tháng/năm)
   - Phân tích: Phần thư giãn tăng lên, xu hướng thời lượng chữa trị

- **Trang Cài đặt:** `/daoanh/sound-healing/settings`
  - Chọn liệu mặc định: Liệu thường xuyên dùng
   - Thiết lập tần số mặc định: Tần số thường xuyên dùng
   - Thông báo: Kích hoạt nhắc nhở khi đến thời điểm chữa trị mới

## Dữ liệu

- **Loại liệu:** 5+ loại liệu Phật tử chính (Bells, Singing bowls, Chanting, Binaural beats)
- **Thời lượng:** Tùy chọn 5min, 15min, 30min, 60min, tùy chỉnh
- **Thời gian thực:** Theo dõng thời lượng chữa trị qua thời gian
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop, thiết bị âm liệu vật lý (tù chọn)

## Acceptance criteria

- [ ] Chữa trị đúng 75% căng thẳng qua âm liệu
- [ ] Phát triển đúng 80% thư giãn qua thời gian thực
- [ ] Lịch sử chữa trị đúng 80% qua 30 ngày
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không gửi tín hiệu âm liệu về máy chủ bên ngoài

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `soundHealing(type, duration)` - Chữa trị bằng âm liệu
2. `getHealingHistory()` - Lấy lịch sử chữa trị
3. `getSettings()` - Lấy cài đặt chữa trị âm liệu
4. `getHistory()` - Lấy lịch sử chữa trị

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T96-sound-healing-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), âm liệu logic, DB