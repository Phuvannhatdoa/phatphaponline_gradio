# KG_CONSOLIDATED · Knowledge Graph Phật Giáo (CONSOLIDATED — Evidence-Based)

**Spec · P2** (Consolidated from archived M12, M51, M97 per T277 Phase A)

## Mục đích (Consolidated — Evidence-Based)

Hệ thống **trực quan hóa và tra cứu Knowledge Graph Phật Giáo hiện có** — không xây dựng graph mới, không AI, không probabilistic, không "PhD level", không "living/sống".

Chỉ thực hiện: (1) hiển thị graph Nexus có sẵn (places.html), (2) tra cứu entity/relationship từ DB thật, (3) xuất báo cáo dựa trên dữ liệu thật.

## Thực tế hiện có (2026-10-11)

| Thành phần | Trạng thái | File thực tế |
|---|---|---|
| Nexus Graph | **Đã có** | `places.html` (tab Nexus), `t16_nexus_etl.py` |
| Entity Resolution | **Đã có** | `entity_claims` (447k), `entity_hub` (167k), `lineage_edge_assertions` (46k) |
| Provenance | **Đã có** | `en_audit_log`, `entity_claims_audit`, `claims_audit` |
| Authority Ranking | **Đã có** | `canonical_decision`, `authority_rank`, `verification_status` |
| Graph API | **Đã có** | `/api/entity/*`, `/api/nexus/*`, `/daoanh/api/public/graph/*` |

**Không có:** Probabilistic edges, AI reasoning, "PhD level queries", "living graph auto-update", "temporal dynamic", probabilistic verification.

## Chỉ giữ: Trực quan hóa & Tra cứu Graph hiện có

| Trang | Mô tả | Dữ liệu nguồn |
|---|---|---|
| `/daoanh/places.html` (tab Nexus) | Graph trực quan entity/relationship | `entity_claims`, `entity_hub`, `lineage_edge_assertions` |
| `/daoanh/api/entity/<id>` | Tra cứu entity + relationships | `entity_hub`, `entity_claims` |
| `/daoanh/api/nexus/*` | Graph traversal | `entity_claims`, `lineage_edge_assertions` |
| `/daoanh/api/public/export/graph` | Xuất graph (GraphML/JSON) | `entity_claims`, `lineage_edge_assertions` |

**Không có:** Probabilistic query builder, "temporal dynamic", "probabilistic verification", "PhD level", "living graph", auto-update.

## Thống kê thực tế (2026-10-11)

| Chỉ số | Giá trị | Nguồn |
|---|---|---|
| Entity claims | 447,885 | `entity_claims` |
| Entity hub | 167,006 | `entity_hub` |
| Lineage edges | 46,004 | `lineage_edge_assertions` |
| Glossary terms | 248,095 | `glossary_term` (Vi 75.54%) |
| Events | 3,530 | `events` (chưa provenance) |
| TTL files | ~1,075 | `data/ttl/` |

## Chỉ giữ: Truy xuất & Xuất báo cáo dựa trên dữ liệu thật

1. **Tra cứu entity:** `/daoanh/api/entity/<id>` → trả về entity + claims + relationships
2. **Graph traversal:** `/daoanh/api/nexus/*` → BFS/DFS trên `lineage_edge_assertions`
3. **Xuất báo cáo:** `/daoanh/api/public/export/graph?format=graphml|json` → GraphML/JSON cho nghiên cứu
4. **Provenance:** `/daoanh/api/research/entity/<id>/audit-trail` → lịch sử thay đổi

**Không có:** Probabilistic query, auto-reasoning, AI inference, "living" auto-update, speculative features.

## Acceptance Criteria (Evidence-Based)

- [x] Graph Nexus hiển thị entity/relationship từ DB thật
- [x] API entity trả về claims + relationships + provenance
- [x] Xuất GraphML/JSON cho nghiên cứu
- [x] Audit trail cho entity
- [ ] Không có probabilistic/ai/speculative features

## Loại bỏ (Archived Speculative Claims)

| Claim gốc (M12/M51/M97) | Lý do loại bỏ |
|---|---|
| Probabilistic edges/verification | Không có probability model, không có training data |
| "PhD level queries" | Không có user segment "PhD", không có advanced query builder |
| "Living graph auto-update" | Không có auto-update mechanism, chỉ batch ETL |
| "Probabilistic verification" | Không có probability model |
| "Temporal dynamic" | Không có temporal model |
| "AI reasoning" | Không có AI model |
| "Auto-update living graph" | Không có auto-update mechanism |
| "Temporal dynamic probabilistic" | Không có temporal/probabilistic model |

## Thực thể code hiện có (2026-10-11)

| File | Mô tả |
|---|---|
| `places.html` (tab Nexus) | Graph visualization (VisJS/D3) |
| `t16_nexus_etl.py` | Nexus ETL pipeline |
| `app.py` routes | `/api/entity/*`, `/api/nexus/*`, `/api/public/export/*` |
| `entity_claims` | 447k claims (DILA/CBETA/Marcus/ZQLOCAL/Wikidata) |
| `entity_hub` | 167k entities với authority ranking |
| `lineage_edge_assertions` | 46k edges verified |

## File liên quan

- Task gốc: `docs/integration/_archive/M-series/M12-knowledge-graph-expansion.md`, `M51-advanced-knowledge-graph.md`, `M97-living-dharma-knowledge-graphs.md` (archived)
- Task T277: `tasks/T277-archive-and-future-integration.md` (Phase A)
- Code: `places.html`, `t16_nexus_etl.py`, `app.py` Nexus routes