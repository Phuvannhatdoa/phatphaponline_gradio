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
        , label_vi_confidence REAL DEFAULT 0.0, label_vi_source TEXT DEFAULT NULL);
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
        );
CREATE TABLE 'lexicon_fts_data'(id INTEGER PRIMARY KEY, block BLOB);
CREATE TABLE 'lexicon_fts_idx'(segid, term, pgno, PRIMARY KEY(segid, term)) WITHOUT ROWID;
CREATE TABLE 'lexicon_fts_docsize'(id INTEGER PRIMARY KEY, sz BLOB);
CREATE TABLE 'lexicon_fts_config'(k PRIMARY KEY, v) WITHOUT ROWID;
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
    , latin_source TEXT, source_id INTEGER REFERENCES dataset_sources(id), bio_vi TEXT);
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
            created_at TEXT DEFAULT CURRENT_TIMESTAMP, name_vi_auto TEXT, name_vi_final TEXT, approved_by TEXT, approved_at TEXT,
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
            );
CREATE TABLE 'places_search_fts_data'(id INTEGER PRIMARY KEY, block BLOB);
CREATE TABLE 'places_search_fts_idx'(segid, term, pgno, PRIMARY KEY(segid, term)) WITHOUT ROWID;
CREATE TABLE 'places_search_fts_docsize'(id INTEGER PRIMARY KEY, sz BLOB);
CREATE TABLE 'places_search_fts_config'(k PRIMARY KEY, v) WITHOUT ROWID;
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
  , content_html TEXT);
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
        , vi_text TEXT, translation_draft INTEGER NOT NULL DEFAULT 0, raw_zh_hash TEXT, passage_id_ref TEXT, segmentation_method TEXT DEFAULT 'punctuation');
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
CREATE TABLE cbeta_ref_passages (
    ref_code      TEXT PRIMARY KEY,
    sigla         TEXT NOT NULL,
    juan          INTEGER,
    page          TEXT,
    line_start    INTEGER,
    line_end      INTEGER,
    han_text      TEXT NOT NULL,
    vi_summary    TEXT,
    created_at    TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at    TEXT DEFAULT CURRENT_TIMESTAMP
, vi_summary_raw TEXT, vi_summary_clean TEXT);
CREATE TABLE lineage_chronology (
    id TEXT PRIMARY KEY,
    title TEXT,
    title_zh TEXT,
    century_start INTEGER,
    century_end INTEGER,
    dynasty TEXT,
    time_from INTEGER,
    time_to INTEGER,
    category TEXT,
    data_source TEXT DEFAULT 'DILA',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_lc_century ON lineage_chronology(century_start, century_end);
CREATE INDEX idx_lc_dynasty ON lineage_chronology(dynasty);
CREATE INDEX idx_lc_time ON lineage_chronology(time_from, time_to);
CREATE INDEX idx_lc_cat ON lineage_chronology(category);
CREATE INDEX idx_pd_name_zh ON places_dila(name_zh);
CREATE INDEX idx_people_id ON people(id);
CREATE TABLE missing_hanzi (
                char TEXT PRIMARY KEY,
                count INTEGER DEFAULT 1,
                last_seen_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
CREATE TABLE cbeta_ref_explanations (
    ref               TEXT NOT NULL,
    place_id          TEXT NOT NULL,
    place_han         TEXT NOT NULL,
    han_sentence      TEXT NOT NULL,
    explanation_vi    TEXT NOT NULL,
    created_at        TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at        TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ref, place_id)
);
CREATE TABLE cbeta_catalog_vn (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  text_code        TEXT,
  sigla            TEXT,
  title_vi         TEXT,
  juans            INTEGER DEFAULT 1,
  dynasty_vi       TEXT,
  translator_vi    TEXT,
  note_vi          TEXT,
  q_number         TEXT,
  page             TEXT,
  sh_number        TEXT,
  title_zh         TEXT,
  juans_zh         INTEGER DEFAULT 1,
  dynasty_zh       TEXT,
  author_zh        TEXT,
  source_name       TEXT,
  source_full_title TEXT,
  source_url        TEXT,
  license_name      TEXT,
  license_url       TEXT,
  source_note       TEXT,
  created_at        TEXT DEFAULT CURRENT_TIMESTAMP
, cbeta_ref TEXT, series TEXT DEFAULT 'T');
CREATE TABLE catalog_mapping (
  id          INTEGER PRIMARY KEY,
  place_id    TEXT NOT NULL,
  catalog_id  TEXT NOT NULL,
  source      TEXT,
  status      TEXT NOT NULL DEFAULT 'pending',
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_by  TEXT,
  reviewed_by TEXT,
  note        TEXT
, quality_flag TEXT DEFAULT NULL);
CREATE INDEX idx_catalog_mapping_place ON catalog_mapping(place_id, status);
CREATE TABLE monk_dict (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dila_id TEXT UNIQUE,
    han_name TEXT NOT NULL,
    vn_name TEXT,
    pinyin TEXT,
    alt_han_names TEXT DEFAULT '[]',
    vn_aliases TEXT DEFAULT '[]',
    era TEXT,
    dynasty TEXT,
    role_main TEXT,
    role_alt TEXT,
    biography TEXT,
    refs TEXT DEFAULT '[]',
    source TEXT DEFAULT 'DILA',
    status TEXT DEFAULT 'pending',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE monk_name_index (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    monk_id INTEGER NOT NULL REFERENCES monk_dict(id),
    lang TEXT NOT NULL CHECK(lang IN ('zh','vi','pinyin','san','other')),
    name_form TEXT NOT NULL,
    name_type TEXT NOT NULL CHECK(name_type IN ('official','alias','primary','alternative')),
    normalized TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_monk_name_index_monk ON monk_name_index(monk_id);
CREATE INDEX idx_monk_name_index_norm ON monk_name_index(normalized);
CREATE INDEX idx_monk_dict_status ON monk_dict(status);
CREATE INDEX idx_monk_dict_dila ON monk_dict(dila_id);
CREATE INDEX idx_cbeta_catalog_vn_ref ON cbeta_catalog_vn(cbeta_ref);
CREATE VIEW v_place_cbeta_vn AS
SELECT
    m.place_id,
    m.catalog_id,
    m.status,
    m.source,
    m.note,
    c.id           AS catalog_pk,
    c.cbeta_ref,
    c.title_vi,
    c.title_zh,
    c.sh_number,
    c.q_number,
    c.page,
    c.sigla,
    c.dynasty_vi,
    c.translator_vi,
    c.source_name,
    c.license_name
FROM catalog_mapping m
LEFT JOIN cbeta_catalog_vn c ON m.catalog_id = c.sh_number
WHERE m.status = 'approved';
CREATE TABLE name_normalization (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    han TEXT,
    raw TEXT,
    vn TEXT,
    type TEXT,
    note TEXT
);
CREATE TABLE cbeta_catalog_place_fuzzy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            place_id TEXT NOT NULL,
            name_zh TEXT NOT NULL,
            catalog_id TEXT NOT NULL,
            title_zh TEXT,
            title_vi TEXT,
            score INTEGER NOT NULL,
            rank INTEGER NOT NULL DEFAULT 1, low_confidence INTEGER DEFAULT 0,
            UNIQUE(place_id, catalog_id)
        );
CREATE INDEX idx_fuzzy_place ON cbeta_catalog_place_fuzzy(place_id);
CREATE INDEX idx_fuzzy_catalog ON cbeta_catalog_place_fuzzy(catalog_id);
CREATE INDEX idx_fuzzy_score ON cbeta_catalog_place_fuzzy(score);
CREATE TABLE vn_person_authority (
    id TEXT PRIMARY KEY,
    ttl_filename TEXT NOT NULL,
    name_vi TEXT,
    name_zh TEXT,
    dharma_title TEXT,
    dharma_lineage TEXT,
    generation_order INTEGER,
    is_lineage_founder INTEGER DEFAULT 0,
    gender TEXT,
    biographical_note_vi TEXT,
    birth_year INTEGER,
    death_year INTEGER,
    appellations TEXT,
    dila_id TEXT,
    status TEXT DEFAULT 'pending',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE vn_person_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    target_id TEXT,
    target_label_vi TEXT,
    ttl_filename TEXT,
    UNIQUE(person_id, relation_type, target_id)
);
CREATE TABLE vn_person_places (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id TEXT NOT NULL,
    place_id TEXT NOT NULL,
    place_label_vi TEXT,
    place_type TEXT,
    ttl_filename TEXT,
    UNIQUE(person_id, place_id)
);
CREATE TABLE vn_person_works (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id TEXT NOT NULL,
    work_id TEXT NOT NULL,
    work_title_vi TEXT,
    ttl_filename TEXT,
    UNIQUE(person_id, work_id)
);
CREATE TABLE vn_person_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_id TEXT,
    event_label_vi TEXT,
    event_year INTEGER,
    ttl_filename TEXT, source TEXT, confidence REAL, source_ref TEXT,
    UNIQUE(person_id, event_type, event_id)
);
CREATE INDEX idx_vn_person_rel_person ON vn_person_relations(person_id);
CREATE INDEX idx_vn_person_places_person ON vn_person_places(person_id);
CREATE INDEX idx_vn_person_works_person ON vn_person_works(person_id);
CREATE INDEX idx_vn_person_events_person ON vn_person_events(person_id);
CREATE VIRTUAL TABLE places_pending_fts USING fts5(id, name_vi, name_zh, name_vi_norm);
CREATE TABLE 'places_pending_fts_data'(id INTEGER PRIMARY KEY, block BLOB);
CREATE TABLE 'places_pending_fts_idx'(segid, term, pgno, PRIMARY KEY(segid, term)) WITHOUT ROWID;
CREATE TABLE 'places_pending_fts_content'(id INTEGER PRIMARY KEY, c0, c1, c2, c3);
CREATE TABLE 'places_pending_fts_docsize'(id INTEGER PRIMARY KEY, sz BLOB);
CREATE TABLE 'places_pending_fts_config'(k PRIMARY KEY, v) WITHOUT ROWID;
CREATE TABLE entity_hub (
    entity_id INTEGER PRIMARY KEY,
    entity_type TEXT NOT NULL,
    canonical_label TEXT,
    status TEXT DEFAULT 'active',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE entity_source_ids (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id INTEGER NOT NULL,
    source TEXT NOT NULL,
    source_entity_id TEXT NOT NULL,
    source_label TEXT,
    match_status TEXT DEFAULT 'candidate',
    confidence REAL,
    verified INTEGER DEFAULT 0,
    verification_note TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(source, source_entity_id)
);
CREATE TABLE data_sources (
    source_id INTEGER PRIMARY KEY,
    source_code TEXT UNIQUE NOT NULL,
    source_name TEXT NOT NULL,
    source_type TEXT,
    authority_scope TEXT,
    license_note TEXT,
    active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
, source_version TEXT DEFAULT '1.0', adapter_version TEXT, schema_version TEXT, last_sync TEXT, last_verified TEXT, enabled INTEGER DEFAULT 1, health TEXT DEFAULT 'unknown', capabilities TEXT DEFAULT '[]', base_url TEXT, attribution_required INTEGER DEFAULT 0, redistribution_allowed INTEGER DEFAULT 1, commercial_use INTEGER DEFAULT 1, api_terms TEXT, license_spdx TEXT, software_license TEXT, data_license TEXT, corpus_license TEXT, documentation_license TEXT, image_license TEXT, derivative_allowed INTEGER DEFAULT 0, sharealike_required INTEGER DEFAULT 0, noncommercial INTEGER DEFAULT 0, noderivatives INTEGER DEFAULT 0, license_verified INTEGER DEFAULT 0, license_verified_at TEXT, license_verified_by TEXT, license_url TEXT, terms_status TEXT DEFAULT 'under_review', version_policy TEXT DEFAULT 'not_available', integration_mode TEXT DEFAULT 'BLOCKED', data_license_status TEXT DEFAULT 'UNKNOWN', data_redistribution INTEGER DEFAULT 0, data_commercial INTEGER DEFAULT 0, legal_status TEXT DEFAULT 'AUDITING', freeze_reason TEXT, legal_status_at_ingest TEXT, repository_url TEXT, updated_at TEXT, canonical_name TEXT, short_name TEXT, organization TEXT, origin_url TEXT, data_url TEXT, api_url TEXT, authority_roles TEXT);
CREATE TABLE entity_claims (
    claim_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id INTEGER NOT NULL,
    source_id INTEGER NOT NULL,
    claim_type TEXT NOT NULL,
    subject TEXT,
    predicate TEXT,
    object_text TEXT,
    source_record_id TEXT,
    source_reference TEXT,
    authority_role TEXT DEFAULT 'supporting',
    confidence REAL,
    verification_status TEXT DEFAULT 'unverified',
    editor_note TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
, source_url TEXT, retrieved_at TEXT, assertion_level TEXT, reviewed_by TEXT, reviewed_at TEXT, license TEXT, usage_level TEXT, source_version TEXT);
CREATE TABLE entity_summary (
    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id INTEGER NOT NULL,
    summary_vi TEXT,
    summary_source INTEGER,
    summary_status TEXT DEFAULT 'unverified',
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE VIEW v_entity_places AS
SELECT 
    e.entity_id,
    e.canonical_label,
    e.entity_type,
    e.status,
    GROUP_CONCAT(DISTINCT es.source) AS source_list,
    GROUP_CONCAT(DISTINCT ecs.claim_type) AS claims,
    p.id AS place_id, p.name_zh, p.name_vi, p.gps_lat, p.gps_long
FROM entity_hub e
LEFT JOIN entity_source_ids es ON es.entity_id = e.entity_id
LEFT JOIN entity_claims ecs ON ecs.entity_id = e.entity_id
LEFT JOIN places p ON p.id = CAST(REPLACE(e.entity_id, 'PL', '') AS INTEGER)
GROUP BY e.entity_id;
CREATE TABLE marcus_people_link (
    person_id TEXT PRIMARY KEY,
    marcus_node_id TEXT NOT NULL,
    match_confidence REAL DEFAULT 1.0,
    match_method TEXT DEFAULT 'exact_id',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_marcus_people_link_node ON marcus_people_link(marcus_node_id);
CREATE TABLE custom_hanviet_override (
                char TEXT PRIMARY KEY,
                hanviet TEXT NOT NULL,
                added_by TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
CREATE TABLE place_person_link (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            place_id TEXT NOT NULL,
            person_id TEXT NOT NULL,
            relation_type TEXT,
            source_name TEXT NOT NULL,
            source_url TEXT NOT NULL,
            note TEXT,
            added_by TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
CREATE TABLE geo_cross_ref (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dila_id TEXT NOT NULL,
        wikidata_qid TEXT,
        chgis_svid TEXT,
        tgaz_id TEXT,
        bgis_id TEXT,
        marcus_ref TEXT,
        notes TEXT,
        confidence TEXT DEFAULT "verified",
        mapped_by TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP, bdrc_id TEXT, enrich_status TEXT DEFAULT 'none', enrich_source_qid TEXT, enrich_lat REAL, enrich_lon REAL, enrich_elevation_m INTEGER, enrich_checked_at TEXT, wikidata_lat REAL, wikidata_lon REAL, elevation_m INTEGER, elevation_source TEXT,
        UNIQUE(dila_id)
    );
CREATE TABLE place_timeline_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    dila_id     TEXT NOT NULL,
    event_type  TEXT NOT NULL DEFAULT 'founding',
    year        INTEGER,
    year_end    INTEGER,
    label_zh    TEXT,
    label_vi    TEXT,
    source      TEXT NOT NULL,
    source_ref  TEXT,
    confidence  TEXT DEFAULT 'verified',
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_pte_dila ON place_timeline_events(dila_id);
CREATE INDEX idx_pte_source ON place_timeline_events(source);
CREATE TABLE term_glossaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term TEXT NOT NULL,
            term_zh TEXT,
            term_vi TEXT,
            person_id TEXT,
            work_cbeta_id TEXT,
            source TEXT NOT NULL DEFAULT 'marcus',
            confidence TEXT DEFAULT 'exact_id',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
CREATE INDEX idx_tg_person ON term_glossaries(person_id);
CREATE INDEX idx_tg_term ON term_glossaries(term);
CREATE INDEX idx_geo_cross_ref_bdrc ON geo_cross_ref(bdrc_id);
CREATE TABLE geo_cross_ref_candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dila_id TEXT NOT NULL,
            wikidata_qid TEXT NOT NULL,
            match_method TEXT,          -- 'coordinate_1km', 'name_zh', etc.
            match_distance_km REAL,
            wd_label_zh TEXT,
            wd_label_vi TEXT,
            wd_inception INTEGER,
            wd_dissolved INTEGER,
            wd_country TEXT,
            admin_review TEXT DEFAULT 'pending',  -- pending/approved/rejected
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(dila_id, wikidata_qid)
        );
CREATE INDEX idx_cand_dila ON geo_cross_ref_candidates(dila_id)
    ;
CREATE TABLE eight_four_thousand (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    toh INTEGER UNIQUE,
    title_en TEXT,
    title_vi TEXT,
    title_zh TEXT,
    publication_date TEXT,
    num_pages INTEGER,
    canon_section TEXT,  -- e.g., "Kangyur", "Tengyur"
    pdf_url TEXT,
    epub_url TEXT,
    description TEXT,
    translator TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE eight_four_thousand_place_map (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    toh INTEGER,
    dila_id INTEGER,
    confidence REAL DEFAULT 0.0,  -- 0.0-1.0, how confident this mapping is
    source TEXT DEFAULT 'cbeta_catalog',  -- how we found the mapping
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(toh, dila_id),
    FOREIGN KEY (dila_id) REFERENCES places_dila(id)
);
CREATE INDEX idx_eft_toh ON eight_four_thousand(toh);
CREATE INDEX idx_eft_map_dila ON eight_four_thousand_place_map(dila_id);
CREATE INDEX idx_eft_map_toh ON eight_four_thousand_place_map(toh);
CREATE TABLE vri_tipitaka_catalog (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nikaya TEXT NOT NULL,
        nikaya_name TEXT,
        vagga TEXT,
        sutta_id TEXT NOT NULL,
        title_pali TEXT,
        title_vi TEXT,
        title_zh TEXT,
        reference TEXT,
        file_path TEXT,
        word_count INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    );
CREATE TABLE vri_place_mapping (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vri_sutta_id INTEGER NOT NULL,
        dila_id TEXT NOT NULL,
        place_name_pali TEXT,
        place_name_zh TEXT,
        context TEXT,
        confidence REAL DEFAULT 0.8,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        UNIQUE(vri_sutta_id, dila_id),
        FOREIGN KEY (vri_sutta_id) REFERENCES vri_tipitaka_catalog(id),
        FOREIGN KEY (dila_id) REFERENCES places_dila(id)
    );
CREATE TABLE vri_cached_texts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sutta_id INTEGER NOT NULL,
        paragraph_id TEXT,
        text_pali TEXT,
        text_vi TEXT,
        text_zh TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    );
CREATE TABLE kanripo_catalog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text_id TEXT UNIQUE NOT NULL,
    title_zh TEXT NOT NULL,
    title_vi TEXT,
    title_en TEXT,
    category TEXT NOT NULL,
    subcategory TEXT,
    taisho_number TEXT,
    dila_ref TEXT,
    cbeta_ref TEXT,
    language TEXT DEFAULT 'zh',
    license TEXT DEFAULT 'CC BY-SA 4.0',
    github_repo TEXT,
    xml_path TEXT,
    catalog_created DATE,
    notes TEXT
);
CREATE TABLE kanripo_place_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text_id TEXT NOT NULL,
    dila_id TEXT NOT NULL,
    confidence REAL DEFAULT 0.8,
    map_type TEXT,
    map_note TEXT,
    UNIQUE(text_id, dila_id)
);
CREATE TABLE kanripo_text_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text_id TEXT NOT NULL,
    paragraph_id TEXT,
    text_pali TEXT,
    text_zh TEXT,
    text_vi TEXT,
    word_count INTEGER DEFAULT 0,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_url TEXT,
    UNIQUE(text_id)
);
CREATE TABLE zqlocal_content (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id     TEXT NOT NULL,
            content_type  TEXT NOT NULL,
            content       TEXT NOT NULL,
            confidence    REAL DEFAULT 0.8,
            generated_by  TEXT,
            reviewed_by   TEXT,
            reviewed_at   TEXT,
            created_at    TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(entity_id, content_type)
        );
CREATE INDEX idx_zqlocal_entity ON zqlocal_content(entity_id);
CREATE TABLE pali_place_ref (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    dila_id      TEXT NOT NULL,
    name_zh      TEXT NOT NULL,
    name_vi      TEXT,
    name_pali    TEXT,
    name_skt     TEXT,
    sc_uid       TEXT NOT NULL,
    sc_uids_more TEXT,
    sc_note_vi   TEXT,
    verified_by  TEXT DEFAULT 'ZQ',
    confidence   REAL DEFAULT 0.9,
    needs_review INTEGER DEFAULT 0,
    created_at   TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(dila_id, sc_uid)
);
CREATE TABLE toh_cbeta_crossref (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    toh           INTEGER NOT NULL,
    cbeta_sigla   TEXT NOT NULL,
    title_zh      TEXT,
    title_vi      TEXT,
    title_en      TEXT,
    title_tib     TEXT,
    url_84000     TEXT,
    canon_section TEXT,
    note_vi       TEXT,
    confidence    REAL DEFAULT 0.95,
    needs_review  INTEGER DEFAULT 0,
    source_ref    TEXT,
    created_at    TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(toh, cbeta_sigla)
);
CREATE TABLE sat_crossref (
            cbeta_sigla  TEXT PRIMARY KEY,
            sat_url      TEXT,
            has_unique   INTEGER DEFAULT 0,
            created_at   TEXT DEFAULT CURRENT_TIMESTAMP
        );
CREATE TABLE place_person_bibl (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    place_id        TEXT NOT NULL,
    person_id       TEXT,
    person_name_raw TEXT,
    cbeta_ref       TEXT,
    source_book     TEXT,
    mention_keyword TEXT,
    confidence      REAL DEFAULT 1.0,
    created_at      TEXT DEFAULT (datetime('now')),
    UNIQUE(place_id, cbeta_ref)
);
CREATE INDEX idx_ppb_place  ON place_person_bibl(place_id);
CREATE INDEX idx_ppb_person ON place_person_bibl(person_id);
CREATE TABLE person_origin_link (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id TEXT NOT NULL,
        place_id TEXT NOT NULL,
        confidence REAL DEFAULT 1.0,
        created_at TEXT DEFAULT (datetime('now')),
        UNIQUE(person_id, place_id)
    );
CREATE INDEX idx_pol_place ON person_origin_link(place_id);
CREATE INDEX idx_pol_person ON person_origin_link(person_id);
CREATE TABLE place_person_bio_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        place_id TEXT NOT NULL,
        person_id TEXT NOT NULL,
        matched_variant TEXT,
        is_direct INTEGER DEFAULT 0,
        relation_hint TEXT,
        bio_snippet TEXT,
        confidence REAL DEFAULT 0.6,
        indexed_at TEXT DEFAULT (datetime('now')),
        UNIQUE(place_id, person_id)
    );
CREATE INDEX idx_ppbc_place ON place_person_bio_cache(place_id);
CREATE INDEX idx_ppbc_person ON place_person_bio_cache(person_id);
CREATE TABLE person_name_correction (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id TEXT NOT NULL,
        name_zh TEXT,
        current_vi TEXT,
        proposed_vi TEXT,
        source TEXT DEFAULT 'lexicon',
        is_clear INTEGER DEFAULT 0,
        clear_reason TEXT,
        dict_frequency INTEGER DEFAULT 0,
        status TEXT DEFAULT 'pending',
        reviewed_by TEXT,
        reviewed_at TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        UNIQUE(person_id, proposed_vi)
    );
CREATE INDEX idx_pnc_person ON person_name_correction(person_id);
CREATE INDEX idx_pnc_status ON person_name_correction(status);
CREATE TABLE legacy_canon_mapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_id TEXT NOT NULL,
            canon_source TEXT NOT NULL,
            title TEXT,
            author_dila_id TEXT,
            year INTEGER,
            volume TEXT,
            page TEXT,
            source_legacy TEXT DEFAULT 'buddhist_db.sqlite',
            imported_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(work_id, canon_source)
        );
