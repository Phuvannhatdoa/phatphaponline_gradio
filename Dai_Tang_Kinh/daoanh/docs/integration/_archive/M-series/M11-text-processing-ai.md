# M11 · Nền xử lý văn bản AI cho Cử Nhân

**Spec · P1**

# M11 Xử lý văn bản và AI

Cung cấp khả năng xử lý văn bản tự động cho trình độ Cử Nhân: tokenization, stemming, classification, và trợ lý tra cứu tự động.

## Mục đích

Tự động hóa các tác vụ xử lý văn bản Kinh Đạo Phật: tách từ, phân loại, trích xuất thông tin cho người dùng trình độ Cử Nhân.

## UI/UX

- **Trang trợ lý tra cứu:** `/daoanh/assistant/search`
  - Nhập câu hỏi tự nhiên (Tiếng Việt/Hán)
  - Kết quả hiển thị: danh sách nhân vật, kinh, quan hệ thầy trò
  - Tùy chọn: cải thiện câu hỏi, hiển thị nguồn

- **Trang thống kê nhanh:** `/daoanh/analytics/quick`
  - Số lượng kết quả, tỷ lệ chính xác, nguồn phổ biến
  - Biểu đồ đơn giản: top 10 truy vấn tuần

## Dữ liệu

- **Model LM:** Phật giáo fine-tuned (chạy offline, Zero-RAM principle)
- **Glossary:** 248.095 từ (glossary_term table, 75.54% Việt hóa)
- **Entity database:** 447.885 claims (entity_claims, verified status)
- **Tokenizer:** Tự phát triển cho Hán-Việt-Pali

## Acceptance criteria

- [ ] Tokenize 100+ câu hỏi Phật giáo chính xác > 90%
- [ ] Phân loại motive chính xác cho 50+ motive tu prática
- [ ] Trợ lý trả kết quả liên quan cho 80% truy vấn mẫu
- [ ] Hiển thị badge nguồn cho mọi kết quả
- [ ] Hoạt động trên dữ liệu có sẵn (không cần DB write)

## File tương tự

- `docs/integration/M11-text-processing-ai.md`
- `docs/Mimo-Flash/T86-m11-text-processing-ai.md`