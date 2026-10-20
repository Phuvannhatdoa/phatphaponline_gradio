# M12 · Mở rộng Knowledge Graph cho Tiến sĩ

**Spec · P2**

# M11 Mở rộng Knowledge Graph

Phát triển và mở rộng Knowledge Graph cho dữ liệu Phật giáo: entity relationships, provenance tracking, advanced query capabilities cho trình độ Tiến sĩ.

## Mục đích

Mở rộng khả năng truy xuất phức tạp qua Knowledge Graph: liên kết đa cấp, xác minh nguồn, truy xuất lịch sử thay đổi cho người dùng trình độ Tiến sĩ.

## UI/UX

- **Trang Explore Graph:** `/daoanh/graph/explore`
  - Đồ thị tương tác: node (người, kinh, chùa) và edge (thầy trò, nguồn, địa lý)
  - Zoom, pan, filter theo loại, nguồn, thời kỳ
  - Hover card: hiển thị metadata (ID, tên, lý do, nguồn, trạng thái)

- **Trang Advance Query:** `/daoanh/graph/advanced`
  - Cypher-like query builder cho Knowledge Graph
  - Presets: "Tất cả thầy trò của X", "Tìm nguồn chung", "Lịch sử thay đổi"
  - Export kết quả: JSON, CSV, GraphML

- **Trang Provenance Tree:** `/daoanh/graph/provenance`
  - Tree view cho một entity cụ thể
  - Hiển thị nguồn gốc, bản vá, audit log
  - Compare versions: trước/sau thay đổi

## Dữ liệu

- **Graph store:** Neo4j hoặc DILA-compatible graph (offline-first)
- **Entity types:** 167.006 entity_hub + 447.885 entity_claims
- **Relationship types:** thầy_trò, cùng_tự, địa_điểm,_thời_kỳ,_NXB
- **Audit logs:** en_audit_log + claims_audit (SHA-256 evidence)

## Acceptance criteria

- [ ] Load 1000+ entities với response < 500ms
- [ ] Cypher queries trả kết quả chính xác cho 90+ preset
- [ ] Provenance tree hiển thị đầy đủ lịch sử thay đổi
- [ ] Export JSON/CSV giữ được integrity dữ liệu
- [ ] Filter theo nguồn (DILA, CBETA, Wikidata) hoạt động đúng

## File tương tự

- `docs/integration/M12-knowledge-graph-expansion.md`
- `docs/Mimo-Flash/T87-m12-knowledge-graph-expansion.md`