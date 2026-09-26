-- CBETA Mentions Schema
-- Target: data/lineage.db (main DB, index/reference only)
-- Full content stored in separate cbeta.db

-- Place mentions in CBETA texts
CREATE TABLE IF NOT EXISTS cbeta_place_mentions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  cbeta_text_sigla TEXT NOT NULL,
  dila_place_id TEXT,
  place_name_zh TEXT NOT NULL,
  juan INTEGER,
  page TEXT,
  context_snippet TEXT
);

-- Person mentions in CBETA texts
CREATE TABLE IF NOT EXISTS cbeta_person_mentions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  cbeta_text_sigla TEXT NOT NULL,
  dila_person_id TEXT,
  person_name_zh TEXT NOT NULL,
  juan INTEGER,
  page TEXT,
  context_snippet TEXT
);

-- Indexes for fast lookup
CREATE INDEX IF NOT EXISTS idx_cbeta_place_dila ON cbeta_place_mentions(dila_place_id);
CREATE INDEX IF NOT EXISTS idx_cbeta_place_name ON cbeta_place_mentions(place_name_zh);
CREATE INDEX IF NOT EXISTS idx_cbeta_person_dila ON cbeta_person_mentions(dila_person_id);
CREATE INDEX IF NOT EXISTS idx_cbeta_person_name ON cbeta_person_mentions(person_name_zh);
CREATE INDEX IF NOT EXISTS idx_cbeta_place_sigla ON cbeta_place_mentions(cbeta_text_sigla);
CREATE INDEX IF NOT EXISTS idx_cbeta_person_sigla ON cbeta_person_mentions(cbeta_text_sigla);
