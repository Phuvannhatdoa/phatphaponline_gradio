# M73 · Buddhist Scripture Search

**Status:** 📄 Consolidated Documentation  
**Module:** M73  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp tìm kiếm Kinh Phật: cho phép practitioner tìm kiếm các đoạn Kinh, giáo Thái, hoặc các từ khóa qua từ khóa, thể loại, hoặc cấu trúc câu.

## UI/UX

- **Trang Tìm kiếm Kinh:** `/daoanh/scripture/search`
  - Input: Từ khóa, thể loại (Kinh, Giáo Thái, Thiền), Bộ lọc (tác giả, thời gian)
   - Kết quả: Danh sách đoạn Kinh khớp, mỗi kết quả có thể preview (2-3 câu đầu), link đến nguồn gốc

- **Trang Preview đoạn Kinh:** `/daoanh/scripture/preview`
  - Hiển thị đoạn Kinh: Toàn bộ đoạn Kinh, thông tin (tác giả, thời gian, nguồn gốc), các đoạn liên quan
   - Tương tác: Bookmark đoạn Kinh, Share đoạn Kinh, Copy đoạn Kinh

- **Trang Cài đặt tìm kiếm:** `/daoanh/scripture/settings`
  - Chọn cơ sở dữ liệu: Local database, Cloud database, Hai hai
   - Thiết lập từ khóa ưu tiên: Từ khóa thường xuyên tìm
   - Thông báo: Kích hoạt nhắc nhở khi tìm thấy đoạn Kinh mới

## Dữ liệu

- **Đoạn Kinh:** 10000+ đoạn Kinh Phật giáo có sẵn
- **Thể loại:** 20+ thể loại Kinh (Sutta, Vinaya, Abhidharma, và các thể loại khác)
- **Thời gian tìm kiếm:** < 2s cho mỗi từ khóa
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Tìm kiếm đúng 90% đoạn Kinh qua từ khóa
- [ ] Thời gian tìm kiếm < 2s cho mỗi từ khóa
- [ ] Tích hợp Bookmark (Module M47) và Share (Module M44)
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không logs tìm kiếm về bên thứ ba

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `searchScripture(query, filter)` - Tìm kiếm đoạn Kinh
2. `getScriptureDetails(segmentId)` - Lấy chi tiết đoạn Kinh
3. `getSettings()` - Lấy cài đặt tìm kiếm Kinh
4. `getHistory()` - Lấy lịch sử tìm kiếm

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T73-scripture-search-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), scripture database, search engine