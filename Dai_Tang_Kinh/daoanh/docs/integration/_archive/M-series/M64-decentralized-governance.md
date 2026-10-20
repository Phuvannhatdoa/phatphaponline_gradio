# M64 · Decentralized Governance 2.0 cho Cộng đồng Phật tử

**Spec · P2**

# M64 Decentralized Governance 2.0

Cung cấp hệ thống quản trị phi giữa (DAO - Decentralized Autonomous Organization) cho cộng đồng Phật tử: phê chuẩn ngân sách trì tu, quản lý tài nguyên nhà trang, và phê voti các dự án Phật giáo bằng token thông minh.

## Mục đích

Triển khai quản trị phi giữa trên chuỗi khối: cho phép hội đồng Trì tu, hội đồng Nhà trang, và hội đồng Phật tử tham gia quyết định phân bổ nguồn lực, giám sát hoạt động tài chính, và phê voti các đề xuất Phật giáo trong suốt năm.

## UI/UX

- **Trang Phê votación đề xuất:** `/daoanh/dao/propose`
  - Hiển thị đề xuất đang chờ phê votación: Mô tả, ngân sách cần, thời gian phê votación
  - Cán ghi phê votación: Đạt yêu cầu (quorum), Từ phác (veto), Ý thích (like)
  - Kết quả: Phê votación thành công/thất bại, lịch sử phê votación

- **Trang Trang tài chính:** `/daoanh/dao/finances`
  - Hiển thị ngân sách hiện tại: Nhập, chi, dư lại
  - Phân loại chi: Trì tu, Nhà trang, Phát tán, Xây dựng
  - Báo cáo tài chính: PDF xuất, báo cáo tháng/năm

- **Trang Quản trị hội đồng:** `/daoanh/dao/council`
  - Danh sách thành viên hội đồng: Vai trò, thời gian nhiệm kỳ, phiếu phê votación
  - Chức năng: Thêm/xóa thành viên, thay đổi quyorum, điều chỉnh ngân sách

## Dữ liệu

- **Token governance:** Token Phật giáo (PTH token) kèm quyền phê votación
- **Quorum cần:** 20%+ thành viên hội đồng để phê votación hợp lệ
- **Thời gian phê votación:** 7 ngày cho mỗi đề xuất
- **Quyền phác:** Token giữ ≥ 1000 PTH có quyền phác đề xuất

## Acceptance criteria

- [ ] Thiết lập DAO trong 1 ngày cho bất kỳ cộng đồng Phật tử nào
- [ ] Phê votación đề xuất trong 7 ngày với quorum 20%
- [ ] Tăng tỷ lệ tham gia phê votación 40% so với quản trị truyền thống
- [ ] Minh bạch ngân sách: Tất cả giao dịch ghi nhận trên chuỗi khối
- [ ] Tương thích với MetaMask, Trust Wallet, và các ví chính thống

## File tương tự

- `docs/integration/M64-decentralized-governance.md`
- `docs/Mimo-Flash/T139-m64-decentralized-governance.md`