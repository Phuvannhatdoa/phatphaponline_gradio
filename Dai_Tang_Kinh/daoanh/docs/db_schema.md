# Database Schema — `lineage.db`

**File:** `data/lineage.db`
**Last updated:** 2026-10-07 (thêm `places_vn` + `places_vn_pending` — T242 GPS chùa Việt Nam)

## 3-Layer Model

| Layer | Tables | Access Rule |
|-------|--------|-------------|
| **RAW** | `places_dila`, `places_vn`, `people_full`, `marcus_reference`, `marcus_networks`, `dila_reference` | Read-only, never modified by app |
| **STAGING / MAPPING** | `places_pending`, `places_vn_pending`, `namevi_map_places`, `ttl_mapping`, `ttl_works`, `ttl_canon_works` | Written by ETL + admin UI |
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

### `places_vn` (RAW) — T242 (GPS chùa Việt Nam)

Ground truth GPS chùa / tổ đình / thiền viện Việt Nam, mirror DILA nhưng ID
namespace `VN` + 10 số. Đặc tả: `docs/integration/Uu-Tien-1-T07-gis-buddhist-maps-vietnam-consolidated.md`.
Không ghi đè `places_dila` / `places` / `entity`.

| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT PRIMARY KEY | `VN` + 10 chữ số (deterministic từ source+external_key), không trùng `PL` |
| `name_vi` | TEXT | Tên chính tiếng Việt (VD "Chùa Trấn Quốc") |
| `name_zh` | TEXT | Pháp danh Hán nếu có |
| `district` | TEXT | Hành chính VN: `Việt Nam-Tỉnh/TP-Quận/Huyện-Xã/Phường` |
| `note_category` | TEXT | Loại: `chùa / tổ đình / tự / thiền viện / tịnh xá / niệm Phật đường / …` |
| `listbibl` | TEXT | Nguồn: `Wikidata (CC0) QID=…` / `OpenStreetMap (ODbL)` / `disantongiao.vn + geocoder …` |
| `geo_lat` | REAL | GPS thực đo trên lãnh thổ VN (bbox 8–24N, 102–110E) |
| `geo_long` | REAL | Kinh độ |
| `name_en` | TEXT | Tên tiếng Anh |
| `name_other` | TEXT | Tên khác |
| `sect` | TEXT | Tông phái |
| `founding_year` | TEXT | Năm thành lập |
| `heritage_status` | TEXT | Di tích quốc gia / UNESCO… |
| `status` | TEXT | `active` / `inactive` / `unknown` |
| `source` | TEXT | `wikidata` / `osm` / `disantongiao` |
| `accuracy` | TEXT | `dila_exact` (T0) / `osm_centroid` (T1) / `geocode_street` (T2) |
| `raw_source` | TEXT | JSON nguồn gốc (thay `raw_xml` vì nguồn VN không TEI) |

ETL: `scripts/vn_places_merge_validate.py --apply` (đọc 3 JSON T0/T1/T2 →
gộp + dedupe 200m + validate bbox → insert). Revert: `--revert` (DROP 2 bảng
+ xoá `dataset_sources` do T242 đăng ký).

### `places_vn_pending` (STAGING) — T242

Hàng đợi review (adapt `admin/geo_review.html`): record chưa geocode được
(`pending_reason='no_gps'`) hoặc tọa độ ngoài bbox VN (`'out_of_bbox_vn'`).
Cùng schema 17 cột; lý do lưu trong `raw_source.pending_reason`.

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

### `place_norm_keys` + `place_norm_fts` (T243 — DERIVED, addditive)

Chỉ số tìm kiếm theo **khóa chuẩn** cho pipeline T244 (khớp tên không dấu tiếng Việt,
bỏ cơ sở thờ tự, Hán-Việt/pinyin). **Không sửa nguồn RAW**; rebuild idempotent toàn bộ
(`DELETE` + `INSERT…rebuild`); revert = `DROP` 2 bảng, mất 0 dữ liệu cũ.