CREATE TABLE cbeta_place_mention_stats (
            place_id   TEXT PRIMARY KEY,
            mention_count INTEGER,
            top_texts  TEXT,
            vi_name    TEXT,
            last_updated TEXT
        );
CREATE INDEX idx_pnc_source ON person_name_correction(source);
CREATE INDEX idx_lex_term ON lexicon(term);
CREATE INDEX idx_lex_entity_type ON lexicon(entity_type);
CREATE TABLE person_bio_vi_draft (
        person_id    TEXT PRIMARY KEY,
        name_vi      TEXT,
        name_zh      TEXT,
        bio_vi_draft TEXT,
        source_lex_id INTEGER,
        source_term  TEXT,
        source_name  TEXT,
        match_type   TEXT DEFAULT 'exact_term',
        char_count   INTEGER,
        admin_approved INTEGER DEFAULT 0,
        admin_note   TEXT,
        created_at   TEXT DEFAULT (datetime('now')),
        updated_at   TEXT DEFAULT (datetime('now'))
    );
CREATE INDEX idx_pbvd_approved ON person_bio_vi_draft(admin_approved);
CREATE INDEX idx_pbvd_name ON person_bio_vi_draft(name_vi);
CREATE TABLE place_desc_vi_draft (
            place_id       TEXT PRIMARY KEY,
            name_vi        TEXT,
            name_zh        TEXT,
            note_category  TEXT,
            desc_vi_draft  TEXT,
            desc_source    TEXT,
            char_count     INTEGER,
            admin_approved INTEGER DEFAULT 0,
            admin_note     TEXT,
            created_at     TEXT,
            updated_at     TEXT
        );
