# M77 · AR Buddhist Gardens for Mindfulness

**Spec · P2**

# M72 Nhà thiền AR cho Tâm lý

Cung cấp trải nghiệm nhà thiền tăng thực (AR - Augmented Reality): tạo không gian tâm lý bên ngoài thiết bị, hiển thị các tượng Phật, hoa sen, và cảnh landscape Kinhvirtual để hỗ trợ prática méditation tại bất kỳ đâu.

## Mục đích

Thực hiện AR cho Phật giáo: cho phép sinh viên, tăng ni trải nghiệm méditation với các yếu tố hình thị thực: tượng Phật hiện ra trên bàn học, hoa sen bung lên trên bàn, và cảnh landscape thiền tự nhiên xung quanh người dùng.

## UI/UX

- **Trang Nhà thiền AR:** `/daoanh/ar/garden`
  - Chọn cảnh: Thiên Nội (Tịnh Độ), Lâm ký (Vipassana), Mountain retreat, Desert meditation
  - Tương tác: Đặt tượng Phật, bật tiếng Glocken, Kích hoạt hoa sen bung ra
  - Cách ly: Chế độ riêng tư (chỉ user thấy), Chế độ cộng đồng (thともに meditation với user khác)

- **Trang Tương tác tử:** `/daoanh/ar/interaction`
  - Hiểu hiện tượng: Quan sát tượng Phật rotate, hoa sen thay đổi màu theo thời gian
  - Phản hồi: Nhạc thiền tự động khi quan sát tượng Phật
  - Ghi nhận: Lưu trữ hình ảnh AR đã tạo vào bộ sưu tập cá nhân

- **Trang Cài đặt AR:** `/daoanh/ar/settings`
  - Chọn thiết bị: iPhone (ARKit), Android (ARCore), Glasses AR
  - Thiết lập kích thước: Kích thước tượng Phật, khoảng cách hiển thị
  - Thông báo: Kích hoạt nhắc nhở méditation khi mở ứng dụng AR

## Dữ liệu

- **Các mô hình 3D:** 50+ tượng Phật, hoa sen, cảnh landscape được scan chính xác
- **Thiết bị hỗ trợ:** iPhone (ARKit), Android (ARCore), AR Glasses (Meta Quest, Apple Vision Pro)
- **Âm thanh:** Tiếng Glocken Phật giáo, tiếng nước chảy, nhạc thiền dài
- **Tương thích:** Tất cả thiết bị di động hiện đại hỗ trợ AR

## Acceptance criteria

- [ ] Hiển thị đúng 80% mô hình 3D AR trên các thiết bị phổ biến
- [ ] Tăng nhận thức tâm lý 30% qua trải nghiệm AR nhà thiền
- [ ] Tương thích với iPhone (ARKit), Android (ARCore), AR Glasses
- [ ] Tải mô hình trong 3s khi mở trang AR
- [ ] Bảo mật dữ liệu: Không lưu trữ vị trí user, chỉ lưu trữ hình ảnh AR

## File tương tự

- `docs/integration/M77-ar-garden.md`
- `docs/Mimo-Flash/T153-m77-ar-garden.md`