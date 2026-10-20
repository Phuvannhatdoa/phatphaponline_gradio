# M48 · Buddhist Decentralized Governance

**Status:** 📄 Consolidated Documentation  
**Module:** M48  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp hệ thống quản trị phi giữa (DAO) cho cộng đồng Phật tử: phê chuẩn ngân sách trì tu, quản lý tài nguyên nhà trang, và phê voti các dự án Phật học bằng token thông minh.

## UI/UX

- **Trang Phê votación đề xuất:** `/dao/dao/propose`
  - Hiển thị đề xuất đang chờ phê votación: Mô tả, ngân sách cần, thời gian phê votación
   - Cán ghi phê votación: Đạt yêu cầu (quorum), Từ phác (veto), Ý thích (like)
   - Kết quả: Phê votación thành công/thất bại, lịch sử phê votación

- **Trang Trang tài chính:** `/dao/dao/finances`
  - Hiển thị ngân sách hiện tại: Nhập, chi, dư lại
   - Phân loại chi: Trì tu, Nhà trang, Phát tán, Xây dựng
   - Báo cáo tài chính: PDF xuất, báo cáo tháng/năm

- **Trang Quản trị hội đồng:** `/dao/dao/council`
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

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `proposeGovernance(msg)` - Phê votación đề xuất
2. `voteGovernance(proposalId, option)` - Phê votación cho đề xuất
3. `getGovernanceStatus()` - Lấy trạng thái governance
4. `getTreasuryInfo()` - Lấy thông tin ngân sách

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T48-decentralized-governance-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), blockchain integration (Ethereum/Polygon), smart contracts