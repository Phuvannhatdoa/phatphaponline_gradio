# M28 · Học đồ số (Online Course Management) cho Tiến sĩ

**Spec · P2**

# M28 Hệ thống quản lý khóa học trực tuyến

Cung cấp nền khung quản lý khóa học Phật giáo trực tuyến: tạo khóa học, video bài giảng, đánh giá, và certificate hoàn thành cho trình độ Tiến sĩ và cơ quan đào tạo.

## Mục đích

Đỗ các cơ sở đào tạo, thầy tọt able tạo và bán khóa học trực tuyến, theo dõi tiến độ học tập, và cấp chứng chỉ cho sinh viên không thể đến trực tiếp chùa.

## UI/UX

- **Trang Dashboard giáo viên:** `/daoanh/course/teacher`
  - Tạo khóa học mới: Tiêu đề, mô tả, tải video, cài đặt phí (nếu có)
  - Quản lý khóa học: Danh sách tất cả khóa, trạng thái (Đang mở, Đóng, Hoàn thành)
  - Biểu đồ tiến độ: Số lượng sinh viên, phầnTrình trung, hoàn thành

- **Trang Đăng ký học:** `/daoanh/course/enroll`
  - Chi tiết khóa học: Preview video đầu, Mục tiêu học tập, Thời lượng
  - Nút Đăng ký: Đăng ký với email/tài khoản
  - Trình tự bài học: Theo dõi bài đã xem, bài chưa xem

- **Trang Học tập:** `/daoanh/learning/study`
  - Video bài giảng hiện tại, các phần trước/tiếp theo
  - Quiz đánh giá: Trắc nghiệm, câu tự luận
  - Tiến độ: % hoàn thành, thời gian còn lại

- **Trang Certificate:** `/daoanh/certificate/issue`
  - Tạo certificate PDF khi hoàn thành khóa học
  - QR code verification, mã sốCertificate duy nhất
  - Xuất lịch sử học tập, số giờ tu práctica

## Dữ liệu

- **Video hosting:** DILA-video (tối ưu cho giáo dục, CC BY-NC)
- **Khóa học:** 100+ mẫu khóa học (Thiền cơ bản, Luật Phật, Tâm lý...)
- **Sinh viên:** 1.000+ accounts đã đăng ký
- **Quiz:** 10+ câu hỏi cho mỗi môn học, ngẫu nhiên mỗi lần làm

## Acceptance criteria

- [ ] Tạo khóa học hoàn tất dưới 10 phút (tải video + cài đặt)
- [ ] Đăng ký học hoạt động đúng với các phương thức: email, tài khoản Google/Facebook
- [ ] Quiz tự chấm điểm, kết quả xuất hiện tức thời
- [ ] Certificate xuất PDF kèm QR code trong 5 phút sau hoàn thành
- [ ] Tiến độ học tập hiển thị chính xác (theo % và giờ thực tế)

## File tương tự

- `docs/integration/M28-online-course-management.md`
- `docs/Mimo-Flash/T103-m28-online-course-management.md`