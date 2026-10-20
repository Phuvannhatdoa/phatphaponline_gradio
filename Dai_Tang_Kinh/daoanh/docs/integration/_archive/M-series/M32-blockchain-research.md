# M32 · Blockchain cho Dữ liệu Nghiên cứu Tiến sĩ

**Spec · P2**

# M32 Sử dụng Blockchain xác thực dữ liệu nghiên cứu

Áp dụng công nghệ Blockchain để xác minh nguồn gốc, tính toàn vẹn, và lịch sử thay đổi cho dữ liệu nghiên cứu Phật giáo: entity_claims, glossary_term, và audit logs.

## Mục đích

Đảm bảo tính chính xác và có thể kiểm chứng cho mọi dữ liệu nghiên cứu: ai đã sửa sửa, khi nào, nội dung thay đổi ra sao, và dữ liệu gốc vẫn được duy trì nguyên vẹn.

## UI/UX

- **Trang Dashboard Xác thực:** `/daoanh/blockchain/research`
  - Tổng quan: Số bản ghi đã xác minh, tỷ lệ thành công
  - Danh sách bản ghi chờ xác minh: entity_ref, action, trạng thái
  - Nút Xác minh: Bắt đầu quy trình verify cho từng bản ghi

- **Trang Chi tiết bản ghi:** `/daoanh/blockchain/tx-detail/:id`
  - Thông tin: Hash bản ghi, khối chứa, xác nhận, phí gas
  - Lịch sử thay đổi: Bản ghi cũ, bản ghi mới, ai thực hiện
  - Xuất báo cáo: PDF, CSV cho kiểm toán nhà nghiên cứu

- **Trang Lịch sử:** `/daoanh/blockchain/history`
  - Toàn bộ lịch sử giao dịch Blockchain từ ngày đầu
  - Lọc: Theo ngày, loại thay đổi, thành công/thất bại
  - Xuất log: TXT, JSON cho nhà nghiên cứu

## Dữ liệu

- **Blockchain:** DILA-chain (phi tập trung, based on Ethereum)
- **Smart contracts:** Quản lý entity_claims verification, audit trail
- **Token:** DILA-research-token (dùng cho cộng nghiên cứu)
- **Metadata:** entity_id, field_name, old_value, new_value, evidence_sources, authority_rank

## Acceptance criteria

- [ ] Tạo xác minh cho 100 entity_claims hoàn tất dưới 5 phút (xác nhận blockchain)
- [ ] Lịch sử thay đổi hiển thị đúng 100% với timestamp chính xác
- [ ] Tính phí gas minh bạch (hiển thị trước khi confirm)
- [ ] Tích hợp lại với hệ thống entity_claims có thể truy vấn GET /api/v1/blockchain/research/status
- [ ] Test kiểm tra integrity > 95% so sánh với dữ liệu thô

## File tương tự

- `docs/integration/M32-blockchain-research.md`
- `docs/Mimo-Flash/T117-m32-blockchain-research.md`