CREATE TABLE glossary_term (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term TEXT NOT NULL,
            language TEXT NOT NULL,
            definition TEXT,
            full_text TEXT,
            source_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(term, language)
        );
CREATE INDEX idx_glossary_term ON glossary_term(term);
CREATE INDEX idx_glossary_lang ON glossary_term(language);
CREATE TABLE event_text_link (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type   TEXT,
            entity_type  TEXT,
            entity_id    TEXT,
            related_id   TEXT,
            related_name TEXT,
            cbeta_ref    TEXT,
            source_book  TEXT,
            source_table TEXT,
            source_ref   TEXT,
            source_id    INTEGER,
            year         INTEGER,
            confidence   REAL,
            created_at   TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source_table, source_id)
        );
CREATE INDEX idx_etl_entity ON event_text_link(entity_type, entity_id);
CREATE INDEX idx_etl_cbetaref ON event_text_link(cbeta_ref);
CREATE TABLE era_year_jdn (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL UNIQUE,
            era_name TEXT,
            jdn INTEGER,
            year_bce INTEGER,
            source TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
CREATE INDEX idx_era_year_jdn_year ON era_year_jdn(year);
CREATE INDEX idx_era_year_jdn_jdn ON era_year_jdn(jdn);
CREATE TABLE canonical_decision (
        entity_ref TEXT PRIMARY KEY,           -- 'PL…' (DILA ID)
        canonical_name_vi TEXT,
        source_id INTEGER,                     -- REFERENCES dataset_sources(id)
        authority_rank TEXT,
        confidence REAL,
        verification_status TEXT,               -- pending|needs_review|verified|canonical
        decision_note TEXT,
        evidence_citations TEXT,                -- JSON list
        editor TEXT,
        decided_at TEXT,
        updated_at TEXT
    );
CREATE TABLE en_audit_log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_ref TEXT,
        action TEXT,                            -- create|update|approve
        field_name TEXT,
        old_value TEXT,
        new_value TEXT,
        evidence_sources TEXT,                  -- JSON
        authority_rank TEXT,
        editor TEXT,
        verification_status TEXT,
        created_at TEXT
    );
