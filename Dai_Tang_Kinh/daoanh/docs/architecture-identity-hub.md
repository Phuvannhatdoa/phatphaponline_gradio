# Kiến Trúc Identity Hub — Phật Tổ Đạo Ảnh

**Cập nhật:** 2026-08-20  
**Trạng thái:** T23 đang triển khai — populate `entity_claims`, thiết kế source adapters  
**Audit thực tế:** `lineage.db` → 80 tables, `entity_hub` 167,006 entities, `entity_claims` 0 rows  

---

## Trạng thái Hiện Tại (sau inspect DB)

### Đã có (reused, không đổi schema)

| Table | Rows | Tình trạng |
|-------|------|-----------|
| `entity_hub` | 167,006 | ✅ Đã có — Integer PK (100001-267006), source-neutral identity. **IS** Identity Hub core. |
| `entity_source_ids` | 167,009 | ✅ Đã có — Maps `entity_id → source + source_entity_id`. 100% `match_status = candidate`, 0% verified. **NEEDS** T25 admin review. |
| `data_sources` | 4 | ✅ Đã có — DILA/CBETA/MARCUS/ZQLOCAL đều đã register. BDRC skip theo quyết định admin. |
| `place_timeline_events` | 551 | ✅ Đã có — Timeline events (founding/dissolved, 122 wikidata). **T21/T22 complete.** |
| `geo_cross_ref` | 148 | ✅ Đã có — Place bridge DILA↔Wikidata (P571). **T21 complete.** BDRC IDs = NULL (verified default, không có fake DILA copy). |
| `cbeta_ref_passages` | exists | ✅ Đã có — CBETA text passage references. |

### Chưa có (sẽ tạo/migrate trong T23)

| Table | Lý do |
|-------|-------|
| `entity_claims` | Schema hoàn hảo (15 cols RDF), 0 rows — **Cần populate** từ places_dila, cbeta |
| `source_registry_metadata` | `data_sources` đủ 5 entry, nhưng thiếu priority/license/enabled fields cho adapter logic |
| `source_adapter_interfaces` | Chưa có Python adapter modules (chỉ DILA/MARCUS adapter có sẵn) |

---

## Vấn Đề Kiến Trúc

### 1. entity_hub ↔ entity_source_ids ✅ LINK VERIFIED

```python
# Thực tế:
# entity_hub.entity_id: INTEGER, min=100001, max=267006, count=167006
# entity_source_ids.entity_id: INTEGER, min=100001, max=BDRC_SOURCE
# 1 row orphaned (entity_id beyond hub range = BDRC_SOURCE marker)
# Tất cả match_status = candidate, verified = 0

# Kết luận: Hub link hoạt động được. 1 orphan row là BDRC_SOURCE marker (không liên quan đến entity thực).
```

### 2. entity table (TEXT PK) tách biệt

```python
# entity table: entity_id TEXT (A000001-X77n1524) — DILA-centric, dùng cho UI display
# entity_hub: entity_id INTEGER (100001-267006) — source-neutral identity core
# Không merge. Dùng entity_source_ids làm cầu cầu.
```

### 3. entity_claims = 0 rows ❌ Cần populate

Schema RDF sẵn có: `claim_id, entity_id, source_id, claim_type, subject, predicate, object_text, source_record_id, source_reference, authority_role, confidence, verification_status`

**3 claim type cấp cao đầu tiên (T23 Priority):**

| claim_type | Source | Ví dụ |
|-----------|--------|-------|
| `COORDINATE` | DILA | `(PL023255, DILA, 34.507018, 112.935331)` |
| `TEXTUAL_REF` | CBETA | `(PL023255, CBETA, 'T50n2060_p0457c16')` |
| `VIETNAMESE_SUMMARY` | ZQLOCAL | `(PL023255, ZQLOCAL, 'Thiếu Lâm Tự tại tỉnh Yên...)'` |

---

## Mục tiêu T23

### T23.1: Populate `entity_claims` từ places_dila (Phase 1-3)

