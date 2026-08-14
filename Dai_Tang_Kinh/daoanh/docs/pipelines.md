# Pipelines — ETL & Data Flow

**Last updated:** 2026-05-30 (thêm monk ETL)

---

## 1. DILA Import → `places_dila`

**Source:** DILA Authority Databases (authority.dila.edu.tw)
**Format:** XML/TEI P5
**Target table:** `places_dila` (RAW)

### Flow

1. Download TEI XML files from DILA (Place Authority, ~19,000 places)
2. Parse XML → extract fields: `name_zh`, `district`, `geo_lat/long`, `name_en/san/jpn/peo`, `raw_xml`
3. Insert/update into `places_dila`
4. Academia Sinica supplement: +40,000 places with GPS

### Key Columns from TEI

```xml
<ns0:placeName xml:lang="zho-Hant">勝境關</ns0:placeName>
<ns0:placeName type="alternative" xml:lang="zho-Hant">界關</ns0:placeName>
<ns0:location>
  <ns0:place key="PLD002572">富源縣</ns0:place>
  <ns0:geo cert="high">104.313295 25.64813</ns0:geo>
</ns0:location>
<ns0:district>中國-雲南省-曲靖市-富源縣</ns0:district>
<ns0:note>...</ns0:note>
<ns0:note type="category">地點</ns0:note>
```

### TEI Parsing Functions (app.py)

| Function | Purpose |
|----------|---------|
| `parse_han_variants(raw_xml)` | Extract zho-Hant `<placeName>` tags → `han_variants` |
| `parse_name_variants(raw_xml)` | Extract ALL `<placeName>` tags, any language → `name_variants` |
| `extractHanContextFromTei(rawTei)` | (frontend) Extract `<note>` + `<bibl>` for historical context |
| `formatTeiAsPlainText()` → replaced by `parseTeiFields()` | (frontend) Parse TEI into labeled fields |

---

## 2. Places Pending Queue → `places_pending`

**Source:** Combined DILA + Marcus + other place lists
**Target table:** `places_pending` (STAGING)
**Size:** ~175,000 records

### Flow

1. Aggregate place IDs from DILA, Marcus, and other sources
2. Deduplicate by DILA ID (`PL` + 12 digits)
3. Insert into `places_pending` with `name_zh`, empty `name_vi`
4. Admin UI (`placevn.html`) reads from `places_pending` via paginated API

---

## 3. Lexicon Build (StarDict 22 Dictionaries)

**Source:** 22 StarDict dictionary files
**Target table:** `lexicon` (FINAL)
**Size:** 166,278 entries, 15,863 `entity_type='ĐỊA DANH'`

### Flow

1. Parse all 22 dictionary `.idx` + `.dict` files
2. Extract `term`, `definition`, `source` fields
3. Classify `entity_type` (ĐỊA DANH = place names)
4. Compute `key_norm` = lowercase + diacritics-free
5. Insert into `lexicon` with priority ordering

### Key Index

```sql
CREATE INDEX idx_lexicon_key_norm ON lexicon(key_norm);
-- 166,278 rows updated with LOWER(TRIM(key_norm))
```

---

## 4. Name-Vi Mapping Save Flow

**Source:** Admin dashboard (`placevn.html`)
**Target table:** `namevi_map_places` (STAGING)

### Flow

1. Admin opens a place in the dashboard
2. `POST /daoanh/api/admin/ai_judge/{id}` → returns full details (DILA + existing mapping)
3. Admin enters/edits `name_vi`, `note_vi`
4. `POST /daoanh/api/admin/namevi-map-places/save` → upserts into `namevi_map_places`
5. Place removed from pending queue

### Lexicon Suggestion Pipeline

```
suggest_api = han_name (Chinese)
  → normalize_text()
  → key_norm lookup in lexicon
  → filter self-match (text == han_name)
  → definition LIKE fallback if empty
  → API fallback if still empty
```

---

## 5. Census / GeoNames → VN GPS

**Source:** GeoNames.org (Vietnam places)
**Target table:** `places_dila` (GPS update)

### Flow

1. Query GeoNames for Vietnamese place GPS coordinates
2. Match by place name (Chinese → Vietnamese)
3. Update `gps_lat`/`gps_long` in `places_dila`
4. Fallback: manual GPS from admin dashboard

---

## 6. CBETA / TTL → Genealogy / Ontology

**Source:** CBETA XML, TTL (Turtle) files
**Target:** `ttl_mapping`, `ttl_works`, `ttl_canon_works`, `people`

### Flow

1. Parse CBETA TEI → extract person-place relationships
2. Build lineage tree (teacher → student)
3. Export to TTL ontology (namespace `pth:`)
4. Store in GraphDB (localhost:7200) for SPARQL queries

---

## 7. Translation Pipeline

### AI Translation (Gemini + GoogleTranslator)