| Column | Type | Description |
|--------|------|-------------|
| `rowid` | INTEGER PK | rowid (content_rowid cho FTS external-content) |
| `dila_id` | TEXT | FK → `places_dila.id` |
| `name_role` | TEXT | `dila` \| `dila_zh` \| `vi` (nguồn tên) |
| `name_text` | TEXT | Chuỗi gốc đã NFKC |
| `norm_key` | TEXT | Khóa chuẩn (không dấu tiếng Việt) |
| `key_kind` | TEXT | `full` (nguyên tên) \| `stripped` (bỏ cơ sở thờ tự) |
| `hanvi` | TEXT | Phiên âm Hán-Việt (chỉ role `dila_zh`) |
| `pinyin` | TEXT | Phiên âm pinyin (chỉ role `dila_zh`) |
| `district` | TEXT | `places_dila.district` |
| `has_geo` | INTEGER | 1 nếu places_dila có `geo_lat` AND `geo_long` |

- `place_norm_fts` = FTS5 `(norm_key, name_text, hanvi, pinyin)`, `content='place_norm_keys'`,
  `content_rowid='rowid'`; index: `idx_pnk_dila(dila_id)`, `idx_pnk_normkey(norm_key)`.
- Nguồn dữ liệu: `places_dila` (READ-ONLY) + `namevi_map_places GROUP BY dila_id MIN(name_vi)`.
- Sinh bởi: `python -X utf8 scripts/vn_places_t243_normalize.py --apply`
  (số đo thật: `rows_keys` = 250.784, distinct key = 86.818 từ 59.167 places).
- Ràng buộc: 3-Layer LOCK — bảng nằm class DERIVED, không phải SSOT.

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

## Translation System (T79 / T123 / T165)

### `translation_rules` (T123 + T165)

Translation Constitution — rule-driven constraints applied to every LLM translation prompt.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-increment |
| `rule_code` | TEXT | Short code (terminology/style/forbidden/gate, `RULE-%`) |
| `rule_type` | TEXT | terminology / style / forbidden / gate |
| `description` | TEXT | Human description |
| `rule_text` | TEXT | Full rule body (Hán tự + quy tắc) |
| `is_active` | INTEGER | 1 = active, 0 = inactive |
| `priority` | INTEGER | Ordering at prompt build |
| `match_scope` | TEXT | **T165 +2 cột (2026-09-25):** `always` (ép áp mọi bản dịch) hoặc `terms` (chỉ áp khi nguồn chứa term trong `match_terms`) |
| `match_terms` | TEXT | **T165:** JSON array các Hán từ ≥2 ký tự fallback (`_t165_extract_match_terms`) — auto-backfill khi `rule_text` đổi (decode dòng `| ... | `) |
| `status` | TEXT | active / draft / dismissed (T167) |
| `ruleset_id` / `ruleset_version` / `is_canonical` | TEXT/TEXT/INTEGER | T167 seed |
| `created_by` / `created_at` / `updated_at` | TEXT | Audit metadata |

Backfill 2026-09-25 (T169/T165): 112 rules — `match_scope='always'` = 41, `'terms'` = 71 (terminology/forbidden tự động `terms`; style/gate `always` khi không extract được term → forced-always).

### `translation_cache` (T73/T79 + T165)

