# M34 · Buddhist AI Research Assistant

**Status:** 📄 Consolidated Documentation  
**Module:** M34  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp trợ lý AI cho nghiên cứu Phật học: hỗ trợ tìm nguồn, so sánh văn bản, và tạo bản tóm tắt cho các đoạn văn bản nghiên cứu.

## UI/UX

- **Trang trợ lý nghiên cứu:** `/daoanh/ai/research-assistant`
  - Input: Câu hỏi nghiên cứu, đoạn văn bản cần phân tích
   - Kết quả: Trả lời AI, nguồn tham khảo, bản tóm tắt

- **Trang Tìm nguồn:** `/daoanh/ai/search-source`
  - Tìm nguồn: CBETA, DILA, Wikidata, nguồn khác
   - Kết quả: Danh sách nguồn kèm độ tin cậy

- **Trang Tóm tắt:** `/daoanh/ai/summary`
  - Tóm tắt đoạn văn bản: Tóm tắt ngắn (100 từ), tóm tắt chi tiết (500 từ)
   - Xuất báo cáo: Xuất báo cáo tóm tắt ra file PDF hoặc Word

## Dữ liệu

- **Nguồn chính:** CBETA, DILA, Wikidata, nguồn khác
- **Độ tin cậy:** 0-100% cho mỗi nguồn
- **Loại tóm tắt:** Ngắn (100 từ), Chi tiết (500 từ)
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Trợ lý AI trả lời đúng 85% cho câu hỏi nghiên cứu Phật học
- [ ] Tìm nguồn chính xác 90% cho nguồn CBETA/DILA/Wikidata
- [ ] Tạo tóm tắt đúng 90% nội dung quan trọng giữ lại
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không gửi đoạn văn bản nghiên cứu nhạy cảm về server bên ngoài

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `researchAssistant(query)` - Trợ lý nghiên cứu trả lời câu hỏi
2. `searchSource(topic)` - Tìm nguồn cho chủ đề
3. `generateSummary(text, length)` - Tạo bản tóm tắt
4. `getAssistantSettings()` - Lấy cài đặt trợ lý AI

**File path:** `docs/Mimo-Flash/M34-research-ai-assistant-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), AI model, knowledge base