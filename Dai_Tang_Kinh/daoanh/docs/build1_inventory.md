# Build 1 Inventory — Đạo Ảnh (daoanh)

**Cập nhật:** 2026-08-30
**Phạm vi:** app daoanh (`Dai_Tang_Kinh/daoanh`) — server `app.py` + `admin/placevn.html`
**Mục đích:** Ghi rõ những gì BUILD 1 ĐÃ CÓ (đã verify) để Build 2+ KHÔNG xây trùng. Theo directive BUILD 2 §3.

> Rule: Chỉ ghi những gì đã verify trong repo. Không bịa entry.

## Bảng Inventory

| Capability | Existing file/API/table | Status | Build |
|---|---|---|---|
| DILA ID | `entity.dila_id` + `entity_hub.canonical_label` ('PL…' raw/padded); `places_pending.id`; `ensure_long_id()` (app.py:125) | IMPLEMENTED | B1 |
| SQLite mapping | `namevi_map_places` (118,296); `places_pending` (176,783); ké dụng `places_dila` | IMPLEMENTED | B1 |
| Đạo Ảnh dashboard | `admin/placevn.html` (React 18, createRoot); routes `/daoanh/api/admin/*` (61) | IMPLEMENTED | B1 |
| GIS | Leaflet (trong `admin/placevn.html`, map container + marker) | IMPLEMENTED | B1 |
| Admin save | `POST /daoanh/api/admin/namevi-map-places/save` → `save_mapping()` (app.py ≈7307) | IMPLEMENTED | B1 |
| Auto transliterate | `POST /daoanh/api/admin/auto_save_name` → `auto_save_name()` (app.py ≈7336) | IMPLEMENTED | B1 |
| Search | `/daoanh/api/admin/places_search`, `places_auto_names`, `ai_judge` (app.py:2063); SQLite **FTS5** `places_search_fts`/`places_pending_fts` | IMPLEMENTED | B1 |
| Canonical Entity (Identity Hub) | `entity_hub` (167,006: entity_id INT surrogate, entity_type, canonical_label, status, created_at, updated_at) + `entity` (entity_id TEXT, dila_id, aliases) | **ALREADY IMPLEMENTED (T23)** | B1 |
| Source Identity Mapping | `entity_source_ids` (167,009: entity_id→source/source_entity_id/match_status/confidence/verified) + `entity_claims` (447,885 sau T69: claim_type/source_id/authority_role/confidence/verification_status; + `source_url`/`retrieved_at` provenance Phase B) | **ALREADY IMPLEMENTED (T23) + B2-B** | B1 |
| Evidence-canonical decision | `canonical_decision` + `en_audit_log` — T67 (commit a5bb07f) | IMPLEMENTED (provenance) | B1 |
| Place Person Bibl | `place_person_bibl` (13,933) — nguồn CBETA ref + source_book | IMPLEMENTED | B1 |
| CBETA mentions | `cbeta_place_mentions` (16,311) / `cbeta_person_mentions` (72,628) / `event_text_link` (17,284) | IMPLEMENTED | B1 |
| Marcus | `marcus_networks` (11,169) / `marcus_reference` (18,127) | IMPLEMENTED (data sẵn) | B1 |
| Wikidata cross-ref | `geo_cross_ref` (181; wikidata_qid 148 verified) | IMPLEMENTED | B1 |
| Authority matrix | `source_authority` (13 nguồn: DILA=100>CBETA=80>SAT=75>Kanripo=70>Marcus=60>CHGIS=58>TGAZ=55>ZQLOCAL=50>SuttaCentral=50>84000=BDRC=FoJin=40>Wikidata=25) | **DONE** — T68 + Build2-PhaseD | B2 |
| Conflict detection | `conflict_pending` + `_detect_conflicts()` + GET /conflicts | **DONE** — T68 | B2 |
| Evidence wire đa-nguồn vào claims | `entity_claims` 447,885 (CBETA TEXT + Marcus NETWORK + Wikidata EXTERNAL_ID); `source_url`+`retrieved_at` provenance (Build2-PhaseB); GET /places/<id>/claims endpoint + UI panel (PhaseC) | **DONE** — T69 + B2-B/C | B2 |
| Governance scope CHGIS/BDRC/FoJin/SAT | `source_authority` khai báo minh bạch `implemented=0` cho nguồn chưa tích hợp; build2-wikidata registered; place_wiki_snapshots test rows xóa | **DONE** — T70 + B2-A/D | B2 |
| OpenSearch | **KHÔNG có trong app daoanh** (0 refs trong app.py/scripts) | NOT IN DAOANH (external) | — |
| GraphDB / Fuseki | **KHÔNG có trong app daoanh** (0 refs) — thuộc parent visjs-app (thientong.py:7200) | NOT IN DAOANH (external) | — |

## Kết luận Build 1 → Build 2

Tầng **Canonical Entity + Source Identity Mapping đã IMPLEMENTED** (Identity Hub T23; provenance T67).
Build 2 KHÔNG xây lại identity.
Gap thật của Build 2 = **T68 (authority + conflict)** → **T69 (wire evidence đa-nguồn)** → **T70 (governance)**.

**Build 2 trạng thái (2026-08-30/31):** T68/T69/T70 **DONE**. Ngoài ra:
- **Phase A** — fix `entity_unified` CBETA source_id động + Wikidata vào `data_sources` (id 6) + evidence indexes + backup `lineage_backup_t69_a2.db`.
- **Phase B** — provenance: `source_url` (148 Wikidata URLs) + `retrieved_at` (36,413 claims) trên `entity_claims`.
- **Phase C** — evidence API `GET /daoanh/api/places/<id>/claims` + UI panel "Evidence đa-nguồn (authority)" trong `admin/placevn.html`.
- **Phase D** — cross-ref sources vào matrix (`implemented=0`): SAT, CHGIS, FoJin, Kanripo, SuttaCentral, 84000, TGAZ; script reversible `scripts/build2_register_crossref_sources.py`.
