"""
build_integration_layer.py
Xây dựng integration layer DILA: ENTITY, PASSAGE, PASSAGE_ENTITY tables.

Chạy:
    python scripts/build_integration_layer.py

Có thể chạy lại nhiều lần (idempotent).
Phase 1: chỉ dùng CBETA text T51n2076 (đã import sẵn).
"""

import sqlite3
import os
import sys
import time
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINEAGE_DB = os.path.join(BASE_DIR, 'data', 'lineage.db')
CBETA_DB = os.path.join(BASE_DIR, 'data', 'cbeta', 'cbeta.db')


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")


def get_conn(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def create_tables(conn):
    log("Creating tables if not exist...")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS entity (
            entity_id   TEXT PRIMARY KEY,
            entity_type TEXT NOT NULL CHECK(entity_type IN ('PERSON','PLACE','TEXT')),
            dila_id     TEXT NOT NULL,
            alias_vi    TEXT,
            alias_zh    TEXT,
            cbeta_occ   TEXT,
            marcus_id   TEXT,
            extra_alias TEXT
        );

        CREATE TABLE IF NOT EXISTS passage (
            passage_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            source      TEXT NOT NULL DEFAULT 'CBETA',
            text_id     TEXT NOT NULL,
            loc_ref     TEXT NOT NULL DEFAULT '',
            raw_text    TEXT NOT NULL,
            norm_text   TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_passage_text_id ON passage(text_id);

        CREATE TABLE IF NOT EXISTS passage_entity (
            passage_id INTEGER NOT NULL,
            entity_id  TEXT NOT NULL,
            PRIMARY KEY (passage_id, entity_id)
        );
        CREATE INDEX IF NOT EXISTS idx_pe_entity_id ON passage_entity(entity_id);
    """)
    conn.commit()


def populate_entity_places(conn):
    log("Populating ENTITY (PLACE) from places_pending...")
    count = conn.execute("""
        INSERT OR IGNORE INTO entity (entity_id, entity_type, dila_id, alias_vi, alias_zh)
        SELECT id, 'PLACE', id, name_vi, name_zh
        FROM places_pending
        WHERE id LIKE 'PL%' AND id IS NOT NULL AND id != ''
    """).rowcount
    conn.commit()
    log(f"  → {count} PLACE entities inserted")


def populate_entity_people(conn):
    log("Populating ENTITY (PERSON) from people...")
    count = conn.execute("""
        INSERT OR IGNORE INTO entity (entity_id, entity_type, dila_id, alias_vi, alias_zh)
        SELECT id, 'PERSON', id, name_vi, name_zh
        FROM people
        WHERE id IS NOT NULL AND id != ''
    """).rowcount
    conn.commit()
    log(f"  → {count} PERSON entities inserted")


def populate_entity_texts(conn):
    log("Populating ENTITY (TEXT) from cbeta_texts...")
    cconn = get_conn(CBETA_DB)
    rows = cconn.execute("SELECT sigla, title_zh FROM cbeta_texts").fetchall()
    cconn.close()
    count = 0
    cur = conn.cursor()
    for row in rows:
        cur.execute(
            "INSERT OR IGNORE INTO entity (entity_id, entity_type, dila_id, alias_vi, alias_zh) VALUES (?, 'TEXT', ?, NULL, ?)",
            (row['sigla'], row['sigla'], row['title_zh'])
        )
        if cur.rowcount > 0:
            count += 1
    conn.commit()
    log(f"  → {count} TEXT entities inserted")


def populate_passages(conn):
    log("Populating PASSAGE from cbeta_content_index (ALL texts)...")
    cconn = get_conn(CBETA_DB)

    rows = cconn.execute("""
        SELECT ct.sigla, cci.juan, cci.page, cci.line_num, cci.content_zh, cci.id as cid
        FROM cbeta_content_index cci
        JOIN cbeta_texts ct ON cci.text_id = ct.id
        ORDER BY cci.id
    """).fetchall()
    cconn.close()

    total = len(rows)
    log(f"  Found {total} total rows in cbeta_content_index")

    cur = conn.cursor()
    # Truncate and re-insert to avoid duplicates
    cur.execute("DELETE FROM passage WHERE source='CBETA'")
    log(f"  Cleared {cur.rowcount} old passages")

    # Insert with explicit passage_id matching cbeta_content_index.id
    batch = []
    for r in rows:
        loc_ref = f"{r['juan']}-{r['page'] or ''}-{r['line_num'] or ''}"
        batch.append((r['cid'], r['sigla'], loc_ref, r['content_zh']))

    cur.executemany(
        "INSERT OR REPLACE INTO passage (passage_id, source, text_id, loc_ref, raw_text) VALUES (?, 'CBETA', ?, ?, ?)",
        batch
    )
    conn.commit()
    log(f"  → {len(batch)} passages inserted from {len(set(r[0] for r in batch))} texts")


def populate_passage_entity_text(conn):
    log("Populating PASSAGE_ENTITY for TEXT entities (direct match)...")
    # For each TEXT entity, link all passages with matching text_id
    texts = conn.execute("SELECT entity_id FROM entity WHERE entity_type='TEXT'").fetchall()
    cur = conn.cursor()
    total = 0
    for t in texts:
        eid = t['entity_id']
        cur.execute("""
            INSERT OR IGNORE INTO passage_entity (passage_id, entity_id)
            SELECT passage_id, ? FROM passage WHERE text_id = ?
        """, (eid, eid))
        total += cur.rowcount
    conn.commit()
    log(f"  → {total} TEXT passage-entity links")


def build_alias_index(conn):
    entities = conn.execute("""
        SELECT entity_id, alias_zh FROM entity
        WHERE entity_type IN ('PERSON', 'PLACE')
          AND alias_zh IS NOT NULL
          AND LENGTH(alias_zh) >= 2
    """).fetchall()

    index = {}
    for ent in entities:
        first = ent['alias_zh'][0]
        index.setdefault(first, []).append((ent['alias_zh'], ent['entity_id']))
    return index


def populate_passage_entity_matching(conn):
    """
    Name matching: dùng Python string search để tìm entity alias_zh
    trong passage raw_text.
    """
    log("Populating PASSAGE_ENTITY for PERSON/PLACE (matching ALL texts)...")

    # Clear all old passage_entity links
    conn.execute("DELETE FROM passage_entity")
    conn.commit()
    log("  Cleared all old passage_entity links")

    # Build reverse index by first char
    alias_index = build_alias_index(conn)
    total_entities = sum(len(v) for v in alias_index.values())
    log(f"  {total_entities} entities indexed by first char")

    # Load all passages
    passages = conn.execute(
        "SELECT passage_id, raw_text FROM passage WHERE source='CBETA' ORDER BY passage_id"
    ).fetchall()
    log(f"  {len(passages)} passages loaded")

    cur = conn.cursor()
    total_links = 0
    matched = 0

    for p in passages:
        pid = p['passage_id']
        text = p['raw_text']
        if not text:
            continue

        seen_chars = set(text)
        for ch in seen_chars:
            bucket = alias_index.get(ch)
            if not bucket:
                continue
            for alias, eid in bucket:
                if alias in text:
                    cur.execute(
                        "INSERT OR IGNORE INTO passage_entity (passage_id, entity_id) VALUES (?, ?)",
                        (pid, eid)
                    )
                    total_links += cur.rowcount
                    if cur.rowcount > 0:
                        matched += 1

        if pid % 1000 == 0:
            conn.commit()

    conn.commit()
    log(f"  → Total: {total_links} passage-entity links, at least {matched} new links added")
    log(f"  → {total_entities} entities in index")


def print_stats(conn):
    print()
    log("=" * 60)
    log("INTEGRATION LAYER - STATISTICS")
    log("=" * 60)

    rows = conn.execute("SELECT entity_type, COUNT(*) as cnt FROM entity GROUP BY entity_type ORDER BY entity_type").fetchall()
    for r in rows:
        log(f"  ENTITY {r['entity_type']:>8}: {r['cnt']:>8}")
    log(f"  ENTITY total:       {conn.execute('SELECT COUNT(*) FROM entity').fetchone()[0]:>8}")

    pcount = conn.execute("SELECT COUNT(*) FROM passage").fetchone()[0]
    log(f"  PASSAGE total:      {pcount:>8}")

    pecount = conn.execute("SELECT COUNT(*) FROM passage_entity").fetchone()[0]
    log(f"  PASSAGE_ENTITY:     {pecount:>8}")

    # Sample: show entity with most passages
    log("")
    log("  Top 5 entities by passage count:")
    top = conn.execute("""
        SELECT pe.entity_id, e.entity_type, e.alias_zh, e.alias_vi, COUNT(*) as cnt
        FROM passage_entity pe
        JOIN entity e ON pe.entity_id = e.entity_id
        GROUP BY pe.entity_id
        ORDER BY cnt DESC
        LIMIT 5
    """).fetchall()
    for r in top:
        log(f"    {r['entity_id']:>20} [{r['entity_type']:>6}] zh={r['alias_zh'] or '':<20} vi={r['alias_vi'] or '':<20} → {r['cnt']} passages")


def main():
    log("DILA Integration Layer - Build Script")
    log(f"lineage.db: {LINEAGE_DB}")
    log(f"cbeta.db:   {CBETA_DB}")
    print()

    conn = get_conn(LINEAGE_DB)

    create_tables(conn)

    populate_entity_places(conn)
    populate_entity_people(conn)
    populate_entity_texts(conn)

    populate_passages(conn)

    populate_passage_entity_text(conn)
    populate_passage_entity_matching(conn)

    print_stats(conn)

    conn.close()
    log("")
    log("✅ Integration layer build complete!")
    log("")


if __name__ == '__main__':
    main()
