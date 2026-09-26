# T76 — B2 Real Data Environment Report

**Task:** T76 — B2 Real Data Acceptance Test
**Ngày:** 2026-08-31
**Chế độ:** REAL DATA ACCEPTANCE TEST (read-only, không mock, không database test thay thế)

---

## 1. Database đang sử dụng

| Hạng mục | Giá trị |
|---|---|
| DB thật | `data/lineage.db` (production, git-ignored) |
| Driver | SQLite3 |
| DILA canonical prefix | `PL0...` (entity_hub.canonical_label) |
| DILA canonical count | `entity_hub` = **167,006** rows |
| Evidence records | `entity_claims` = **447,885** |
| External source refs | `entity_source_ids` = **182,715** |
| Conflict pending | `conflict_pending` = **0** |

## 2. Canonical / evidence tables thực tế

| Bảng | Vai trò | Row |
|---|---|---|
| `entity_hub` | Canonical identity hub (PLACE/MONK/...), status active/verified | 167,006 |
| `entity_claims` | Multi-source evidence (claim_type, subject/predicate/object, provenance) | 447,885 |
| `entity_source_ids` | External source cross-reference IDs (DILA/CBETA/MARCUS/ZQLOCAL/BDRC) | 182,715 |
| `source_authority` | Authority ranking matrix (score/order/implemented) | 13 rows |
| `data_sources` | Source registry | 13 rows |
| `canonical_decision` | HITL confirmed mapping | 2 |
| `en_audit_log` | Audit trail | 2 |
| `conflict_pending` | Unresolved conflicts | 0 |
| `geo_cross_ref` | Cross-geo reference (DILA↔Wikidata/CHGIS/TGAZ/BGIS/Marcus/BDRC) | 181 |

## 3. Source connectors + ingestion thực tế

| Source | `implemented` | Evidence claims | source_ids | Trạng thái thực |
|---|---|---|---|---|
| **DILA** | 1 | 293,177 | 167,006 | ✅ INTEGRATED (canonical) |
| **CBETA** | 1 | 13,933 | 4,409 | ✅ INTEGRATED (text evidence) |
| **MARCUS** | 1 | 22,332 | 11,297 | ✅ INTEGRATED (historical geo/network) |
| **ZQLOCAL** | 1 | 118,295 | 2 | ⚠️ PARTIAL (claims lớn, source_ids rất ít) |
| **Wikidata** | 1 | 148 | 0 | ⚠️ PARTIAL (reference, không có source_id) |
| **BDRC** | 0 | 0 | 1 | 🔌 CONNECTOR_ONLY |
| **SAT** | 0 | 0 | 0 | 🔌 CONNECTOR_ONLY |
| **CHGIS** | 0 | 0 | 0 | 🔌 CONNECTOR_ONLY |
| **FoJin** | 0 | 0 | 0 | 🔌 CONNECTOR_ONLY |
| **Kanripo** | 0 | 0 | 0 | 🔌 CONNECTOR_ONLY |
| **SuttaCentral** | 0 | 0 | 0 | 🔌 CONNECTOR_ONLY |
| **84000** | 0 | 0 | 0 | 🔌 CONNECTOR_ONLY |
| **TGAZ** | 0 | 0 | 0 | 🔌 CONNECTOR_ONLY |

## 4. Kết luận môi trường

- Hệ thống có **dữ liệu thật dồi dào** cho canonical (DILA 167k), text evidence (CBETA 13.9k), historical geo (MARCUS 22.3k).
- **5 source thực sự đã ingest** (DILA, CBETA, MARCUS, ZQLOCAL, Wikidata).
- **8 source chỉ có connector** (implemented=0, chưa retrieve data): SAT, CHGIS, BDRC, FoJin, Kanripo, SuttaCentral, 84000, TGAZ.
- **Conflict thật hiện = 0** trong `conflict_pending`/`conflicts` — chưa có case conflict đã ingest.
- Matching thin: `geo_cross_ref=181`, `name_vi_map_places=0`.
