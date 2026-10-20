# DB SCHEMA SNAPSHOT (VPS)

- Generated at: 2026-05-25 10:52:40
- Host: vmi2916572

## DB FILES ON VPS
  - `/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/daoanh.db` (0)
  - `/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/cbeta/cbeta.db` (5.2M)
  - `/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/lineage_backup_20260514.db` (506M)
  - `/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/lineage.db` (570M)
  - `/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/sqlite/backup/buddhist_db_20260421_075056.sqlite` (25M)
  - `/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/sqlite/buddhist_db.sqlite` (33M)
  - `/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/lineage.db` (0)
  - `/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/src_python/data/lineage.db` (0)

## SCHEMA: cbeta.db
```sql
CREATE TABLE cbeta_texts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sigla TEXT UNIQUE NOT NULL,
  canon TEXT NOT NULL,
  vol INTEGER,
  title_zh TEXT,
  author_zh TEXT,
  translator_zh TEXT,
  juan_count INTEGER,
  cbeta_url TEXT,
  xml_file_path TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE cbeta_content_index (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  text_id INTEGER NOT NULL,
  juan INTEGER NOT NULL,
  page TEXT,
  line_num INTEGER,
  content_zh TEXT,
  FOREIGN KEY (text_id) REFERENCES cbeta_texts(id) ON DELETE CASCADE
);
CREATE VIRTUAL TABLE cbeta_fts USING fts5(
  sigla UNINDEXED,
  title_zh,
  juan UNINDEXED,
  page UNINDEXED,
  content_zh,
  tokenize='unicode61'
)
/* cbeta_fts(sigla,title_zh,juan,page,content_zh) */;
CREATE TABLE IF NOT EXISTS 'cbeta_fts_data'(id INTEGER PRIMARY KEY, block BLOB);
CREATE TABLE IF NOT EXISTS 'cbeta_fts_idx'(segid, term, pgno, PRIMARY KEY(segid, term)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS 'cbeta_fts_content'(id INTEGER PRIMARY KEY, c0, c1, c2, c3, c4);
CREATE TABLE IF NOT EXISTS 'cbeta_fts_docsize'(id INTEGER PRIMARY KEY, sz BLOB);
CREATE TABLE IF NOT EXISTS 'cbeta_fts_config'(k PRIMARY KEY, v) WITHOUT ROWID;
CREATE TRIGGER cbeta_content_ai AFTER INSERT ON cbeta_content_index BEGIN
  INSERT INTO cbeta_fts(rowid, sigla, title_zh, juan, page, content_zh)
  SELECT new.id, t.sigla, t.title_zh, new.juan, new.page, new.content_zh
  FROM cbeta_texts t WHERE t.id = new.text_id;
END;
CREATE TRIGGER cbeta_content_ad AFTER DELETE ON cbeta_content_index BEGIN
  DELETE FROM cbeta_fts WHERE rowid = old.id;
END;
CREATE TABLE cbeta_import_log (
  xml_file_path TEXT PRIMARY KEY,
  imported_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  status TEXT DEFAULT 'success'
);
CREATE INDEX idx_cbeta_texts_sigla ON cbeta_texts(sigla);
CREATE INDEX idx_cbeta_texts_canon ON cbeta_texts(canon);
CREATE INDEX idx_cbeta_content_text_juan ON cbeta_content_index(text_id, juan);
```