Content-addressable translation cache.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-increment |
| `source_hash` | TEXT | `sha256(source_text)[:24]` — **legacy key** (giữ nguyên) |
| `source_type` | TEXT | person_bio / place_note / passage / relation_evidence / dila_card ... |
| `entity_id` | TEXT | Owner entity ID |
| `source_text` | TEXT | Original Hán văn |
| `translated_text` | TEXT | Kết quả dịch |
| `model_id` / `rules_version` | TEXT | Model + legacy rules version |
| `status` | TEXT | auto / draft / edited / reported / invalidated |
| `report_count` | TEXT | Báo lỗi dịch |
| `constitution_hash` | TEXT | **T165 +3 cột (2026-09-25, NULL sau migrate):** `sha256[:16]` = FULL rule_text (sorted) + filtered glossary `zh→vi` (post-resolver) + exemplar `zh:vi` + `PROMPT_FORMAT_VERSION='t165-v1'` + label + json_mode + extra_hash (VD dila person_name_lock) + fingerprint |
| `selected_rule_codes` | TEXT | **T165:** JSON array mã rule khớp (`match_scope='terms'` chỉ các rule có term xuất hiện trong nguồn) |
| `glossary_hash` | TEXT | **T165:** sha256 of filtered glossary block được inject vào prompt |
| `identity_status` | TEXT | **T166 +3 cột (2026-09-26):** `pass` / `review_required` / `failed` / `conflict` — kết quả T166 §6.3 post-check sau LLM. **NULL = legacy pass** (không đoán lịch sử). Trusted = NULL/pass; draft = failed/conflict/review_required (SPEC §8.1/§8.3) |
| `identity_issues` | TEXT | **T166:** JSON array lỗi `{code, severity, detected, canonical_id, entity_type, expected, ...}` (CANONICAL_IDENTITY_MISMATCH / CANONICAL_INVENTION / LOCKED_NAME_NOT_RENDERED / MOJIBAKE) |
| `identity_lock_hash` | TEXT | **T166:** `t166_lock_fingerprint` npm of CanonicalLock (rỗng khi không có LOCKED entry — gate chống mass-miss §9); phải bằng `t166_lock_fingerprint` ghi trong `constitution_hash` |
| `identity_lock_policy` | TEXT | **T166 (trên `translation_rules`):** `P-PARTIAL` (mặc định — vẫn gọi LLM, gắn cờ review) / `P-STOP` (có LOCKED conflict nặng thì chặn luôn LLM) — Admin đổi được |

Unique: `UNIQUE(source_hash, source_type)`. Lookup T165: `constitution_hash` trước, fallback legacy `rules_version`; luôn kèm `source_type` + `status!='invalidated'`; ưu tiên `status='edited'` (row human không bao giờ bị REPLACE). Index T166: `idx_tc_identity (identity_status)`.

Baseline T166 (2026-09-26): 1762 cache rows — **0 có `constitution_hash`** (cache đang chạy legacy `rules_version`); T166 fingerprint chỉ làm miss các row LOCKED thật (không mass-miss toàn bộ).

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
| `vn_person_authority` | ✅ Active (2026-07-29) | **Authority nhân vật Việt Nam** (từ TTL thiền sư): `id PK (slug), ttl_filename, name_vi, name_zh, dharma_title, dharma_lineage, generation_order, is_lineage_founder, gender, biographical_note_vi, birth_year, death_year, appellations JSON, dila_id, status, created_at` — nguồn: `data/ttl/old/*.ttl`. ⚠ **KHÔNG có cột `person_id`**; xem §9.1 về `status` + §9.2 về `dila_id` không unique |
| `vn_person_relations` | ✅ Active (2026-07-29) | Quan hệ nhân vật: `id PK, person_id FK, relation_type (hasTeacher/hasDisciple/hasRelatedFigure), target_id, target_label_vi, ttl_filename` — UNIQUE `(person_id, relation_type, target_id)`, index `(person_id)` |
| `vn_person_places` | ✅ Active (2026-07-29) | Địa danh liên quan nhân vật: `id PK, person_id FK, place_id, place_label_vi, place_type (Monastery/SacredSite), ttl_filename` — UNIQUE `(person_id, place_id)`, index `(person_id)` |
| `vn_person_works` | ✅ Active (2026-07-29) | Tác phẩm nhân vật: `id PK, person_id FK, work_id, work_title_vi, ttl_filename` — UNIQUE `(person_id, work_id)`, index `(person_id)` |
| `vn_person_events` | ✅ Active (2026-07-29) | Sự kiện nhân vật: `id PK, person_id FK, event_type (Birth/Death/KeyLifeEvent/Contribution/PhilosophicalStance), event_id, event_label_vi, event_year, ttl_filename` — UNIQUE `(person_id, event_type, event_id)`, index `(person_id)` |

