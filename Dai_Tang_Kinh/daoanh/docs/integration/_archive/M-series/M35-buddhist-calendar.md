# M35 · Lịch Phật giáo và Ngày quan trọng cho Cử Nhân

**Spec · P1**

# M35 Tích hợp Lịch Phật giáo và Ngày quan trọng

Cung cấp lịch Phật giáo đầy đủ với các ngày Thánh, tiết, và các ngày quan trọng khác, giúp Cử nhân lên kế hoạch tu práctica và tham gia các kiện lễ đúng đắn.

## Mục đích

Độ cung cấp lịch Phật giáo chính xác, bao gồm 366 ngày (năm nhuận), 108 Thánh ngày chính, và các tiết hàng tháng, cùng với khả năng theo dõi ngày quan trọng cá nhân.

## UI/UX

- **Trang Lịch Phật giáo:** `/daoanh/calendar/buddhist`
  - Hiển thị ngày tháng lunar, thông tin tiết/thánh hàng ngày
  - Màu sắc phân biệt: Thánh ngày (vàng), Tiết (xanh lá), Ngày thường (trắng)
  - Click ngày: Xem chi tiết lễ tiễn, kinh cần đọc

- **Trang Ngày quan trọng cá nhân:** `/daoanh/calendar/personal-dates`
  - Thêm ngày sinh nhật, ngày lễ gia đình vào lịch Phật giáo
  - Đồng bộ với Google Calendar, Apple Calendar
  - Nhắc nhở trước ngày quan trọng (1 ngày, 3 ngày, 1 tuần)

- **Trang Tìm ngày:** `/daoanh/calendar/search`
  - Tìm theo ngày, theo tên tiết, theo tên Thánh
  - Kết quả: Ngày corresponded, lý do quan trọng, Kinh cần đọc

## Dữ liệu

- **Lịch Phật giáo:** DILA calendar (366 tiết, 108 Thánh ngày chính)
- **Người dùng:** Cá nhân dates (tùy chọn đồng bộ)
- **Cảnh báo:** Thông báo trước ngày quan trọng (tùy chọn)
- **Cấp phép:** Tuân thủ quy tắc lịch (không trùng lịch)

## Acceptance criteria

- [ ] Lịch hiển thị đúng 366 ngày (năm nhuận có 29 ngày tháng 2)
- [ ] Thông báo ngày quan trọng gửi đúng theo cài đặt của user
- [ ] Đồng bộ với Google Calendar/Apple Calendar trong 5 phút
- [ ] Tìm ngày hoạt động đúng cho 100+ từ khóa Phật giáo
- [ ] Tối đa 1 thông báo/c ngày (không spam user)

## File tương tự

- `docs/integration/M35-buddhist-calendar.md`
- `docs/Mimo-Flash/T110-m35-buddhist-calendar.md`