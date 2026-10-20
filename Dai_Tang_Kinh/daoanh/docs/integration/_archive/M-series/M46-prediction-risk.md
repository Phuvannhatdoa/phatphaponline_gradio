# M46 · Dự đoán Rủi ro và Tiến độ cho Tiến sĩ

**Spec · P2**

# M46 Hỗ trợ Dự đoán rủi ro và Tiến độ

Cung cấp mô hình dự đoán rủi ro dừng tu práctica và tiến độ dựa trên dữ liệu lịch sử: phân tích xu hướng, cảnh báo sớm, và khuyến nghị can thiệp.

## Mục đích

Giúp thầy tọt và cơ quan quản lý phát hiện sớm những practitioner có nguy cơ dừng tập, và đưa ra các khuyến nghị can thiệp để duy trì tính liên tục của chương trình tu práctica.

## UI/UX

- **Trang Dashboard Rủi ro:** `/daoanh/prediction/risk`
  - Tổng quan: Số practitioner có rủi ro, mức độ rủi ro (Thấp/Trung bình/CAo)
  - Thống kê: % practitioner được can thiệp thành công
  - Danh sách: Practitioner có nguy cơ dừng tập sắp tới

- **Trang Cảnh báo sớm:** `/daoanh/prediction/early-warning`
  - Cảnh báo: Practitioner nào có hoạt động giảm sút
  - Lý do dự đoán: Thiếu tập luyện, thay đổi tham gia, v.v.
  - Khuyến nghị: Gửi nhắc nhở, gói quà thiền, v.v.

- **Trang Phản hồi can thiệp:** `/daoanh/prediction/intervention`
  - Hành động: Gửi nhắn tin, email, gọi điện
  - Kết quả: Thông lượng practitioner đã phản ứng, tiếp tục tập hay không
  - Lịch sử: Ghi nhận tất cả các lần can thiệp và kết quả

## Dữ liệu

- **Sự kiện tập luyện:** Duration, type, time-of-day, consistency (days/week)
- **Chỉ số hành vi:** Login frequency, query count, feature usage change
- **Chỉ tâm lý:** Self-reported stress, focus level weekly
- **Dự đoán:** Model machine learning (Random Forest, xác suất rủi ro 0-1)

## Acceptance criteria

- [ ] Dự đoán rủi ro đúng 80% so sánh với kết quả thực tế (practitioner dừng tập trong 30 ngày)
- [ ] Cảnh báo sớm phát hiện 75% practitioner có xu hướng giảm tập
- [ ] Khuyến nghị can thiệp có tỷ lệ phản ứng 70%+
- [ ] Hiển thị đúng danh sách practitioner có rủi ro
- [ ] Tốc độ xử lý dữ liệu 1 năm dưới 5s

## File tương tự

- `docs/integration/M46-prediction-risk.md`
- `docs/Mimo-Flash/T121-m46-prediction-risk.md`