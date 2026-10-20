# M26 · Buddhist Research Data Curation

**Status:** 📄 Consolidated Documentation  
**Module:** M26  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp hệ thống quản lý dữ liệu nghiên cứu Phật học: quản lý, phân loại, và bảo存研究 dữ liệu nghiên cứu cho các đoạn văn bản, đồ thị, và nguồn tài nguyên học thuật.

## UI/UX

- **Trang Quản lý dữ liệu nghiên cứu:** `/daoanh/research/data-management`
  - Hiển thị bộ sưu tập dữ liệu: Tên, loại, mô tả, trạng thái
   - Các chức năng: Import, export, classification, tagging

- **Trang Phân loại dữ liệu:** `/daoanh/research/classification`
  - Phân loại: Văn bản, Đồ thị, Audiovisual, Metadata
   - Thẻ: Thẻ tùy chỉnh, từ vựng kiểm soát

- **Trang Bảo存研究:** `/daoanh/research/preservation`
  - Kiểm tra checksum: MD5, SHA256
   - Lịch backup: Định kỳ (tuần/quý/năm)
   - Phục phục: Hướng dẫn phục phục dữ liệu nếu hư hỏng

## Dữ liệu

- **Bộ sưu tập dữ liệu:** 10,000+ dữ liệu nghiên cứu Phật học
- **Loại dữ liệu:** Văn bản, Đồ thị, Audiovisual, Metadata
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop
- **Thời gian backup:** Định kỳ theo cấu hình

## Acceptance criteria

- [ ] Quản lý 10,000+ dữ liệu nghiên cứu chính xác
- [ ] Phân loại dữ liệu đúng 90% tự động
- [ ] Tạo checksum cho 100% bộ sưu tập
- [ ] Tạo báo cáo backup trong 10 phút
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Tất cả backup thực hiện cục bộ

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `manageResearchData(data)` - Quản lý dữ liệu nghiên cứu
2. `classifyResearchData(dataType)` - Phân loại dữ liệu nghiên cứu
3. `calculateChecksum(filePath)` - Tính checksum
4. `scheduleBackup()` - Lên lịch backup

**File path:** `docs/Mimo-Flash/M26-research-data-curation-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), research data DB