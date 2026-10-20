# M34 · Trợ lý nghiên cứu AI cho Tiến sĩ

**Spec · P2**

# M34 Hỗ trợ nghiên cứu với trí tuệ nhân tạo

Cung cấp công cụ hỗ trợ nghiên cứu AI cho trình độ Tiến sĩ: tìm kiếm tự động, tổng hợp so sánh, và tạo bản mẫu báo cáo nghiên cứu từ dữ liệu Phật giáo.

## Mục đích

Tăng tốc độ nghiên cứu cho thầy tọt và nhà nghiên cứu bằng cách sử dụng AI để: tìm nguồn liên quan, so sánh các bản phiên bản Kinh, và tạo bản phân tích dữ liệuเบื้องต้น.

## UI/UX

- **Trang Tìm kiếm AI:** `/daoanh/research/ai-search`
  - Input: Chủ đề, từ khái niệm, hoặc entity_ref
  - Kết quả: Danh sách kinh liên quan, entity matching, luận án tương tự
  - Tùy chọn: Cải thiện truy vấn, xem nguồn

- **Trang Tổng hợp so sánh:** `/daoanh/research/comparison`
  - So sánh hai bản Kinh hoặc hai entity
  - Highlight điểm khác nhau, điểm giống nhau
  - Xuất báo cáo so sánh: PDF, HTML

- **Trang Tạo bản phân tích:** `/daoanh/research/generate`
  - Input: Mục tiêu nghiên cứu, phạm vi, phương pháp
  - Output: Bản mẫu báo cáo, bản tóm tắt kết quả, bảng dữ liệu sơ bộ
  - Tùy chọn: Chỉnh sửa, xuất tài liệu chính thức

## Dữ liệu

- **Model AI:** Phật giáo fine-tuned (chạy offline, Zero-RAM principle)
- **Knowledge base:** 2865 monk names, 912 nodes lineage, 447.885 entity_claims
- **Vector store:** Embeddings cho kinh, từ ngữ, entity để tìm kiếm tương đồng
- **Prompt templates:** Mẫu câu hỏi cho AI về Phật học (chắc chắn tuân thủ doctrine)

## Acceptance criteria

- [ ] Tìm kiếm AI trả kết quả liên quan cho 80+ chủ đề nghiên cứu mẫu
- [ ] So sánh bản Kinh hiển thị đúng các điểm khác nhau/sống nhau
- [ ] Bản mẫu báo cáo chứa đủ: Mục tiêu, Phương pháp, Kết quả, Kết luận
- [ ] Tạo bản mẫu dưới 5 phút cho từng yêu cầu nghiên cứu
- [ ] Kết quả AI có thể chỉnh sửa và xuất ra tài liệu chính thức

## File tương tự

- `docs/integration/M34-research-ai-assistant.md`
- `docs/Mimo-Flash/T109-m34-research-ai-assistant.md`