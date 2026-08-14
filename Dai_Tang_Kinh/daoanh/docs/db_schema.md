# Database Schema — `lineage.db`

**File:** `data/lineage.db`
**Last updated:** 2026-07-29 (thêm vn_person_authority + bảng phụ trợ)

## 3-Layer Model

| Layer | Tables | Access Rule |
|-------|--------|-------------|
| **RAW** | `places_dila`, `people_full`, `marcus_reference`, `marcus_networks`, `dila_reference` | Read-only, never modified by app |
| **STAGING / MAPPING** | `places_pending`, `namevi_map_places`, `ttl_mapping`, `ttl_works`, `ttl_canon_works` | Written by ETL + admin UI |
| **FINAL / PUBLIC** | `places`, `places_vps`, `canon_catalog`, `dataset_sources`, `networks`, `lexicon`, `places_search_fts*`, `lineage_conflicts_v2`, `person_refs`, `time_periods` | Consumed by UI, exported |

---

## Core Tables

### `places_dila` (RAW)

DILA Place Authority data, imported from DILA XML/TEI.

| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT PRIMARY KEY | DILA ID, format `PL` + 12 digits |
| `name_zh` | TEXT | Chinese name |
| `district` | TEXT | Administrative district (e.g. 中國-雲南省-曲靖市-富源縣) |
| `note_category` | TEXT | DILA category note |
| `listbibl` | TEXT | Bibliography references |
| `geo_lat` | REAL | Latitude |
| `geo_long` | REAL | Longitude |
| `name_en` | TEXT | English name |
| `name_san` | TEXT | Sanskrit name |
| `name_jpn` | TEXT | Japanese name |
| `name_peo` | TEXT | Persian / other name |
| `name_other` | TEXT | Other language names |
| `raw_xml` | TEXT | Full TEI/XML source |

### `places_pending` (STAGING)

Queue for admin review — places awaiting Vietnamese name mapping.

| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT PRIMARY KEY | DILA ID |
| `name_zh` | TEXT | Chinese name |
| `name_vi` | TEXT | Auto-generated Vietnamese name |
| `address` | TEXT | Pending address |
| `country` | TEXT | Country |
| `gps_lat` | REAL | Latitude |
| `gps_long` | REAL | Longitude |
| `province` | TEXT | Province |
| `place_type` | TEXT | Place type |
| `raw_xml` | TEXT | Raw XML (added in V3 migration) |
| `district_raw` | TEXT | Raw district (added in V3) |
| `hist_country_raw` | TEXT | Historical country (added in V3) |

### `namevi_map_places` (STAGING)

Mapping between DILA places and Vietnamese names. This is the **primary save target** for the admin dashboard.

| Column | Type | Description |
|--------|------|-------------|
| `dila_id` | TEXT | DILA ID (FK to places_dila.id) |
| `name_vi` | TEXT | Vietnamese name (verdict) |
| `name_zh` | TEXT | Chinese name (denormalized) |
| `source` | TEXT | Source identifier (e.g. 'admin', 'gemini') |
| `source_id` | INTEGER | FK to dataset_sources.id |
| `needs_review` | INTEGER | 0 = approved, 1 = needs review |
| `note_vi` | TEXT | Editor's Vietnamese note |
| `district_vi` | TEXT | Vietnamese district translation |
| `country_vi` | TEXT | Vietnamese country name |
| `vn_name_status` | TEXT | Status flag |
| `gps_lat` | REAL | Manual GPS latitude |
| `gps_long` | REAL | Manual GPS longitude |

### `lexicon` (FINAL)

StarDict dictionary entries — 166,278 entries from 22 dictionaries.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-increment |
| `term` | TEXT | Dictionary headword |
| `definition` | TEXT | Dictionary definition |
| `source` | TEXT | Dictionary source name |
| `entity_type` | TEXT | Entity classification (e.g. 'ĐỊA DANH') |
| `priority` | INTEGER | Display priority |
| `key_norm` | TEXT | Lowercase, diacritics-free headword for matching |

