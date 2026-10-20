# M29 · Buddhist Flashcards Spaced Repetition

**Status:** 📄 Consolidated Documentation  
**Module:** M29  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp hệ thống thẻ thắc khắc phân tán (spaced repetition) cho từ vựng Phật học: hỗ trợ practitioner ghi nhớ và ôn tập từ vựng quan trọng qua các khoảng thời gian tăng dần.

## UI/UX

- **Trang Flashcards:** `/daoanh/flashcards/study`
  - Hiển thị thẻ: Từ, Phiên âm, Nghĩa, Ví dụ
   - Chức năng: Đánh dấu "Known", "Review", "Forgotten"

- **Trang Cài đặt spaced repetition:** `/daoanh/flashcards/settings`
  - Thiết lập khoảng thời gian: 1 ngày, 3 ngày, 1 tuần, 1 tháng
   - Thống kê: Số thẻ đã học, đang ôn tập, quên

- **Trang Từ vựng:** `/daoanh/flashcards/vocabulary`
  - Danh sách từ vựng: 500+ từ vựng Phật học phổ biến
   - Tìm kiếm: Tìm từ vựng theo chữ cái, thể loại

## Dữ liệu

- **Số thẻ vựng:** 500+ từ vựng Phật học phổ biến
- **Khoảng thời gian:** 4 mức (1 ngày, 3 ngày, 1 tuần, 1 tháng)
- **Thống kê:** Số thẻ đã học, đang ôn tập, quên
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Hiển thị đúng 500+ từ vựng Phật học
- [ ] Hệ thống spaced repetition tăng khả ghỉnh nhớ 40% so với review cố định
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không chia sẻ hồ sơ học tập với bên thứ ba

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `studyFlashcard(cardId)` - Học thẻ thắc khắc
2. `updateCardStatus(cardId, status)` - Cập nhật trạng thái thẻ
3. `getVocabularyList(filter)` - Lấy danh sách từ vựng
4. `getStudyStats()` - Lấy thống kê học tập

**File path:** `docs/Mimo-Flash/M29-flashcards-spaced-repetition-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), spaced repetition algorithm