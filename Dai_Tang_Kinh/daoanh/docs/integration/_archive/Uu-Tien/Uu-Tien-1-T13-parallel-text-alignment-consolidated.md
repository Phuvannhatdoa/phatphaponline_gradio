# M13 · Buddhist Parallel Text Alignment

**Status:** 📄 Consolidated Documentation  
**Module:** M13  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp alignment song song cho văn bản Phật học: căn chỉnh hai (hoặc nhiều) phiên bản văn bản Hán-Pali-Sanskrit, đánh dấu từ tương ứng và tìm ra các từ đồng nghĩa/phản nghĩa giữa các phiên bản.

## UI/UX

- **Trang Alignment song song:** `/daoanh/text/alignment`
  - Input: Hai đoạn văn bản cần căn chỉnh (Ví dụ: Hán-Pali)
   - Kết quả: Bản song song kèm dấu vị trí từ tương ứng, độ tin cậy
   - Tùy chọn: Chỉ định dạng song song hoặc xuất file bilingual

- **Trang Tìm từ đồng nghĩa:** `/daoanh/text/synonyms`
  - Input: Từ Hán, tìm từ đồng nghĩa trong Pali/Sanskrit
   - Kết quả: Danh sách từ đồng nghĩa, nguồn gốc, độ khớp

- **Trang Cài đặt:** `/daoanh/text/alignment-settings`
  - Chọn cặp ngôn ngữ: Hán-Pali, Pali-Sanskrit, Hán-Việt, v.v.
   - Thiết lập độ khớp: Chỉ khớp chính xác, khớp lỏng, tự động
   - Thông báo: Kích hoạt lịch sử alignment

## Dữ liệu

- **Cặp văn bản:** 1000+ cặp đoạn văn bản Hán-Pali-Sanskrit đã căn chỉnh
- **Thể loại:** 4 thể loại chính căn chỉnh (Sự kiện, Tâm lý, Triết lý, Kịch bản)
- **Mẫu từ:** 5000+ từ đồng nghĩa/phản nghĩa giữa các ngôn ngữ Phật học
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Căn chỉnh đúng 90% từ trong cặp văn bản có ground truth
- [ ] Tìm từ đồng nghĩa đúng 85% cho từ Phật học phổ biến
- [ ] Tạo file bilingual đúng format trong 5 phút
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không gửi đoạn văn bản về server bên ngoài

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `alignTexts(text1, text2)` - Căn chỉnh hai đoạn văn bản
2. `findSynonyms(word, targetLang)` - Tìm từ đồng nghĩa
3. `getAlignmentDetail(alignmentId)` - Lấy chi tiết alignment
4. `getHistory()` - Lấy lịch sử alignment

**File path:** `docs/Mimo-Flash/M13-parallel-text-alignment-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), dữ liệu parallel text từ DB