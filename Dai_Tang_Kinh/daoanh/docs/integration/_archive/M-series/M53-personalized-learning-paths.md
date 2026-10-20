# M53 · Học đường AI cá nhân hóa cho Tiến sĩ

**Spec · P2**

# M53 Học đường AI cá nhân hóa

Cung cấp lộ trình học tập AI cá nhân hóa cho trình độ Tiến sĩ: đề xuất khóa học, nghiên cứu, và tài nguyên dựa trên trình độ, mục tiêu, và lịch sử học tập.

## Mục đích

Tận dụng AI để tạo ra lộ trình học tập cá nhân hóa: đề xuất khóa học, tác phẩm nghiên cứu, và tài nguyên dựa trên trình độ hiện tại, mục tiêu dài hạn, và lịch sử học tập của mỗi người.

## UI/UX

- **Trang Lộ trình học tập:** `/daoanh/learning/path`
  - Hiển thị lộ trình đề xuất: Khóa học, Nghiên cứu, Tài nguyên
  - Tiến độ: % hoàn thành, thời gian còn lại để đạt mục tiêu
  - Tùy chọn: Điều chỉnh mục tiêu, thêm/loại bỏ khóa học

- **Trang Cài đặt cá nhân hóa:** `/daoanh/learning/settings`
  - Chọn mục tiêu: Nghiên cứu sâu, Triển khai ứng dụng, Dạy học
  - trình độ hiện tại: Tiểu học, Trung cấp, Cao đẳng, Nghiên cứu viên
  - Tần suất học tập: Mỗi ngày, mỗi tuần, mỗi tháng

- **TrangTheo dõi tiến độ:** `/daoanh/learning/progress`
  - Biểu đồ tiến độ: % hoàn thành theo thời gian
  - Mục tiêu đã đạt: Những mục tiêu đã hoàn thành
  - Khuyến nghị: Tài nguyên tiếp theo nên học

## Dữ liệu

- **Lịch sử học tập:** Query log, kết quả nghiên cứu, thời gian dành cho mỗi tác vụ
- **Mục tiêu cá nhân:** Mục tiêu đã thiết lập, tiến độ, ngày hoàn thành dự kiến
- **Khuyến nghị AI:** Khóa học, nghiên cứu, tài nguyên dựa trên mô hình học máy
- **Mức độ:** trình độ hiện tại, mục tiêu muốn đạt

## Acceptance criteria

- [ ] Lộ trình đề xuất đúng 80% cho 100试用 user có trình độ và mục tiêu różb
- [ ] Tỷ lệ hoàn thành lộ trình > 60% cho 80% user trong 3 tháng
- [ ] Mô hình AI tái training mỗi 3 tháng với dữ liệu mới
- [ ] Tương thích với thiết bị: Web, iOS, Android
- [ ] Tự động lưu tiến độ mỗi khi hoàn thành một mục tiêu

## File tương tự

- `docs/integration/M53-personalized-learning-paths.md`
- `docs/Mimo-Flash/T128-m53-personalized-learning-paths.md`