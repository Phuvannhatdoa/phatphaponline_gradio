# M89 · Buddhist Scripture Exporter

**Status:** 📄 Consolidated Documentation  
**Module:** M89  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp xuất xuất Kinh Phật: xuất đoạn Kinh, giáo Thái, hoặc các văn bản Phật tử ra các định dạng (PDF, JSON, CSV) để lưu trữ hoặc phân phối.

## UI/UX

- **Trang Xuất xuất:** `/daoanh/scripture/export`
  - Input: Đoạn Kinh, hoặc chọn mẫu xuất
   - Chọn định dạng xuất: PDF, JSON, CSV
   - Kết quả: File đã xuất, có thể Download

- **Trang Lịch sử xuất:** `/daoanh/scripture/export-history`
  - Lịch sử: Các lần xuất trước, thống kê qua thời gian (ngày/tháng/năm)
   - Phân tích: Loại file xuất nhiều nhất, xu hướng xuất

- **Trang Cài đặt:** `/daoanh/scripture/export-settings`
  - Chọn định dạng mặc định: Định dạng xuất thường xuyên
   - Thiết lập mẫu xuất mặc định: Mẫu xuất được chọn thường xuyên
   - Thông báo: Kích hoạt nhắc nhở khi xuất định dạng mới

## Dữ liệu

- **Định dạng:** 3 định dạng chính (PDF, JSON, CSV)
- **Thời gian xuất:** < 5s cho mỗi đoạn Kinh
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Xuất đúng 95% đoạn Kinh qua định dạng
- [ ] Thời gian xuất < 5s cho mỗi đoạn Kinh
- [ ] Tích hợp với Module M73 (Scripture Search) và M47 (Bookmarks)
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không logs xuất về bên thứ ba

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `exportScripture(segment, format)` - Xuất đoạn Kinh
2. `getExportHistory()` - Lấy lịch sử xuất
3. `getSettings()` - Lấy cài đặt xuất
4. `getSupportedFormats()` - Lấy danh sách định dạng hỗ trợ

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T89-scripture-export-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), xuất xuất library