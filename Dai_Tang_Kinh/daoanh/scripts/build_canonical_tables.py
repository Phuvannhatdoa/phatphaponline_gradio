#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_canonical_tables.py — T67a: tạo 2 bảng additive cho HITL Canonical Decision.

Bảng mới (chỉ THÊM, không sửa bảng nguồn — reversible bằng DROP):
  1. canonical_decision — 1 dòng / entity (trạng thái canonical hiện tại).
  2. en_audit_log       — append-only, bất biến (provenance: ai/khi nào/đổi gì/nguồn/trạng thái).

Idempotent: CREATE TABLE IF NOT EXISTS. An toàn chạy nhiều lần.
KHÔNG dùng wal_checkpoint/backup trong script (bài học T58) — backup riêng, server dừng hoặc via backup().
"""
import os
import sys
import sqlite3
import io

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'lineage.db')

SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS canonical_decision (
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
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS en_audit_log (
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
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_en_audit_log_entity ON en_audit_log (entity_ref)",
    "CREATE INDEX IF NOT EXISTS idx_canonical_decision_status ON canonical_decision (verification_status)",
]


def main():
    if not os.path.isfile(DB_PATH):
        print(f"[ERR] Không tìm thấy DB: {DB_PATH}")
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    try:
        for stmt in SCHEMA:
            conn.execute(stmt)
        conn.commit()
        # Verify
        for t in ('canonical_decision', 'en_audit_log'):
            n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info({t})")]
            print(f"  [OK] bảng {t}: rows={n} cols={cols}")
    finally:
        conn.close()
    print("[OK] T67a hoàn tất — 2 bảng đã sẵn sàng.")


if __name__ == '__main__':
    main()
