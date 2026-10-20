# M87 · Decentralized Sangha Governance 3.0

**Spec · P2**

# M87 Quản trị Sangha Phi giữa 3.0

Cung cấp hệ thống quản trị phi giữa (DAO) nâng cao cho Sangha: phê chuẩn ngân sách trì tu, quản lý tài nguyên nhà trang, và phê voti các dự án Phật giáo bằng token thông minh có cơ chế reputation hệ thống.

## Mục đích

Triển khai quản trị DAO nâng cao cho Sangha: cho phép hội đồng Trì tu, hội đồng Nhà trang, và hội đồng Phật tử tham gia quyết định phân bổ nguồn lực, giám sát hoạt động tài chính, và phê voti các đề xuất Phật giáo trong suốt năm với cơ chế repuation system kèm theo.

## UI/UX

- **Trang Phê votación đề xuất:** `/dao/dao/propose`
  - Hiển thị đề xuất đang chờ phê votación: Mô tả, ngân sách cần, thời gian phê votación
  - Cán ghi phê votación: Đạt yêu cầu (quorum), Từ phác (veto), Ý thích (like)
  - Kết quả: Phê votación thành công/thất bại, lịch sử phê votación

- **Trang Trang tài chính:** `/dao/dao/finances`
  - Hiển thị ngân sách hiện tại: Nhập, chi, dư lại
  - Phân loại chi: Trì tu, Nhà trang, Phát tán, Xây dựng
   - Báo cáo tài chính: PDF xuất, báo cáo tháng/năm

- **Trang Quản trị hệ thống:** `/dao/dao/system`
  - Danh sách thành viên hệ thống: Vai trò, thời gian nhiệm kỳ, điểm reputation
   - Chức năng: Thêm/xóa thành viên, thay đổi quyorum, điều chỉnh ngân sách
   - Phát hiện gian lận: Phát hiện các giao dịch bất thường qua pattern recognition

## Dữ liệu

- **Token governance:** Token Phật giáo (PTH token) kèm quyền phê votación
- **Hệ thống reputation:** Điểm reputation dựa trên lịch sử tham gia, đóng góp, và phê votación chính xác
- **Quorum cần:** 20%+ thành viên hội đồng để phê votación hợp lệ
- **Thời gian phê votación:** 7 ngày cho mỗi đề xuất

## Acceptance criteria

- [ ] Thiết lập DAO trong 1 ngày cho bất kỳ Sangha nào
- [ ] Phê votación đề xuất trong 7 ngày với quorum 20%
- [ ] Tăng tỷ lệ tham gia phê votación 40% so với quản trị truyền thống
- [ ] Minh bạch ngân sách: Tất cả giao dịch ghi nhận trên chuỗi khối
- [ ] Tương thích với MetaMask, Trust Wallet, và các ví chính thống

## File tương tự

- `docs/integration/M87-decentralized-sangha-governance.md`
- `docs/Mimo-Flash/T163-m87-decentralized-sangha-governance.md`