# M6 · Buddhist Academic Research Tools

**Status:** 📄 Consolidated Documentation  
**Module:** M6  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp bộ công cụ học術研究 Phật học: hỗ trợ pesquisers in text comparison, knowledge graph expansion, parallel text alignment, and digital preservation cho các đoạn Kinh và văn học Phật học.

## UI/UX

- **Trang So sánh văn bản:** `/daoanh/research/text-comparison`
  - Input: Hai đoạn văn bản cần so sánh
   - Kết quả: Báo độ đồng nhất, điểm khác biệt, đánh giá nguồn

- **Trang Mở rộng Knowledge Graph:** `/daoanh/research/knowledge-graph`
  - Hiển thị đồ thị kiến thức: Các nút (Sư, Kinh, Khái niệm) và các đường (truyền承, quan hệ)
   - Tương tác: Click vào nút để xem chi tiết, kéo/thả để điều chỉnh xem
   - Bộ lọc: Lọc theo thời gian, nguồn gốc, thể loại

- **Trang Phân tích song song:** `/daoanh/research/parallel-text`
  - Hiển thị bản song song: Hai phiên bản Hán-Pali-Sanskrit kèm hàng hàng
   - Tìm kiếm ngữ cảnh: Tìm theo từ khóa, ngữ cảnh

- **Trang Bảo quản số:** `/daoanh/research/digital-preservation`
  - Kiểm tra checksum: MD5, SHA256 cho từng file Kinh
   - Lịch sử thay đổi: Ghi nhận các thay đổi qua thời gian
   - Sao lưu: Tạo bản sao lưu an toàn

## Dữ liệu

- **So sánh văn bản:** 1000+ cặp đoạn văn bản Phật học so sánh
- **Knowledge Graph:** 500+ nút, 2000+ quan hệ Triết lý
- **Bản song song:** 500+ cặp văn bản Hán-Pali-Sanskrit
- **Bảo存 digital:** 1000+ file Kinh có checksum

## Acceptance criteria

- [ ] So sánh văn bản đúng 90% so vớireview chuyên gia
- [ ] Mở rộng Knowledge Graph đúng 80% quan hệ mới
- [ ] Phân tích song song đúng 85% ngữ cảnh
- [ ] Bảo存 digital: Tạo bản sao lưu an toàn cho 100% file
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `compareTexts(text1, text2)` - So sánh hai đoạn văn bản
2. `expandKnowledgeGraph(nodes, edges)` - Mở rộng đồ thị kiến thức
3. `alignParallelText(text1, text2)` - Phân tích bản song song
4. `checksumFile(filePath)` - Tạo checksum cho file

**File path:** `docs/Mimo-Flash/Uu-Tien-1-T06-academic-research-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), dữ liệu research từ DB