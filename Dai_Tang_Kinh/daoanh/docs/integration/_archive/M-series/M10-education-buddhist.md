# M10 · Nền giáo dục và đào tạo Phật giáo

**Spec · P2**

# M10 Giáo dục và đào tạo Phật học

Khóa học Phật học, đào tạo hệ thống: course management, learning outcomes, certificate generation, progress tracking.

## Mục đích

Xây dựng hệ thống quản lý khóa học Phật học, theo dõi kết quả học tập và cấp chứng chỉ.

## UI/UX

- **Trang quản lý khóa học:** `/daoanh/course/management`
  - Quản lý syllabus, lectures, assignments
  - Theo dõi enrollment, completion rate

- **Trang outcomes tracking:** `/daoanh/learning/outcomes`
  - Đặt learning outcomes, track achievement
  - Heatmap kiến thức theo topic/concept

- **Trang certificate:** `/daoanh/certificate/generator`
  - Tạo certificate hoàn thành khóa học kèm badge
  - QR code verification
  - Xuất PDF kèm metadata

- **Trang progress tracking:** `/daoanh/student/progress`
  - Theo dõi progress student
  - Assessment results, quiz scores
  - Progress theo Bloom's taxonomy

## Dữ liệu

- **Dharma Drum Institute** – Khóa học Phật học chính thức (CC BY-NC-SA)
- **Dharma College** – Higher education Buddhist studies (CC BY-NC)
- **Buddhist Studies Portal** – Các bài giảng mở (OpenCourseWare) (CC BY)

## Acceptance criteria

- [ ] Course management quản lý 20+ khóa học cấp bậc khác nhau
- [ ] Certificate xuất PDF kèm QR code verification
- [ ] Progress tracking hiển thị heatmap theo topic/concept
- [ ] Assessment auto-grade cho 80%+ câu hỏi trắc nghiệm
- [ ] Learning outcomes measurable theo Bloom's taxonomy

## File tương tự

- `docs/integration/M10-education-buddhist.md`