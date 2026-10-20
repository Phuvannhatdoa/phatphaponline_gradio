# M24 · Blockchain cho Dana và Pháp quyền cho Tiến sĩ

**Spec · P2**

# M24 Sử dụng Blockchain quản lý Dana và Pháp quyền

Áp dụng công nghệ Blockchain để quản lý an toàn Dana (tiền đóng góp), xác minh Pháp quyền, và theo dõi lịch sử giao dịch trong cộng đồng Phật giáo.

## Mục đích

Đảm bảo tính minh bạch, an toàn, và có thể kiểm chứng cho mọi giao dịch Dana, đồng thời bảo vệ Pháp quyền của các kinh và tác phẩm Phật giáo.

## UI/UX

- **Trang Dashboard Dana:** `/daoanh/blockchain/dana`
  - Tổng quan: Số dana đã đóng, số dana đang chờ xác nhận, tổng giá trị
  - Lịch sử giao dịch: Danh sách đầy đủ kèm thời gian, mục đích, trạng thái
  - Nút Donate: Đóng dana với ví crypto (MetaMask, Trust Wallet)

- **Trang Xem chi tiết giao dịch:** `/daoanh/blockchain/tx-detail`
  - Thông tin: Hash giao dịch, khối chứa, xác nhận, phí gas
  - Trạng thái: Chờ xác nhận, Đã hoàn tất, Đã hủy
  - Xuất báo cáo: PDF, CSV cho kế toán chùa

- **Trang Pháp quyền:** `/daoanh/blockchain/copyright`
  - Danh sách kinh đã đăng ký FP (False Positive prevention)
  - Thông tin tác giả, năm đăng ký, trạng thái
  - Xem chữ ký số, lịch sử thay đổi

## Dữ liệu

- **Blockchain:** DILA-chain (phi tập trung, based on Ethereum)
- **Smart contracts:** Quản lý tài khoản donor, mục đích dana, phát tán thưởng
- **Token:** DILA-token (phi thương mại, dùng cho cộng đồng)
- **Metadata:** Tên kinh, tác giả, nguồn, ngày đăng ký, hash nội dung

## Acceptance criteria

- [ ] Tích hợp víMetaMask/TrustWallet hoạt động đúng 95% transaction
- [ ] Tạo giao dịch dana hoàn tất dưới 3 phút (xác nhận blockchain)
- [ ] Lịch sử giao dịch hiển thị đúng 100% với timestamp chính xác
- [ ] Tính phí gas minh bạch (hiển thị trước khi confirm)
- [ ] Tích hợp lại với hệ thống entity_claims có thể truy vấn GET /api/v1/blockchain/status

## File tương tự

- `docs/integration/M24-blockchain-dana-rights.md`
- `docs/Mimo-Flash/T99-m24-blockchain-dana-rights.md`