# M27 · Tìm kết nối Thầy/Trainee cho Cử Nhân

**Spec · P1**

# M27 Hệ thống kết nối giữa Thầy và Trainee

Cung cấp trang để người dùng tìm thầy tọt, sư자의, hoặc kết nối với người tu práctica cùng mục đích, tạo cộng đồng tập training.

## Mục đích

Đỗ người dùng tìm được đối象 practice phù hợp, thầy tọt có kinh nghiệm, và thiết lập mối quan hệ hướng dẫn - được theo dõi để hỗ trợ tu práctica dài hạn.

## UI/UX

- **Trang Tìm thầy/Trainee:** `/daoanh/connection/search`
  - Bộ lọc: Vùng/thành Phố, Chủ đề (Thiền, Luật, Sutra), Trình độ (Mới bắt đầu, Trình trung, Nâng cao)
  - Kết quả hiển thị: Tên, ảnh đại diện, số buổi tu prática, đánh giá (1-5 sao)
  - Nút Kết nối: Gửi yêu cầu kết nối, theo dõi lịch sử

- **Trang Hồ sơ cá nhân:** `/daoanh/connection/profile`
  - Hiển thị lịch sử tu prática của chính mình
  - Hiển thị danh sách người theo dõi, theo theo dõi
  - Tùy chọn: Đăng bài tu prática, kinh nghiệm cá nhân

- **Trang Yêu cầu kết nối:** `/daoanh/connection/requests`
  - Xem các yêu cầu kết nối đang chờ xử lý
  - Chấp nhận/Từ chối yêu cầu
  - Ghi chú ngắn về mối quan hệ sau khi đồng ý

## Dữ liệu

- **Người dùng:** 10.000+ practitioners đã đăng ký
- **Thẻ kỹ năng:** Thiền, nghiên cứu Kinh, tuân giới,...
- **Đánh giá:** 1-5 sao từ các người đã tu práctica cùng
- **Mối quan hệ:** Thầy trò, cùng nhóm tu práctica, bạn tập chung

## Acceptance criteria

- [ ] Tìm kiếm có bộ lọc theo vùng, chủ đề, trình độ
- [ ] Kết quả hiển thị đúng 20 người mỗi trang
- [ ] Yêu cầu kết nối có thể chấp nhận/từ chối
- [ ] Hồ sơ cá nhân chứa đủ thông tin: tên, ảnh, lịch sử, đánh giá
- [ ] Tích hợp với hệ thống notifications cho kết nối mới

## File tương tự

- `docs/integration/M27-connection-monk-disciple.md`
- `docs/Mimo-Flash/T102-m27-connection-monk-disciple.md`