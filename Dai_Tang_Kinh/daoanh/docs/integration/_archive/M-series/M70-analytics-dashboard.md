# M70 · Advanced Analytics Dashboard cho Nhà Giáo Phật

**Spec · P2**

# M70 Bảng điều khiển Phân tích Nâng cao

Cung cấp bảng điều khiển phân tích cho các nhà giáo Phật: thống kê người dùng, độ bao trùm kinh đọc, và chỉ số tu prática để hỗ trợ quản lý và điều chỉnh chương trình dạy Phật.

## Mục đích

Triển khai analytics đen cho giáo Phật: cho phép nhà giáo theo dõi lượng người dùng, phân tích độ bao trùm các đoạn kinh phổ biến, và đo lường hiệu quả các chương trình tu práctica theo bối cảnh cụ thể.

## UI/UX

- **Trang Bảng điều khiển:** `/daoanh/analytics/dashboard`
  - Thống kê tổng quan: Số user hoạt động, đọc kinh hôm nay, số liệu tu práctica
  - Biểu đồ tương tác: Phân bố user theo thời gian, độ phổ biến kinh
  - Bộ lọc: Chọn khoảng thời gian, nhà trang, chương trình cụ thể

- **Trang Phân tích độ bao trùm:** `/daoanh/analytics/coverage`
  - Độ bao trùm theo đoạn kinh: 백분율 (0-100%) user đã đọc từng kinh
  - Phân tích vùng dead: Đoạn kinh ít người đọc, cần chú trọng
  - Xuất báo cáo: PDF kèm đồ thị độ bao trùm

- **Trang Đo lường hiệu quả:** `/daoanh/analytics/effectiveness`
  - Chỉ số: Tỷ lệ hoàn thành trì tu, thay đổi thái độ qua khảo sát
  - Phân loại chương trình: Retreat, Talk, Workshop, Online course
  - Báo cáo chi tiết: Theo từng chương trình, từng giai đoạn

- **Trang Cài đặt:** `/daoanh/analytics/settings`
  - Chọn dữ liệu hiển thị: User activity, Kinh coverage, Effectiveness metrics
  - Thiết lập thời gian: Tuần trước, Tháng trước, Quý này, Năm nay
  - Xuất bản: Xuất báo cáo PDF, Excel, hoặc chia sẻ trực tiếp

## Dữ liệu

- **Con số user:** 2865 monk names, activity log mỗi đọc kinh
- **Biểu đồ độ bao trùm:** 500+ đoạn kinh phổ biến, phân bố 0-100%
- **Chỉ số hiệu quả:** 20+ chỉ số tu práctica (tiến độ méditation, thay đổi thái độ)
- **Thời gian thực:** Cập nhật mỗi giờ, lưu trữ lịch sử 1 năm

## Acceptance criteria

- [ ] Tải báo cáo trong 3s với dữ liệu 10000+ user
- [ ] Phân tích độ bao trùm đúng 90% so sánh với khảo sát trực tiếp
- [ ] Tăng hiệu quả chương trình tu práctica 20% qua dựa trên analytics
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Chỉ cho phép admin xem báo cáo chi tiết

## File tương tự

- `docs/integration/M70-analytics-dashboard.md`
- `docs/Mimo-Flash/T145-m70-analytics-dashboard.md`