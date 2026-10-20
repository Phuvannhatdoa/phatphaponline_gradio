#!/usr/bin/env python3
"""
T75 — Web Enrichment Cache
==========================
Tạo bảng web_enrichment_cache để lưu thông tin mới từ internet
(Wikipedia, Wikidata...) cho địa danh / thiền sư.

Idempotent. Chạy lại an toàn.
"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
DB_PATH = ROOT / 'data' / 'lineage.db'

DDL = """
CREATE TABLE IF NOT EXISTS web_enrichment_cache (
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
CREATE INDEX IF NOT EXISTS idx_web_enrich_entity ON web_enrichment_cache(entity_id, entity_type, status);
"""

def run():
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(DDL)
        conn.commit()
        # Stats
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'web_enrichment%'"
        ).fetchall()]
        count = conn.execute("SELECT COUNT(*) FROM web_enrichment_cache").fetchone()[0]
        print(f"[T75] Bảng: {tables}")
        print(f"[T75] Hiện có {count} enrichment rows")
        print("[T75] OK")
    finally:
        conn.close()

if __name__ == '__main__':
    run()
