# M70 · Buddhist Mindfulness Statistics

**Status:** 📄 Consolidated Documentation  
**Module:** M70  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp thống kê thính lực Phật học: theo dõng và phân tích các chỉ số thính lực qua thời gian, bao gồm số session, thời lượng trung bình, độ phức tạp cảm xúc, và các xu hướng thống kê khác.

## UI/UX

- **Trang Thống kê thính lực:** `/daoanh/stats/mindfulness`
  - Hiển thị các chỉ số: Số session méditation, Thời lượng trung bình, Phần trăm session hoàn thành, Xu hướng qua thời gian
   - Bộ lọc: Theo ngày/tháng/năm, theo thiết bị, theo cảm xúc
   - Biểu đồ: Đồ cột, đồ đường, đồ tròn cho các chỉ số khác nhau

- **Trang Phân tích xu hướng:** `/daoanh/stats/trends`
  - Phân tích xu hướng: Thay đổi số session, thời lượng, độ phức tạp qua thời gian
   - Biểu đồ so sánh: So sánh thực tế với dự đoán, phát hiện anomaly (thống kê bất thường)

- **Trang Cài đặt thống kê:** `/daoanh/stats/settings`
  - Chọn chỉ số hiển thị: Chọn các chỉ số muốn hiển thị trên bảng điều khiển
   - Thiết lập ngưỡng cảnh báo: Cảnh báo khi session giảm/thu hoặc thời lượng thay đổi đáng kể
   - Xuất báo cáo: Xuất báo cáo thống kê ra file PDF hoặc JSON

## Dữ liệu

- **Chỉ số:** 20+ chỉ số thống kê thính lực chính
- **Thời gian theo dõng:** Hàng ngày, hàng tuần, hàng tháng, năm
- **Biểu đồ:** 5+ loại biểu đồ khác nhau (cột, đường, tròn, khuếchart, progress bar)
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Hiển thị đúng 20+ chỉ số thống kê chính xác
- [ ] Phân tích xu hướng đúng 80% qua 30 ngày
- [ ] Tạo báo cáo thống kê trong 5 phút
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không chia sẻ dữ liệu thống kê nhạy cảm với bên thứ ba

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getMindfulnessStats(filter)` - Lấy thống kê thính lực
2. `getTrendAnalysis(period)` - Phân tích xu hướng
3. `getSettings()` - Lấy cài đặt thống kê
4. `exportReport(format)` - Xuất báo cáo thống kê

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T70-mindfulness-stats-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), thống kê DB, biểu đồ library