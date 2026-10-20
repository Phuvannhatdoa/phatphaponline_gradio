# M85 · AI Dharma Teachings Verification

**Spec · P2**

# M85 Xác minh AI Giáo Thái Phật

Cung cấp công cụ xác minh giáo Thái do AI tạo ra cho Phật giáo: kiểm tra tính chính xác, tính nhất quán ngữ nghĩa, và phù hợp với bối cảnh Phật giáo cho các bài giảng, sách lược, và nội dung truyền thông.

## Mục đích

Thực hiện công cụ xác minh AI cho giáo Thái Phật: đảm bảo nội dung giáo Thái do AI tạo ra không sai ngữ nghĩa, phù hợp tôn giáo, và có nguồn gốc có thể kiểm chứng cho các nhà giảng dạy, biên tập viên truyền thông Phật giáo.

## UI/UX

- **Trang Xác minh giáo Thái:** `/daoanh/ai-teachings/verify`
  - Input: Giáo Thái do AI tạo, Giáo Thái gốc (nếu có)
  - Kết quả: Điểm chính xác (0-100), Phân tích sai ngữ nghĩa, Phê bình tôn giáo
  - Xuất báo cáo: PDF, HTML kèm các điểm cần sửa

- **Trang Từ điển AI Phật giáo:** `/daoanh/ai-teachings/dictionary`
  - Danh sách từ được phép/intercept cho AI giảng dạy Phật giáo
  - Thêm từ mới, từ interdit, định nghĩa
  - Tìm kiếm từ: Hán-Pali-Sanskrit

- **Trang Sửa đổi:** `/daoanh/ai-teachings/fix`
  - Hiển thị các điểm cần sửa từ kết quả xác minh
  - Công cụ chỉnh sửa đồng đắc, Lưu phiên bản so sánh

## Dữ liệu

- **Biên tập gia:** 5+ giáo sư Phật giáo certified
- **Bộ từ:** 1000+ từ giảng dạy Phật họcspecial, từ interdit, từ đồng nghĩa
- **Mẫu xác minh:** 500+ giáo Thái AI test có ground truth
- **Chính sách:** Chỉ chấp nhận giáo Thái AI có điểm > 70/100 cho xuất bản

## Acceptance criteria

- [ ] Xác minh giáo Thái chính xác phù hợp 80% so sánh với xác minh của giáo sư người
- [ ] Phát hiện sai ngữ nghĩa đúng 90% trường hợp có ground truth
- [ ] Bộ từ chứa 1000+ từ giảng dạy Phật họcspecial
- [ ] Xuất báo cáo PDF kèm điểm chi tiết trong 2 phút
- [ ] Tăng công suất giảng dạy 30% (ít thời gian xem bản)

## File tương tự

- `docs/integration/M85-ai-dharma-teachings-verification.md`
- `docs/Mimo-Flash/T161-m85-ai-dharma-teachings-verification.md`