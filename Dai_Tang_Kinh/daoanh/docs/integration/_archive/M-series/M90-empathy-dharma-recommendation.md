# M90 · Empathy-Driven Dharma Recommendation

**Spec · P2**

# M90 Khuyến nghị Dharma dựa trên thăm thạ

Cung cấp hệ thống khuyến nghị Dharma dựa trên cảm xúc: đề xuất các nội dung, pratique, và retreat phù hợp với trạng thái cảm xúc hiện tại của practitioner.

## Mục đích

Thực hiện empathy-driven recommendation cho Dharma: cho phép hệ thống hiểu cảm xúc practitioner thông qua Module M65, sau đó đề xuất các nội dung Dharma, practice, retreat phù hợp để hỗ trợ nâng cao tâm lý và tu prática.

## UI/UX

- **Trang Khuyến nghị cảm xúc:** `/daoanh/empathy/recommend`
  - Input: Trạng thái cảm xúc hiện tại (từ Module M65), Mục tiêu (Tăng serenity, Giảm anxiety, Tăng trí tuệ)
  - Output: Các nội dung Dharma đề xuất (Kinh, giáo Thái, Bài giảng), Practice đề xuất, Retreat đề xuất
   - Chi tiết: Lý do khuyên nghị cho mỗi mục đề xuất

- **Trang Phản hồi:** `/daoanh/empathy/feedback`
  - Đánh giá khuyên nghị: Có hữu ích không, đã thay đổi trạng thái cảm xúc ra sao
   - Cập nhật mô hình: Đào tạo lại mô hình khuyên nghị từ phản hồi của practitioner

- **Trang Cài đặt:** `/daoanh/empathy/settings`
  - Chọn loại nội dung: Kinh, Giáo Thái, Sách tịch, Tạp chí
   - Thiết lập mục tiêu: Mục tiêu tâm lý theo tiêu chí riêng
   - Thông báo: Kích hoạt nhắc nhở khi trạng thái cảm xúc thay đổi

## Dữ liệu

- **Mô hình khuyên nghị:** Híbrí: Mô hình cảm xúc (Module M65) + dữ liệu lịch sử practice (50000+ user-session)
- **Loại nội dung:** 2000+ nội dung Phật giáo khác nhau
- **Thời gian thực:** Khuyên nghị tức khi trạng thái cảm xúc được phân tích
- **Tỷ lệ phù hợp:** 80% nội dung đề xuất phù hợp với mục tiêu tâm lý

## Acceptance criteria

- [ ] Phát hiện đúng trạng thái cảm xúc và đề xuất nội dung phù hợp 80% trường hợp
- [ ] Tăng sự hài lòng tâm lý 25% qua khuyến nghị cá nhân
- [ ] Tích hợp với Module M65 (Phân tích cảm xúc) và M68 (Lời khuyên trì tu)
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không chia sẻ trạng thái cảm xúc với bên thứ ba

## File tương tự

- `docs/integration/M90-empathy-dharma-recommendation.md`
- `docs/Mimo-Flash/T166-m90-empathy-dharma-recommendation.md`