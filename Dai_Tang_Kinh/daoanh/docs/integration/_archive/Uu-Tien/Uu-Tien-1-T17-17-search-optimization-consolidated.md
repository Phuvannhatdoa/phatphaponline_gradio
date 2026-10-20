# M17 · Buddhist Search Optimization

**Status:** 📄 Consolidated Documentation  
**Module:** M17  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Tối ưu hóa tìm kiếm Phật học: fuzzy search, tìm từ khóa, tìm theo ngữ cảnh cho các đoạn Kinh và từ Phật học.

## UI/UX

- **Trang Tìm kiếm chính:** `/daoanh/search`
  - Input: Từ khóa, frase, từ Hán/Pali/Sanskrit
   - Kết quả: Danh sách kết quả kèm độ khớp, nguồn, độ chính xác
   - Bộ lọc: Theo thể loại, nguồn, khoảng thời gian

- **Trang Tìm fuzzy:** `/daoanh/search/fuzzy`
  - Tìm cho dù có lỗi đánh máy hoặc từ chưa chính xác
   - Hiển thị kết quả: Kết quả chính xác + kết quả tương tự

- **Trang Tìm ngữ cảnh:** `/daoanh/search/context`
  - Tìm theo ngữ cảnh: Tìm đoạn văn chứa từ khóa trong bối cảnh Phật học
   - Hiển thị: Đoạn văn trước/sau từ khóa, nguồn, ngữ cảnh

- **Trang Cài đặt:** `/daoanh/search/settings`
  - Chọn kiểu tìm: Fuzzy chính xác, ngữ cảnh, từ khóa
   - Thiết lập từ ngững: Từ tiếng Việt, tiếng Pali, tiếng Sanskriet
   - Thông báo: Kích hoạt lịch sử tìm kiếm

## Dữ liệu

- **Index tìm kiếm:** 50000+ đoạn văn bản Phật học đã index
- **Kiểu tìm:** Fuzzy search, ngữ từ khóa, ngữ cảnh
- **Thời gian phản hồi:** < 500ms cho tìm kiếm chính thường, < 2s cho fuzzy search
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Tìm kiếm chính xác 95% cho từ khóa phổ biến
- [ ] Tìm fuzzy đúng 80% cho từ có lỗi đánh máy
- [ ] Tìm ngữ cảnh đúng 85% cho đoạn văn chứa từ khóa trong bối cảnh
- [ ] Thời gian phản hồi < 500ms cho tìm kiếm thường
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không lưu trữ truy vấn tìm kiếm nhạy cảm

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `searchKeywords(keyword, options)` - Tìm kiếm theo từ khóa
2. `searchFuzzy(keyword, options)` - Tìm fuzzy
3. `searchContext(keyword, options)` - Tìm theo ngữ cảnh
4. `getSearchSettings()` - Lấy cài đặt tìm kiếm

**File path:** `docs/Mimo-Flash/M17-search-optimization-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), search index DB