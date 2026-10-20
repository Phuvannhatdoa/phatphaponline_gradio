# M91 · Temporal Dharma Journey Tracking

**Spec · P2**

# M91 Theo dõi hành trình Dharma theo thời gian

Cung cấp hệ thống theo dõi hành trình Dharma theo thời gian: ghi nhận và trực quan hóa quá trình tu práctica practitioner theo thời gian, từ người mới bắt đầu đến trình độ tiến sĩ, và cung cấp các milestones đánh dấu.

## Mục đích

Thực hiện timeline tracking cho Dharma: cho phép practitioner xem nhận lộ trình tu práctica của mình, đánh dấu các điểm mốc quan trọng (đầu tiên đọc kinh, nhập môn,증명证书 đạt được), và nhận được khuyến khích khi đạt các milestone.

## UI/UX

- **Trang Hành trình Dharma:** `/daoanh/journey/track`
  - Hiển thị tiến độ: Tổng thời gian práctica, số lượng Kinh đã đọc, số retreat đã tham gia
   - Biểu đồ thời gian: Theo cấp hiệu (tháng/năm), xu hướng tăng/giảm
   - Milestones: Điểm mốc đã đạt, điểm mốc tới

- **Trang Điểm mốc:** `/daoanh/journey/milestones`
  - Danh sách điểm mốc: "Đọc đầu tiên Kinh", "Tham gia retreat đầu tiên", "Hoàn thành đọc toàn bộ 84 Kinh"
   - Trạng thái: Đã đạt/chưa đạt, ngày đạt
   - Phần thưởng: Badges, điểm reputation

- **Trang Xem lại:** `/daoanh/journey/retrospective`
  - Xem lại lịch sử: Review quá khứ 1 tháng, 6 tháng, 1 năm
   - Phân tích: Phân tích xu hướng practice, thay đổi thái độ
   - Xuất báo cáo: PDF kèm biểu đồ tiến độ

## Dữ liệu

- **Con số practice:** Ngày pratica, phút práctica, Kinh đã đọc, retreat tham gia
- **Điểm mốc:** 20+ điểm mốc Phật giáo được định nghĩa sẵn
- **Thời gian theo dõi:** Tất cả lịch sử practice từ ngày đầu tiên
- **Thống kê:** 10+ chỉ số thống kê práctica qua thời gian

## Acceptance criteria

- [ ] Ghi nhận đúng 100% prática history cho practitioner tích cực
- [ ] Hiển thị đúng 80% điểm mốc qua thời gian
- [ ] Tăng retention practitioner 20% qua visualization tiến độ
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Tất cả dữ liệu lưu trên thiết bị user

## File tương tự

- `docs/integration/M91-temporal-dharma-journey.md`
- `docs/Mimo-Flash/T167-m91-temporal-dharma-journey.md`