## SCHEMA: lineage.db (Main Production DB)
```sql
CREATE TABLE networks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            monk_id TEXT NOT NULL,
            related_id TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            source_origin TEXT NOT NULL CHECK(source_origin IN ('Marcus', 'DILA', 'Admin')),
            confidence REAL DEFAULT 1.0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(monk_id, related_id, source_origin)
        );
CREATE TABLE sqlite_sequence(name,seq);
CREATE INDEX idx_networks_monk_id ON networks(monk_id)
    ;
CREATE INDEX idx_networks_source ON networks(source_origin)
    ;
CREATE TABLE conflicts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            monk_id TEXT NOT NULL,
            monk_name TEXT,
            source_origin TEXT DEFAULT 'MARCUS',
            conflict_type TEXT DEFAULT 'lineage',
            only_dila_teachers TEXT,
            only_marcus_teachers TEXT,
            only_dila_students TEXT,
            only_marcus_students TEXT,
            dila_count INTEGER DEFAULT 0,
            marcus_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'resolved', 'ignored')),
            admin_choice TEXT,
            resolution_timestamp TEXT,
            resolution_notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
CREATE INDEX idx_conflicts_status ON conflicts(status)
    ;
CREATE INDEX idx_conflicts_monk ON conflicts(monk_id)
    ;
CREATE TABLE resolutions_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conflict_id INTEGER NOT NULL,
            monk_id TEXT NOT NULL,
            chosen_source TEXT NOT NULL,
            previous_source TEXT,
            notes TEXT,
            resolved_by TEXT DEFAULT 'admin',
            resolved_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conflict_id) REFERENCES conflicts(id)
        );
CREATE TABLE dila_reference (
            id TEXT PRIMARY KEY,
            name_vi TEXT,
            name_zh TEXT,
            name_ja TEXT,
            name_en TEXT,
            dynasty TEXT,
            bio TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
CREATE TABLE marcus_reference (
            node_id TEXT PRIMARY KEY,
            label TEXT,
            label_vi TEXT,
            birth_year INTEGER,
            death_year INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
CREATE TABLE places (
            id TEXT PRIMARY KEY,
            name_zh TEXT,
            name_vi TEXT,
            name_en TEXT,
            location TEXT,
            gps_lat REAL,
            gps_long REAL,
            address TEXT,
            province TEXT,
            country TEXT DEFAULT 'Vietnam',
            place_type TEXT,
            source_origin TEXT DEFAULT 'DILA',
            confidence REAL DEFAULT 1.0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
CREATE INDEX idx_places_province ON places(province);
CREATE INDEX idx_places_type ON places(place_type);
CREATE INDEX idx_networks_monk ON networks(monk_id);
CREATE INDEX idx_networks_rel ON networks(relation_type);
CREATE TABLE time_periods (
            id TEXT PRIMARY KEY,
            period_name TEXT NOT NULL,
            period_name_zh TEXT,
            period_name_vi TEXT,
            start_year INTEGER,
            end_year INTEGER,
            era_name TEXT,
            source_origin TEXT DEFAULT 'DILA',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
CREATE INDEX idx_time_periods_name ON time_periods(period_name);
CREATE TABLE canons_catalog (
            id TEXT PRIMARY KEY,
            canon_name TEXT NOT NULL,
            canon_code TEXT NOT NULL,
            volume TEXT,
            title_zh TEXT,
            title_vi TEXT,
            title_en TEXT,
            author TEXT,
            year INTEGER,
            pages TEXT,
            source_origin TEXT DEFAULT 'DILA',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
CREATE INDEX idx_canons_name ON canons_catalog(canon_name);
CREATE INDEX idx_canons_code ON canons_catalog(canon_code);
CREATE TABLE text_mapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id TEXT NOT NULL,
            target_id TEXT NOT NULL,
            canon TEXT NOT NULL,
            mapping_type TEXT NOT NULL,
            confidence REAL DEFAULT 1.0,
            source_origin TEXT DEFAULT 'DILA',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source_id, target_id, canon)
        );
CREATE INDEX idx_mapping_source ON text_mapping(source_id);
CREATE INDEX idx_mapping_target ON text_mapping(target_id);
CREATE TABLE lexicon (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term TEXT NOT NULL,
            normalized TEXT NOT NULL,
            definition TEXT,
            source TEXT NOT NULL,
            priority INTEGER CHECK(priority IN (1,2,3)),
            entity_type TEXT,
            lang TEXT DEFAULT 'vi',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP, key_norm TEXT,
            UNIQUE(term, source)
        );
CREATE INDEX idx_priority ON lexicon(priority);
CREATE INDEX idx_entity ON lexicon(entity_type);
CREATE INDEX idx_normalized ON lexicon(normalized);
CREATE INDEX idx_source ON lexicon(source);
CREATE VIRTUAL TABLE lexicon_fts USING fts5(
            term, definition, content=lexicon, content_rowid=id
        )
/* lexicon_fts(term,definition) */;
CREATE TABLE IF NOT EXISTS 'lexicon_fts_data'(id INTEGER PRIMARY KEY, block BLOB);
CREATE TABLE IF NOT EXISTS 'lexicon_fts_idx'(segid, term, pgno, PRIMARY KEY(segid, term)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS 'lexicon_fts_docsize'(id INTEGER PRIMARY KEY, sz BLOB);
CREATE TABLE IF NOT EXISTS 'lexicon_fts_config'(k PRIMARY KEY, v) WITHOUT ROWID;
CREATE INDEX idx_places_gps ON places(gps_lat, gps_long);
CREATE TABLE marcus_networks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id TEXT NOT NULL,
            student_id TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            teacher_label TEXT,
            student_label TEXT,
            source_data TEXT DEFAULT 'MARCUS',
            ref TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(teacher_id, student_id, relation_type)
        );
CREATE TABLE lineage_conflicts_v2 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id TEXT NOT NULL,
            label TEXT,
            name_vi TEXT,
            conflict_type TEXT,
            dila_data TEXT,
            marcus_data TEXT,
            dila_count INTEGER,
            marcus_count INTEGER,
            is_conflict BOOLEAN DEFAULT 1,
            resolved BOOLEAN DEFAULT 0,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
CREATE TABLE people (
        id TEXT PRIMARY KEY,
        name_zh TEXT,
        name_vi TEXT,
        name_en TEXT,
        name_ja TEXT,
        sect TEXT,
        dynasty TEXT,
        birth_year INTEGER,
        death_year INTEGER,
        bio TEXT,
        source_origin TEXT DEFAULT 'DILA',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    , latin_source TEXT, source_id INTEGER REFERENCES dataset_sources(id));
CREATE TABLE entity_temples (
        id INTEGER PRIMARY KEY,
        name TEXT,
        definition TEXT,
        source TEXT,
        entity_type TEXT DEFAULT 'temple'
    );
CREATE TABLE entity_monks (
        id INTEGER PRIMARY KEY,
        name TEXT,
        definition TEXT,
        source TEXT,
        entity_type TEXT DEFAULT 'monk'
    );
CREATE TABLE entity_works (
        id INTEGER PRIMARY KEY,
        title TEXT,
        definition TEXT,
        source TEXT,
        entity_type TEXT DEFAULT 'work'
    );
CREATE TABLE ttl_mapping (
        id INTEGER PRIMARY KEY,
        ttl_filename TEXT,
        name_vi TEXT,
        name_zh TEXT,
        dila_id TEXT,
        status TEXT DEFAULT 'pending'
    );
CREATE TABLE canon_catalog (
        work_id INTEGER PRIMARY KEY AUTOINCREMENT,
        -- Title fields
        title_vi TEXT,                    -- Ca Diếp Kết Kinh (Vietnamese)
        title_zh TEXT,                   -- 迦葉結經 (Chinese full)
        title_search TEXT,              -- ca diep ket kinh (normalized for search)
        
        -- Author/Translator
        author_vi TEXT,                  -- An Thế Cao
        author_zh TEXT,                -- 安世高
        author_dila_id TEXT,            -- A000xxx (link to people)
        author_role TEXT DEFAULT 'translator',  -- 'translator', 'author', 'compiler'
        
        -- Era/Time
        era_vi TEXT,                     -- Hậu Hán (Vietnamese)
        era_zh TEXT,                   -- 後漢 (Chinese)
        year_start INTEGER,             -- Start year (e.g., 25)
        year_end INTEGER,               -- End year
        
        -- Location (CBETA reference)
        cbeta_id TEXT,                 -- Sh.2027
        location_text TEXT,             -- Q.49, Tr.4, Sh.2027
        volume INTEGER,                -- 1 quyển
        
        -- Source tracking
        source TEXT DEFAULT 'MucLucDaiChanh',
        verified INTEGER DEFAULT 0,
        search_rank INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    , cb_volume INTEGER, cb_page INTEGER, cb_cbeta TEXT);
CREATE INDEX idx_canon_title ON canon_catalog(title_search);
CREATE INDEX idx_canon_author ON canon_catalog(author_vi);
CREATE INDEX idx_canon_era ON canon_catalog(era_vi);
CREATE TABLE canon_author_mapping (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        work_id INTEGER,
        author_name_vi TEXT,
        author_name_zh TEXT,
        author_dila_id TEXT,
        author_marcus_id TEXT,
        author_role TEXT,
        verified_source TEXT,
        created_at TEXT
    );
CREATE TABLE ttl_canon_works (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ttl_filename TEXT,
        work_uri TEXT,
        work_id INTEGER,
        relation_type TEXT,
        created_at TEXT
    );
CREATE TABLE ttl_works (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ttl_filename TEXT,
        work_title_vi TEXT,
        work_title_zh TEXT,
        work_id INTEGER,
        relation_source TEXT,
        relation_type TEXT,
        matched_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
CREATE TABLE translator_dila_map (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    translator_vi TEXT UNIQUE,
    translator_zh TEXT,
    dila_id TEXT,
    source TEXT DEFAULT 'manual',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE name_vi_map (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_vi TEXT NOT NULL,
            name_zh TEXT,
            birth_year INTEGER,
            death_year INTEGER,
            bio_snippet TEXT,
            dila_id TEXT,
            marcus_ids TEXT,
            source TEXT DEFAULT 'daoanh_dict',
            confidence REAL DEFAULT 1.0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(name_vi, name_zh)
        );
CREATE INDEX idx_name_zh ON name_vi_map(name_zh);
CREATE INDEX idx_name_vi ON name_vi_map(name_vi);
CREATE INDEX idx_dila_id ON name_vi_map(dila_id);
CREATE TABLE ttl_master (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                monk_id TEXT UNIQUE,
                name_vi TEXT,
                dila_id TEXT,
                lineage TEXT,
                ttl_content TEXT,
                filename TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
CREATE TABLE places_vps (
    id TEXT PRIMARY KEY,
    name_zh TEXT,
    name_vi TEXT,
    name_en TEXT,
    location TEXT,
    gps_lat REAL,
    gps_long REAL,
    address TEXT,
    province TEXT,
    country TEXT,
    place_type TEXT,
    source_origin TEXT,
    confidence REAL,
    created_at TEXT,
    updated_at TEXT
);
CREATE TABLE places_pending (id TEXT PRIMARY KEY, name_zh TEXT, name_vi TEXT, name_en TEXT, location TEXT, gps_lat REAL, gps_long REAL, address TEXT, province TEXT, country TEXT DEFAULT 'Vietnam', place_type TEXT, source_origin TEXT DEFAULT 'DILA', confidence REAL DEFAULT 1.0, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP, note TEXT, source_id INTEGER REFERENCES dataset_sources(id), raw_xml TEXT, district_raw TEXT, hist_country_raw TEXT, name_vi_norm TEXT);
CREATE TABLE name_vi_map_places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_vi TEXT NOT NULL,
            name_zh TEXT,
            dila_id TEXT UNIQUE,
            confidence REAL DEFAULT 1.0,
            source TEXT DEFAULT 'admin',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
CREATE TABLE people_full (id TEXT PRIMARY KEY, name TEXT, name_zh TEXT, name_en TEXT, name_san TEXT, name_jpn TEXT, name_peo TEXT, name_other TEXT, birth TEXT, death TEXT, floruit TEXT, gender TEXT, occupation TEXT, note TEXT, note_category TEXT, listbibl TEXT, raw_xml TEXT);
CREATE TABLE places_dila (
            id TEXT PRIMARY KEY,
            name TEXT,
            name_zh TEXT,
            name_en TEXT,
            name_san TEXT,
            name_jpn TEXT,
            name_peo TEXT,
            name_other TEXT,
            location_xml TEXT,
            geo_lat REAL,
            geo_long REAL,
            place_key TEXT,
            district TEXT,
            note TEXT,
            note_category TEXT,
            listbibl TEXT,
            raw_xml TEXT
        , source_id INTEGER REFERENCES dataset_sources(id));
CREATE TABLE namevi_map_places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_vi TEXT,
            name_zh TEXT,
            dila_id TEXT UNIQUE,
            confidence REAL DEFAULT 0.5,
            source TEXT DEFAULT 'manual',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        , needs_review INTEGER DEFAULT 0, note_vi TEXT, gps_lat TEXT, gps_long TEXT, source_id INTEGER REFERENCES dataset_sources(id), district_vi TEXT, country_vi TEXT, vn_name_status TEXT DEFAULT NULL);
CREATE VIRTUAL TABLE places_search_fts USING fts5(
                name_vi, name_zh, dila_id,
                content='namevi_map_places', content_rowid='id'
            )
/* places_search_fts(name_vi,name_zh,dila_id) */;
CREATE TABLE IF NOT EXISTS 'places_search_fts_data'(id INTEGER PRIMARY KEY, block BLOB);
CREATE TABLE IF NOT EXISTS 'places_search_fts_idx'(segid, term, pgno, PRIMARY KEY(segid, term)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS 'places_search_fts_docsize'(id INTEGER PRIMARY KEY, sz BLOB);
CREATE TABLE IF NOT EXISTS 'places_search_fts_config'(k PRIMARY KEY, v) WITHOUT ROWID;
CREATE TABLE hanviet_fallback (ch TEXT PRIMARY KEY, hv TEXT);
CREATE TABLE person_refs (id INTEGER PRIMARY KEY AUTOINCREMENT, person_id TEXT NOT NULL, source_name TEXT NOT NULL, ref_type TEXT, value TEXT, note TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (person_id) REFERENCES people(id));
CREATE INDEX idx_person_refs_person ON person_refs(person_id);
CREATE INDEX idx_person_refs_source ON person_refs(source_name);
CREATE TABLE dataset_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            source_type TEXT,
            origin_url TEXT,
            license TEXT,
            usage_level TEXT CHECK(usage_level IN ('GREEN', 'YELLOW', 'RED')) DEFAULT 'YELLOW',
            attribution_text TEXT,
            notes TEXT
        );
CREATE INDEX idx_places_pending_name_zh ON places_pending(name_zh);
CREATE INDEX idx_places_pending_id ON places_pending(id);
CREATE INDEX idx_lexicon_key_norm ON lexicon(key_norm);
CREATE TABLE place_cbdb_map (
    place_id TEXT NOT NULL,
    cbdb_addr_id INTEGER NOT NULL,
    note TEXT,
    PRIMARY KEY (place_id, cbdb_addr_id)
);
CREATE INDEX idx_place_cbdb_map_cbdb ON place_cbdb_map(cbdb_addr_id);
CREATE TABLE cbeta_place_mentions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  cbeta_text_sigla TEXT NOT NULL,
  dila_place_id TEXT,
  place_name_zh TEXT NOT NULL,
  juan INTEGER,
  page TEXT,
  context_snippet TEXT
);
CREATE TABLE cbeta_person_mentions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  cbeta_text_sigla TEXT NOT NULL,
  dila_person_id TEXT,
  person_name_zh TEXT NOT NULL,
  juan INTEGER,
  page TEXT,
  context_snippet TEXT
);
CREATE INDEX idx_cbeta_place_dila ON cbeta_place_mentions(dila_place_id);
CREATE INDEX idx_cbeta_place_name ON cbeta_place_mentions(place_name_zh);
CREATE INDEX idx_cbeta_person_dila ON cbeta_person_mentions(dila_person_id);
CREATE INDEX idx_cbeta_person_name ON cbeta_person_mentions(person_name_zh);
CREATE INDEX idx_cbeta_place_sigla ON cbeta_place_mentions(cbeta_text_sigla);
CREATE INDEX idx_cbeta_person_sigla ON cbeta_person_mentions(cbeta_text_sigla);
CREATE TABLE place_wiki_snapshots (
    place_id TEXT PRIMARY KEY,
    wiki_title TEXT,
    wiki_url TEXT,
    snippet TEXT,
    full_text TEXT,
    source TEXT DEFAULT 'wikipedia',
    license TEXT DEFAULT 'CC BY-SA 4.0',
    created_at TEXT,
    updated_at TEXT
  );
CREATE TABLE entity (
            entity_id   TEXT PRIMARY KEY,
            entity_type TEXT NOT NULL CHECK(entity_type IN ('PERSON','PLACE','TEXT')),
            dila_id     TEXT NOT NULL,
            alias_vi    TEXT,
            alias_zh    TEXT,
            cbeta_occ   TEXT,
            marcus_id   TEXT,
            extra_alias TEXT
        );
CREATE TABLE passage (
            passage_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            source      TEXT NOT NULL DEFAULT 'CBETA',
            text_id     TEXT NOT NULL,
            loc_ref     TEXT NOT NULL DEFAULT '',
            raw_text    TEXT NOT NULL,
            norm_text   TEXT
        );
CREATE INDEX idx_passage_text_id ON passage(text_id);
CREATE TABLE passage_entity (
            passage_id INTEGER NOT NULL,
            entity_id  TEXT NOT NULL,
            PRIMARY KEY (passage_id, entity_id)
        );
CREATE INDEX idx_pe_entity_id ON passage_entity(entity_id);
CREATE TABLE keyword_map (id INTEGER PRIMARY KEY AUTOINCREMENT, keyword TEXT NOT NULL, value TEXT NOT NULL, category TEXT DEFAULT 'import_ui', source TEXT DEFAULT 'manual', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX idx_keyword ON keyword_map(keyword);
CREATE INDEX idx_category ON keyword_map(category);
```

