# M85 · Buddhist Incense Calculator

**Status:** 📄 Consolidated Documentation  
**Module:** M85  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp máy tính hoa phiến Phật tử: tính toán số lượng hoa phiến cần thiết cho pratica méditation, nghi tạc, và các dịp lễ tết Phật tử dựa trên số lượng practitioner và thời gian pratica.

## UI/UX

- **Trang Tính toán hoa phiến:** `/daoanh/incense-calculator`
  - Input: Số lượng practitioner, Thời lượng pratica, Loại pratica (thiền, nghi tạc, lễ tết)
   - Kết quả: Số lượng hoa phiến cần thiết, số lượng hoa phiến theo từng loại (bình thường, nhiều, ít)
   - Xuất báo cáo: Xuất báo cáo hóa đơn ra file PDF

- **Trang Lịch sử tính toán:** `/daoanh/incense-calculator/history`
  - Lịch sử: Các lần tính toán trước, thống kê qua thời gian (ngày/tháng/năm)
   - Phân tích: Loại hương được tính toán nhiều nhất, xu hướng số lượng

- **Trang Cài đặt:** `/daoanh/incense-calculator/settings`
  - Chọn loại pratica mặc định: Loại pratica được thực hiện thường xuyên
   - Thiết lập ngưỡng cảnh báo: Cảnh báo khi số lượng hoa phiến dưới ngưỡng (cấu hình số lượng còn lại)
   - Thông báo: Kích hoạt nhắc nhở khi đến thời điểm补充 hoa phiến

## Dữ liệu

- **Chế độ tính toán:** 3 chế độ chính (thiền, nghi tạc, lễ tết)
- **Ngưỡng cảnh báo:** Có thể tùy chỉnh (mặc định: dưới 10 bình)
- **Thời gian theo dõng:** Hàng ngày, hàng tuần, hàng tháng
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Tính toán đúng số lượng hoa phiến theo chế độ prática
- [ ] Phát hiện ngưỡng cảnh báo đúng 90% qua thời gian thực
- [ ] Lịch sử tính toán đúng 80% qua 30 ngày
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không lưu trữ số liệu cálculo nhạy cảm

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getIncenseCalculator()` - Lấy máy tính hoa phiến
2. `calculateIncense(practitionerCount, duration, type)` - Tính toán hoa phiến
3. `getSettings()` - Lấy cài đặt hoa phiến
4. `getHistory()` - Lấy lịch sử tính toán

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T85-incense-calculator-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), incense calculator logic, DB