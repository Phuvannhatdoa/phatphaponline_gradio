# M11 · Buddhist Text Processing AI

**Status:** 📄 Consolidated Documentation  
**Module:** M11  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp AI xử lý văn bản Phật học: tokenization, classification, và các tác vụ xử lý ngôn ngữ tự nhiên cho các đoạn Kinh và văn học Phật học.

## UI/UX

- **Trang Tokenization:** `/daoanh/ai/tokenization`
  - Input: Đoạn văn bản Phật học
   - Kết quả: Token danh sách, loại token (Từ, Thái từ, Tư duy), độ tin cậy

- **Trang Phân loại:** `/daoanh/ai/classification`
  - Input: Đoạn văn bản
   - Kết quả: Loại (Sự kiện, Tâm lý, Triết lý, Kịch bản), độ tin cậy

- **Trang Xử lý nâng cao:** `/daoanh/ai/advanced`
  - Tính toán: Số lượng từ, entropy, độ phức tạp
   - Xuất báo cáo: PDF kèm phân tích어 ngữ

## Dữ liệu

- **Mô hình xử lý:** Mô hình Phật học fine-tuned trên 50000+ đoạn văn bản
- **Loại token:** 1000+ loại token Phật học cơ bản
- **Thể loại:** 4 thể loại chính (Sự kiện, Tâm lý, Triết lý, Kịch bản)
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Tokenization chính xác 95% so với ground truth
- [ ] Phân loại đúng 90% cho 4 thể loại chính
- [ ] Phân tích nâng cao tạo báo cáo trong 5 phút
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không gửi đoạn văn bản về server bên ngoài

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `tokenize(text)` - Token hóa đoạn văn bản
2. `classifyText(text)` - Phân loại đoạn văn bản
3. `analyzeAdvanced(text)` - Phân tích nâng cao
4. `getModelInfo()` - Lấy thông tin mô hình

**File path:** `docs/Mimo-Flash/M11-text-processing-ai-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), mô hình AI đã training