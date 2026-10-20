# M67 · Deep Learning Text Generation cho Kinh TựĐắc

**Spec · P2**

# M67 Sinh văn bằng Deep Learning

Cung cấp mô hình sinh văn Deep Learning cho các đoạn kinh tự động: tạo đoạn trích mới, phong phú ngữ 어 (vocabulary), và hỗ trợ biên tập viên trong việc tạo nội dung Phật giáo.

## Mục đích

Triển khai mô hình GPT fine-tuned cho Phật giáo: cho phép sinh văn đoạn kinh theo phong cách các sư grandes, tạo sách sách phụ cho tu práctica, và cung cấp ground truth cho việc kiểm tra AI (Module M60).

## UI/UX

- **Trang Sinh văn:** `/daoanh/dlgen/generate`
  - Input: Chủ đề (Ngôn cảnh, Tâm lý, Triết lý), Phong cách (Sư X, Sư Y), Độ dài (100 từ, 500 từ, 1000 từ)
  - Output: Đoạn văn sinh ra kèm độ tin cậy (probability score)
  - Tùy chọn: Sửa đổi, lưu vào bộ sưu tập, xuất bản

- **Trang Đầu vào chủ đề:** `/daoanh/dlgen/topics`
  - Danh sách chủ đề Phật giáo phổ biến: 1000+ chủ đề có ground truth
  - Tìm kiếm từ khóa: Hán-Pali-Sanskrit
  - Chủ đề ngẫu nhiên: Sinh văn với chủ đề không xác định trước

- **Trang Xác minh AI:** `/daoanh/dlgen/verify`
  - So sánh đoạn văn sinh ra với ground truth (nếu có)
  - Điểm chính xác: 0-100%
  - Phân tích: Phát hiện sai ngữ nghĩa, phong cách không phù hợp

## Dữ liệu

- **Mô hình:** GPT-3 fine-tuned trên 10000+ đoạn kinh có ground truth
- **Thể loại:** Nền kinh, Từ bi, Triết lý Phật giáo
- **Chủ đề:** 500+ chủ đề Phật giáo được xác định sẵn
- **Độ dài:** 100-2000 từ tùy ý

## Acceptance criteria

- [ ] Sinh văn đoạn kinh đúng ngữ nghĩa 70% so sánh với do tạo ra bằng tay
- [ ] Tạo văn phong đúng phong cách sư giả 60% trường hợp
- [ ] Bộ chứa 500+ chủ đề Phật giáo
- [ ] Xuất bản nội dung trong 30s cho 500 từ
- [ ] Tăng tốc độ tạo nội dung cho biên tập gia 40%

## File tương tự

- `docs/integration/M67-deep-learning-generation.md`
- `docs/Mimo-Flash/T142-m67-deep-learning-generation.md`