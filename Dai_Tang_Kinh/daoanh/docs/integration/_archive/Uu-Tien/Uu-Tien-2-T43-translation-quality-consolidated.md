# M43 · Buddhist Translation Quality

**Status:** 📄 Consolidated Documentation  
**Module:** M43  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp hệ thống đánh giá chất lượng dịch Phật học: kiểm tra chính xác, nhất quán ngữ nghĩa, và phù hợp với bối cảnh Phật học cho các bản dịch Kinh và giáo Thái.

## UI/UX

- **Trang Đánh giá dịch:** `/daoanh/translation/quality`
  - Input: Bản dịch cần đánh giá, Bản gốc (nếu có)
   - Kết quả: Điểm chính xác (0-100), Phân tích sai ngữ nghĩa, Phê bình tôn giáo
   - Xuất báo cáo: PDF, HTML kèm các điểm cần sửa

- **Trang Từ điển đánh giá:** `/daoanh/translation/dictionary`
  - Danh sách từ được phép/intercept cho AI dịch Phật học
  - Thêm từ mới, từ interdit, định nghĩa
  - Tìm kiếm từ: Hán-Pali-Sanskrit

- **Trang Sửa đổi:** `/daoanh/translation/fix`
  - Hiển thị các điểm cần sửa từ kết quả đánh giá
  - Công cụ chỉnh sửa đồng đắc, Lưu phiên bản so sánh

## Dữ liệu

- **Biên tập gia:** 5+ biên tập gia Phật học certified
- **Bộ từ:** 1000+ từ Phật họcspecial, từ interdit, từ đồng nghĩa
- **Mẫu đánh giá:** 200+ bản dịch AI test có ground truth
- **Chính sách:** Chỉ chấp nhận bản dịch có điểm > 70/100 cho xuất bản

## Acceptance criteria

- [ ] Đánh giá chính xác phù hợp 80% so sánh với đánh giá của biên tập gia người
- [ ] Phát hiện sai ngữ nghĩa đúng 90% trường hợp có ground truth
- [ ] Bộ từ chứa 1000+ từ Phật họcspecial
- [ ] Xuất báo cáo PDF kèm điểm chi tiết trong 2 phút
- [ ] Tăng công suất biên tập gia 30% (ít thời gian xem bản)

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `evaluateTranslation(translation, original)` - Đánh giá bản dịch
2. `manageDictionary(word, action)` - Quản lý từ điển
3. `getEvaluationDetails(assessmentId)` - Lấy chi tiết đánh giá
4. `getSettings()` - Lấy cài đặt đánh giá

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T43-translation-quality-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), bién tập gia đội ngũ, bộ từ Phật học