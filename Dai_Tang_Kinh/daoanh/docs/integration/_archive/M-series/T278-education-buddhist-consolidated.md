# T278 · Buddhist Education Course Management

> Đổi số ngày 2026-10-10: M1 (trùng số kế hoạch M-series) → T278. Nội dung không đổi.

**Status:** 📄 Consolidated Documentation  
**Module:** M1  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp hệ thống quản lý khóa học Phật giáo: cho phép nhà giáo tạo, theo dõng và quản lý khóa học Phật giáo từ sơ cấp đến nâng cao, kèm theo track tiến độ học sinh và xuất bản certificate.

## UI/UX

- **Trang Quản lý khóa học:** `/daoanh/education/courses`
  - Hiển thị danh sách khóa học: Tên, mô tả, giáo viên, số học sinh, tiến độ
   - Tạo khóa học mới: Tên khóa học, mô tả, nội dung, giai đoạn (Sơ cấp, Nâng cao, Chuyên sâu)
   - Sửa/xóa khóa học: Cập nhật thông tin, thay đổi giáo viên hoặc nội dung

- **Trang Theo dõng tiến độ:** `/daoanh/education/progress`
  - Hiển thị tiến độ học sinh: % hoàn thành, bài học đã xong, bài học chờ
   - Biểu đồ tiến độ: Theo tuần, theo tháng, theo khóa học
   - Xuất báo cáo: PDF kèm bảng tiến độ học sinh

- **Trang Chi tiết bài học:** `/daoanh/education/lesson`
  - Hiển thị nội dung bài học: Văn bản, ảnh, video nhúng
   - Phản hồi: Học sinh đánh giá bài học (1-5 sao)
   - Tìm kiếm: Tìm từ khóa trong bài học

## Dữ liệu

- **Khóa học:** 50+ khóa học Phật giáo kèm thông tin giáo viên và mô tả
- **Học sinh:** 1000+ học sinh enrolled kèm tiến độ cá nhân
- **Bài học:** 500+ bài học kèm nội dung đa phương thức
- **Certificate:** Certificate mẫu cho mỗi mức hoàn thành khóa học

## Acceptance criteria

- [ ] Tạo khóa học trong 5 phút với đầy đủ thông tin
- [ ] Theo dõng tiến độ học sinh đúng 90% so với survey trực tiếp
- [ ] Tạo certificate tùy chỉnh cho mỗi khóa học
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Chỉ hiển thị dữ liệu cho giáo viên và admin

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `createCourse(name, description, teacher, level)` - Tạo khóa học mới
2. `enrollStudent(courseId, studentId)` - Đăng ký học sinh vào khóa học
3. `updateProgress(courseId, studentId, lessonId, completed)` - Cập nhật tiến độ học sinh
4. `generateCertificate(courseId, studentId)` - Tạo certificate cho học sinh hoàn thành

**File path:** `docs/Mimo-Flash/M1-education-buddhist-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created)