---

## 9. Caveat data integrity (verify 2026-10-01, task T199/T200/T201)

### 9.1 `vn_person_authority.status` — là NHÃN NGUỒN GỐC, KHÔNG phải thang chất lượng

`id`-prefix và `status` ánh xạ **1:1** (verify trên 1.506 row):

| `id` prefix | `status` | Rows | Ý nghĩa |
|---|---|---|---|
| `alias_*` | `alias_vi_suffix` | 450 | row **alias**: `name_vi` là tên đầy đủ có tiền/hậu tố Hán-Việt |
| `alias_*` | `alias_zh_match` | 7 | row **alias**: khớp qua tên Hán |
| khác | `auto_ttl` | 599 | tự sinh từ TTL |
| khác | `pending` | 448 | chờ duyệt |
| khác | `verified` | **2** | **hạng duy nhất mà `canonical_lock` đọc** (level 0.95) |

`canonical_lock.SOURCE_LEVELS` chỉ khai báo `'vn_person_authority.verified': 0.95`;
`_LOCK_FLAGS` chỉ chứa `'vn_person_authority.verified'`. `git grep` toàn bộ `*.py`:
**không consumer nào** đọc `alias_vi_suffix` / `alias_zh_match` / `auto_ttl` ⇒ 4 giá trị này
chỉ mô tả **cách dòng sinh ra**, KHÔNG phải "chưa xác minh".

> ⚠ **438/450 row `alias_vi_suffix` có `name_vi` KHÁC `people.name_vi`** — đúng thiết kế:
> alias giữ tên đầy đủ có tiền tố triều đình, `people.name_vi` giữ tên lõi
> (vd `alias_A000035` = `Mạt Sơn Liễu Nhiên` vs `people[A000035].name_vi` = `Liễu Nhiên`).
> ⇒ **TUYỆT ĐỐI KHÔNG** `UPDATE status='verified'` hàng loạt trên các row alias: sẽ khiến
> `canonical_lock` khóa (LOCKED) 438 tên sai. Task T179 (2026-09-26) đề xuất việc này và **đã bác**.
> Guard: `SELECT count(*) FROM vn_person_authority WHERE id LIKE 'alias_%' AND status='verified'` phải = **0**.

### 9.2 `vn_person_authority.dila_id` KHÔNG unique + `LIMIT 1` không `ORDER BY`

- **1.259** `dila_id` khác nhau / **1.506** row ⇒ **33** `dila_id` mang **2–3 dòng**
- **9/33** nhóm có **cả** dòng `alias_*` lẫn dòng non-alias

`app.py:5964` và `app.py:12841` đọc bằng:
```sql
SELECT … FROM vn_person_authority WHERE dila_id=? LIMIT 1   -- KHÔNG ORDER BY
```
⇒ với 33 người này dòng trả về **không xác định**. Vì dòng `alias_*` mang tên đầy đủ có
tiền tố, nếu nó thắng `LIMIT 1` thì UI hiển thị tên của người khác.

Ví dụ xung đột thật:
| `dila_id` | Các dòng trùng |
|---|---|
| **A021395** | `Ngũ Tổ Pháp Diễn` (alias) · `Báo Ân Pháp Diễn` (pending) · `Tứ Tổ Pháp Diễn` (pending) — **3 tên khác nhau** |
| **A047679** | `Phù Sơn Đức Tuyên` · `Quảng Tuệ Đức Tuyên` — **2 người khác nhau, chung 1 `dila_id`** |
| **A026824** | `Dương Châu Tuệ Giác` · `Lang Nha Tuệ Giác` · `Linh Thứu Tuệ Giác` — cùng gốc `Tuệ Giác` |

