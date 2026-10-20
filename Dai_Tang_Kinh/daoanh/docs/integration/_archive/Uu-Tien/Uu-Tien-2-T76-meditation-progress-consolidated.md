# M76 · Buddhist Meditation Progress

**Status:** 📄 Consolidated Documentation  
**Module:** M76  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp theo dõng tiến độ méditation: theo dõng và phân tích tiến độ méditation cá nhân qua thời gian, bao gồm số session, thời lượng, độ sâu méditation, và các chỉ số tiến độ khác.

## UI/UX

- **Trang Tiến độ méditation:** `/daoanh/progress`
  - Hiển thị tiến độ: Phần trăm session hoàn thành, Thời lượng tổng méditation, Độ sâu méditation trung bình
   - Bộ lọc: Theo ngày/tháng/năm, theo thiết bị, theo cảm xúc
   - Biểu đồ: Đồ cột tiến độ, đồ đường thời lượng, đồ tròn độ sâu

- **Trang Phân tích chi tiết:** `/daoanh/progress/detailed`
  - Phân tích chi tiết: Thay đổi tiến độ qua thời gian, phát hiện anomaly (thống kê bất thường)
   - So sánh: So sánh tiến độ thực tế với dự đoán

- **Trang Cài đặt:** `/daoanh/progress/settings`
  - Chọn chỉ số hiển thị: Chọn các chỉ số muốn hiển thị trên bảng điều khiển
   - Thiết lập mục tiêu: Mục tiêu session/thời lượng/độ sâu theo định nghĩa riêng
   - Xuất báo cáo: Xuất báo cáo tiến độ ra file PDF hoặc JSON

## Dữ liệu

- **Chỉ số:** 15+ chỉ số tiến độ méditation chính
- **Thời gian theo dõng:** Hàng ngày, hàng tuần, hàng tháng, năm
- **Biểu đồ:** 4+ loại biểu đồ khác nhau (cột, đường, tròn, progress bar)
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Hiển thị đúng 15+ chỉ số tiến độ chính xác
- [ ] Phân tích tiến độ đúng 80% qua 30 ngày
- [ ] Tạo báo cáo tiến độ trong 5 phút
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không chia sẻ dữ liệu tiến độ nhạy cảm với bên thứ ba

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getMeditationProgress(filter)` - Lấy tiến độ méditation
2. `getDetailedAnalysis(period)` - Phân tích chi tiết tiến độ
3. `getSettings()` - Lấy cài đặt tiến độ
4. `exportReport(format)` - Xuất báo cáo tiến độ

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T76-meditation-progress-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), tiến độ DB, biểu đồ library