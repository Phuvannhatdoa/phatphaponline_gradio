# M27 · Buddhist Citation & Referencing

**Status:** 📄 Consolidated Documentation  
**Module:** M27  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp hệ thống trích dẫn và tham khảo cho văn bản Phật học: chuẩn hóa định dạng trích dẫn, quản lý danh sách tham khảo, và kiểm tra tính chính xác trích dẫn.

## UI/UX

- **Trang Trích dẫn:** `/daoanh/citation/generate`
  - Input: Đoạn văn bản, nguồn (CBETA, DILA, sách giáo khoa)
   - Kết quả: Định dạng trích dẫn (APA, MLA, Chicago, Phật học), mã QR truy cập nguồn

- **Trang Quản lý tham khảo:** `/daoanh/citation/manage`
  - Hiển thị danh sách tham khảo: Tên, tác giả, năm, định dạng
   - Chức năng: Thêm/xóa/sửa tham khảo, sắp xếp

- **Trang Kiểm tra trích dẫn:** `/daoanh/citation/verify`
  - Kiểm tra tính chính xác: So sánh trích dẫn với nguồn gốc
   - Xuất báo cáo: PDF kèm báo cáo trích dẫn

## Dữ liệu

- **Định dạng trích dẫn:** APA, MLA, Chicago, Phật học (4 định dạng)
- **Nguồn chính:** CBETA, DILA, sách giáo khoa Phật học
- **Số lượng trích dẫn:** 10,000+ trích dẫn Phật học đã chuẩn hóa
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Tạo trích dẫn đúng 95% so với ground truth
- [ ] Quản lý 10,000+ tham chiếu chính xác
- [ ] Kiểm tra trích dẫn đúng 90% so với ground truth
- [ ] Tạo báo cáo trong 5 phút
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không gửi đoạn văn bản nhạy cảm về server bên ngoài

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `generateCitation(segment, format)` - Tạo trích dẫn cho đoạn văn bản
2. `manageReferences(referenceList)` - Quản lý danh sách tham khảo
3. `verifyCitation(citationId)` - Kiểm tra trích dẫn
4. `getCitationDetails(citationId)` - Lấy chi tiết trích dẫn

**File path:** `docs/Mimo-Flash/M27-citation-referencing-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), citation DB, format standards