## SCHEMA: buddhist_db.sqlite (Legacy)
```sql
CREATE TABLE people (
            id TEXT PRIMARY KEY,
            name_zh TEXT,
            name_vi TEXT,
            name_en TEXT,
            lineage TEXT,
            dynasty TEXT,
            birth_year INTEGER,
            death_year INTEGER,
            dila_id TEXT,
            wiki_url TEXT,
            biography TEXT,
            sources TEXT,
            works TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
CREATE INDEX idx_people_name_zh ON people(name_zh);
CREATE INDEX idx_people_name_vi ON people(name_vi);
CREATE INDEX idx_people_lineage ON people(lineage);
CREATE INDEX idx_people_dynasty ON people(dynasty);
CREATE INDEX idx_people_dila_id ON people(dila_id);
CREATE TABLE places (
            id TEXT PRIMARY KEY,
            name_zh TEXT,
            name_vi TEXT,
            name_en TEXT,
            lat REAL,
            lng REAL,
            country TEXT,
            province TEXT,
            source TEXT,
            dila_place_id TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
CREATE INDEX idx_places_name_zh ON places(name_zh);
CREATE INDEX idx_places_country ON places(country);
CREATE INDEX idx_places_gps ON places(lat, lng);
CREATE TABLE networks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id TEXT NOT NULL,
            target_id TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            weight INTEGER DEFAULT 10,
            source TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (person_id) REFERENCES people(id),
            FOREIGN KEY (target_id) REFERENCES people(id)
        );
CREATE TABLE sqlite_sequence(name,seq);
CREATE INDEX idx_networks_person ON networks(person_id);
CREATE INDEX idx_networks_target ON networks(target_id);
CREATE INDEX idx_networks_relation ON networks(relation_type);
CREATE TABLE time_periods (
            id TEXT PRIMARY KEY,
            name_zh TEXT,
            name_en TEXT,
            start_year INTEGER,
            end_year INTEGER,
            era TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
CREATE INDEX idx_time_years ON time_periods(start_year, end_year);
CREATE TABLE canons_catalog (
            text_id TEXT PRIMARY KEY,
            title_zh TEXT,
            title_en TEXT,
            author_id TEXT,
            author_name TEXT,
            canon_type TEXT,
            volume TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP, canon_source TEXT DEFAULT 'CBETA', work_url TEXT,
            FOREIGN KEY (author_id) REFERENCES people(id)
        );
CREATE INDEX idx_canons_title ON canons_catalog(title_zh);
CREATE INDEX idx_canons_author ON canons_catalog(author_id);
CREATE TABLE text_mapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            taisho_id TEXT,
            cbeta_id TEXT,
            linhson_id TEXT,
            source TEXT
        );
CREATE TABLE lexicon (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term TEXT NOT NULL,
            definition TEXT,
            priority INTEGER DEFAULT 3,
            source TEXT,
            language TEXT DEFAULT 'zh',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
CREATE INDEX idx_lexicon_term ON lexicon(term);
CREATE INDEX idx_lexicon_priority ON lexicon(priority);
CREATE INDEX idx_lexicon_source ON lexicon(source);
CREATE TABLE metadata (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
CREATE TABLE canon_mapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_id TEXT NOT NULL,
            canon_source TEXT NOT NULL,
            title TEXT,
            author_dila_id TEXT,
            year INTEGER,
            volume TEXT,
            page TEXT,
            UNIQUE(work_id, canon_source)
        );
CREATE INDEX idx_canon_mapping_work ON canon_mapping(work_id)
    ;
CREATE INDEX idx_canon_mapping_author ON canon_mapping(author_dila_id)
    ;
CREATE TABLE lineage_conflicts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT,
            label TEXT,
            source TEXT DEFAULT 'MARCUS',
            conflict_type TEXT DEFAULT 'lineage',
            only_dila_teacher TEXT,
            only_marcus_teacher TEXT,
            only_dila_student TEXT,
            only_marcus_student TEXT,
            resolved INTEGER DEFAULT 0,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
CREATE TABLE marcus_networks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id TEXT NOT NULL,
            student_id TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            teacher_label TEXT,
            student_label TEXT,
            source_data TEXT DEFAULT 'MARCUS',
            ref TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(teacher_id, student_id, relation_type)
        );
CREATE INDEX idx_marcus_teacher ON marcus_networks(teacher_id);
CREATE INDEX idx_marcus_student ON marcus_networks(student_id);
CREATE TABLE lineage_conflicts_v2 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id TEXT NOT NULL,
            label TEXT,
            name_vi TEXT,
            conflict_type TEXT,
            dila_data TEXT,
            marcus_data TEXT,
            dila_count INTEGER,
            marcus_count INTEGER,
            is_conflict BOOLEAN DEFAULT 1,
            resolved BOOLEAN DEFAULT 0,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
```

