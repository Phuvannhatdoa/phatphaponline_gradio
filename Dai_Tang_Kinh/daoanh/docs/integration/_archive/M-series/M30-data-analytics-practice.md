# M30 · Phân tích dữ liệu tu práctica cho Tiến sĩ

**Spec · P2**

# M30 Hệ thống phân tích và báo cáo dữ liệu tu prática

Cung cấp công cụ phân tích dữ liệu nâng cao cho dữ liệu tu pratica: thống kê độ thường, xu hướng theo thời gian, và các chỉ số tâm lý để hỗ trợ thầy tọt và nhà nghiên cứu.

## Mục đích

Động lực từ dữ liệu để tối ưu hóa chương trình tu práctica, đo lường hiệu quả các phương pháp tập luyện, và cung cấp báo cáo chính xác cho cơ quan quản lý.

## UI/UX

- **Trang Tổng quan:** `/daoanh/analytics/overview`
  - Tổng lượt tập luyện: Số buổi/tháng/năm
  - Biểu đồ xu hướng: Thăng giảm theo mùa, theo ngày trong tuần
  - Top 5 bài tập phổ biến nhất

- **Trang Chỉ số tâm lý:** `/daoanh/analytics/psychology`
  - Điểm tâm lý: Tăng/giảm theo thời gian
  - Phân tích: Mối liên hệ giữa thời gian tập luyện và mức điểm
  - Biểu đồ nhiệt: Mức stress, trạng thái tăng năng lượng

- **Trang Báo cáo chi tiết:** `/daoanh/analytics/report`
  - Xuất báo cáo PDF/CSV cho kỳ tu pratica cụ thể
  - Bao gồm: Thời gian tập luyện, kết quả quiz, development trajectory
  - Chia sẻ với thầy tọt hoặc cơ quan quản lý

## Dữ liệu

- **Sự kiện tập luyện:** Query log, result record, session duration
- **Chỉ số tâm lý:** Stress level, focus level, energy level (self-reported 1-10)
- **Kết quả quiz:** Accuracy, speed, improvement rate
- **Thời gian:** Ghi nhận hour/minute/second cho mỗi session

## Acceptance criteria

- [ ] Phân tích xu hướng đúng 90% so sánh với dữ liệu thô
- [ ] Xuất báo cáo PDF chứa đầy đủ tiêu đề và dữ liệu thống kê
- [ ] Biểu đồ nhiệt phản ánh đúng mức độ thay đổi theo thời gian
- [ ] Tốc độ xử lý truy vấn dữ liệu < 2s cho 1 năm log
- [ ] Tích hợp với hệ thống push notification khi có báo cáo mới

## File tương tự

- `docs/integration/M30-data-analytics-practice.md`
- `docs/Mimo-Flash/T105-m30-data-analytics-practice.md`