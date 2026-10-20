# M94 · Buddhist Mantra Composer

**Status:** 📄 Consolidated Documentation  
**Module:** M94  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp tự tạo mắc Phật tử: dùng để tự tạo mắc Phật tử tùy chỉnh dựa trên từ khóa, nguyện vọng, hoặc giai đoạn pratica.

## UI/UX

- **Trang Tự tạo mắc:** `/daoanh/mantra/compose`
  - Input: Từ khóa, nguyện vọng, giai đoạn prática (Sơ cấp, Nâng cao, Chuyên sâu)
   - Kết quả: Mắc tùy chỉnh (tên, chữ mantra, số lượng), xem trước mantra
   - Chức năng: Lưu mantra, chia sẻ mantra

- **Trang Mẫu mắc:** `/daoanh/mantra/templates`
  - Hiển thị mẫu mắc: 50+ mẫu mắc Phật tử đã được curate
   - Tìm kiếm: Tìm mẫu qua từ khóa
   - Chọn mẫu: Chọn mẫu mắc làm cơ sở cho mantra tùy chỉnh

- **Trang Cài đặt:** `/daoanh/mantra/settings`
  - Chọn mẫu mặc định: Mẫu mắc thường xuyên dùng
   - Thiết lập từ khóa ưu tiên: Từ khóa thường xuyên sử dụng
   - Thông báo: Kích hoạt nhắc nhở khi tạo mantra mới

## Dữ liệu

- **Mẫu mắc:** 50+ mẫu mắc Phật tử đã được curate
- **Từ khóa:** 100+ từ khóa mantra phổ biến
- **Thời gian tạo:** < 30s cho mỗi mantra tùy chỉnh
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Tạo mantra đúng 80% qua từ khóa và nguyện vọng
- [ ] Tìm mẫu đúng 90% qua từ khóa
- [ ] Thời gian tạo < 30s cho mỗi mantra tùy chỉnh
- [ ] Tích hợp với Module M79 (Mantra Tracker) và M88 (Malas Counter)
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không lưu trữ mantra nhạy cảm

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `composeMantra(keywords, wish, level)` - Tự tạo mantra
2. `getMantraTemplates()` - Lấy danh sách mẫu mắc
3. `getSettings()` - Lấy cài đặt tự tạo mantra
4. `getHistory()` - Lấy lịch sử tạo mantra

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T94-mantra-composer-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), tự tạo mantra logic, DB