1. `POST /daoanh/api/admin/translate_context`
2. Source: `extractHanContextFromTei()` (Chinese notes from TEI)
3. Primary: Gemini 2.0 Flash (`AIzaSyB8qS0elX9NZ7IIFpmeZSkKfvAV6WiukiE`)
4. Fallback: GoogleTranslator (free tier)
5. Result stored as `hanContextVi` in frontend state

---

## 8. Monk Personography — `monk_dict` → `monk_name_index`

**Source:** `monk_dict` (DILA Person authority via `persons.json`)
**Target table:** `monk_name_index` (STAGING / SEARCH INDEX)
**Script:** `scripts/sync_monk_names.py`

### Flow

1. Read all `monk_dict WHERE status = 'approved'`
2. For each monk, extract all name forms:
   - `han_name` → lang=`zh`, type=`official`
   - `vn_name` → lang=`vi`, type=`official`
   - `pinyin` → lang=`pinyin`, type=`official`
   - `alt_han_names[]` (JSON) → lang=`zh`, type=`alias`
   - `vn_aliases[]` (JSON) → lang=`vi`, type=`alias`
3. Normalize each name: NFD → remove combining marks → đ→d → lowercase → trim
4. Insert/ignore into `monk_name_index`
5. Old index entries for the same monk are deleted before re-index

### Key API

| Endpoint | Description |
|----------|-------------|
| `GET /daoanh/api/monk/<dila_id>` | Full monk profile |
| `GET /daoanh/api/monk/<dila_id>?view=tooltip` | Tooltip (6 fields) |
| `GET /daoanh/api/monk/search?q=<query>&limit=20` | Prefix search on `normalized` |

### Run

```bash
python3 scripts/sync_monk_names.py
```

### Transliteration (Chinese → Han-Viet)

1. `GET /daoanh/api/public/transliterate?text=...`
2. Rule-based: adminMapping dictionary (e.g. 中國→Trung Quốc)
3. Overrides for common patterns

---

## 9. TTL Person Authority — `vn_person_authority`

**Source:** 16 file TTL thiền sư trong `data/ttl/old/*.ttl`
**Target tables:** `vn_person_authority`, `vn_person_relations`, `vn_person_places`, `vn_person_works`, `vn_person_events`
**Script:** `scripts/etl_ttl_person_authority.py` (dùng rdflib 7.1.4)

### Flow

1. Parse từng file TTL bằng `rdflib.Graph.parse(format='turtle')`
2. Xác định node chính: subject có `rdf:type bkg:Monk` (fallback: node có `bkg:hasTeacher` / `bkg:isLineageFounder`)
3. Trích xuất thông tin nhân vật:
   - **Tên**: `rdfs:label @vi` → `name_vi`; appellation `@zh` → `name_zh`; `bkg:hasAppellationType = bkg:DharmaTitle` → `dharma_title`; toàn bộ appellation lưu JSON vào cột `appellations`
   - **Dòng phái**: `bkg:dharmaLineageName`, `bkg:generationOrder`, `bkg:isLineageFounder`
   - **Năm sinh/tử**: định dạng giàu dùng `crm:E67_Birth`/`crm:E69_Death` + `crm:P4_has_time-span`; định dạng dòng phái dùng `bkg:BirthEvent`/`bkg:DeathEvent` + `bkg:year`; fallback từ khoảng năm trong `biographical_note_vi` (regex `YYYY-YYYY`)
   - **dila_id**: nối từ `ttl_mapping` (5 file đã verified)
4. Trích xuất bảng phụ trợ:
   - `vn_person_relations`: `bkg:hasTeacher`, `bkg:hasDisciple`, `bkg:hasRelatedFigure`
   - `vn_person_places`: `bkg:associatedPlaces` + `bkg:placeType` (rút gọn bỏ tiền tố `bkg:`)
   - `vn_person_works`: `bkg:authoredWorks`
   - `vn_person_events`: `bkg:birthEvent`/`bkg:deathEvent` (Birth/Death), `bkg:hasKeyLifeEvent`, `bkg:hasContribution`, `bkg:hasPhilosophicalStance`
5. Chạy lại idempotent: `DELETE` toàn bộ 5 bảng trước khi ghi

### Run

```bash
python3 scripts/etl_ttl_person_authority.py
```

### Lưu ý kỹ thuật

- `rdflib.Namespace` KHÔNG tự chuyển `_` thành `-`, nên predicate `crm:P4_has_time-span` phải dùng `URIRef` trực tiếp
- Giá trị `placeType` / `gender` / `hasAppellationType` là **literal chuỗi** dạng `"bkg:Monastery"` → phải tách phần sau dấu `:`
- 2 định dạng TTL khác nhau được xử lý tự động (giàu: appellation/places/works; dòng phái: teacher/disciple/generationOrder)