CREATE INDEX idx_en_audit_log_entity ON en_audit_log (entity_ref);
CREATE INDEX idx_canonical_decision_status ON canonical_decision (verification_status);
CREATE TABLE source_authority (
        source_code TEXT PRIMARY KEY,      -- 'DILA','CBETA','SAT','MARCUS','CHGIS','BDRC','FoJin','Wikidata','ZQLOCAL'
        source_id INTEGER,                 -- FK tham chiếu data_sources.source_id (NULL nếu chưa có trong data_sources)
        authority_score INTEGER,           -- điểm xếp hạng nguồn (cao = đáng tin hơn)
        precedence_order INTEGER,          -- thứ tự ưu tiên khi điểm bằng nhau (nhỏ = ưu tiên hơn)
        implemented INTEGER DEFAULT 0,     -- 1 = nguồn đã có dữ liệu trong DB; 0 = chưa implement (khớp T70 governance)
        note TEXT
    );
CREATE TABLE conflict_pending (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_ref TEXT,                   -- 'PL…' (DILA ID dạng raw trong DB)
        field TEXT,                        -- 'name_vi' | 'gps_lat' | 'gps_long' | ...
        value_a TEXT, value_b TEXT,        -- 2 giá trị xung đột
        source_a TEXT, source_b TEXT,      -- tên nguồn tương ứng
        authority_a INTEGER, authority_b INTEGER,  -- điểm nguồn tương ứng
        status TEXT DEFAULT 'pending',     -- pending|resolved|accepted
        resolved_choice TEXT,
        resolved_by TEXT,
        resolved_at TEXT
    , needs_review INTEGER DEFAULT 0, notes TEXT);