Indexes:
- `idx_lexicon_key_norm` on `key_norm`
- `idx_lexicon_entity_type` on `entity_type`

### `missing_hanzi` (META)

Tracking Hán tự that could not be automatically transliterated (logged by `_log_missing_hanzi`). Admin uses this table to expand `CUSTOM_HANVIET`.

| Column | Type | Description |
|--------|------|-------------|
| `char` | TEXT PRIMARY KEY | CJK character that was skipped |
| `count` | INTEGER | Number of times this char was encountered (auto‑incremented) |
| `last_seen_at` | DATETIME | Last occurrence timestamp |

### `dataset_sources` (FINAL)

License and provenance tracking for all imported data.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-increment |
| `name` | TEXT | Source name |
| `origin_url` | TEXT | Original URL |
| `license` | TEXT | License type (CC0, CC-BY, etc.) |
| `usage_level` | TEXT | GREEN/YELLOW/RED |

### `people` / `people_full` (RAW + FINAL)

Person authority data (for genealogy/lineage).

| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT PRIMARY KEY | DILA Person ID (A + 6 digits) |
| `name_zh` | TEXT | Chinese name |
| `name_vi` | TEXT | Vietnamese name |
| `birth` | TEXT | Birth year |
| `death` | TEXT | Death year |
| `teacher_id` | TEXT | Teacher's person ID |
| `biography` | TEXT | Biography text |

### `person_refs` (FINAL)

References for persons (sources, citations).

| Column | Type | Description |
|--------|------|-------------|
| `person_id` | TEXT | FK to people.id |
| `source_name` | TEXT | Source name |
| `ref_type` | TEXT | Reference type |
| `value` | TEXT | Reference value |
| `note` | TEXT | Note |

### `marcus_reference` (RAW)

Marcus FoJin reference data.

| Column | Type | Description |
|--------|------|-------------|
| `node_id` | TEXT | Node ID |
| `label` | TEXT | Chinese label |
| `label_vi` | TEXT | Vietnamese label |

---

### `place_cbdb_map` (STAGING / MAPPING)

Mapping between Đạo Ảnh place IDs and CBDB address IDs. CBDB data is stored in **separate** `data/cbdb/cbdb_20260516.sqlite3` (read-only, 21 tables, 30K+ places, 130K+ persons).

| Column | Type | Description |
|--------|------|-------------|
| `place_id` | TEXT | Đạo Ảnh place ID (PL + 12 digits) |
| `cbdb_addr_id` | INTEGER | CBDB address ID (ADDR_CODES.c_addr_id) |
| `note` | TEXT | Optional note about the mapping |

Indexes:
- `idx_place_cbdb_map_cbdb` on `cbdb_addr_id`

---

## Legacy / Auxiliary Tables

