# M57 · Buddhist Living Dharma Knowledge Graphs

**Status:** 📄 Consolidated Documentation  
**Module:** M57  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp đồTriết lý Dharma Sống: xây dựng và duy trì đồTriết lý Phật học liên tục cập nhật, bao gồm quan hệ giữa các Sư, truyền承, Kinh, và các khái niệm thiền.

## UI/UX

- **Trang DồTriết lý:** `/daoanh/knowledge-graph/explore`
  - Hiển thị đồTriết lý: Các nút (Sư, Kinh, Khái niệm) và các đường (truyền承, quan hệ, tương thích)
   - Tương tác: Click vào nút để xem chi tiết, kéo/thả để điều chỉnh xem
   - Bộ lọc: Lọc theo thời gian, nguồn gốc, thể loại

- **Trang Đường truyền承:** `/daoanh/knowledge-graph/lineage`
  - Hiển thị truyền承: Đường truyền từ Bồ-đề đến Sư hiện tại
   - Tìm kiếm Sư: Tìm kiếm theo tên, école, quốc gia

- **Trang Khám phá khái niệm:** `/daoanh/knowledge-graph/concepts`
  - Khái niệm liên quan: Khi click vào một khái niệm, hiển thị các khái niệm liên quan
   - Tìm kiếm ngữ cảnh: Tìm kiếm theo ngữ cảnh (Thiền, Triết lý, Lễ hội)

## Dữ liệu

- **Nút đồTriết lý:** 1000+ nút (Sư, Kinh, Khái niệm, trường phái)
- **Đường đồTriết lý:** 5000+ quan hệ (truyền承, tác phẩm, quan hệ Triết lý)
- **Cập nhật liên tục:** Dữ liệu được cập nhật hàng tuần từ nguồn uy tín
- **Tương thích:** Tất cả thiết bị: điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Hiển thị đúng 1000+ nút và 5000+ quan hệ Triết lý
- [ ] Tìm kiếm Sư/Kinh nhanh chóng (< 2s)
- [ ] Cập nhật dữ liệu hàng tuần thành công
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Không chia sẻ dữ liệu đồTriết lý với bên thứ ba

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `exploreKnowledgeGraph(filter)` - Khám phá đồTriết lý
2. `getLineage()` - Lấy đường truyền承
3. `searchConcepts(query)` - Tìm khái niệm liên quan
4. `getGraphUpdates()` - Lấy cập nhật dữ liệu

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T57-living-dharma-knowledge-graphs-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), knowledge graph database, continuous update system