CREATE INDEX idx_conflict_pending_entity ON conflict_pending (entity_ref, status);
CREATE INDEX idx_conflict_pending_status ON conflict_pending (status);
CREATE TABLE marcus_reference_backup_t51f(
  node_id TEXT,
  label TEXT,
  label_vi TEXT,
  birth_year INT,
  death_year INT,
  created_at TEXT,
  label_vi_confidence REAL,
  label_vi_source TEXT
);
CREATE INDEX ix_entity_claims_entity_source ON entity_claims(entity_id, source_id, claim_type);
CREATE INDEX ix_entity_source_ids_entity ON entity_source_ids(entity_id);
CREATE TABLE translation_rules (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_code   TEXT UNIQUE NOT NULL,
            rule_type   TEXT,
            description TEXT,
            rule_text   TEXT NOT NULL,
            is_active   INTEGER DEFAULT 1,
            priority    INTEGER DEFAULT 100,
            created_by  TEXT DEFAULT 'system',
            created_at  TEXT DEFAULT (datetime('now')),
            updated_at  TEXT DEFAULT (datetime('now'))
        , status TEXT DEFAULT 'active', suggested_by TEXT, ruleset_id TEXT DEFAULT '', ruleset_version TEXT DEFAULT '', is_canonical INTEGER NOT NULL DEFAULT 0);
CREATE TABLE translation_cache (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            source_hash     TEXT NOT NULL,
            source_type     TEXT DEFAULT 'person_bio',
            entity_id       TEXT,
            source_text     TEXT NOT NULL,
            translated_text TEXT NOT NULL,
            model_id        TEXT,
            rules_version   TEXT,
            status          TEXT DEFAULT 'auto',
            report_count    INTEGER DEFAULT 0,
            approved_by     TEXT,
            approved_at     TEXT,
            created_at      TEXT DEFAULT (datetime('now')),
            updated_at      TEXT DEFAULT (datetime('now')),
            UNIQUE(source_hash, source_type)
        );
CREATE INDEX idx_tc_entity ON translation_cache(entity_id, source_type);
CREATE INDEX idx_tc_rules_ver ON translation_cache(rules_version, status);
CREATE INDEX idx_tc_status ON translation_cache(status);
CREATE TABLE web_enrichment_cache (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  entity_id    TEXT NOT NULL,
  entity_type  TEXT NOT NULL DEFAULT 'place',
  source_url   TEXT,
  source_name  TEXT,
  raw_content  TEXT,
  summary_vi   TEXT NOT NULL,
  fetched_by   TEXT DEFAULT 'user',
  status       TEXT DEFAULT 'auto',
  report_count INTEGER DEFAULT 0,
  created_at   TEXT DEFAULT (datetime('now')),
  expires_at   TEXT
);
CREATE INDEX idx_web_enrich_entity ON web_enrichment_cache(entity_id, entity_type, status);
CREATE TABLE nexus_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    passage_id TEXT,
    person_dila_id TEXT,
    place_dila_id TEXT,
    event_year INTEGER,
    event_label TEXT,
    source_book TEXT,
    confidence REAL DEFAULT 0.7,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_ne_place  ON nexus_events(place_dila_id);
CREATE INDEX idx_ne_person ON nexus_events(person_dila_id);
CREATE INDEX idx_ne_conf   ON nexus_events(confidence);
CREATE TABLE text_passages (
    passage_id          TEXT PRIMARY KEY,
    work_id             TEXT NOT NULL,
    source_system       TEXT NOT NULL DEFAULT 'CBETA',
    canonical_ref       TEXT,
    juan                TEXT,
    sequence_no         INTEGER,
    original_zh         TEXT NOT NULL,
    raw_zh_hash         TEXT NOT NULL,
    segmentation_method TEXT,
    tei_anchor_start    TEXT,
    tei_anchor_end      TEXT,
    source_url          TEXT,
    source_version      TEXT,
    import_run_id       TEXT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
, source_status TEXT DEFAULT 'ok', loc_ref TEXT, canonical_start_anchor TEXT, canonical_end_anchor TEXT, legacy_passage_id INTEGER, updated_at DATETIME);
CREATE TABLE translation_segments (
    translation_id      TEXT PRIMARY KEY,
    work_id             TEXT NOT NULL,
    language            TEXT DEFAULT 'vi',
    translation_text    TEXT NOT NULL,
    translator_type     TEXT,
    model_name          TEXT,
    prompt_version      TEXT,
    source_passage_ids  TEXT,
    translation_status  TEXT DEFAULT 'draft',
    review_status       TEXT DEFAULT 'pending',
    reviewer            TEXT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP
, passage_id TEXT DEFAULT '', provider TEXT, source_original_hash TEXT, quality_status TEXT DEFAULT 'unreviewed', created_by_job_id TEXT, revision_no INTEGER DEFAULT 1, supersedes_translation_id TEXT, ruleset_id TEXT DEFAULT '');
CREATE TABLE passage_translation_alignment (
    alignment_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    passage_id          TEXT NOT NULL,
    translation_id      TEXT NOT NULL,
    alignment_type      TEXT NOT NULL,
    source_start_offset INTEGER,
    source_end_offset   INTEGER,
    confidence          REAL DEFAULT 0.5,
    alignment_method    TEXT,
    review_status       TEXT DEFAULT 'pending',
    reviewer            TEXT,
    note                TEXT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME,
    FOREIGN KEY (passage_id) REFERENCES text_passages(passage_id),
    FOREIGN KEY (translation_id) REFERENCES translation_segments(translation_id)
);
CREATE TABLE translation_jobs (
        job_id               TEXT PRIMARY KEY,
        work_id              TEXT NOT NULL,
        requested_scope      TEXT NOT NULL,
        requested_by_user_id TEXT,
        provider             TEXT NOT NULL,
        model_name           TEXT NOT NULL,
        status               TEXT NOT NULL DEFAULT 'queued',
        next_passage_sequence INTEGER,
        total_passages       INTEGER NOT NULL,
        completed_passages   INTEGER NOT NULL DEFAULT 0,
        failed_passages      INTEGER NOT NULL DEFAULT 0,
        started_at           DATETIME,
        finished_at          DATETIME,
        last_error           TEXT,
        created_at           DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at           DATETIME DEFAULT CURRENT_TIMESTAMP
    );