---

# GAP_REPORT.md - Đạo Ảnh System Audit

## Executive Summary

| Category | Count |
|----------|-------|
| Missing Backend APIs | 3 |
| Missing Frontend Files | 2 |
| Data Files Referenced But Missing | 0 |
| Configuration Issues | 2 |

---

## 🔴 MISSING BACKEND (API called but NOT implemented)

### 1. `/api/deepsearch` (CRITICAL)
- **Called by:** `src/js/sutra_sync.js:65, 199`
- **Status:** NOT FOUND in app.py
- **Impact:** Sutra sync feature broken
- **Recommendation:** Implement endpoint or remove calls

### 2. `/api/sutra/<sutraId>` (CRITICAL)
- **Called by:** `src/js/sutra_sync.js:90`
- **Status:** NOT FOUND in app.py
- **Impact:** Individual sutra lookup broken
- **Recommendation:** Implement endpoint or update frontend

### 3. `/api/graphdb/sparql` (MEDIUM)
- **Called by:** `src/js/api_router.js:295`, `orchestrator.js:273`, `intent_router.js:23`
- **Status:** NOT FOUND in app.py (only in external ETL scripts)
- **Impact:** SPARQL queries from frontend fail
- **Recommendation:** Add GraphDB proxy endpoint in app.py OR document that it requires external service

