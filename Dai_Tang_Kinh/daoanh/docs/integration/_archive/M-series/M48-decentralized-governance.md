# M48 · Quản trịPhi tập trung cho Tiến sĩ

**Spec · P2**

# M48 Hỗ trợ Quản trịPhi tập trung (DeFi cho Phật giáo)

Cung cấp hệ thống quản trịPhi tập trung cho cộng đồng Phật giáo: phiếu bầu, quyết định cộng đồng, và quản lý tài nguyênPhi.

## Mục đích

Đỗ cộng đồng Phật giáo tham gia vào các quyết định quản trị: chọn thầy tọt mới, phân bổ tài chính, và đặt hướng đi choCentro sang nhiều năm tới.

## UI/UX

- **Trang Phiếu bầu:** `/daoanh/governance/vote`
  - Đang có: Các đề đề: Chọn thầy tọt mới, Phân bổ tài chính năm tới, Quy định mới
  - Thể loại: Mỗi practitioner 1 phiếu, Thời gian bầu: 7 ngày
  - Kết quả: Hiển thị sau khi bầu, tỷ lệ tham gia

- **Trang Quyết định:** `/daoanh/governance/proposals`
  - Danh sách các đề đề: Đang chờ bầu, Đang thảo luận, Đã chấp nhận, Đã từ chối
  - Chi tiết: Mục đích, lợi ích, người nộp đề đề
  - Tham gia thảo luận: Bài viết, bình luận, phiếu bầu

- **Trang Quản lý tài nguyên:** `/daoanh/governance/funds`
  - Tổng quan: Tài chính hiện có, phân bổ
  - Phiếu bầu về phân bổ: Mục đích, số lượng, thời gian
  - Lịch sử: Các lần phân bổ trước, kết quả

## Dữ liệu

- **Phiếu bầu:** Practitioner ID, đề đề ID, lựa chọn, thời gian bầu
- **Quyết định:** Đề đề ID, nội dung, lượt ủng hộ/phản đối, kết quả
- **Tài chính:** Số dư, lịch sử giao dịch, phiếu bầu về phân bổ

## Acceptance criteria

- [ ] Mỗi practitioner có 1 phiếu bầu, tính đúng 100% trường hợp
- [ ] Tham gia bầu hoạt động đúng cho 80% practitioner đăng ký
- [ ] Kết quả bầu hiển thị đúng số lượng ủng hộ/phản đối
- [ ] Quản lý tài chính minh bạch, lịch sử giao dịch dễ nhìn
- [ ] Tương thích với thiết bị: điện thoại, tablet, desktop

## File tương tự

- `docs/integration/M48-decentralized-governance.md`
- `docs/Mimo-Flash/T123-m48-decentralized-governance.md`