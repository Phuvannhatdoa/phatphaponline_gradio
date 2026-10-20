# M23 · Hệ thống đề xuất Kinh cá nhân hóa cho Cử Nhân

**Spec · P1**

# M23 Tối ưu đề xuất dựa trên sở thích cá nhân

Cung cấp hệ thống đề xuất kinh tự động cho trình độ Cử Nhân dựa trên lịch sử đọc, sở thích, và thời gian tu práctica.

## Mục đích

Tăng cường sự tham gia của người dùng bằng cách đề xuất các kinh mà phù hợp với nền tảng tâm lý, lịch sử tương tác, và目标학습 mål của mỗi người.

## UI/UX

- **Trang Đề xuất cá nhân:** `/daoanh/recommendations/personal`
  - Danh sách kinh đề xuất hiển thị trên basis "Vì bạn đọc Kinh X..."
  - Tùy chọn: Thêm vào "Kinh yêu thích", "Đọc lúc sau"
  - Hiện lý do đề xuất: "Bạn vừa đọc Kinh về Tâm lý, nên thử Kinh về Thiền"

- **Trang Điều chỉnh sở thích:** `/daoanh/recommendations/settings`
  - Trượt trái/phải: Thích/Không thích
  - Chọn chủ đề: Thiền, Luật, Sutra, Tâm lý
  - Thiết lập tần suất: Mỗi ngày, mỗi tuần, mỗi tháng

- **Trang thống kê:** `/daoanh/recommendations/analytics`
  - Tỷ lệ click-through đề xuất
  - Biểu đồ tiến độ đọc theo chủ đề
  - Top 10 Kinh được đề xuất nhất

## Dữ liệu

- **Lịch sử đọc:** Tracking query + result_click trong 90 ngày gần nhất
- **Thẻ chủ đề:** Mỗi kinh được gán 1-3 chủ đề (Tâm lý, Luật, Sutra, Thiền, Sống độ...)
- **Cảm thích người dùng:** Thumbs up/down cho mỗi đề xuất, lưu trong user profile
- **Thời gian:** Đề xuất dựa trên thời gian user thường xuyên đọc (sáng, trưa, tối)

## Acceptance criteria

- [ ] Hệ thống đề xuất hoạt động trên 80% user có lịch sử đọc > 5 kinh
- [ ] Tỷ lệ click-through đề xuất > 20% cho 100 trial user
- [ ] User có thể điều chỉnh sở thích và thấy thay đổi trong 24h
- [ ] Hiển thị lý do đề xuất rõ ràng cho mỗi kinh
- [ ] Tự động tắt đề xuất nếu user không tương tác trong 14 ngày

## File tương tự

- `docs/integration/M23-personalized-recommendations.md`
- `docs/Mimo-Flash/T98-m23-personalized-recommendations.md`