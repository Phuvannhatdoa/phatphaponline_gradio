# M21 · Trình bày Kinh trên Mobile cho Cử Nhân

**Spec · P1**

# M21 Tối ưu trải nghiệm đọc kinh trên Mobile

Cung cấp giao diện đọc kinh responsive, thân thiện với mobile cho trình độ Cử Nhân: tự động điều chỉnh layout, đọc đục, và tùy chọn tùy biến.

## Mục đích

Đảm bảo người dùng có thể đọc kinh anytime, anywhere trên smartphone cá nhân với trải nghiệm đọc mượt mà, không cần máy tính bảng hoặc máy tính để bàn.

## UI/UX

- **Giao diện Responsive:**
  - **Điện thoại (≤ 768px):** Layout đơn cột, nút lớn, đánh dấu vị trí bằng dấu mốc tiến độ,
  - **Tablet (769px – 1024px):** Layout hai cột, bảng lục kinh bên trái,
  - **Màn hình lớn (≥ 1025px):** Layout ba cột, bảng lục toàn diện, toolbar dọc.

- **Thành phần cơ bản:**
  - Thanh tìm kiếm trượt xuống ( sticky search)
  - Nút điều chỉnh kích thước chữ (A+ / A-)
  - Nút đọc đục (auto-scroll)
  - Menu ráp truy cập: Kinh hôm, Kinh yêu thích, Lịch tiết

- **Trải nghiệm đọc:**
  - Tự động lưu vị trí đọc cuối cùng (LocalStorage)
  - Chế độ tối/sáng theo hệ thống hoặc thủ công
  - Hiển thị bản Hán-Pali song song (tùy chọn)
  - Chiaën Đoạn kinh có thể-collapse/expand

## Dữ liệu

- **CBETA API:** Truy vấn nội dung Kinh (phi thương mại)
- **Cache:** Dữ liệu Kinh cache offline (10 Kinh phổ biến nhất)
- **TTS:** Tích hợp Text-to-Speech cho chế độ đọc đục (tùy chọn cài đặt)

## Acceptance criteria

- [ ] Giao diện hiển thị đúng trên 3 kích thước màn hình (điện thoại, tablet, desktop)
- [ ] Tự động lưu vị trí đọc và khôi phục khi quay lại app
- [ ] Tốc độ tải trang đầu tiên < 2s trên mobile 3G
- [ ] Tương thích với trình duyệt: Chrome, Safari, Firefox mobile
- [ ] Nút điều chỉnh kích thúcar chữ hoạt động mượt mà (12 size từ 12px–24px)

## File tương tự

- `docs/integration/M21-mobile-responsive-kinh.md`
- `docs/Mimo-Flash/T96-m21-mobile-responsive-kinh.md`