# M95 · Mindfulness-Based Stress Reduction Analytics

**Spec · P2**

# M95 Phân tích Giảm căng thiền dựa trên Mindfulness

Cung cấp hệ thống phân tích Giảm căng thiền dựa trên Mindfulness: theo dõi mức căng thiền, đánh giá hiệu quả practice mindfulness, và đề xuất các practice cụ thể để giảm căng thiền.

## Mục đích

Thực hiện analytics cho mindfulness-based stress reduction (MBSR): cho phép practitioner theo dõi mức căng thiền hàng ngày, đánh giá hiệu quả các practice mindfulness, và nhận được các đề xuất practice để giảm căng thiền theo khoa học.

## UI/UX

- **Trang Phân tích căng thiền:** `/daoanh/stress_analysis/track`
  - Hiển thị mức căng thiền hiện tại: Cấp độ 1-10, biểu đồ thay đổi qua ngày
   - Phân tích nguyên nhân: Phát hiện nguyên nhân căng thiền chính (làm việc, quan hệ, tài chính,...)

- **Trang Đánh giá hiệu quả:** `/daoanh/stress_analysis/effectiveness`
  - Đánh giá hiệu quả practice: Điểm trước và sau practice (1-100)
   - Phân tích xu hướng: Tăng/cảm giảm căng thiền qua tuần/tháng

- **Trang Khuyên nghị practice:** `/daoanh/stress_analysis/recommend`
  - Khuyên hướng practice: "Thiền 10 phút", "Vayu Mudra", "Body scan 15 phút"
   - Lý do khuyên nghị: Từ mô hình AI phân tích nguyên nhân căng thiền

## Dữ liệu

- **Tham số theo dõi:** 15+ physiological và psychological parameters (nhịp tim, độ thở, căng thiền, giấc ngủ,...)
- **Mô hình đánh giá:** Mô hình Phật giáo fine-tuned cho MBSR (chạy offline)
- **Thời gian theo dõi:** Hàng ngày, hàng tuần, hàng tháng
- **Thiết bị hỗ trợ:** Apple Watch, Fitbit, Garmin, cảm biến riêng

## Acceptance criteria

- [ ] Theo dõi đúng 85% mức căng thiền qua cảm biến
- [ ] Đánh giá hiệu quả practice đúng 80% so với survey trực tiếp
- [ ] Tăng hiệu quả giảm căng thiền 30% qua khuyến nghị AI
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Tất cả dữ liệu lưu trên thiết bị user

## File tương tự

- `docs/integration/M95-mindfulness-stress-reduction-analytics.md`
- `docs/Mimo-Flash/T171-m95-mindfulness-stress-reduction-analytics.md`