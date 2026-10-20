# M47 · TruyềnMarcador và Lưu trữ cho Cử Nhân

**Spec · P1**

# M47 Hỗ trợ TruyềnMarcador và Quản lý đoạn Kinh

Cung cấp khả năng bookmark các đoạn Kinh quan trọng, sắp xếp theo chủ đề, và quản lý bộ sưu tập riêng cho trình độ Cử Nhân.

## Mục đích

Đỗ người dùng Cử nhân bookmark các đoạn kinh đã đọc, sắp xếp theo chủ đề (Tâm lý, Luật, Sutra), và dễ dàng truy xuất khi cần.

## UI/UX

- **Trang Bookmark:** `/daoanh/bookmarks/my-bookmarks`
  - Hiển thị tất cả bookmark của user
  - Thẻ: #tâm lý, #sutra, #ngày_ngày, v.v.
  - Sắp xếp: Theo ngày thêm,Theo tên,Theo thẻ

- **Trang Bookmark nhanh:** `/daoanh/bookmarks/quick-access`
  - Hiển thị 5 bookmark mới nhất
  - Nút "Truy cập ngay", "Xem tất cả"

- **Trang Quản lý chủ đề:** `/daoanh/bookmarks/tags`
  - Tạo/xóa thẻ cá nhân
  - Gán thẻ cho bookmark mới/current
  - Xem bookmark theo từng thẻ

## Dữ liệu

- **Bookmark:** Nội dung đoạn kinh, thẻ, thời gian tạo, owner
- **Thẻ:** Free-form tags do user define (ví dụ: #tâm_lý, #sutra, #thiền)
- **Phân loại:** Chủ đề mặc định: Tâm lý, Luật, Sutra, Thiền, Sống_đạo

## Acceptance criteria

- [ ] Bookmark hoạt động đúng và lưu trữ theo owner
- [ ] Thẻ cá nhân có thể tạo/xóa đúng
- [ ] Sắp xếp theo ngày/thẻ hoạt động đúng
- [ ] Hiển thị 5 bookmark mới nhất trên trang nhanh
- [ ] Tương thích với màn hình thiết bị: điện thoại, tablet, desktop

## File tương tự

- `docs/integration/M47-bookmarks.md`
- `docs/Mimo-Flash/T122-m47-bookmarks.md`