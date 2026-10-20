# M40 · Phân tích hành vi người dùng cho Tiến sĩ

**Spec · P2**

# M40 Hỗ trợ Phân tích hành vi người dùng nâng cao

Cung cấp báo cáo chi tiết về cách người dùng tương tác với hệ thống: đường đi truy vấn, tính retention, và đặc điểm dân số (tổng hợp không cá nhân hóa).

## Mục đích

Đỗ cơ quan quản lý và thầy tọt nhìn nhận cách người dùng tương tác với hệ thống, từ đó cải thiện chức năng, nội dung, và trải nghiệm người dùng.

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

## File tương tự

- `docs/integration/M40-user-behavior-analytics.md`
- `docs/Mimo-Flash/T115-m40-user-behavior-analytics.md`