> **Đã sửa [T200] 2026-10-01:** tie-break chỉ định theo `status`, dùng chung qua
> module `vnpa_lookup.py` (`VNPA_ORDER_BY = ORDER BY CASE status … END ASC, id ASC`):
> `verified` > `pending` > `auto_ttl` > `alias_vi_suffix` > `alias_zh_match`.
> Thứ tự này khớp cả ngữ nghĩa (verified = admin duyệt, `canonical_lock` đọc level 0.95)
> lẫn dữ liệu (% khớp `people.name_vi`: pending 10.5% > auto_ttl 6.3% > alias 2.7%).
> Đã sửa 3 call site `app.py` (tra cứu theo `dila_id` + vòng dựng map bằng `setdefault` để dòng sau không còn đè).
> **22/33 nhóm đổi dòng** — đều thay dòng chọn nhầm.
> Test: `tests/test_t200_vnpa_tiebreak.py` **25/25 PASS**, chạy trong `npm run test:translation`.

**VẪN CÒN LẠI:** để xửa tra cứu cần đọc chắc định danh. Việc **gộp/tách `dila_id` cho 33 nhóm**
(vd `A047679` có vẻ 2 người khác nhau) **chưa làm** — cần Admin duyệt từng nhóm.
Task theo dõi: **T200** (`tasks/T200-vnpa-dila-id-duplicate-limit1.md`).

### 9.2b `vn_person_authority.superseded_by` — cột mới (additive) `[T507]` (2026-11-01)

> Thêm bằng `ALTER TABLE vn_person_authority ADD COLUMN superseded_by TEXT` — **additive**,
> không đổi schema cột nào khác, không đổi `status` của bất kỳ dòng nào.

- **Mục đích:** đánh dấu 1 dòng trong nhóm `dila_id` trùng (xem §9.2) là bản đã bị Admin
  quyết **thay thế** bởi 1 dòng khác cùng `dila_id`, mà KHÔNG xóa dòng cũ (giữ nguyên lịch sử)
  và KHÔNG đổi `status` (status vẫn là NHÃN NGUỒN GỐC theo §9.1, không phải cờ còn/hết hiệu lực).
- `superseded_by` = `id` (slug) của dòng được Admin chọn giữ làm bản đúng; `NULL` = dòng
  bình thường, chưa bị thay thế bởi dòng nào.
- **Case đầu tiên áp dụng (T507, A004981):** Admin xác nhận giữ `nam_vien_hue_ngung`
  (`status='pending'`, tên "Nam Viện Huệ Ngung") làm bản đúng cho `dila_id='A004981'`;
  đánh dấu `phong_huyet_dien_chieu` (`status='auto_ttl'`, tên "Huệ Ngung", `ttl_filename`
  trỏ tới file không tồn tại) là bản superseded bằng
  `UPDATE ... SET superseded_by='nam_vien_hue_ngung' WHERE id='phong_huyet_dien_chieu'`.
  Verify sau ghi: tổng số dòng `vn_person_authority` không đổi (1.512 trước/sau), `status`
  của cả 2 dòng giữ nguyên (`auto_ttl` / `pending`), dòng `nam_vien_hue_ngung` có
  `superseded_by IS NULL`.
- **Chưa có consumer code nào đọc cột này** (cột mới thêm, chưa đổi `_t412_build_index`,
  `vnpa_lookup.py`, hay bất kỳ route nào) — bước đọc/lọc theo `superseded_by` (ví dụ loại dòng
  có `superseded_by IS NOT NULL` khỏi kết quả `LIMIT 1`/crosswalk) thuộc phạm vi việc khác,
  chưa làm trong T507.
- Rollback: `ALTER TABLE vn_person_authority DROP COLUMN superseded_by` (SQLite ≥ 3.35 hỗ trợ
  `DROP COLUMN` trực tiếp) hoặc khôi phục từ backup — xem `docs/ROLLBACK.md` mục T507.