### 4. `/api/rag/health` (LOW)
- **Called by:** `src/js/ai/rag_connector.js:181`
- **Status:** NOT FOUND in daoanh/app.py
- **Impact:** RAG health check fails (but likely uses Gradio RAG at port 7860)
- **Recommendation:** Either implement in daoanh or document that RAG runs separately

---

## 🟡 MISSING FRONTEND FILES (API exists but NOT used)

### 1. `/api/dict/merge` - POST
- **Status:** Implemented in app.py:1456
- **Called by:** None found in JS
- **Impact:** Dictionary merge functionality only accessible via direct API call

### 2. `/api/dict/fuzzy` - GET  
- **Status:** Implemented in app.py:1514
- **Called by:** None found in JS
- **Impact:** Fuzzy search functionality not exposed in UI

---

## 🟢 DATA FILES (OK)

All data files referenced in frontend exist:
- ✅ `data/places.json` - exists
- ✅ `data/processed/search_index_critical.json` - exists
- ✅ `data/processed/temples_master_gps.json` - exists  
- ✅ `data/processed/monk_names.json` - exists

---

## 🔵 CONFIGURATION ISSUES

### 1. nginx POST forwarding (Production)
- **Issue:** POST requests fail on production (502 Bad Gateway)
- **Status:** Documented in SESSION.md:222
- **File:** NOTES_NGINX_FIX.md (notes added)
- **Recommendation:** Fix nginx config for POST forwarding

