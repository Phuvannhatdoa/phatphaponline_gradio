#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETL T109 (Zero-ALTER · Zero-RAM · Lean) — Provenance Compliance & Conflict Workflow
=====================================================================================
Làm TRƯỚC khi bật API admin conflict (app.py) để bảng dẫn xuất có dữ liệu.

Tính chất (tuân điều lệnh check07)
----------------------------------
- ZERO-ALTER: KHÔNG DROP/ALTER bảng base (entity_claims/events/...). Chỉ:
    1) CREATE TABLE  dẫn xuất  `entity_claims_audit`  (audit_id SHA-256 content-hash, M5 SCHEMA_DESIGN)
    2) CREATE TABLE  dẫn xuất  `events_provenance`    (provenance events 3,530 từ places_dila — 100% match verified)
    3) CREATE VIEW   `v_assertions`   — Adapter (SQL View): entity_claims + audit_id + authority (CoreClaim|Provenance|Review)
    4) CREATE VIEW   `v_events_full`  — events LEFT JOIN events_provenance
- IDEMPOTENT: INSERT OR REPLACE theo PK (claim_id/event_id); audit_id deterministic → chạy lại ra cùng giá trị.
- REVERSIBLE: `--revert` chỉ DROP 2 view + 2 bảng dẫn xuất (0 động dữ liệu base).
- BACKUP: backup nhất quán bằng SQLite backup API (Zero-RAM) → data/backups/lineage_t109_<ts>.db khi `--apply`.
- Zero-RAM: duyệt entity_claims theo chunk (fetchmany) — KHÔNG bao giờ load 447,885 row cùng lúc.

Cách dùng
---------
    python scripts/etl_t109_provenance.py --dry-run   # chỉ in kế hoạch + số liệu dự kiến
    python scripts/etl_t109_provenance.py --apply     # tạo bảng/view + backfill (có backup)
    python scripts/etl_t109_provenance.py --revert    # DROP 2 view + 2 bảng dẫn xuất (giữ backup)

content-hash (M5)
-----------------
    audit_id = SHA-256(entity_id | claim_type | predicate | object_text | source_id)
    — entity_id là hub int (100001) → str(); None → ''
"""
import argparse
import hashlib
import os
import sqlite3
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'lineage.db')
BACKUP_DIR = os.path.join(BASE_DIR, 'data', 'backups')

TS = time.strftime('%Y%m%d_%H%M%S')
BUILT_AT = time.strftime('%Y-%m-%dT%H:%M:%S')


def connect():
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.row_factory = sqlite3.Row
    return conn


def has_table(conn, name):
    return conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def has_view(conn, name):
    return conn.execute(
        "SELECT name FROM sqlite_master WHERE type='view' AND name=?", (name,)).fetchone() is not None


def make_backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    dst = os.path.join(BACKUP_DIR, f'lineage_t109_{TS}.db')
    if not os.path.exists(DB_PATH):
        print(f'[backup] KHÔNG tìm thấy {DB_PATH} — bỏ qua backup')
        return None
    src = sqlite3.connect(DB_PATH, timeout=60)
    try:
        dest = sqlite3.connect(dst, timeout=60)
        try:
            src.backup(dest)  # streaming pages, Zero-RAM, nhất quán (an toàn cả khi bật)
        finally:
            dest.close()
    finally:
        src.close()
    print(f'[backup] Đã backup → {dst} ({os.path.getsize(dst):,} bytes)')
    return dst


def audit_id_of(entity_id, claim_type, predicate, object_text, source_id):
    parts = [
        '' if entity_id is None else str(entity_id),
        '' if claim_type is None else str(claim_type),
        '' if predicate is None else str(predicate),
        '' if object_text is None else str(object_text),
        '' if source_id is None else str(source_id),
    ]
    return hashlib.sha256('|'.join(parts).encode('utf-8')).hexdigest()


# ── bước 1: entity_claims_audit ──────────────────────────────────────────────
CREATE_ENTITY_CLAIMS_AUDIT = """
CREATE TABLE IF NOT EXISTS entity_claims_audit (
    claim_id    INTEGER PRIMARY KEY,
    entity_id   TEXT,
    claim_type  TEXT,
    predicate   TEXT,
    object_text TEXT,
    source_id   TEXT,
    audit_id    TEXT NOT NULL,
    built_at    TEXT
)
"""


def build_entity_claims_audit(conn, dry_run):
    total_claims = conn.execute('SELECT COUNT(*) FROM entity_claims').fetchone()[0]
    if has_table(conn, 'entity_claims_audit'):
        now = conn.execute('SELECT COUNT(*) FROM entity_claims_audit').fetchone()[0]
        print(f'[entity_claims_audit] bảng ĐÃ có ({now:,}/{total_claims:,}) — re-backfill idempotent.')
    elif dry_run:
        print(f'[entity_claims_audit][dry-run] Sẽ CREATE TABLE + backfill {total_claims:,} audit_id')
        return
    else:
        conn.execute(CREATE_ENTITY_CLAIMS_AUDIT)
        print('[entity_claims_audit] Đã CREATE TABLE.')

    if dry_run:
        print(f'[entity_claims_audit][dry-run] Sẽ INSERT OR REPLACE {total_claims:,} row (audit_id = SHA-256 content-hash).')
        return

    cur = conn.execute(
        'SELECT claim_id, entity_id, claim_type, predicate, object_text, source_id '
        'FROM entity_claims ORDER BY claim_id')
    batch = []
    done = 0
    while True:
        rows = cur.fetchmany(5000)
        if not rows:
            break
        for r in rows:
            batch.append((
                r['claim_id'],
                None if r['entity_id'] is None else str(r['entity_id']),
                r['claim_type'], r['predicate'], r['object_text'], r['source_id'],
                audit_id_of(r['entity_id'], r['claim_type'], r['predicate'], r['object_text'], r['source_id']),
                BUILT_AT,
            ))
        conn.executemany(
            "INSERT INTO entity_claims_audit "
            "(claim_id, entity_id, claim_type, predicate, object_text, source_id, audit_id, built_at) "
            "VALUES (?,?,?,?,?,?,?,?) "
            "ON CONFLICT(claim_id) DO UPDATE SET audit_id=excluded.audit_id, built_at=excluded.built_at",
            batch)
        conn.commit()
        done += len(batch)
        batch = []
        if done % 100000 < 5000:
            print(f'[entity_claims_audit] ... {done:,}/{total_claims:,}')
    print(f'[entity_claims_audit] backfill xong {done:,}/{total_claims:,}.')


# ── bước 2: events_provenance ────────────────────────────────────────────────
CREATE_EVENTS_PROVENANCE = """
CREATE TABLE IF NOT EXISTS events_provenance (
    event_id         TEXT PRIMARY KEY,
    source_id        TEXT,
    source_reference TEXT,
    source_citation  TEXT,
    attribution_note TEXT,
    created_at       TEXT
)
"""

EVENTS_BACKFILL_SQL = """
INSERT OR REPLACE INTO events_provenance
(event_id, source_id, source_reference, source_citation, attribution_note, created_at)
SELECT
    e.event_id,
    'DILA' AS source_id,
    p.id     AS source_reference,
    COALESCE(NULLIF(p.note, ''), NULLIF(p.listbibl, '')) AS source_citation,
    'T109: event candidate ' || COALESCE(e.event_type,'') || ' (imported) — gán nguồn DILA từ places_dila; chờ thẩm định' AS attribution_note,
    :ts AS created_at