### 9.3 `canonical_decision` — nguồn #1 ĐÃ SỬA `[T201]` (2026-10-01)

> **Trước 2026-10-01 (T201): nguồn #1 `canonical_decision` là DEAD CODE, chưa bao giờ chạy.**

`canonical_lock.py:866-875` (nguồn #1, **đầu** `SOURCE_PRIORITY`):
```sql
FROM canonical_decision cd
LEFT JOIN places_dila pd ON pd.id = cd.entity_ref   -- đúng (T201 sửa từ pd.dila_id)
LEFT JOIN people     pj ON pj.id = cd.entity_ref
```

**Bug đã sửa:** dòng cũ ghi `pd.dila_id`, nhưng `places_dila` có **PK = `id`**, không có cột
`dila_id` (verify `PRAGMA table_info`; `people` cũng vậy) ⇒ query **luôn throw**
`sqlite3.OperationalError: no such column: pd.dila_id` ⇒ `_safe()` nuốt lỗi ⇒ **nguồn #1 rỗng
im lặng mọi lúc**, kể cả row `admin_approved` level 1.0 (T68) cũng **chết**.
`audit:t166` vẫn PASS vì 0 dòng = không có sai lệch để phát hiện.

**Đã sửa (T201):**
1. `pd.dila_id` → `pd.id`
2. `_safe()` **không nuốt im lặng** — `logger.warning` + tích luỹ `_SAFE_ERRORS` + helper `safe_errors()`
3. `scripts/t166_identity_audit.py` thêm `_check_safe_errors()` ⇒ **FAIL** khi có nguồn chết vì lỗi schema
   (red-team đã kiểm chứng: rename `places_dila` trong DB copy ⇒ audit báo `[FAIL]` đúng mô tả lỗi)

**Verify sau sửa (DB thật, `build_canonical_lock('靈祐')`) — 2 entity:**
| canonical_id | canonical_value | level | source | LOCKED |
|---|---|---|---|---|
| `A001984` | `Quy Sơn Linh Hựu` | **1.0** | `canonical_decision.admin_approved` | ✅ True |
| `4bc1b80d` | `Linh Hữu` | 0.7 | `name_vi_map.auto` | ❌ False |

> ⚠ **Data cũ cần vệ sinh:** 2 row `canonical_decision` cũ (T68) có `canonical_name_vi`
> **corrupt** — chứa **byte `?` thật (0x3F)**, không phải lỗi hiển thị:
> `PL000000000314` = `Th? S?t H?i` (hex `54683F20533F7420483F69`) · `PL000000000001` = `Kho?t T?t ?a Qu?c`.
> `is_valid_vi()` trả **False** cho cả hai (chuỗi toàn ASCII) ⇒ **được lọc đúng** khi bật nguồn #1,
> nhưng cần sửa dữ liệu gốc (task riêng — xem `docs/bugs.md`).

---

## 9b. Mojibake `Ð` (U+00D0) — quy tắc bắt buộc khi nhập dữ liệu (T206/T207)

### Vấn đề
Chữ **Đ** tiếng Việt là **U+0110** (LATIN CAPITAL LETTER D WITH STROKE).
Một số nguồn ghi ra **U+00D0** (LATIN CAPITAL LETTER **ETH**) — ký tự **không tồn
tại trong tiếng Việt**, chỉ dùng cho tiếng Iceland. Hiển thị sai:
`Ðại sư` thay vì `Đại sư`.

### Vì sao nguy hiểm — nó phá vỡ tra cứu `lexicon`
`app.py:96 normalize_text()` (dùng bởi **cả 2** call site đọc bảng này:
`app.py:1226 _translate_zh_term`, `app.py:2800`) làm:

```python
s = unicodedata.normalize('NFD', s)          # bỏ dấu
s = ''.join(c for c in s if category(c) != 'Mn')
s = s.replace('đ','d').replace('Đ','d')     # chỉ map U+0110/U+0111
return s.lower().strip()
```

**U+00D0 không có canonical decomposition** (`decomposition=''`) nên **sống sót**
qua toàn bộ chuỗi ⇒ `Ðoạn lạc` → `'ðoan lac'` thay vì `'doan lac'`.

| Term | `normalize_text()` | Đúng? |
|------|--------------------|-------|
| `Đoạn lạc` | `'doan lac'` | ✅ |
| `Ðoạn lạc` | `'ðoan lac'` | ❌ |

### Quy ước `key_norm` — CẢNH BÁO khi tính lại
Cột `lexicon.key_norm` là khoá tra cứu. Đo trên 166.278 row:

| Nhóm | Row |
|------|-----|
| `key_norm == normalize_text(term)` | **112.430 (67,6%)** — quy ước chuẩn |
| lệch vì `đ/Đ` **đúng** | 53.384 — lỗi quy ước có sẵn |
| lệch vì `Ð` | **162** — phạm vi T207 |

⇒ **KHÔNG tính lại `key_norm` toàn bộ bảng** (sẽ đổi hành vi tra cứu trên 53k+
row). Chỉ xử lý đúng 162 row có `Ð`.

### `lexicon_fts` là FTS5 external-content — CẢNH BÁO khi UPDATE
```sql
CREATE VIRTUAL TABLE lexicon_fts USING fts5(
    term, definition, content=lexicon, content_rowid=id);
```
Bảng này **không có trigger** ⇒ `UPDATE lexicon` thẳng sẽ **lệch index FTS**.
Phải theo đúng thứ tự:

```sql
INSERT INTO lexicon_fts(lexicon_fts, rowid, term, definition)
  VALUES('delete', :id, :old_term, :old_def);   -- gỡ index cũ
UPDATE lexicon SET term=:new, definition=:new_def WHERE id=:id;
INSERT INTO lexicon_fts(lexicon_fts, rowid, term, definition)
  VALUES('delete', :id, :new, :new_def);        -- đẩy index mới
```

**Không** dùng `INSERT INTO lexicon_fts(lexicon_fts) VALUES('rebuild')` cho lô nhỏ
— sẽ dựng lại 166.278 row, chậm và khoá DB lâu.

### Quy trình chuẩn khi phát hiện mojibake
1. Quét read-only trước, đếm theo bảng/cột.
2. **Kiểm chứng vị trí cấu trúc**: `Ð` có nằm trong URI / `@prefix` / slug
   `ex:monk/…` / `label@zh` không? Nếu có ⇒ **dừng**, không sửa hàng loạt.
3. Kiểm token nhiều ký tự — nếu tồn tại từ hợp lệ ngoài tiếng Việt thì phải so tay.
4. Backup (TTL: file-level; DB: sqlite3 backup API).
5. Sửa, rồi **kiểm chứng theo vị trí ký tự**: mọi khác biệt giữa bản gốc và bản
   sửa phải đúng là `Ð`→`Đ`, tổng khớp số ký tự lỗi, 0 đổi ngoài dự kiến.

### Công cụ
| Script | Phạm vi |
|--------|--------|
| `scripts/t206_fix_mojibake.py` | 302 file TTL — `--stats/--dry-run/--apply/--verify/--revert` |
| `scripts/probe_t207.py` / `probe_t207b.py` / `probe_t207c.py` | đo lỗi trong DB (read-only) |

> ⚠️ **Bẫy shell khi làm việc này:** heredoc PowerShell làm hỏng UTF-8
> (`Ð` → `?`) khiến kết quả probe sai. Viết probe ra **file** và dùng escape
> `\uXXXX`. Tương tự, đừng dùng phép thử đảo ngược `Đ`→`Ð` để so sánh bản gốc
> (nó thay cả các `Đ` đúng sẵn có ⇒ kết quả sai).
