# M30 · Buddhist Data Analytics for Practice

**Status:** 📄 Consolidated Documentation  
**Module:** M30  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp analytics dữ liệu practice Phật học: theo dõng độ sâu méditation, tỷ lệ hoàn thành, và đánh giá hiệu quả practice theo thời gian.

## UI/UX

- **Trang Analytics practice:** `/daoanh/practice/analytics`
  - Hiển thị chỉ số: Thời lượng méditation, số lượng Kinh đã đọc, số retreat tham gia
   - Biểu đồ thời gian thực: Theo ngày/Tuần/Tháng/Năm

- **Trang Đánh giá hiệu quả:** `/daoanh/practice/effectiveness`
  - Đánh giá: Điểm trước và sau practice (1-100)
   - Phân tích xu hướng: Tăng/cảm giảm practice qua thời gian

- **Trang Cài đặt:** `/daoanh/practice/settings`
  - Chọn metrics: Chọn metrics muốn theo dõng
   - Thiết lập ngưỡng: Ngưỡng cảnh báo practice
   - Thông báo: Kích hoạt email báo cáo định kỳ

## Dữ liệu

- **Chỉ số practice:** 15+ chỉ số practice theo dõng
- **Thời gian theo dõng:** Hàng ngày, hàng tuần, hàng tháng, năm
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop
- **Thống kê:** 1000+ dữ liệu practice theo dõng

## Acceptance criteria

- [ ] Theo dõng 15+ chỉ số practice chính xác 90% so với survey trực tiếp
- [ ] Đánh giá hiệu quả practice đúng 85% so với kết quả thực tế
- [ ] Biểu đồ thời gian thực cập nhật dưới 5s
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không phân phối dữ liệu practice về bên thứ ba

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `trackPractice(session)` - Theo dõng session practice
2. `getEffectivenessScore(userId)` - Lấy điểm đánh giá hiệu quả
3. `getAnalyticsReport(period)` - Lấy báo cáo analytics cho khoảng thời gian
4. `getSettings()` - Lấy cài đặt practice

**File path:** `docs/Mimo-Flash/M30-data-analytics-practice-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), practice analytics DB