FROM events e
JOIN places_dila p ON p.id = SUBSTR(e.event_id, 13)
"""


def build_events_provenance(conn, dry_run):
    n_events = conn.execute('SELECT COUNT(*) FROM events').fetchone()[0]
    n_match = conn.execute(
        "SELECT COUNT(*) FROM events e JOIN places_dila p ON p.id = SUBSTR(e.event_id, 13)"
    ).fetchone()[0]
    print(f'[events_provenance] events={n_events:,} · match places_dila={n_match:,} ({100.0*n_match/max(n_events,1):.1f}%)')
    if has_table(conn, 'events_provenance'):
        now = conn.execute('SELECT COUNT(*) FROM events_provenance').fetchone()[0]
        print(f'[events_provenance] bảng ĐÃ có ({now:,}) — re-backfill idempotent.')
    elif dry_run:
        print(f'[events_provenance][dry-run] Sẽ CREATE TABLE + backfill {n_match:,} row.')
        return
    else:
        conn.execute(CREATE_EVENTS_PROVENANCE)
        print('[events_provenance] Đã CREATE TABLE.')

    if dry_run:
        return
    cur = conn.execute(EVENTS_BACKFILL_SQL, {'ts': BUILT_AT})
    conn.commit()
    print(f'[events_provenance] backfill xong {conn.execute("SELECT COUNT(*) FROM events_provenance").fetchone()[0]:,}.')


# ── bước 3: Adapter Views ────────────────────────────────────────────────────
CREATE_V_ASSERTIONS = """
CREATE VIEW IF NOT EXISTS v_assertions AS
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
LEFT JOIN data_sources ds ON ds.source_code = c.source_id
"""

CREATE_V_EVENTS_FULL = """
CREATE VIEW IF NOT EXISTS v_events_full AS
SELECT
    e.event_id, e.event_type, e.title_zh, e.title_vi,
    e.start_year, e.end_year, e.precision,
    e.extraction_method, e.review_status, e.confidence, e.notes,
    p.source_id, p.source_reference, p.source_citation, p.attribution_note
