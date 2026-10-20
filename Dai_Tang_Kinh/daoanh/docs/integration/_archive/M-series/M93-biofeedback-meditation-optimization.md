# M93 · Biofeedback Meditation Optimization

**Spec · P2**

# M93 Tối ưu hóa méditation Biofeedback

Cung cấp hệ thống tối ưu hóa méditation biofeedback: theo dõi và điều chỉnh các tham số Physiological (nhịp đ tim, thở, căng thẳng) để tối ưu hóa trạng thái méditation theo thời gian thực.

## Mục đích

Thực hiện biofeedback cho méditation: cho phép practitioner theo dõi nhịp đ tim, tỷ lệ thở, mức căng thẳng qua cảm biến, và nhận được phản hồi tức thời để điều chỉnh tư thế, nhịp thở, để đạt được trạng thái méditation sâu nhanh hơn.

## UI/UX

- **Trang Biofeedback méditation:** `/daoanh/biofeedback/monitor`
  - Hiển thị các tham số sinh lý: Nhịp tim (bpm), Tỷ lệ thở (breaths/min), Mức căng thẳng (stress level 1-10)
   - Biểu đồ thời gian thực: Đồng bộ hóa các tham số sinh lý với trạng thái méditation
   - Phản hồi tức thời: "Hãy hít sâu 3 lần" hoặc "Điều chỉnh tư thế ngồi"

- **Trang Tối ưu hóa:** `/daoanh/biofeedback/optimize`
  - Kế hoạch tối ưu: Khuyên hướng nhịp thở, tư thế méditation cho session tới
   - Theo dõi tiến độ: So sánh hiệu quả trước và sau khi tối ưu

- **Trang Cài đặt:** `/daoanh/biofeedback/settings`
  - Chọn cảm biến: Tim (HR), Thở ( respiration), Căng thẳng (Galvanic skin response)
   - Thiết lập ngưỡng cảnh báo: Nhịp tim cao/trung bình/thấp, Căng thẳng cao/trung bình/thấp
   - Thông báo: Kích hoạt nhắc nhở khi đạt ngưỡng mới

## Dữ liệu

- **Cảm biến:** Mạch đHeart Rate Monitor, Thai đo đếm, GSR skin conductance sensor
- **Tham số phân tích:** 20+ physiological parameters theo dõi
- **Thời gian thực:** Phản hồi từ cảm biến đến hiển thị < 500ms
- **Thiết bị hỗ trợ:** Apple Watch, Fitbit, Garmin, các cảm biến riêng tư

## Acceptance criteria

- [ ] Theo dõi đúng 85% các tham số sinh lý qua cảm biến
- [ ] Phản hồi tức thời < 500ms từ tín hiệu cảm biến
- [ ] Tăng độ sâu méditation 20% qua tối ưu hóa biofeedback
- [ ] Tương thích với Apple Watch, Fitbit, Garmin, cảm biến riêng
- [ ] Bảo mật dữ liệu: Tất cả dữ liệu lưu trên thiết bị user

## File tương tự

- `docs/integration/M93-biofeedback-meditation-optimization.md`
- `docs/Mimo-Flash/T169-m93-biofeedback-meditation-optimization.md`