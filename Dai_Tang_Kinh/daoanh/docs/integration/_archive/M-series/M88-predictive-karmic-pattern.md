# M88 · Predictive Karmic Pattern Analysis

**Spec · P2**

# M88 Phân tích Tiễn Triệu Dự báo Kármic

Cung cấp hệ thống phân tích tiên tri trend kármic: sử dụng AI và dữ liệu lịch sử practice để dự báo xu hướng kármic, định hướng practitioner về các hành động có thể tạo ra kết quả tích cực hoặc tiêu cực trong tương lai.

## Mục đích

Thực hiện AI tiên tri cho kármic: cho phép practitioner nhận được các cảnh báo về các hành động có thể tạo ra kết quả tiêu cực, và được khuyên hướng về các prática tạo ra thiện karma trong tương lai dựa trên dữ liệu practice lịch sử và mô hình dự báo.

## UI/UX

- **Trang Phân tích kármic:** `/daoanh/karmic/analysis`
  - Hiển thị trạng thái kármic hiện tại: Tích lũy thiện / Tích lũy tệ
  - Dự báo xu hướng: 30 ngày tới, 90 ngày tới, 1 năm tới
   - Phân tích hành động: Đề xuất các hành động có thể tạo ra thiện karma

- **Trang Khuyên hướng:** `/daoanh/karmic/guidance`
  - Khuyên hướng hành động: "Hôm nay nên làm gì để tạo thiện karma", "Tránh làm gì để tránh tệ karma"
   - Lý do giải thích: Phân tích lý do từ mô hình AI
   - Theo dõi tiến độ: Kết quả thực tế so với dự báo

- **Trang Cài đặt:** `/daoanh/karmic/settings`
  - Chọn mô hình dự báo: Mô hình cảm xúc, Mô hình lịch sử, Kết hợp cả hai
  - Thiết lập mục tiêu cá nhân: Mục tiêu tạo thiện karma theo tiêu chí riêng
   - Thông báo: Kích hoạt nhắc nhở khi tiến độ đạt ngưỡng dự báo

## Dữ liệu

- **Mô hình dự báo:** Mô hình AI fine-tuned trên 10000+ user-session kármic
- **Giai đoạn theo dõi:** Niệm (Beginner), Săt (Intermediate), Thấu (Advanced)
- **Chỉ số chính xác:** 75%+ độ chính xác dự báo xu hướng kármic
- **Thời gian cập nhật:** Mỗi ngày tự động tính toán lại dự báo

## Acceptance criteria

- [ ] Dự báo đúng 75% xu hướng kármic theo đúng giai đoạn
- [ ] Tăng tỷ lệ thực hành thiện karma 30% qua khuyến nghị AI
- [ ] Tích hợp với Module M65 (Phân tích cảm xúc) và M68 (Lời khuyên trì tu)
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không chia sẻ dữ liệu cá nhân với bên thứ ba

## File tương tự

- `docs/integration/M88-predictive-karmic-pattern.md`
- `docs/Mimo-Flash/T164-m88-predictive-karmic-pattern.md`