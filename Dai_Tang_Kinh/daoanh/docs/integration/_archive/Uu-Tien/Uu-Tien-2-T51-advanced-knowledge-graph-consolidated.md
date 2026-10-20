# M51 · Buddhist Advanced Knowledge Graph

**Status:** 📄 Consolidated Documentation  
**Module:** M51  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp Knowledge Graph nâng cao cho Phật học: multi-layer relationships với dynamics theo thời gian, provenance cho mỗi phần tử, và các truy vấn phức tạp qua Knowledge GraphQL.

## UI/UX

- **Trang Knowledge Graph:** `/daoanh/knowledge-graph/advanced`
  - Hiển thị Knowledge Graph: Multi-layer nodes và edges kèm provenance
   - Tương tác: Click vào nút/đường để xem chi tiết, filter theo thời gian, nguồn gốc, thể loại
   - Tìm kiếm: Tìm nút/lối qua Knowledge GraphQL

- **Trang Truy vấn phức tạp:** `/daoanh/knowledge-graph/advanced-query`
  - Truy vấn: Knowledge GraphQL queries phức tạp
   - Kết quả: Kết quả truy vấn kèm độ tin cậy, provenance

- **Trang Provenance:** `/daoanh/knowledge-graph/provenance`
  - Hiển thị provenance: Mỗi nút và đường có provenance, phiên bản, ngày thêm
   - Audit log: Ghi nhận các thay đổi qua thời gian

## Dữ liệu

- **Nút Knowledge Graph:** 1000+ nút có thể thêm
- **Đường Knowledge Graph:** 5000+ đường có thể thêm
- **Thông tin provenance:** source_type (DILA/Marcus/WhG), version, date_added, verified_by
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Mở rộng Knowledge Graph đúng 80% nút/lối mới không gây conflict
- [ ] Hiển thị provenance đúng 90% cho mỗi phần tử
- [ ] Tìm Knowledge GraphQL nhanh chóng (< 2s)
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Tất cả thay đổi được ghi nhận trong audit log

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `expandKnowledgeGraph(nodes, edges)` - Mở rộng Knowledge Graph với nút và đường mới
2. `advancedQuery(query)` - Tri Knowledge GraphQL phức tạp
3. `getProvenance(elementId)` - Lấy provenance cho phần tử
4. `getHistory()` - Lấy lịch sử thay đổi

**File path:** `docs/Mimo-Flash/Uu-Tien-2-T51-advanced-knowledge-graph-consolidated.md`
**Dependencies:** Module M0 (base foundation already created), Knowledge Graph database (Neo4j/janusgraph), provenance tracking system