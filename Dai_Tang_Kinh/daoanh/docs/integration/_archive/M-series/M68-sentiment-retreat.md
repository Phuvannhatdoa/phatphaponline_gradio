# M68 · Sentiment-Driven Retreat Recommendations

**Spec · P2**

# M68 Lời khuyên trì tu dựa trên cảm xúc

Cung cấp hệ thống khuyến nghị trì tu dựa trên phân tích cảm xúc: đề xuất các phòng trì tu phù hợp với trạng thái tâm lý hiện tại, mục tiêu tu práctica, và lịch trình cá nhân.

## Mục đích

Thực hiện kết hợp mô hình cảm xúc (Module M65) với dữ liệu trì tu: cho phép sinh viên Phật giáo nhận được lời khuyên trì tu cá nhân: "Hôm nay phù hợp trì tu Thiền thọ", "Ngày này tốt cho retreat Vipassana", và theo dõi tiến độ qua từng giai đoạn trì tu.

## UI/UX

- **Trang Khuyến nghị:** `/daoanh/recommendations/retreat`
  - Input: Trạng thái cảm xúc hôm nay, mục tiêu tu práctica, thời gian có sẵn
  - Output: Các phòng trì tu đề xuất (1-3 lựa chọn), lý do khuyến nghị
  - Chi tiết: Thời lượng, vị trí (Offline/Online), mức độ thách thức

- **Trang Theo dõi tiến độ:** `/daoanh/recommendations/tracking`
  - Lịch sử khuyến nghị: Các phòng trì tu đã tham gia, kết quả
  - Biểu đồ tiến độ: Độ sâu méditation, trạng thái cảm xúc qua thời gian
  - Xuất báo cáo: PDF kèm biểu đồ tiến độ tu práctica

- **Trang Cài đặt:** `/daoanh/recommendations/settings`
  - Chọn loại trì tu: Thiền thọ, Vipassana, Zen, Pure Land
  - Thiết lập mục tiêu: Tăng świadomoś (sự tỉnh thức), Giảm stress, Tăng trí tuệ
  - Thông báo: Kích hoạt nhắc nhở hàng ngày, hàng tuần

## Dữ liệu

- **Mô hình khuyến nghị:** Híbrí: Mô hình cảm xúc + dữ liệu lịch sử trì tu (10000+ user-session)
- **Phông loại:** Thiền thọ, Vipassana, Zen, Pure Land, Tiantai
- **Thời lượng:** Từ 1 ngày đến 30 ngày
- **Đánh giá:** Người dùng đánh giá mức độ phù hợp (1-5 sao) cho mỗi khuyến nghị

## Acceptance criteria

- [ ] Khuyến nghị đúng 75% độ phù hợp với mục tiêu tu prática của user
- [ ] Tăng tỷ lệ hoàn thành trì tu 25% qua khuyến nghị cá nhân
- [ ] Tích hợp với Module M65 (Phân tích cảm xúc)
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không chia sẻ trạng thái cảm xúc với bên thứ ba

## File tương tự

- `docs/integration/M68-sentiment-retreat.md`
- `docs/Mimo-Flash/T143-m68-sentiment-retreat.md`