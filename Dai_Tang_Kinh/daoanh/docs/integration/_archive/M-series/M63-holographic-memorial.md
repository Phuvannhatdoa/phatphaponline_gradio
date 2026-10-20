# M63 · Holographic Memorial Platform cho Người Phù Hữu

**Spec · P2**

# M63 Holographic Memorial Platform

Cung cấp nền tảng tưởng niệm holographic cho người đã quá đời: tạo mô hình tưởng niệm 3D, ai ngay trong các buổi trì tu, và kết nối linh mục qua bối cảnh holographic.

## Mục đích

Thực hiện trải tưởng niệm cao cấp: cho phép sinh viên, tăng ni, và cư sĩ tạo memorial holographic cho người đã quá đời, tương tác qua giao diện hiển thị 3D trong phòng thiền, và lưu trữ 영구 trong dữ liệu Phật giáo.

## UI/UX

- **Trang Tạo memorial:** `/daoanh/holographic/create`
  - Input: Tên người đã qua đời, ảnh 2D, đoạn trích kinh ưa thích
  - Output: Mô hình holographic 3D kèm motion data
  - Tùy chọn: Âm thanh tự động từ đoạn kinh đã chọn

- **Trang Truyền承接 memorial:** `/daoanh/holographic/transmit`
  - Hiển thị memorial 3D trong không gian thiền
  - Tương tác: Đặt hương ảo, bái敬礼 (bowing), cung cấp hoa ảo
  - Lịch sử: Ghi nhận các buổi tưởng niệm, ai đã tham gia

- **Trang Lịch sử tưởng niệm:** `/daoanh/holographic/history`
  - Danh sách memorial đã tạo
  - Thống kê: Số lượng buổi tưởng niệm, người tham gia
  - Xuất báo cáo: PDF kèm hình memorial 3D

## Dữ liệu

- **Mô hình 3D:** Đối tượng phong phao (3D mesh) kèm texture dữ liệu Phật giáo
- **Phản hồi không gian:** Hỗ trợ HTC Vive, Oculus Quest,desktop hologram
- **Cách quản lý:** Metadata memorial (tên, ngày sinh/quá đời, kinh đã chọn, số lần tưởng niệm)
- **Tích hợp:** Kết nối với Cemetery DB để xác minh danh sách người qua đời

## Acceptance criteria

- [ ] Tạo memorial 3D từ ảnh 2D trong 5 phút
- [ ] Hiển thị đúng trên các thiết bị VR/AR phổ biến (80%+)
- [ ] Tương thích với HTC Vive, Oculus Quest, desktop hologram
- [ ] Lưu trữ memorial trong 10 năm (bảo tồn dữ liệu)
- [ ] Xuất báo cáo PDF kèm hình memorial trong 2 phút

## File tương tự

- `docs/integration/M63-holographic-memorial.md`
- `docs/Mimo-Flash/T138-m63-holographic-memorial.md`