CREATE TABLE translation_job_items (
        job_item_id        TEXT PRIMARY KEY,
        job_id             TEXT NOT NULL,
        passage_id         TEXT NOT NULL,
        sequence_no        INTEGER NOT NULL,
        status             TEXT NOT NULL DEFAULT 'queued',
        attempt_count      INTEGER NOT NULL DEFAULT 0,
        provider_request_id TEXT,
        raw_response_path  TEXT,
        error_message      TEXT,
        started_at         DATETIME,
        completed_at       DATETIME, created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (job_id) REFERENCES translation_jobs(job_id),
        UNIQUE (job_id, passage_id)
    );
CREATE INDEX idx_tp_work_seq ON text_passages(work_id, sequence_no);
CREATE INDEX idx_ts_passage ON translation_segments(passage_id);
CREATE INDEX idx_ts_status ON translation_segments(translation_status, quality_status);
CREATE INDEX idx_align_passage ON passage_translation_alignment(passage_id);
CREATE INDEX idx_tjobs_work ON translation_jobs(work_id, status);
CREATE INDEX idx_tjitems_job ON translation_job_items(job_id);
CREATE TABLE t95_import_runs (
        run_id TEXT PRIMARY KEY,
        work_id TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        units_inserted INTEGER DEFAULT 0,
        units_skipped INTEGER DEFAULT 0,
        units_replaced INTEGER DEFAULT 0
    );
CREATE TABLE time_mentions (
            mention_id   TEXT PRIMARY KEY,
            source_table TEXT NOT NULL,
            source_record_id TEXT NOT NULL,
            raw_time_zh  TEXT NOT NULL,
            normalized_start INTEGER,
            normalized_end   INTEGER,
            precision    TEXT NOT NULL
                CHECK(precision IN ('exact_day','month','year','year_range',
                                    'reign_era','dynasty_period','relative','unknown')),
            time_authority_id TEXT,
            extraction_method TEXT NOT NULL
                CHECK(extraction_method IN ('regex_rule','authority_mapping',
                                            'editorial','imported')),
            confidence   REAL DEFAULT 0.8,
            created_at   TEXT DEFAULT (datetime('now'))
        );
CREATE TABLE events (
            event_id     TEXT PRIMARY KEY,
            event_type   TEXT,
            title_zh     TEXT,
            title_vi     TEXT,
            start_year   INTEGER,
            end_year     INTEGER,
            precision    TEXT,
            extraction_method TEXT,
            review_status TEXT NOT NULL DEFAULT 'candidate'
                CHECK(review_status IN ('candidate','reviewed','disputed','rejected')),
            confidence   REAL DEFAULT 0.5,
            notes        TEXT,
            created_at   TEXT DEFAULT (datetime('now')),
            updated_at   TEXT DEFAULT (datetime('now'))
        );
CREATE TABLE event_entities (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id    TEXT NOT NULL,
            entity_id   TEXT NOT NULL,
            entity_type TEXT NOT NULL
                CHECK(entity_type IN ('place','person','text','institution')),
            role        TEXT,
            UNIQUE(event_id, entity_id, entity_type)
        );
CREATE TABLE event_evidence (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id     TEXT NOT NULL,
            time_mention_id TEXT,
            source_record TEXT NOT NULL,
            source_table  TEXT,
            exact_span    TEXT,
            source_ref    TEXT,
            evidence_type TEXT,
            reviewer_note TEXT,
            created_at    TEXT DEFAULT (datetime('now'))
        );
CREATE INDEX idx_time_mentions_src ON time_mentions(source_table, source_record_id);
CREATE INDEX idx_events_status ON events(review_status);
CREATE INDEX idx_event_entities_event ON event_entities(event_id);
CREATE INDEX idx_event_evidence_event ON event_evidence(event_id);
CREATE TABLE person_display_names (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id             TEXT    NOT NULL,
            dila_person_id        TEXT,
            locale                TEXT    NOT NULL DEFAULT 'vi',
            display_name_vi       TEXT    NOT NULL,
            display_name_zh       TEXT,
            authority_name_vi     TEXT,
            authority_name_zh     TEXT,
            appellation_vi        TEXT,
            appellation_zh        TEXT,
            style_type            TEXT    DEFAULT 'formal',
            is_preferred          INTEGER DEFAULT 1,
            verification_status   TEXT    NOT NULL,
            source_type           TEXT    DEFAULT 'ttl',
            source_file           TEXT    NOT NULL,
            source_subject_uri    TEXT,
            source_predicate      TEXT    DEFAULT 'rdfs:label',
            source_ref            TEXT,
            mapping_method        TEXT,
            mapping_evidence      TEXT,
            import_run_id         TEXT,
            created_at            TEXT    DEFAULT CURRENT_TIMESTAMP,
            updated_at            TEXT    DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (person_id, locale, source_file)
        );
CREATE TABLE pali_cbeta_map (
                    sh TEXT PRIMARY KEY,
                    pali_title TEXT,
                    sc_uid TEXT,
                    pts_sutta TEXT,
                    note TEXT
                );
CREATE TABLE doctrine_concept (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name_vi TEXT,
                    name_zh TEXT,
                    pth_uri TEXT UNIQUE,
                    definition_vi TEXT,
                    related_entities TEXT,
                    assertion_level TEXT DEFAULT 'THEMATIC',
                    updated_at TEXT
                );
