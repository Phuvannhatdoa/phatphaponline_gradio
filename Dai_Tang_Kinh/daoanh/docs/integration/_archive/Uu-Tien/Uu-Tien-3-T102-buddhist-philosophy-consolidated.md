# M102 · Buddhist Philosophy Fundamentals

**Status:** 📄 Consolidated Documentation  
**Module:** M102  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp nền tảng triết lý Phật giáo hệ thống cho trình độ Sĩ/Vương vấn: đề cập đến tư duy cốt lõi, khái niệm chủ đạo và luận pháp Phật giáo qua các đại phái và truyền thống.

## UI/UX

- **Trang Tổng quan Triết lý:** `/daoanh/philosophy/overview`
  - Hiển thị các đại nghi cốt lõi: Không-an, Không-thể, Niết-bàn
  - Biểu đồ tương quan: Mối liên hệ giữa các khái niệm chính
  - Chọn truyền thống: Theravāda, Mahāyāna, Vajrayāna, Zen

- **Trang Sâu trường luận:** `/daoanh/philosophy/debate`
  - Xem các sáo trật cốt lõi: Tư tưởng vuông vắn, Chánh kiến, Đạo chí
  - Lua chọn tranh luận: Chọn chủ đề tranh luận Phật học tiêu biểu
  - Kết quả: Hiển thị quan điểm khác nhau qua các phái

- **Trang Từ điển khái niệm:** `/daoanh/philosophy/glossary`
  - Tra từ Pali, Sanskrit, Tiếng Việt
  - Hiển thị origin, biến thiên qua giai đoạn, tham chiếu Kinh
  - Tìm kiếm liên quan: Khái niệm liên quan, таксономи

- **Trang Cài đặt:** `/daoanh/philosophy/settings`
  - Chọn phạm vi hiển thị: Toàn bộ các phái hoặc chỉ một phái
  - Thiết lập ngôn ngữ mặc định: Pali, Sanskrit, Tiếng Việt, Anh
  - Tích hợp tham chiếu: Kết nối với CBETA, SuttaCentral cho nguồn gốc

## Dữ liệu

- **Khái niệm cốt lõi:** 50+ khái niệm nền tắc (Anatta, Dukkha, Nibbana, Pratītyasamutpāda,...)
- **Tham chiếu Kinh:** 100+ đoạn kinh trích dẫn cho khái niệm cốt lõi
- **Phân phái:** 4 đại phái chính (Theravāda, Mahāyāna, Vajrayāna, Zen) kèm đặc điểm riêng
- **Thời đại:** 20+ trí tuệ Phật học contemporáneo, tác giả, tác phẩm
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Hiển thị đúng 50+ khái niệm nền tắc Phật giáo kèm định nghĩa
- [ ] Tra cứu từ hoạt động đúng 90% từ khóa Phật học phổ biến
- [ ] Biểu đồ tương quan hiển thị đúng 80% mối liên hệ cốt lõi
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Tích hợp tham chiếu CBETA/SuttaCentral cho 100+ đoạn kinh trích dẫn
- [ ] Hỗ trợ 4 đại phái chính kèm đặc điểm chuyên biệt

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `getPhilosophyOverview()` - Lấy tổng quan triết lý Phật giáo
2. `searchConcept(term)` - Tra cứu khái niệm
3. `getSchoolComparisons()` - So sánh các phái Phật học
4. `getSettings()` - Lấy cài đặt triết lý

**File path:** `docs/Mimo-Flash/Uu-Tien-3-T102-buddhist-philosophy-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), CBETA/SuttaCentral API, Phật học ontology database, Multilingual dictionary system

## Mối liên hệ với các module trước

- Tích hợp dữ liệu từ M7 (GIS Maps) cho bản đồ phân tán trí tuệ Phật học
- Xây dựng trên M50 (Neural Network Optimization) cho ability tìm kiếm khái niệm
- Tuân thủ chung zero-RAM principle với toàn bộ hệ thống PTDA
- Mở rộng từ M35 (Lịch Phật giáo) về mặt khái niệm thời gian/tranh luận

---