```sql
-- Phase 1: COORDINATE claims
INSERT INTO entity_claims (entity_id, source_id, claim_type, subject, predicate, object_text, source_record_id, confidence, authority_role)
SELECT DISTINCT e.entity_id, d.source_id, 'COORDINATE', 'hasCoordinate', 'coordinates', 
    CAST(p.geo_lat AS TEXT) || ',' || CAST(p.geo_long AS TEXT), p.id, 1.0, 'PRIMARY'
FROM entity_hub e
JOIN entity_source_ids d ON e.entity_id = d.entity_id AND d.source = 'DILA'
JOIN places_dila p ON p.id = d.source_entity_id
WHERE p.geo_lat IS NOT NULL AND p.geo_long IS NOT NULL;

-- Phase 2: NAME claims (ZH + VI)
INSERT INTO entity_claims (entity_id, source_id, claim_type, subject, predicate, object_text, source_record_id, confidence, authority_role)
SELECT DISTINCT e.entity_id, d.source_id, 'NAME', 'canonicalNameZh', p.name_zh, p.name_zh, p.id, 0.95, 'PRIMARY'
FROM entity_hub e
JOIN entity_source_ids d ON e.entity_id = d.entity_id AND d.source = 'DILA'
JOIN places_dila p ON p.id = d.source_entity_id
WHERE p.name_zh IS NOT NULL AND p.name_zh != '';

-- Phase 3: ADMIN_UNIT claims
INSERT INTO entity_claims (entity_id, source_id, claim_type, subject, predicate, object_text, source_record_id, confidence, authority_role)
SELECT DISTINCT e.entity_id, d.source_id, 'ADMIN_UNIT', 'hasAdministrativeUnit', p.district, p.district, p.id, 0.8, 'PRIMARY'
FROM entity_hub e
JOIN entity_source_ids d ON e.entity_id = d.entity_id AND d.source = 'DILA'
JOIN places_dila p ON p.id = d.source_entity_id
WHERE p.district IS NOT NULL AND p.district != '';
```

### T23.2: Populate `entity_claims` từ cbeta_ref_passages (Phase 4)

```sql
-- INSERT INTO entity_claims ... from cbeta_catalog_vn linked via dila_reference
-- SELECT ... WHERE cbeta_ref_explanations.place_id = p.id
```

### T23.3: Source Adapter Interfaces

Tạo `adapters/` thư mục với các module độc lập:

```
adapters/
  __init__.py
  base.py           — Abstract adapter interface (resolve, get_entity, get_evidence, get_events, get_source_link)
  dila/adapter.py   — Wraps places_dila + entity_source_ids + entity_claims queries
  cbeta/adapter.py  — Wraps cbeta_catalog_vn + cbeta_ref_passages + cbeta_ref_explanations
  bdrc/adapter.py   — Đã tồn tại, cần wrap Entity/SameAs API
  local/adapter.py  — Wraps namevi_map_places + zqlocal_content (chưa có table)
```

Mỗi adapter implements:
- `resolve_entity(query: str) → List[EntityCandidate]`
- `get_entity(entity_id: str) → EntityData`
- `get_evidence(entity_id: str) → List[EvidenceRecord]`
- `get_events(entity_id: str) → List[TimelineEvent]`
- `get_source_link(source_id: str) → str`

### T23.4: Authority Ranking Logic

```python
def rankEvidence(evidence, purpose):
    """Return preferred_source, supporting_sources, confidence"""
    purpose_rank = {
        'MAP': ['DILA', 'Wikidata', 'CBETA'],
        'TEXT': ['CBETA', 'DILA', 'BDRC'],
        'BIO': ['BDRC', 'MARCUS', 'entity_claims'],
        'VIETNAMESE': ['ZQLOCAL', 'DILA'],
        'TIMELINE': ['place_timeline_events', 'Wikidata'],
    }
    preferred = purpose_rank.get(purpose, ['DILA'])
    # Return structured result
```

### T23.5: Integration Test (Thiếu Lâm Tự)

```python
# Test pipeline:
result = resolve_entity("Thiếu Lâm Tự")
# Kết quả phải trả:
# - ZENQ_PLACE_ID: PL023255
# - claims: [COORDINATE(DILA), TEXTUAL_REF(CBETA), VIETNAMESE_SUMMARY(ZQLOCAL)]
# - sources: {"dila": True, "cbeta": True, "zqlocal": True}
# - Không crash, không entity_merge_silent
```

---

## Roadmap Task (update)

| Task | Mô tả | Status | Priority |
|------|-------|--------|---------|
| **T23** | Populate `entity_claims` + Source Adapters + Authority Ranking | 🔨 Đang thực hiện | 🔴 High |
| **T24** | `zqlocal_content` table + ZQLOCAL source separation | ⏳ Chờ T23 kết quả | 🟠 Medium |
| **T25** | Admin review entity_source_ids → verified | ⏳ Chờ T23 kết quả | 🟠 Medium |
| **T26** | Unified API Response object `/api/resolve` | ⏳ Sau T23 | 🟡 Low |
| **T27** | DILA→INTEGER entity_id migration (dài hạn) | ⚪ Undone | ⚪ Long-term |