CREATE TABLE entity_claims_audit (
    claim_id    INTEGER PRIMARY KEY,
    entity_id   TEXT,
    claim_type  TEXT,
    predicate   TEXT,
    object_text TEXT,
    source_id   TEXT,
    audit_id    TEXT NOT NULL,
    built_at    TEXT
);
CREATE TABLE events_provenance (
    event_id         TEXT PRIMARY KEY,
    source_id        TEXT,
    source_reference TEXT,
    source_citation  TEXT,
    attribution_note TEXT,
    created_at       TEXT
);
CREATE VIEW v_assertions AS
SELECT
    c.claim_id, c.entity_id, c.claim_type, c.predicate, c.object_text,
    c.source_id, c.source_reference, c.source_url, c.retrieved_at,
    c.confidence, c.verification_status, c.assertion_level, c.reviewed_by, c.reviewed_at,
    a.audit_id,
    sa.authority_score, sa.precedence_order,
    ds.source_name
FROM entity_claims c
LEFT JOIN entity_claims_audit a ON a.claim_id = c.claim_id
LEFT JOIN source_authority sa ON sa.source_code = c.source_id
LEFT JOIN data_sources ds ON ds.source_code = c.source_id;
CREATE VIEW v_events_full AS
SELECT
    e.event_id, e.event_type, e.title_zh, e.title_vi,
    e.start_year, e.end_year, e.precision,
    e.extraction_method, e.review_status, e.confidence, e.notes,
    p.source_id, p.source_reference, p.source_citation, p.attribution_note
FROM events e
LEFT JOIN events_provenance p ON p.event_id = e.event_id;
CREATE TABLE glossary_vi (
    glossary_id        INTEGER PRIMARY KEY,
    term               TEXT NOT NULL,
    language           TEXT NOT NULL,
    term_vi            TEXT,
    match_type         TEXT,
    match_source       TEXT,
    vi_confidence      REAL,
    source_glossary_id INTEGER,
    created_at         TEXT
);
CREATE TABLE data_gap_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type TEXT NOT NULL,          -- person | place | work | entity
        entity_id TEXT NOT NULL,
        entity_name TEXT,
        gap_type TEXT NOT NULL,             -- thieu_noidung | thieu_nguon | loi_hien_thi | khac
        note_plain TEXT,
        source_hint TEXT,
        status TEXT DEFAULT 'new',          -- new | ack | closed
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(entity_type, entity_id, gap_type)
    );
CREATE TABLE user_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_id TEXT,
        entity_type TEXT,
        feedback_type TEXT NOT NULL,        -- sai_du_lieu | thieu_nguon | loi_hien_thi | khac
        note_plain TEXT NOT NULL,
        user_level TEXT,
        status TEXT DEFAULT 'new',          -- new | ack | closed
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
CREATE INDEX idx_data_gap_status ON data_gap_requests (status);
CREATE INDEX idx_user_feedback_status ON user_feedback (status);
CREATE TABLE text_reading_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text_id TEXT NOT NULL,           -- short sigla chuẩn hoá ('T2076','X1524',...)
        session TEXT NOT NULL DEFAULT 'anon',
        ts TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(session, text_id)
    );
CREATE INDEX idx_t55c_text ON text_reading_log (text_id);
CREATE INDEX idx_t55c_session ON text_reading_log (session);
CREATE TABLE cbeta_topic_clusters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text_id TEXT NOT NULL,
            topic TEXT NOT NULL,
            score REAL NOT NULL DEFAULT 1.0
        );
CREATE INDEX idx_cbeta_topic_clusters_text ON cbeta_topic_clusters(text_id);
CREATE INDEX idx_cbeta_topic_clusters_topic ON cbeta_topic_clusters(topic);
CREATE TABLE translation_exemplar (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      zh TEXT NOT NULL,
      vi TEXT NOT NULL,
      source_lexicon TEXT DEFAULT '',
      source_label TEXT DEFAULT 'tu_dien_danh_tac',
      length_zh INTEGER DEFAULT 0,
      is_active INTEGER NOT NULL DEFAULT 0,
      created_at TEXT DEFAULT (datetime('now'))
    );
CREATE INDEX idx_exemplar_active ON translation_exemplar(is_active, length_zh);
CREATE TABLE translation_glossary (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      term_zh TEXT NOT NULL,
      term_vi TEXT NOT NULL,
      source_label TEXT DEFAULT 'tu_dien_danh_tac',
      is_locked INTEGER NOT NULL DEFAULT 1,
      created_at TEXT DEFAULT (datetime('now')),
      UNIQUE (term_zh, term_vi)
    );
CREATE TABLE translation_error_report (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      cache_id INTEGER DEFAULT NULL,
      source_type TEXT DEFAULT '',
      entity_id TEXT DEFAULT '',
      translated_text_snapshot TEXT DEFAULT '',
      error_type TEXT DEFAULT 'style',
      note TEXT DEFAULT '',
      page_url TEXT DEFAULT '',
      status TEXT NOT NULL DEFAULT 'pending',
      created_at TEXT DEFAULT (datetime('now'))
    );
CREATE INDEX idx_error_report_status ON translation_error_report(status, created_at);
CREATE TABLE lineage_edge_assertions (
    id                  INTEGER PRIMARY KEY,
    edge_key            TEXT NOT NULL,
    subject_person_id   TEXT NOT NULL,
    relation_type       TEXT NOT NULL,
    object_person_id    TEXT NOT NULL,
    source_code         TEXT NOT NULL,
    raw_relation_type   TEXT,
    ref                 TEXT,
    citation_tier       TEXT,
    mapping_verified    INTEGER DEFAULT 0,
    trust_level         TEXT NOT NULL,
    status              TEXT DEFAULT 'active',
    created_at          TEXT
);
CREATE INDEX idx_lea_subject ON lineage_edge_assertions(subject_person_id);
CREATE INDEX idx_lea_object  ON lineage_edge_assertions(object_person_id);
CREATE INDEX idx_lea_edgekey ON lineage_edge_assertions(edge_key);
CREATE TABLE source_staging (
    source_code        TEXT NOT NULL,
    source_version     TEXT NOT NULL,
    row_type           TEXT NOT NULL,      -- 'master' | 'transmission'
    source_entity_id   TEXT NOT NULL,      -- zen slug / transmission id
    primary_name       TEXT,
    teacher_slug       TEXT,
    student_slug       TEXT,
    school_slug        TEXT,
    tier               TEXT,
    human_review_needed INTEGER DEFAULT 0,
    extra_json         TEXT,
    ingested_at        TEXT,
    PRIMARY KEY (source_code, row_type, source_entity_id)
);
CREATE INDEX idx_ss_type ON source_staging(row_type);
CREATE INDEX idx_ss_school ON source_staging(school_slug);
CREATE TABLE zenlineage_review (
    source_entity_id   TEXT PRIMARY KEY,
    status             TEXT NOT NULL,
    dila_person_id     TEXT,
    entity_hub_id      INTEGER,
    confidence         REAL,
    editor             TEXT,
    note               TEXT,
    created_at         TEXT,
    updated_at         TEXT
);
CREATE TABLE lineage_edge_consensus (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_id           TEXT NOT NULL,
    disciple_id          TEXT NOT NULL,
    relation_type        TEXT NOT NULL DEFAULT 'dharma_transmission',
    dila_asserted        INTEGER NOT NULL DEFAULT 0,
    marcus_asserted      INTEGER NOT NULL DEFAULT 0,
    ttl_asserted         INTEGER NOT NULL DEFAULT 0,
    lineage_asserted     INTEGER NOT NULL DEFAULT 0,
    agreeing_source_count INTEGER NOT NULL DEFAULT 0,
    opposite_source_count INTEGER NOT NULL DEFAULT 0,
    consensus_status     TEXT NOT NULL DEFAULT 'single_source',
    is_default_visible   INTEGER NOT NULL DEFAULT 0,
    human_override       TEXT DEFAULT NULL,
    source_badge         TEXT DEFAULT NULL,
    migration_marker     TEXT DEFAULT 'T158_MIGRATION',
    created_at           TEXT DEFAULT (datetime('now')),
    updated_at           TEXT DEFAULT (datetime('now')),
    UNIQUE(teacher_id, disciple_id, relation_type)
);
CREATE INDEX idx_lec_teacher ON lineage_edge_consensus(teacher_id, is_default_visible);
CREATE INDEX idx_lec_disciple ON lineage_edge_consensus(disciple_id, is_default_visible);
CREATE INDEX idx_lec_visible ON lineage_edge_consensus(is_default_visible, relation_type);
CREATE TABLE translation_rulesets (
        ruleset_id          TEXT PRIMARY KEY,
        ruleset_version     TEXT NOT NULL,
        description         TEXT NOT NULL,
        is_canonical        INTEGER NOT NULL DEFAULT 0,
        created_by          TEXT DEFAULT 'system',
        created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (ruleset_version)
    );
