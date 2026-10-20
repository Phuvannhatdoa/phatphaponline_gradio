# M71 · Predictive Practice Paths using AI

**Spec · P2**

# M71 Đường exercise dự đoán bằng AI

Cung cấp đường exercise (practice path) dự đoán bằng AI: dựa trên trạng thái cảm xúc, mục tiêu, và lịch sử practice, AI đề xuất lộ trình tu pratica phù hợp cho từng giai đoạn (niệm, sát, thấu).

## Mục đích

Thực hiện mô hình dự đoán theo học Phật giáo: cho phép hệ thống dự đoán lộ trình tu pratica tối ưu: "Sau 30 ngày thiền tâm lý sẽ chuyển sang Vipassana", "Đạt ngưỡngfocus này thì nên thư giãn bằng Thiền thỏa", và theo dõi tiến độ thực tế so với dự đoán.

## UI/UX

- **Trang Dự đoán lộ trình:** `/daoanh/predict/path`
  - Input: Trạng thái cảm xúc hiện tại, mục tiêu (Tăng świadomoś, Giảm stress), Thời gian có sẵn
  - Output: Lộ trình đề xuất (7 ngày, 30 ngày, 90 ngày), các bước thực hiện
  - Xem tiến độ: So sánh thực tế vs dự đoán, điều chỉnh lộ trình

- **Trang Theo dõi dự đoán:** `/daoanh/predict/tracking`
  - Lịch sử dự đoán: Các lộ trình đã đề xuất, kết quả thực tế
  - Độ chính xác: Tỷ lệ dự đoán đúng so với kết quả thực tế
  - Phản hồi: Đánh giá lộ trình dự đoán (1-5 sao)

- **Trang Cài đặt dự đoán:** `/daoanh/predict/settings`
  - Chọn mô hình dự đoán: Mô hình cảm xúc, Mô hình lịch sử, Kết hợp cả hai
  - Thiết lập mục tiêu cá nhân: Mục tiêu tu práctica theo tiêu chí riêng
  - Thông báo: Kích hoạt nhắc nhở khi tiến độ đạt ngưỡng dự đoán

## Dữ liệu

- **Mô hình dự đoán:** Mô hình Phật giáo fine-tuned trên 10000+ user-session
- **Giai đoạn:** Niệm (Beginner), Săt (Intermediate), Thấu (Advanced)
- **Chỉ số chính xác:** 75%+ độ chính xác dự đoán lộ trình đúng
- **Thời gian cập nhật:** Mỗi ngày tự động tính toán lại lộ trình

## Acceptance criteria

- [ ] Dự đoán đúng 75% lộ trình tu prática theo đúng giai đoạn
- [ ] Tăng tỷ lệ hoàn thành lộ trình 30% qua khuyến nghị AI
- [ ] Tích hợp với Module M65 (Phân tích cảm xúc) và M68 (Lời khuyên trì tu)
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không chia sẻ dữ liệu cá nhân với bên thứ ba

## File tương tự

- `docs/integration/M71-predictive-paths.md`
- `docs/Mimo-Flash/T146-m71-predictive-paths.md`