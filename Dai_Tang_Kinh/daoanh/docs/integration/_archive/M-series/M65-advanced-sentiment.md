# M65 · Advanced Sentiment Analytics cho Trình độ Tiến sĩ

**Spec · P2**

# M65 Phân tích cảm xúc nâng cao

Cung cấp mô hình phân tích cảm xúc nâng cao cho trình độ Tiến sĩ: theo dõi trạng thái tâm lý qua nội dung kinh đã đọc, phát hiện các xu hướng cảm xúc, và khuyên khích tu práctica phù hợp.

## Mục đích

Thực hiện mô hình Phật giáo fine-tuned cho phân tích cảm xúc: cho phép theo dõi trạng thái tâm lý hàng ngày, phát hiện các vùng cảm xúc cần chú ý, và xuất báo cáo tiến độ tu prática theo từng giai đoạn (niệm, sát, thấu).

## UI/UX

- **Trang Phân tích cảm xúc:** `/daoanh/sentiment/analyze`
  - Input: Đoạn kinh vừa đọc, ghi chú cá nhân (tùy chọn)
  - Output: Biểu đồ trạng thái cảm xúc ( Bình yên, Tranh tấn, Tâm lý, Nức lực)
  - Thời gian: Theo dõi hàng ngày, hàng tuần, hàng tháng

- **Trang Xuất bản tiến độ:** `/daoanh/sentiment/report`
  - Báo cáo cảm xúc: PDF kèm biểu đồ tiến độ
  - Xuất bản: Xuất bản vào bộ sưu tập cá nhân, hoặc chia sẻ với huấn luyện viên
  - Thống kê: Số lượng đoạn kinh đã đọc, điểm cảm xúc trung bình, xu hướng tăng/giảm

- **Trang Cài đặt cảm xúc:** `/daoanh/sentiment/settings`
  - Chọn mô hình cảm xúc: Tiếng Việt Phật giáo, English Buddhist
  - Thiết lập ngưỡng cảnh báo: Độ căng thẳng cao/trung bình/thấp
  - Kích hoạt khuyến khích: Phát tín hiệu khi trạng thái 개好转 (tốt lên)

## Dữ liệu

- **Mô hình cảm xúc:** Mô hình Phật giáo fine-tuned trên 10000+ đoạn trích kinh
- **Cảm xúc:** Bình yên, Tranh tấn, Tâm lý, Nức lực, Hoài nghi (mức 1-10)
- **Thời gian theo dõi:** Điểm dữ liệu mỗi đọc kinh xong, tổng hợp theo ngày/tuan/thang
- **Xã hội:** Khán giả cảm xúc chung cộng đồng (trung bình, phân bố)

## Acceptance criteria

- [ ] Phát hiện đúng 85% trạng thái cảm xúc so sánh với báo cáo của biên tập gia
- [ ] Tạo báo cáo PDF kèm biểu đồ trong 3 phút
- [ ] Tăng tiến độ tu práctica 25% qua nhận thức cảm xúc
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Lưu trữ dữ liệu riêng tư: Không gửi dữ liệu cảm xúc về máy chủ bên ngoài

## File tương tự

- `docs/integration/M65-advanced-sentiment.md`
- `docs/Mimo-Flash/T140-m65-advanced-sentiment.md`