CREATE TABLE translation_ruleset_rules (
        ruleset_id      TEXT NOT NULL,
        rule_code       TEXT NOT NULL,
        priority        INTEGER NOT NULL DEFAULT 0,
        is_active       INTEGER NOT NULL DEFAULT 1,
        created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (ruleset_id, rule_code),
        FOREIGN KEY (ruleset_id) REFERENCES translation_rulesets(ruleset_id),
        FOREIGN KEY (rule_code) REFERENCES translation_rules(rule_code)
    );
CREATE INDEX idx_ts_ruleset ON translation_segments(ruleset_id);
CREATE INDEX idx_ruleset_rules ON translation_ruleset_rules(ruleset_id, rule_code);
CREATE INDEX idx_rules_ruleset ON translation_rules(ruleset_id, ruleset_version);
CREATE TABLE dharma_lineage_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id TEXT NOT NULL,
            student_id TEXT NOT NULL,
            source TEXT DEFAULT 'DILA',
            confidence REAL DEFAULT 1.0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(teacher_id, student_id, source)
        );
CREATE TABLE dharma_lineage_ttl_vn (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id TEXT NOT NULL,
            student_id TEXT NOT NULL,
            source TEXT DEFAULT 'TTL',
            confidence REAL DEFAULT 0.95,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(teacher_id, student_id, source)
        );
CREATE TABLE ai_person_name (
                dila_id     TEXT PRIMARY KEY,
                name_vi_ai  TEXT,
                model       TEXT DEFAULT 'gemini-3.8-flash',
                created_at  TEXT DEFAULT CURRENT_TIMESTAMP
            );
CREATE TABLE lineage_primary_teacher (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_id       TEXT NOT NULL,
    disciple_id      TEXT NOT NULL,
    is_primary       INTEGER NOT NULL DEFAULT 0,
    evidence_source  TEXT,
    confidence       TEXT DEFAULT 'low',
    marcus_subtype   TEXT DEFAULT 'unknown',
    marcus_kw        TEXT,
    ttl_confirmed    INTEGER DEFAULT 0,
    conflict         INTEGER DEFAULT 0,
    notes            TEXT,
    created_at       TEXT DEFAULT (datetime('now')),
    UNIQUE(teacher_id, disciple_id)
);
CREATE INDEX idx_lpt_teacher ON lineage_primary_teacher(teacher_id);
CREATE INDEX idx_lpt_disciple ON lineage_primary_teacher(disciple_id);
CREATE INDEX idx_lpt_primary ON lineage_primary_teacher(is_primary);
CREATE INDEX idx_lpt_evidence ON lineage_primary_teacher(evidence_source);
CREATE TABLE hanviet_char_map (
  char           TEXT PRIMARY KEY,
  reading        TEXT NOT NULL,
  source         TEXT NOT NULL,
  is_polyphonic  INTEGER NOT NULL DEFAULT 0,
  candidates     TEXT
);
CREATE INDEX idx_hvcm_source ON hanviet_char_map(source);
CREATE INDEX idx_hvcm_poly  ON hanviet_char_map(is_polyphonic);
CREATE TABLE hanviet_exception_list (
  char_sequence TEXT PRIMARY KEY,
  note          TEXT,
  added_by      TEXT
);
CREATE TABLE person_hanviet_debug (
  person_id                  TEXT PRIMARY KEY,  -- = people.id (A000001…)
  han_name_raw               TEXT,
  han_viet_legacy            TEXT,
  han_viet_charwise          TEXT,
  han_char_count             INTEGER,
  han_viet_syllable_count    INTEGER,
  unknown_characters         TEXT,
  han_viet_validation_status TEXT,
  han_viet_validation_reason TEXT,
  legacy_match_status        TEXT,
  is_transliteration         INTEGER DEFAULT 0,
  dict_version               TEXT,
  updated_at                 TIMESTAMP
);
CREATE INDEX idx_hvd_status ON person_hanviet_debug(han_viet_validation_status);
CREATE INDEX idx_hvd_legacy ON person_hanviet_debug(legacy_match_status);
CREATE INDEX idx_hvd_translit ON person_hanviet_debug(is_transliteration);
CREATE TABLE ttl_v2_source_import_runs (
 id TEXT PRIMARY KEY, status TEXT NOT NULL, started_at TEXT NOT NULL,
 finished_at TEXT, metadata_json TEXT NOT NULL, counts_json TEXT
);
CREATE UNIQUE INDEX idx_ttl_v2_one_source_import ON ttl_v2_source_import_runs(status) WHERE status='in_progress';
CREATE TABLE ttl_v2_source_records (
 id INTEGER PRIMARY KEY, kind TEXT NOT NULL, record_id TEXT NOT NULL,
 source_group TEXT NOT NULL, filename TEXT NOT NULL, version TEXT NOT NULL,
 sha256 TEXT NOT NULL, raw_text TEXT NOT NULL, parse_status TEXT NOT NULL,
 main_slug TEXT, metadata_json TEXT NOT NULL, import_run_id TEXT NOT NULL,
 created_at TEXT NOT NULL,
 UNIQUE(kind,record_id,source_group,version,sha256)
);
CREATE INDEX idx_ttl_v2_source_lookup ON ttl_v2_source_records(kind,record_id,source_group,id);
CREATE INDEX idx_ttl_v2_source_slug ON ttl_v2_source_records(kind,main_slug,source_group,id);
