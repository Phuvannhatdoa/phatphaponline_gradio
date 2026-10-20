# M37 · Âm thanh Thiền và Nhạc chữ cho Cử Nhân

**Spec · P1**

# M37 Tích hợp Âm thanh Thiền

Cung cấp thư viện nhạc thiền, bản đọc kinh âm thanh, và hỗ trợ phát nhạc đồng bộ với thiền cho trình độ Cử Nhân.

## Mục đích

Cung cấp không khí thư giãn và hỗ trợ tập thiền qua âm thanh, nhạc bản đọc kinh, và các yếu tố ambiental cho người dùng Cử Nhân.

## UI/UX

- **Trang Thư viện nhạc:** `/daoanh/music/library`
  - Danh sách nhạc thiền: Nhạc bình yên, Nhạc đàn bầu, Nhạc Piano tuyến tinh
  - Lọc theo Thể loại: Tâm lý, Trang cảnh, Trọng tài
  - Phát nhạc đồng thời với màn hình thời gian thiền

- **Trang Cài đặt phát nhạc:** `/daoanh/music/settings`
  - Chọn nhạc nền: Tự động, Định lượng, Tắt nhạc
  - Đặt khoảng thời gian: 10 phút, 20 phút, 30 phút, Không giới hạn
  - Điều chỉnh âm lượng, tốc độ phát

- **Trang Phát kinh âm thanh:** `/daoanh/music/sutra-recitation`
  - Chọn Kinh: Kinh Thất Nghiệp, Kinh Tâm Sự, Các kinh ngắn
  - Phát cùng nhạc nền hoặc chỉ giọng đọc thuần túy
  - Tốc độ đọc: 1x, 1.2x, 1.5x

## Dữ liệu

- **Thư viện nhạc:** 50+ tracks thiền (CC BY-NC, nguồn: DILA, artists cộng đồng)
- **Bản đọc kinh:** 20+ kinh nổi tiếng (Tiếng Việt, đọc bởi thầy tọt certified)
- **Thời lượng:** Tổng 10+ giờ âm thanh chất lượng

## Acceptance criteria

- [ ] Thư viện nhạc hiển thị đúng 50+ track với thumbnail
- [ ] Phát nhạc đồng bộ với đếm thời gian thiền
- [ ] Bản đọc kinh có sẵn cho 20+ kinh phổ biến
- [ ] Tốc độ đọc có thể điều chỉnh (1x, 1.2x, 1.5x)
- [ ] Tương thích với thiết bị: iOS, Android, Web

## File tương tự

- `docs/integration/M37-meditation-music.md`
- `docs/Mimo-Flash/T112-m37-meditation-music.md`