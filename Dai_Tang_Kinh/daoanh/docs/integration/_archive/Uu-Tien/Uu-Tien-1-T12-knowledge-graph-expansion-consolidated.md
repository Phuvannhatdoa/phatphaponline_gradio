# M12 · Buddhist Knowledge Graph Expansion

**Status:** 📄 Consolidated Documentation  
**Module:** M12  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Mở rộng Knowledge Graph cho Phật học: thêm các nút mới (Sư, Kinh, Khái niệm) và các đường liên hệ (truyền承, quan hệ, tương thích) vào đồ thị kiến thức Phật giáo đang mở rộng, kèm provenance và độ tin cậy.

## UI/UX

- **Trang Mở rộng Knowledge Graph:** `/daoanh/knowledge-graph/expand`
  - Input: Danh sách nút mới, danh sách đường mới
   - Kết quả: Đồ thị cập nhật kèm provenance cho mỗi phần tử
   - Tương tác: Click vào nút để xem chi tiết, kéo/thả để điều chỉnh xem

- **Trang Xem đồ thị:** `/daoanh/knowledge-graph/view`
  - Hiển thị đồ thị hiện tại: Các nút và đường hiện có
   - Bộ lọc: Lọc theo thời gian, nguồn gốc, thể loại
   - Tìm kiếm: Tìm nút hoặc đường theo ID hoặc tên

- **Trang Provenance:** `/daoanh/knowledge-graph/provenance`
  - Hiển thị nguồn gốc: Mỗi nút và đường có nguồn gốc, phiên bản, ngày thêm
   - Audit log: Ghi nhận các thay đổi qua thời gian

## Dữ liệu

- **Nút đồ thị:** 500+ nút có thể thêm
- **Đường đồ thị:** 2000+ đường có thể thêm
- **Thông tin provenance:** source_type (DILA/Marcus/WhG), version, date_added, verified_by
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Mở rộng đồ thị đúng 80% nút/lối mới không gây conflict
- [ ] Hiển thị provenance đúng 90% cho mỗi phần tử
- [ ] Tìm kiếm nút/lối nhanh chóng (< 2s)
- [ ] Tương thích với tất cả các thiết bị: điện thoại, tablet, desktop
- [ ] Bảo mật dữ liệu: Tất cả thay đổi được ghi nhận trong audit log

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `expandGraph(nodes, edges)` - Mở rộng Knowledge Graph với nút và đường mới
2. `getGraphView(filter)` - Lấy xem đồ thị theo bộ lọc
3. `searchGraph(query)` - Tìm nút/lối trong đồ thị
4. `getProvenance(elementId)` - Lấy provenance cho phần tử

**File path:** `docs/Mimo-Flash/M12-knowledge-graph-expansion-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), dữ liệu graph từ Neo4j/Triple store