FROM events e
LEFT JOIN events_provenance p ON p.event_id = e.event_id
"""


def build_views(conn, dry_run):
    for v, sql in (('v_assertions', CREATE_V_ASSERTIONS), ('v_events_full', CREATE_V_EVENTS_FULL)):
        if has_view(conn, v):
            print(f'[{v}] view ĐÃ có.')
        elif dry_run:
            print(f'[{v}][dry-run] Sẽ CREATE VIEW.')
        else:
            conn.execute(sql)
            conn.commit()
            print(f'[{v}] Đã CREATE VIEW.')


# ── revert ───────────────────────────────────────────────────────────────────
def revert(conn, dry_run):
    dropped = []
    for v in ('v_assertions', 'v_events_full'):
        if has_view(conn, v):
            if dry_run:
                print(f'[revert][dry-run] Sẽ DROP VIEW {v}')
            else:
                conn.execute(f'DROP VIEW IF EXISTS {v}')
                dropped.append(f'view {v}')
    for t in ('entity_claims_audit', 'events_provenance'):
        if has_table(conn, t):
            if dry_run:
                print(f'[revert][dry-run] Sẽ DROP TABLE {t}')
            else:
                conn.execute(f'DROP TABLE IF EXISTS {t}')
                dropped.append(f'table {t}')
    if not dry_run and dropped:
        conn.commit()
    if dry_run:
        print('[revert][dry-run] Xong (mô phỏng).')
    else:
        print(f'[revert] Đã xoá: {", ".join(dropped) if dropped else "không có gì"}. 0 động dữ liệu base.')


# ── verify ───────────────────────────────────────────────────────────────────
def verify(conn):
    print('\n[verify] Kiểm tra sau ETL:')
    n_claims = conn.execute('SELECT COUNT(*) FROM entity_claims').fetchone()[0]
    n_events = conn.execute('SELECT COUNT(*) FROM events').fetchone()[0]
    if has_table(conn, 'entity_claims_audit'):
        n_audit = conn.execute('SELECT COUNT(*) FROM entity_claims_audit').fetchone()[0]
        n_null = conn.execute('SELECT COUNT(*) FROM entity_claims_audit WHERE audit_id IS NULL OR audit_id = ""').fetchone()[0]
        print(f'  entity_claims_audit: {n_audit:,}/{n_claims:,} claims · audit_id NULL/empty = {n_null:,}')
    else:
        print('  entity_claims_audit: KHÔNG tồn tại')
    if has_table(conn, 'events_provenance'):
        n_ep = conn.execute('SELECT COUNT(*) FROM events_provenance').fetchone()[0]
        n_missing = n_events - n_ep
        print(f'  events_provenance: {n_ep:,}/{n_events:,} events · còn thiếu provenance = {n_missing:,}')
    else:
        print('  events_provenance: KHÔNG tồn tại')
    for v in ('v_assertions', 'v_events_full'):
        print(f'  view {v}: {"✓ tồn tại" if has_view(conn, v) else "KHÔNG tồn tại"}')
    if has_view(conn, 'v_assertions'):
        r = conn.execute('SELECT entity_id, predicate, object_text, source_id, audit_id FROM v_assertions WHERE audit_id IS NOT NULL LIMIT 2').fetchall()
        print('  v_assertions sample:', [dict(x) for x in r])
    print(f'  base: entity_claims={n_claims:,} (không đổi) · events={n_events:,} (không đổi) · places_dila={conn.execute("SELECT COUNT(*) FROM places_dila").fetchone()[0]:,}')


def main():
    ap = argparse.ArgumentParser(description='T109 — Provenance Compliance (Zero-ALTER · Zero-RAM · Lean)')
    ap.add_argument('--dry-run', action='store_true', help='chỉ in kế hoạch + số liệu, không đổi DB')
    ap.add_argument('--apply', action='store_true', help='CREATE bảng dẫn xuất + view + backfill (có backup)')
    ap.add_argument('--revert', action='store_true', help='DROP 2 view + 2 bảng dẫn xuất')
    args = ap.parse_args()

    dry_run = args.dry_run
    revert_mode = args.revert
    apply_mode = args.apply or (not dry_run and not revert_mode)

    print(f'[ETL] T109 — Provenance Compliance (Zero-ALTER · Zero-RAM · Lean) — DB: {DB_PATH}')
    print(f'[ETL] mode: {"revert" if revert_mode else ("dry-run" if dry_run else "apply")}')

    if not os.path.exists(DB_PATH):
        print(f'[ETL] LỖI: không tìm thấy DB {DB_PATH}')
        sys.exit(1)

    if not dry_run and not revert_mode:
        make_backup()

    conn = connect()
    try:
        if revert_mode:
            revert(conn, dry_run)
        else:
            build_entity_claims_audit(conn, dry_run)
            build_events_provenance(conn, dry_run)
            build_views(conn, dry_run)
            if dry_run:
                print('\n[ETL][dry-run] KHÔNG đổi gì — mô phỏng xong.')
        verify(conn)
    finally:
        conn.close()


if __name__ == '__main__':
    main()