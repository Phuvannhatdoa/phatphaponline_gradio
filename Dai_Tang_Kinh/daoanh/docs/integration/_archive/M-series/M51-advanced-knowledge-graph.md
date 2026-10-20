# M51 · Mở rộng Knowledge Graph tiên tiến cho Tiến sĩ

**Spec · P2**

# M51 Mở rộng Knowledge Graph tiên tiến

Mở rộng Knowledge Graph với các thuộc tính phức tạp: mối quan hệ đa cấp, thời gian động, và xác suất xác minh cho dữ liệu Phật giáo tiên tiến.

## Mục đích

Mở rộng khả năng truy xuất phức tạp qua Knowledge Graph: liên kết đa cấp, xác suất xác minh, và truy xuất lịch sử thay đổi theo thời gian cho người dùng trình độ Tiến sĩ.

## UI/UX

- **Trang Explore Graph nâng cao:** `/daoanh/graph/advanced`
  - Đồ thị tương tác: node (người, kinh, chùa) và edge (thầy trò, nguồn, địa lý, thời gian)
  - Filter động: Thời gian, xác suất, loại quan hệ
  - Hover card: hiển thị metadata (ID, tên, lý do, nguồn, trạng thái, xác suất)

- **Trang Query Builder nâng cao:** `/daoanh/graph/query/advanced`
  - Cypher-like query builder cho Knowledge Graph với thời gian
  - Presets: "Tất cả thầy trò của X trong thời gian T", "Tìm nguồn chung thời gian T"
  - Export kết quả: JSON, CSV, GraphML kèm thời gian

- **Trang Provenance Tree với thời gian:** `/daoanh/graph/provenance/time`
  - Tree view cho một entity cụ thể với lịch sử thay đổi theo thời gian
  - Hiển thị nguồn gốc, bản vá, xác suất xác minh, thời gian thay đổi

## Dữ liệu

- **Graph store:** Neo4j hoặc DILA-compatible graph (offline-first)
- **Entity types:** 167.006 entity_hub + 447.885 entity_claims + các thuộc tính thời gian
- **Relationship types:** thầy_trò, cùng_tự, địa_điểm,_thời_kỳ, nguồn, xác_suất
- **Audit logs:** en_audit_log + claims_audit kèm thời gian xác minh

## Acceptance criteria

- [ ] Load 1000+ entities kèm thời gian với response < 500ms
- [ ] Cypher queries kèm thời gian trả kết quả chính xác cho 90+ preset
- [ ] Provenance tree hiển thị đầy đủ lịch sử thay đổi kèm xác suất
- [ ] Export JSON/CSV kèm integrity dữ liệu và thời gian
- [ ] Filter theo thời gian và xác suất hoạt động đúng

## File tương tự

- `docs/integration/M51-advanced-knowledge-graph.md`
- `docs/Mimo-Flash/T126-m51-advanced-knowledge-graph.md`