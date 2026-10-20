# M79 · Predictive Temple Resource Management

**Spec · P2**

# M79 Quản lý tài nguyên tịnh viện dự báo

Cung cấp hệ thống quản lý tài nguyên tịnhiện dự báo: sử dụng analytics và AI để dự báo nhu cầu người đến, tài chính, và nhân lực cho các tə Giảng đồ, giúp tối ưu hóa việc phân bổ nguồn lực.

## Mục đích

Thực hiện predictive analytics cho quản trị tịnh viện: cho phép quản trị tỉnh viện dự báo lượngvisit hằng ngày, dự báo nhu cầu cung nhà trú, và lên lịch nhân lực theo thời gian thực dựa trên các lễ hội,เทศกาล, và các sự kiện Phật giáo.

## UI/UX

- **Trang Dự báo lượng khách:** `/daoanh/temple/forecast`
  - Hiển thị dự báo: Số lượng visitante hôm nay, tuần tới, tháng tới
  - Biểu đồ theo thời gian: Thống kê theo giờ, ngày, tuần
  - Phân loại: Lễ hội Phật giáo, Thứ thường, Thử thách đặc biệt

- **Trang Dự báo tài chính:** `/daoanh/temple/finances`
  - Dự thu: Nhặt hương, 기부, bán của xốp
  - Dự chi: ThuốcMen, điện, nước, nhân lực
  - Báo cáo kế: Dự báo tài chính 3 tháng, 6 tháng, 1 năm

- **Trang Lên lịch nhân lực:** `/daoanh/temple/schedule`
  - Dự báo nhu cầu: Số lượng tăng_lộ cần cho mỗi buổi/tuan
  - Tự động lên lịch: Tạo lịch cho tăng_lộ, nhân lực hỗ trợ
  - Thay đổi thời gian thực: Điều chỉnh lịch khi có sự thay đổi bất ngờ

## Dữ liệu

- **Lịch sử visit:** 3 năm dữ liệu visit hằng ngày (tổng cộng 100000+ dữ liệu điểm)
- **Thống kê lễ hội:** 20+ lễ hội Phật giáo chính cần dự báo hàng năm
- **Mô hình dự báo:** Mô hình AI kết hợp saisonality, ngày lễ, điều kiện thời tiết
- **Tỷ lệ chính xác:** 80%+ độ chính xác dự báo lượng khách

## Acceptance criteria

- [ ] Dự báo lượng khách đúng 80% so sánh với thực tế
- [ ] Tối ưu hóa nhân lực 25% qua dự báo đúng nhu cầu
- [ ] Tăng thu nhập temple 15% qua dự báo tài chính chính xác
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không chia sẻ dữ liệu temple với bên thứ ba

## File tương tự

- `docs/integration/M79-predictive-temple.md`
- `docs/Mimo-Flash/T155-m79-predictive-temple.md`