### 2. External API hardcoded URLs
- **Issue:** Frontend uses hardcoded `https://phatphaponline.org/api/*`
- **Called by:** `src/js/search.js:100, 672, 676`
- **Impact:** May fail if external service unavailable
- **Recommendation:** Use CONFIG.apiBase for all API calls

---

## 📊 Gap by Feature

| Feature | Status | Gap |
|---------|--------|-----|
| **Search/Person** | ✅ Working | None |
| **Lineage Map** | ✅ Working | None |
| **Admin Dashboard** | ✅ Working | None |
| **Entity Linking** | ✅ Working | None |
| **Dictionary** | ⚠️ Partial | `/api/dict/fuzzy`, `/api/dict/merge` not exposed |
| **Sutra Sync** | ❌ Broken | `/api/deepsearch`, `/api/sutra/*` missing |
| **SPARQL** | ❌ Broken | `/api/graphdb/sparql` missing |
| **RAG Integration** | ⚠️ Partial | `/api/rag/health` not in daoanh |

---

## ✅ COMPLETED

- All core Place APIs implemented
- All Person/Lineage APIs implemented  
- All Admin CRUD APIs implemented
- All Entity Linking APIs implemented
- Dictionary base APIs implemented
- Data files present and valid

---

## 🚨 ACTION ITEMS

| Priority | Task | Effort |
|----------|------|--------|
| P0 | Implement `/api/deepsearch` | Medium |
| P0 | Implement `/api/sutra/<id>` | Medium |
| P1 | Add `/api/graphdb/sparql` proxy | Medium |
| P2 | Fix nginx POST forwarding | Low |
| P2 | Add dict/fuzzy UI | Low |
