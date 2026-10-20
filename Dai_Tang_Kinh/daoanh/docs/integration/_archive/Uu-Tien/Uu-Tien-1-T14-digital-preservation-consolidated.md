# M14 · Buddhist Digital Preservation

**Status:** 📄 Consolidated Documentation  
**Module:** M14  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp hệ thống bảo quản số cho văn bản Phật học: kiểm tra checksum, migration dữ liệu, và đảm bảo tính bền vững của tài nguyên số qua thời gian.

## UI/UX

- **Trang Kiểm tra checksum:** `/daoanh/preservation/checksum`
  - Input: File văn bản/Kinh cần kiểm tra
   - Kết quả: Checksum (MD5, SHA256), trạng thái: Bình thường/Cảnh báo/ Nguy hiểm
   - Lịch sử: Ghi nhận các thay đổi checksum qua thời gian

- **Trang Migration dữ liệu:** `/daoanh/preservation/migration`
  - Kế hoạch migration: Từ format cũ sang format mới
   - Báo cáo migration: Chi tiết các thay đổi, dữ liệu thất / thành công
   - Xuất báo cáo: PDF kèm báo cáo migration

- **Trang Tài nguyên an toàn:** `/daoanh/preservation/safe-resources`
  - Danh sách tài nguyên an toàn: File đã kiểm tra, sao lưu, có checksum
   - Thời gian kiểm tra: Lần kiểm tra gần nhất, kế hoạch kiểm tra tiếp theo
   - Phục phục: Hướng dẫn phục phục dữ liệu nếu hư hỏng

## Dữ liệu

- **File kiểm tra:** 1000+ file Kinh/văn bản đã có checksum
- **Thuật toán:** MD5, SHA1, SHA256
- **Lịch kiểm tra:** Định kỳ (mỗi tháng, mỗi quý, mỗi năm)
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Tạo checksum cho 100% file quan trọng
- [ ] Migration dữ liệu đúng 95% không mất dữ liệu
- [ ] Tạo báo cáo migration trong 10 phút
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Tất cả kiểm tra thực hiện cục bộ, không gửi dữ liệu nhạy cảm về server

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `calculateChecksum(filePath, algorithm)` - Tính checksum cho file
2. `migrateData(oldFormat, newFormat)` - Di chuyển dữ liệu từ format cũ sang format mới
3. `getChecksumHistory(filePath)` - Lấy lịch sử checksum
4. `getSafeResources()` - Lấy danh sách tài nguyên an toàn

**File path:** `docs/Mimo-Flash/M14-digital-preservation-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), file system access