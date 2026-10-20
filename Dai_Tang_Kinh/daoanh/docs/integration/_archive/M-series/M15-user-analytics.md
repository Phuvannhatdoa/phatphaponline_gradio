# M15 · Phân tích người dùng cho Cử Nhân

**Spec · P1**

# M15 Phân tích hành vi người dùng

Cung cấp cơ bản analytics và báo cáo cho trình độ Cử Nhân: truy vấn phổ biến, đường đi người dùng, độ tham gia, và thông tin demographics.

## Mục đích

Đồ họa đơn giản về cách người dùng tương tác với hệ thống tra cứu Kinh Đạo Phật, giúp cải thiện trải nghiệm người dùng cho trình độ Cử Nhân.

## UI/UX

- **Trang Tổng quan:** `/daoanh/analytics/overview`
  - Tổng truy vấn hôm/năm
  - Top 10 truy vấn phổ biến
  - Biểu đồ đường đi: từ khóa → kết quả → hành động sau

- **Trang Độ tham gia:** `/daoanh/analytics/engagement`
  - Streak: số ngày liên tục truy vấn
  - Biến động: xu hướng truy vấn theo tuần/tháng
  - Thân:m cao nhất: kinh, nhân vật, địa danh

- **Trang Demographics ( tổng hợp):** `/daoanh analytics/demographics`
  - Thống kê danh nghĩa (tự báo, không cá nhân hóa)
  - Phân bố: Quốc gia, trình độ, mục đích truy vấn
  - Báo cáo xuất: PDF, CSV

## Dữ liệu

- **Event tracking:** query_submitted, result_clicked, result_shared
- **Storage:** SQLite aggregated (Zero-RAM principle, cũ hơn 30 ngày xóa)
- **Cookies:** Chỉ session ID, không lưu IP hay thông tin cá nhân
- **Báo cáo:** Xuất hàng tuần, tổng hợp vô danh

## Acceptance criteria

- [ ] Biểu đồ top 10 truy vấn cập nhật real-time
- [ ] Báo cáo streak tính chính xác cho 80%+ user
- [ ] Xuất PDF/CSV chứa đủ tiêu đề và dữ liệu
- [ ] Không lưu dữ liệu cá nhân nhạy cảm
- [ ] Tốc độ thu thập < 10ms/query

## File tương tự

- `docs/integration/M15-user-analytics.md`
- `docs/Mimo-Flash/T90-m15-user-analytics.md`