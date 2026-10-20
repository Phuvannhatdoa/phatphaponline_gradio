# M14 · Bảo lưu số cho Tiến sĩ

**Spec · P2**

# M14 Bảo lưu số và Di sản kỹ thuật

Hệ thống bảo lưu số cho các tài liệu Kinh Đạo Phật: format preservation, migration, integrity verification, và long-term access cho trình độ Tiến sĩ.

## Mục đích

Đảm bảo các tài liệu Kinh Đạo Phbat được bảo lưu số theo chuẩn quốc tế, có thể truy cập lâu dài và di chuyển giữa các hệ thống khác cho người dùng trình độ Tiến sĩ.

## UI/UX

- **Trang Dashboard Bảo lưu:** `/daoanh/preservation/dashboard`
  - Tổng quan: tổng tài liệu, tài liệu đang bảo lưu, tài liệu cần migrate
  - Biểu đồ tiến độ: % tài liệu đã migrate, % còn giữ nguyên
  - Cảnh báo: tài liệu近期过期, format lỗ hổng

- **Trang Chi tiết tài liệu:** `/daoanh/preservation/detail`
  - Thông tin format, version, kiểm tra integrity
   - Lịch sử migration, ai thực hiện, khi nào
  - Nút Migration hiện thực, quay về version trước

- **Trang Audit Log:** `/daoanh/preservation/audit`
  - Daft: ai, khi nào, hành động gì, kết quả
  - Lọc: theo ngày, loại format, thành công/thất bại
  - Export log: JSON, CSV cho việc kiểm toán

## Dữ liệu

- **Format hỗ trợ:** TXT, XML, JSON, PDF, EPUB, ODT
- **Checksum:** SHA-256 cho từng file, album checksum cho bộ tài liệu
- **Migration history:** Bản ghi mỗi migration: từ→số, lý do, ai thực hiện, khi nào, kết quả
- **Storage:** DILA repository + backup archival (3-2-1 rule)

## Acceptance criteria

- [ ] Tạo checksum SHA-256 cho 100% tập tin quan trọng
- [ ] Migration test trên 50+ file mẫu: thành công > 95%
- [ ] Audit log chứa đủ trường: user, timestamp, action, result
- [ ] Hệ thống khôi phục từ backup trong 24h cho kịch bản catastrophe
- [ ] Tuân thủ quy tắc 3-2-1 (3 copy, 2 media, 1 off-site)

## File tương tự

- `docs/integration/M14-digital-preservation.md`
- `docs/Mimo-Flash/T89-m14-digital-preservation.md`