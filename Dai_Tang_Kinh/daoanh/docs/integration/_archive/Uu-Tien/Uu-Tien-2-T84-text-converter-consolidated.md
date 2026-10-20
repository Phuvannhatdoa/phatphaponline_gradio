# M84 · Buddhist Text Converter

**Status:** 📄 Consolidated Documentation  
**Module:** M84  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp chuyển đổi văn bản Phật học: chuyển đổi giữa các định dạng văn bản (Tiếng Việt, Tiếng Trung, English), và giữa các bộ ký tự (Unicode, UTF-8, diacritics-free).

## UI/UX

- **Trang Chuyển đổi định dạng:** `/daoanh/text/convert`
  - Input: Đoạn văn bản Phật học
   - Chọn định dạng đầu ra: Tiếng Việt, Tiếng Trung, English
   - Chọn bộ ký tự: Unicode, UTF-8, diacritics-free
   - Kết quả: Văn bản đã chuyển đổi, có thể Copy

- **Trang Lịch sử chuyển đổi:** `/daoanh/text/history`
  - Lịch sử: Các đoạn văn bản đã chuyển đổi trước, xu hướng chuyển đổi qua thời gian

- **Trang Cài đặt:** `/daoanh/text/settings`
  - Chọn định dạng mặc định: Định dạng thường xuyên dùng
   - Thiết lập bộ ký tự mặc định: Bộ ký tự được chọn thường xuyên
   - Thông báo: Kích hoạt nhắc nhở khi chuyển đổi định dạng mới

## Dữ liệu

- **Định dạng:** 3 định dạng chính (Tiếng Việt, Tiếng Trung, English)
- **Bộ ký tự:** 3 bộ ký tự chính (Unicode, UTF-8, diacritics-free)
- **Thời gian chuyển đổi:** < 1s cho mỗi đoạn văn bản
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Chuyển đổi đúng 95% đoạn văn bản qua định dạng
- [ ] Thời gian chuyển đổi < 1s cho mỗi đoạn văn bản
- [ ] Tích hợp với Module M47 (Bookmarks) và M73 (Scripture Search)
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không lưu trữ đoạn văn bản chuyển đổi nhạy cảm

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `convertText(text, format, characterSet)` - Chuyển đổi văn bản
2. `getConversionHistory()` - Lấy lịch sử chuyển đổi
3. `getSettings()` - Lấy cài đặt chuyển đổi
4. `getSupportedFormats()` - Lấy danh sách định dạng hỗ trợ

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T84-text-converter-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), chuyển đổi văn bản library