| Table | Status | Notes |
|-------|--------|-------|
| `name_vi_map_places` | ⚠️ Legacy | Duplicate of `namevi_map_places`, needs consolidation |
| `people_new` | ⚠️ Legacy | Should be renamed to `people_staging` |
| `places_new` | ⚠️ Legacy | Should be renamed to `places_staging` |
| `places_search_fts*` | ✅ Active | FTS for place search |
| `lineage_conflicts_v2` | ✅ Active | Lineage conflict resolution |
| `time_periods` | ✅ Active | Historical time periods |
| `networks` | ✅ Active | Network/relationship data |
| `canon_catalog` | ✅ Active | Canon catalog |
| `ttl_mapping` | ✅ Active | TTL ontology mapping |
| `ttl_works` / `ttl_canon_works` | ✅ Active | TTL works |
| `place_wiki_snapshots` | ✅ Active (2026-05-22) | Wikipedia snapshot cache: `place_id PK, wiki_title, wiki_url, snippet, full_text, source, license, created_at, updated_at` |
| `entity` | ✅ Active (2026-05-23) | Integration layer: unified entity index (PERSON/PLACE/TEXT): `entity_id PK, entity_type, dila_id, alias_vi, alias_zh, cbeta_occ, marcus_id, extra_alias` |
| `passage` | ✅ Active (2026-05-23) | Integration layer: CBETA passages: `passage_id PK, source, text_id, loc_ref, raw_text, norm_text` |
| `passage_entity` | ✅ Active (2026-05-23) | Integration layer: passage-entity links: `(passage_id PK, entity_id PK)` |
| `keyword_map` | ✅ Active (2026-05-24) | Keyword import: `id PK, keyword TEXT, value TEXT, category TEXT DEFAULT 'import_ui', source TEXT DEFAULT 'manual', created_at TEXT` |
| `cbeta_ref_explanations` | ✅ Active (2026-05-28) | CBETA place explanation cache: `ref TEXT, place_id TEXT, place_han TEXT, han_sentence TEXT, explanation_vi TEXT, created_at TEXT, updated_at TEXT, PRIMARY KEY (ref, place_id)` |
| `cbeta_catalog_vn` | ✅ Active (2026-05-29) | CBETA catalog VN (Nguyễn Minh Tiến): 3122 records with license tracking |
| `catalog_mapping` | ✅ Active (2026-05-30) | Place ↔ catalog mapping with approval: `id PK, place_id TEXT, catalog_id TEXT, source TEXT, status TEXT (pending/approved/rejected), created_at, updated_at, created_by, reviewed_by, note` — index on `(place_id, status)` |
| `monk_dict` | ✅ Active (2026-05-30) | Monk authority: `id PK, dila_id UNIQUE, han_name, vn_name, pinyin, alt_han_names JSON, vn_aliases JSON, era, dynasty, role_main, role_alt, biography, refs JSON, source, status (pending/approved/rejected), created_at, updated_at` — index on `(status)`, `(dila_id)` |
| `monk_name_index` | ✅ Active (2026-05-30) | Monk name search index: `id PK, monk_id FK, lang (zh/vi/pinyin/san/other), name_form, name_type (official/alias), normalized, created_at` — index on `(monk_id)`, `(normalized)` |
| `vn_person_authority` | ✅ Active (2026-07-29) | **Authority nhân vật Việt Nam** (từ TTL thiền sư): `id PK (slug), ttl_filename, name_vi, name_zh, dharma_title, dharma_lineage, generation_order, is_lineage_founder, gender, biographical_note_vi, birth_year, death_year, appellations JSON, dila_id, status (pending), created_at` — nguồn: `data/ttl/old/*.ttl` |
| `vn_person_relations` | ✅ Active (2026-07-29) | Quan hệ nhân vật: `id PK, person_id FK, relation_type (hasTeacher/hasDisciple/hasRelatedFigure), target_id, target_label_vi, ttl_filename` — UNIQUE `(person_id, relation_type, target_id)`, index `(person_id)` |
| `vn_person_places` | ✅ Active (2026-07-29) | Địa danh liên quan nhân vật: `id PK, person_id FK, place_id, place_label_vi, place_type (Monastery/SacredSite), ttl_filename` — UNIQUE `(person_id, place_id)`, index `(person_id)` |
| `vn_person_works` | ✅ Active (2026-07-29) | Tác phẩm nhân vật: `id PK, person_id FK, work_id, work_title_vi, ttl_filename` — UNIQUE `(person_id, work_id)`, index `(person_id)` |
| `vn_person_events` | ✅ Active (2026-07-29) | Sự kiện nhân vật: `id PK, person_id FK, event_type (Birth/Death/KeyLifeEvent/Contribution/PhilosophicalStance), event_id, event_label_vi, event_year, ttl_filename` — UNIQUE `(person_id, event_type, event_id)`, index `(person_id)` |
