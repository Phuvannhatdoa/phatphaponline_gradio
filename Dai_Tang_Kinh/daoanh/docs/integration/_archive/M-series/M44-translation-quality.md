# M44 · Đánh giá chất lượng Dịch thuật AI cho Tiến sĩ

**Spec · P2**

# M44 Đánh giá và Bảo minh chất lượng Dịch thuật

Cung cấp công cụ tự động đánh giá chất lượng dịch thuật AI cho các bản phiên bản Kinh, đảm bảo tính chính xác ngôn ngữ và phẩm chất phù hợp với bối cảnh Phật giáo.

## Mục đích

Độ bao kiểm tự động cho các nhà nghiên cứu và biên tập viên: độ chính xác ngữ nghĩa, sự phù hợp tôn giáo, và tính nhất quán từ vựng giữa các bản phiên bản.

## UI/UX

- **Trang Đánh giá dịch:** `/daoanh/translation/evaluate`
  - Input: Bản dịch AI, Bản gốc (Hán/Pali/Sanskrit)
  - Kết quả: Điểm chính xác (0-100), Phân tích sai ngữ nghĩa, Phê bình tôn giáo
  - Xuất báo cáo: PDF, HTML kèm các điểm cần sửa

- **Trang Quản lý bộ từ:** `/daoanh/translation/glossary`
  - Danh sách từ được phép/intercept cho dịch Phật giáo
  - Thêm từ mới, từ interdit, định nghĩa
  - Tìm kiếm từ: Hán-Pali-Sanskrit

- **Trang Sửa đổi:** `/daoanh/translation/fix`
  - Hiển thị các điểm cần sửa từ kết quả đánh giá
  - Công cụ chỉnh sửa đồng đắc, Lưu phiên bản so sánh

## Dữ liệu

- **Biên tập gia:** 5+ biên tập gia Phật giáo certified
- **Bộ từ:** 500+ từ Phật họcpecial, từ interdit, từ đồng nghĩa
- **Mẫu đánh giá:** 200+ bản dịch test có ground truth
- **Chính sách:** Chỉ chấp nhận bản dịch có điểm > 70/100 cho xuất bản

## Acceptance criteria

- [ ] Đánh giá chính xác phù hợp 80% so sánh với đánh giá của biên tập gia người
- [ ] Phát hiện sai ngữ nghĩa đúng 90% trường hợp có ground truth
- [ ] Bộ từ chứa 500+ từ Phật họcspecial
- [ ] Xuất báo cáo PDF kèm điểm chi tiết trong 2 phút
- [ ] Tăng công suất biên tập gia 30% (ít thời gian xem bản)

## File tương tự

- `docs/integration/M44-translation-quality.md`
- `docs/Mimo-Flash/T119-m44-translation-quality.md`