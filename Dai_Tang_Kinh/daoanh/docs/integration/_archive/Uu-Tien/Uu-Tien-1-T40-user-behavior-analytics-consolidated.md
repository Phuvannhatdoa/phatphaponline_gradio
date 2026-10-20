# M40 · User Behavior Analytics

**Status:** 📄 Consolidated Documentation  
**Module:** M40  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp báo cáo chi tiết về cách người dùng tương tác với hệ thống: đường đi truy vấn, tính retention, và đặc điểm dân số (tổng hợp không cá nhân hóa).

## UI/UX

- **Trang Tổng quan hành vi:** `/daoanh/behavior/overview`
  - Tổng truy vấn: hôm/năm
  - Top truy vấn: 10 từ khóa phổ biến
  - Retention rate: Người dùng quay lại trong 7/30/90 ngày
  - Phân bố khu vực: Quốc gia (tổng hợp, không cá nhân)

- **Trang Đường đi truy vấn:** `/daoanh/behavior/journey`
  - Thuo trình: Từ khóa -> Kết quả -> Hành động sau (click, share, dismiss)
  - trực quan hóa: Diagram dòng chảy cho từng bước
  - Xuất biểu đồ: PNG, SVG

- **Trang Phân tán hoạt động:** `/daoanh/behavior/distribution`
  - Thời gian sử dụng trung bình mỗi ngày
  - Phân bố tính năng được sử dụng nhiều nhất
  - Biểu đồ nhiệt: Giờ cao điểm sử dụng

## Dữ liệu

- **Sự kiện truy vấn:** query_text, result_clicked, result_shared, time_spent
- **Sự kiện đăng nhập:** login_count, last_login, retention_day_7/30/90
- **Phân tán khu vực:** Country-level (tổng hợp, không IP cá nhân)
- **Thời gian:** Ghi nhận theo giờ máy chủ, chuyển đổi về múi giờ địa lý

## Acceptance criteria

- [ ] Báo cáo xuất PDF chứa đầy đủ biểu đồ và dữ liệu thống kê
- [ ] Retention rate tính đúng so với cohort analysis
- [ ] Đường đi truy vấn trực quan hóa đúng 100% bước đi
- [ ] Phân tán hoạt động hiển thị đúng theo khu vực Quốc gia
- [ ] Tốc độ truy vấn dữ liệu < 2s cho 1 năm log

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getBehaviorOverview()` - Lấy tổng quan hành vi
2. `getQueryJourney()` - Lấy đường đi truy vấn
3. `getActivityDistribution()` - Lấy phân tán hoạt động
4. `exportReport(format)` - Xuất báo cáo (PDF/SVG)

**File path:** `docs/Mimo-Flash/M40-user-behavior-analytics-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), Query event tracking, Retention calculation, Charting library (D3/Chart.js)