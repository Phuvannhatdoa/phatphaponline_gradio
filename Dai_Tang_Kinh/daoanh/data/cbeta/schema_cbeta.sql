-- CBETA Database Schema
-- Target: data/cbeta/cbeta.db (read-only, full content)
-- License: CBETA Non-commercial use only

-- Text metadata
CREATE TABLE IF NOT EXISTS cbeta_texts (
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

-- Full text content index
CREATE TABLE IF NOT EXISTS cbeta_content_index (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  text_id INTEGER NOT NULL,
  juan INTEGER NOT NULL,
  page TEXT,
  line_num INTEGER,
  content_zh TEXT,
  FOREIGN KEY (text_id) REFERENCES cbeta_texts(id) ON DELETE CASCADE
);

-- Full-text search (FTS5 standalone, triggers handle sync)
CREATE VIRTUAL TABLE IF NOT EXISTS cbeta_fts USING fts5(
  sigla UNINDEXED,
  title_zh,
  juan UNINDEXED,
  page UNINDEXED,
  content_zh,
  tokenize='unicode61'
);

-- FTS triggers
CREATE TRIGGER IF NOT EXISTS cbeta_content_ai AFTER INSERT ON cbeta_content_index BEGIN
  INSERT INTO cbeta_fts(rowid, sigla, title_zh, juan, page, content_zh)
  SELECT new.id, t.sigla, t.title_zh, new.juan, new.page, new.content_zh
  FROM cbeta_texts t WHERE t.id = new.text_id;
END;

CREATE TRIGGER IF NOT EXISTS cbeta_content_ad AFTER DELETE ON cbeta_content_index BEGIN
  DELETE FROM cbeta_fts WHERE rowid = old.id;
END;

-- Import checkpoint log
CREATE TABLE IF NOT EXISTS cbeta_import_log (
  xml_file_path TEXT PRIMARY KEY,
  imported_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  status TEXT DEFAULT 'success'
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_cbeta_texts_sigla ON cbeta_texts(sigla);
CREATE INDEX IF NOT EXISTS idx_cbeta_texts_canon ON cbeta_texts(canon);
CREATE INDEX IF NOT EXISTS idx_cbeta_content_text_juan ON cbeta_content_index(text_id, juan);