---

## Data Flow Ví Dụ: Thiếu Lâm Tự

```text
User search: "Thiếu Lâm Tự"
    ↓
resolve_entity("Thiếu Lâm Tự")
    ↓
1. Search places_dila.name_zh LIKE '%Thiếu Lâm Tự%'
2. Search namevi_map_places.name_vi LIKE '%Thiếu Lâm Tự%'  
3. Search entity_hub.canonical_label LIKE '%Thiếu Lâm Tự%'
    ↓
Candidates: [PL023255 (DILA), ...]
    ↓
Load entity_source_ids for each candidate
    ↓
Load entity_claims for each candidate
    ↓
Authority ranking
    ↓
Unified Response → Dashboard
```

---

## HOME Page as Identity Hub Entry Point

**HOME** is the public-facing entry point to the Identity Hub. It is a static/Flask-served page (`/daoanh/home`) that presents **15 TABs** organized into **3 clusters**, each TAB calling academic APIs on-demand.

### Architecture

```
HOME (index/Flask route)
    │
    ├── Cluster 1: Kinh Văn & Giáo Lý
    │   ├── TAB: Đại Tạng  → CBETA, SAT, 84000
    │   ├── TAB: Giáo Lý   → Giao lý passages
    │   ├── TAB: Thư Viện  → OCBS, GRETIL, DDBC
    │   ├── TAB: Nghi Lễ  → CBETA, THL rituals
    │   └── TAB: Giáo Dục  → DDBC, OCBS courses
    │
    ├── Cluster 2: Thực Thế & Niên Đại
    │   ├── TAB: Thực Thể  → DILA core data
    │   ├── TAB: Niên Đại  → Wikidata P571, timeline events
    │   ├── TAB: Sự Kiện  → CHGIS, BGIS, Marcus timeline
    │   ├── TAB: Bản Đồ    → CHGIS, BGIS, Marcus maps
    │   └── TAB: Dữ Liệu   → entity_claims (411K rows)
    │
    └── Cluster 3: Con Người & Không Gian
        ├── TAB: Nhân Vật  → BDRC, Treasury of Lives
        ├── TAB: Truyền Thừa  → BDRC lineage, Marcus SNA
        ├── TAB: Đồ Thị      → Marcus GIS, VisJS graph
        ├── TAB: Hình Ảnh    → IDP, Kanripo images
        └── TAB: Nghệ Thuật  → IDP, BGIS, Kanripo art
```

### Data Source Integration (15 Sources)

| Source | TABs Covered | Integration Method |
|--------|-------------|-------------------|
| **DILA** | Tất cả 15 TABs | `/api/places/<id>` core, `/api/places/<id>/claims` provenance |
| **BDRC** | Nhân Vật, Truyền Thừa | `/api/bdrc/person?id=`, P2477 SPARQL for IDs |
| **CBETA** | Đại Tạng, Giáo Lý, Nghi Lễ | `/api/places/<id>/cbeta` text passages |
| **Wikidata** | Niên Đại, Thực Thể | SPARQL P571 (inception), P2477 (BDRC IDs) |
| **CHGIS** | Bản Đồ, Sự Kiện, Niên Đại | New endpoint, 717 refs from raw_xml |
| **BGIS** | Bản Đồ, Hình Ảnh | New endpoint, map tiles & coords |
| **Marcus GIS** | Đồ Thị, Truyền Thừa | `/api/places/<id>/graph`, SNA networks |
| **THL** | Nghi Lễ, Nhân Vật | External API, biographies |
| **Treasury of Lives** | Nhân Vật | External API, 40K entries |
| **84000** | Đại Tạng, Giáo Lý | External API, translations |
| **SAT** | Giáo Lý | Via CBETA adapter |
| **VRI** | Giáo Lý | External API, vinaya rules |
| **Kanripo** | Hình Ảnh, Nghệ Thuật | External API, IDP scans |
| **OCBS** | Thư Viện, Giáo Dục | External API, research papers |
| **PTS** | Giáo Lý | External API, Pali canon |

### Tab → API Mapping Table

See `docs/HOME-identity-hub-spec.md` for the complete 15 TAB → API mapping.

### Coverage Matrix

**Definition**: `source × TAB` mapping table indicating availability status (available/partial/missing), endpoint, and coverage percentage.

**Location**: `docs/HOME-identity-hub-spec.md` (Data Sources table + Coverage Matrix table).

**Purpose**: Administrator visibility — know which sources power which TABs, identify gaps for future extension.

