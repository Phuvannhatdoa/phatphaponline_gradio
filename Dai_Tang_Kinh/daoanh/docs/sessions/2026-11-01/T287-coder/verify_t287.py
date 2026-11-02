#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T287 — kiểm chứng nhánh LicenseGate + nhánh từ chối en_audit_log.

Chỉ dùng DB tạm trong %TEMP% — KHÔNG mở/ghi data/lineage.db thật.
Chạy: python -X utf8 docs/sessions/2026-11-01/T287-coder/verify_t287.py
"""
import importlib.util
import os
import sqlite3
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, ROOT)

from gate.license import LicenseGate  # noqa: E402

SCHEMA = """
CREATE TABLE data_sources (
    source_id INTEGER PRIMARY KEY,
    source_code TEXT,
    source_name TEXT,
    legal_status TEXT,
    data_license_status TEXT,
    integration_mode TEXT,
    legal_status_at_ingest TEXT,
    freeze_reason TEXT,
    data_redistribution INTEGER DEFAULT 0,
    data_commercial INTEGER DEFAULT 0
);
CREATE TABLE en_audit_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_ref TEXT, action TEXT, field_name TEXT, old_value TEXT, new_value TEXT,
    evidence_sources TEXT, authority_rank TEXT, editor TEXT,
    verification_status TEXT, created_at TEXT
);
CREATE TABLE entity_claims (
    claim_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id INTEGER NOT NULL, source_id INTEGER NOT NULL, claim_type TEXT NOT NULL,
    subject TEXT, predicate TEXT, object_text TEXT, source_record_id TEXT,
    source_reference TEXT, authority_role TEXT, confidence REAL, verification_status TEXT
);
"""


def make_db():
    fd, path = tempfile.mkstemp(prefix='t287_', suffix='.db')
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    conn.executemany(
        "INSERT INTO data_sources (source_id, source_code, legal_status, data_license_status,"
        " integration_mode) VALUES (?,?,?,?,?)",
        [
            (3, 'CBETA', 'ACTIVE', 'APPROVED', 'INGEST'),
            (4, 'MARCUS', 'ACTIVE', 'APPROVED', 'INGEST'),
            (99, 'BLOCKED_SRC', 'BLOCKED', 'BLOCKED', 'BLOCKED'),
        ])
    conn.executemany(
        "INSERT INTO entity_claims (entity_id, source_id, claim_type, source_reference)"
        " VALUES (?,?,?,?)",
        [(100001, 3, 'TEXT_EVIDENCE', 'T69:x'), (100002, 99, 'TEXT_EVIDENCE', 'T69:y')])
    conn.commit()
    conn.close()
    return path


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def audit_rows(db):
    conn = sqlite3.connect(db)
    try:
        return conn.execute(
            "SELECT log_id, entity_ref, action, field_name, new_value, evidence_sources,"
            " editor, verification_status FROM en_audit_log ORDER BY log_id").fetchall()
    finally:
        conn.close()


def check(name, cond, extra=''):
    print(('  PASS ' if cond else '  FAIL ') + name + (f'  [{extra}]' if extra else ''))
    return cond


def main():
    db = make_db()
    print(f'[temp db] {db}')
    ok = True

    wire = load(os.path.join(ROOT, 'scripts', 'wire_evidence_into_entity_claims.py'), 't287_wire')
    t109 = load(os.path.join(ROOT, 'scripts', 'etl_t109_provenance.py'), 't287_t109')
    wire._gate = LicenseGate(db_path=db)
    t109._gate = LicenseGate(db_path=db)

    print('\n[1] wire_evidence — nguồn hợp lệ (CBETA=3):')
    ok &= check('CBETA được phép', wire._gate_check(3, 'INGEST')['allowed'] is True)

    print('\n[2] wire_evidence — nguồn BLOCKED (99) phải bị từ chối + ghi en_audit_log:')
    try:
        wire._gate_check(99, 'INGEST')
        ok &= check('raise PermissionError', False)
    except PermissionError as e:
        ok &= check('raise PermissionError', True, str(e)[:60])
    rows = audit_rows(db)
    ok &= check('có đúng 1 dòng audit', len(rows) == 1, f'rows={len(rows)}')
    if rows:
        r = rows[0]
        ok &= check('action=license_gate_block', r[2] == 'license_gate_block', r[2])
        ok &= check("entity_ref='source:99'", r[1] == 'source:99', r[1])
        ok &= check('field_name=entity_claims', r[3] == 'entity_claims', r[3])
        ok &= check('verification_status=blocked', r[7] == 'blocked', r[7])
        ok &= check('editor=đường dẫn script', r[6].endswith('wire_evidence_into_entity_claims.py'), r[6])
        ok &= check('evidence_sources chứa status BLOCKED', 'BLOCKED' in (r[5] or ''), (r[5] or '')[:60])

    print('\n[3] wire_evidence — dry-run (allow_block) KHÔNG ghi audit:')
    before = len(audit_rows(db))
    wire._gate_check(99, 'INGEST', allow_block=True)
    ok &= check('không thêm dòng audit khi dry-run', len(audit_rows(db)) == before)

    print('\n[4] etl_t109 — gate_preflight thấy source 99 trong entity_claims -> SystemExit(2):')
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    before = len(audit_rows(db))
    try:
        t109.gate_preflight(conn, dry_run=False)
        ok &= check('raise SystemExit(2)', False)
    except SystemExit as e:
        ok &= check('raise SystemExit(2)', e.code == 2, f'code={e.code}')
    rows = audit_rows(db)
    ok &= check('có thêm 1 dòng audit', len(rows) == before + 1, f'{before}->{len(rows)}')
    new_row = rows[-1]
    ok &= check('audit target=entity_claims_audit,events_provenance',
                new_row[3] == 'entity_claims_audit,events_provenance', new_row[3])

    print('\n[5] etl_t109 — dry-run không chặn, không ghi audit:')
    before = len(audit_rows(db))
    t109.gate_preflight(conn, dry_run=True)
    ok &= check('không thêm dòng audit khi dry-run', len(audit_rows(db)) == before)
    conn.close()

    print('\n==== KẾT QUẢ:', 'PASS' if ok else 'FAIL', '====')
    os.unlink(db)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
