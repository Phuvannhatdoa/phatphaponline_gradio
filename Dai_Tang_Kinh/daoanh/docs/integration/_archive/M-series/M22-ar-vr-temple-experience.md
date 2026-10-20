# M22 · Kinh nghiệm AR/VR chùa cho Tiến sĩ

**Spec · P2**

# M22 Triết lý và ứng dụng AR/Virtual Reality

Cung cấp trải nghiệm tăng thêm thực tại (AR) và thực thái ảo (VR) cho các chùa, tự viện, giúp người dùng thâm nhập sâu hơn vào không gian tu práctica và kiến trúc Phật giáo.

## Mục đích

Thực hiện trải nghiệm AR/VR cho các ngôi chùa, tự viện, cung cấp kênh giới thiệu Phật giáo sinh động, nâng cao sự tham gia của giới trẻ và du khách quốc tế.

## UI/UX

- **Trang AR/VR Tour:** `/daoanh/vr/tour`
  - **Chế độ AR:** Sử dụng camera thực tế, đè lên các điểm tương tác (icon chùa, tháp Phật, cây Bồ)
  - **Chế độ VR:** Đồ thị 360°, điều khiển bằng controller hoặc cảm ứng
  - **Tour tự dẫn:** Route đi kèm giải thích ngắn gọn tại từng điểm quan tâm

- **Trang Kiến trúc chùa:** `/daoanh/vr/architecture`
  - Bản vẽ 3D kiến trúc chùa theo triều đại
  - Thu phóng/Thu nhỏ, xoay quanh
  - Hiện thông tin lịch sử khi rê chuột/tiếp cận

- **Trang tương tác:** `/daoanh/vr/interactions`
  - Mini-game: Tìm chữ Hán, phao bồ, câu Trí tuệ
  - Kết nối cộng đồng: Chia sẻ hình ảnh AR/VR của chính bạn

## Dữ liệu

- **3D Models:** Đối tượng chùa, tháp Phật, cảnh tuyết nguyệt pháp (theo chuẩn glTF)
- **Tour routes:** Điểm hotspot kèm nội dung giải thích (tối đa 20 điểm/chùa)
- **Audio guide:** Âm thanh dẫn tour (tùy chọn tiếng Việt, English, Pali)
- **DILA integration:** Địa chỉ chùa, lịch sử triều đại kèm dữ liệu DILA

## Acceptance criteria

- [ ] Trải nghiệm AR/VR tải dưới 5s trên mobile trung bình
- [ ] Hiển thị đúng 3 chế độ: AR cơ bản, VR 360°, Tour tự dẫn
- [ ] Tour routes bao gồm ít nhất 10 điểm hotspot cho mỗi chùa mẫu
- [ ] Tương thích với thiết bị: iPhone (ARKit), Android (ARCore), Google Cardboard/VR headset
- [ ] Tích hợp dữ liệu DILA: địa chỉ chùa, lịch sử, tên tiếng Hán

## File tương tự

- `docs/integration/M22-ar-vr-temple-experience.md`
- `docs/Mimo-Flash/T97-m22-ar-vr-temple-experience.md`