### Parallel API Display Pattern (per TAB)

Every TAB JSON response includes:

```json
{
  "dila_id": "PL000000023255",
  "bdrc_id": null,                    // null = verified default (no fake DILA copy)
  "wikidata_qid": "Q232771",          // from geo_cross_ref
  "founding_year": 495,                // Wikidata P571 from place_timeline_events
  "founding_source": "wikidata",
  "founding_source_ref": "Q232771·P571",
  "dila_founding_year": 495,           // fallback from DILA note regex "始建於495年"
  "dila_rawtext": "始建於495年...",    // raw DILA description
  "claims": [COORDINATE/NAME/ADMIN_UNIT ...]  // from entity_claims (411K rows)
}
```

### UI/UX Design

- **3-cluster accordion**: Collapsible groups, each cluster expands independently
- **Responsive**: Desktop → 3 columns; Mobile → bottom sheet, single cluster
- **Priority hiển thị**:
  - Với tăng ni: Giáo Lý, Truyền Thừa, Nghi Lễ nổi bật
  - Với học giả: Niên Đại, Thực Thể, Đồ Thị nổi bật
- **Bug fixes required before expansion**:
  1. `tamDich()` baseUrl ReferenceError (line 976 in places.html)
  2. Broken CSS braces in inline `<style>` block (lines 26–98)
  3. `_tabLoaded` set before fetch → no retry on failure
  4. Duplicated reset arrays in `selectItem` + `selectPerson`

## Data Flow Ví Dụ: Thiếu Lâm Tự (ở HOME)

```text
User clicks "Thiếu Lâm Tự" from search results
    ↓
HOME calls /api/places/PL000000023255/hub (aggregation endpoint)
    ↓
Parallel fetch from:
  - DILA: /api/places/PL000000023255 → core data + claims
  - Wikidata: SPARQL P571 → 495 CE founding
  - BDRC: /api/bdrc/person?id=PL000000023255 → person data (or null)
  - CHGIS: /api/places/PL000000023255/timeline → events
  - CBETA: /api/places/PL000000023255/cbeta → sutras
    ↓
Render 15 TABs in 3 clusters
│
Chip ✓ DILA (bdrc_id = NULL → ○ BDRC, not ✓)
│
Year block: "Năm thành lập: 495" (from Wikidata)
│
Rawtext: "始建於495年" (from DILA note)
│
Claims badges: [DILA] [Wikidata] [entity_claims]
```

## Rollback & Versioning

- **HOME page**: Flask route `@app.route('/daoanh/home')` serves `home.html`
  - Can revert to static `index.html` served by nginx if needed
- **places.html TAB expansion**: All bug fixes committed before new TABs
- **Architecture doc**: Each section independently revertible
- **Backup**: `lineage.db.bak_YYYYMMDD_HHMMSS` before any ETL

## Files Affected

| File | Change Type |
|------|-------------|
| `docs/architecture-identity-hub.md` | Add HOME section (+50 lines) |
| `docs/HOME-identity-hub-spec.md` | **NEW** (master spec, ~300 lines) |
| `tasks/T30-home-identity-hub.md` | **NEW** (task spec) |
| `tasks/T31-coverage-matrix.md` | **NEW** |
| `tasks/T32-places-tab-expansion.md` | **NEW** |
| `places.html` | Modify: 6→15 TABs, bug fixes |
| `home.html` | **NEW** (~500 lines) |
| `app.py` | Modify: add `/hub` route + `/daoanh/home` |
| `styles/daoanh-design.css` | Modify: scrollable tabs |

---

### Flag Domains

- `claim_type`: COORDINATE / NAME / ADMIN_UNIT / TEXTUAL_REF / TEMPORAL / EXTERNAL_ID
- `authority_role`: PRIMARY / SUPPORTING / SECONDARY / CONTRIBUTOR
- `verification_status`: UNVERIFIED / CANDIDATE / VERIFIED / ADMIN_VERIFIED
- `source`: DILA / BDRC / CBETA / MARCUS / ZQLOCAL

---

## Files Đang Được Cập Nhật

1. `docs/architecture-identity-hub.md` — Đang sửa (file này)
2. `tasks/T23-entity-claims-provenance-layer.md` — Cần edit để align với full architecture
3. `scripts/etl_entity_claims.py` — Chưa có, sẽ tạo mới
4. `adapters/` — Chưa có, sẽ tạo mới

### Backup Trước ETL

```bash
cp data/lineage.db data/lineage.db.bak_$(date +%Y%m%d_%H%M%S)
```