# M38 · Phân tích nâng cao cho Tiến sĩ

**Spec · P2**

# M38 Hỗ trợ Phân tích dữ liệu Tu práctica nâng cao

Cung cấp công cụ phân tích sâu cho dữ liệu tu prática: tương thích suất, xu hướng tâm lý, và dự đoán tiến độ dựa trên dữ liệu lịch sử.

## Mục đích

Giúp thầy tọt và cơ quan quản lý đánh giá hiệu quả chương trình tu práctica, phát hiện xu hướng, và đưa ra các định hướng cải thiện dựa trên dữ liệu khoa học.

## UI/UX

- **Trang Tổng quan toàn cảnh:** `/daoanh/analytics/overview-advanced`
  - Tổng điểm tâm lý: Trending up/down so với kỳ trước
  - Biểu đồ tương thích suất: Theo tuần, theo tháng
  - Dự đoán tiến độ: Ngày hoàn thành mục tiêu dự kiến

- **Trang Phân tích tương thích:** `/daoanh/analytics/compatibility`
  - Phân tích giữa các phương pháp tu práctica khác nhau
  - Biểu đồ nhiệt: Mức tương thích giữa các kỹ thuật
  - Xuất báo cáo tương thích: PDF, CSV

- **Trang Dự đoán tiến độ:** `/daoanh/analytics/prediction`
  - Dự đoán ngày hoàn thành mục tiêu dựa trên lịch sử
  - Rủi ro dừng tu práctica: Cảnh báo khi hoạt động giảm sút
  - Khuyến nghị: Kỹ thuật tu práctica tốt nhất cho profile này

## Dữ liệu

- **Sự kiện tập luyện:** Duration, type, time-of-day, consistency
- **Chỉ số tâm lý:** Stress level, focus level, energy level (self-reported 1-10, weekly)
- **Kết quả tu práctica:** Success rate, improvement rate, dropout risk
- **Thời gian:** Ghi nhận hàng ngày, weekly aggregates

## Acceptance criteria

- [ ] Phân tích tương thích đúng 80% so sánh với đánh giá chuyên gia
- [ ] Dự đoán tiến độ có sai số dưới 15% so với kết quả thực tế
- [ ] Cảnh báo rủi ro dừng đúng 80% trường hợp có xu hướng giảm sút
- [ ] Xuất báo cáo PDF chứa đầy đủ biểu đồ và phân tích
- [ ] Tốc độ xử lý dữ liệu 1 năm dưới 3s

## File tương tự

- `docs/integration/M38-advanced-analytics.md`
- `docs/Mimo-Flash/T113-m38-advanced-analytics.md`