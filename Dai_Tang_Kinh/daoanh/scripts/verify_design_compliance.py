#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_design_compliance.py — Compliance Meter (T113, doc SCHEMA_DESIGN M7.2).

Đọc-ONLY + Zero-RAM: chỉ dùng COUNT/SELECT aggregate (generator nếu duyệt theo hàng),
KHÔNG sửa database. Sinh data/design_compliance.json để dashboard hiển thị "Data Quality".

Cách chạy:
    python scripts/verify_design_compliance.py            # in summary + ghi JSON
    python scripts/verify_design_compliance.py --json     # in raw JSON ra stdout

Output schema (data/design_compliance.json):
    {generated_at, db_path, read_only, total_tables, metrics: [{id,label,formula,
      passed,total,ratio,percent,goal,status,note}], baseline_20260908: {...},
     summary: {pass_metrics, warn_metrics, total_metrics}}
"""
import os
import io
import sys
import json
import sqlite3
from datetime import datetime

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'lineage.db')
OUT_PATH = os.path.join(DATA_DIR, 'design_compliance.json')

RAW_ONLY = '--json' in sys.argv

# Baseline 2026-09-08 (SCHEMA_DESIGN M7.2 — trước T109/T110) → goal là "hiện trạng"
# đã chốt sau T109/T110; thêm chuẩn bootstrap >= 1% cho metrics chưa khởi động.
BASELINE_20260908 = {
    'claims_with_source': 100.0,
    'claims_with_confidence': 100.0,
    'claims_reviewed': 0.0,
    'claims_verified': 0.0,
    'claims_assertion_level': 0.0,
    'claims_with_audit': 0.0,     # -> 100% sau T109 backfill
    'events_provenance': 0.0,     # -> 100% sau T109
    'conflicts_resolved': 0.0,
    'glossary_vi_coverage': 0.0,  # -> 75.54% sau T110
}

# Metric definitions: id, label gốc (bảng M7.2), công thức, goal (đã chốt), mô tả.
METRICS = [
    {
        'id': 'claims_with_source',
        'label': 'claims_with_source',
        'formula': 'entity_claims có source_id / tổng claims',
        'goal': 100.0,
        'baseline': BASELINE_20260908['claims_with_source'],
        'total_sql': 'SELECT COUNT(*) FROM entity_claims',
        'passed_sql': 'SELECT COUNT(*) FROM entity_claims WHERE source_id IS NOT NULL',
    },
    {
        'id': 'claims_with_confidence',
        'label': 'claims_with_confidence',
        'formula': 'entity_claims có confidence / tổng claims',
        'goal': 100.0,
        'baseline': BASELINE_20260908['claims_with_confidence'],
        'total_sql': 'SELECT COUNT(*) FROM entity_claims',
        'passed_sql': 'SELECT COUNT(*) FROM entity_claims WHERE confidence IS NOT NULL',
    },
    {
        'id': 'claims_reviewed',
        'label': 'claims_reviewed',
        'formula': 'entity_claims có reviewed_by / tổng claims',
        'goal': 1.0,  # bootstrap >= 1% (SCHEMA_DESIGN: "claims bootstrap sau T109 ≥ 1%")
        'baseline': BASELINE_20260908['claims_reviewed'],
        'total_sql': 'SELECT COUNT(*) FROM entity_claims',
        'passed_sql': 'SELECT COUNT(*) FROM entity_claims WHERE reviewed_by IS NOT NULL',
    },
    {
        'id': 'claims_verified',
        'label': 'claims_verified',
        'formula': "entity_claims verification_status='verified' / tổng claims",
        'goal': 1.0,
        'baseline': BASELINE_20260908['claims_verified'],
        'total_sql': 'SELECT COUNT(*) FROM entity_claims',
        'passed_sql': "SELECT COUNT(*) FROM entity_claims WHERE verification_status='verified'",
    },
    {
        'id': 'claims_assertion_level',
        'label': 'claims_assertion_level',
        'formula': 'entity_claims có assertion_level / tổng claims',
        'goal': 1.0,
        'baseline': BASELINE_20260908['claims_assertion_level'],
        'total_sql': 'SELECT COUNT(*) FROM entity_claims',
        'passed_sql': 'SELECT COUNT(*) FROM entity_claims WHERE assertion_level IS NOT NULL',
    },
    {
        'id': 'claims_with_audit',
        'label': 'claims_with_audit',
        'formula': 'entity_claims có audit_id trong entity_claims_audit / tổng claims',
        'goal': 100.0,
        'baseline': BASELINE_20260908['claims_with_audit'],
        'total_sql': 'SELECT COUNT(*) FROM entity_claims',
        'passed_sql': 'SELECT COUNT(*) FROM entity_claims ec WHERE ec.claim_id IN (SELECT claim_id FROM entity_claims_audit)',
    },
    {
        'id': 'events_provenance',
        'label': 'events_provenance',
        'formula': 'events có source_id trong events_provenance / tổng events',
        'goal': 100.0,
        'baseline': BASELINE_20260908['events_provenance'],
        'total_sql': 'SELECT COUNT(*) FROM events',
        'passed_sql': 'SELECT COUNT(*) FROM events e WHERE e.event_id IN (SELECT event_id FROM events_provenance)',
    },
    {
        'id': 'conflicts_resolved',
        'label': 'conflicts_resolved',
        'formula': 'lineage_conflicts_v2 resolved=1 / tổng conflicts',
        'goal': 1.0,
        'baseline': BASELINE_20260908['conflicts_resolved'],
        'total_sql': 'SELECT COUNT(*) FROM lineage_conflicts_v2',
        'passed_sql': 'SELECT COUNT(*) FROM lineage_conflicts_v2 WHERE resolved = 1',
    },
    {
        'id': 'glossary_vi_coverage',
        'label': 'glossary_vi_coverage',
        'formula': 'glossary_term có term_vi trong glossary_vi / tổng glossary_term',
        'goal': 75.5,
        'baseline': BASELINE_20260908['glossary_vi_coverage'],
        'total_sql': 'SELECT COUNT(*) FROM glossary_term',
        'passed_sql': 'SELECT COUNT(*) FROM glossary_term g WHERE g.id IN (SELECT glossary_id FROM glossary_vi WHERE term_vi IS NOT NULL)',
    },
]


def count(cur, sql):
    """Zero-RAM: aggregate COUNT của SQLite — không nạp hàng vào Python."""
    row = cur.execute(sql).fetchone()
    return int(row[0]) if row else 0


def open_conn():
    conn = sqlite3.connect('file:%s?mode=ro' % DB_PATH.replace('\\', '/'), uri=True)
    conn.execute('PRAGMA query_only = ON')
    return conn


def compute():
    conn = open_conn()
    cur = conn.cursor()
    out_metrics = []
    for m in METRICS:
        passed = count(cur, m['passed_sql'])
        total = count(cur, m['total_sql'])
        ratio = (passed / total) if total else 0.0
        percent = round(ratio * 100, 2)
        goal = m['goal']
        status = 'pass' if percent >= goal else ('warn' if percent > 0 else 'fail')
        out_metrics.append({
            'id': m['id'],
            'label': m['label'],
            'formula': m['formula'],
            'passed': passed,
            'total': total,
            'ratio': round(ratio, 6),
            'percent': percent,
            'goal': goal,
            'baseline_2026-09-08': m['baseline'],
            'status': status,
            'note': 'Sau T109/T110' if m['id'] in ('claims_with_audit', 'events_provenance', 'glossary_vi_coverage') else (
                'Bootstrap: %s đã duyệt' % passed if passed else 'Chưa review'
            ),
        })
    total_tables = cur.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchone()[0]
    conn.close()

    summary = {
        'pass_metrics': sum(1 for m_ in out_metrics if m_['status'] == 'pass'),
        'warn_metrics': sum(1 for m_ in out_metrics if m_['status'] == 'warn'),
        'fail_metrics': sum(1 for m_ in out_metrics if m_['status'] == 'fail'),
        'total_metrics': len(out_metrics),
    }
    payload = {
        'generated_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        'db_path': DB_PATH,
        'read_only': True,
        'total_tables': total_tables,
        'metrics': out_metrics,
        'baseline_20260908': BASELINE_20260908,
        'summary': summary,
        'source': 'docs/SCHEMA_DESIGN.md M7.2',
    }
    return payload


def main():
    payload = compute()
    if RAW_ONLY:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    out = io.open(OUT_PATH, 'w', encoding='utf-8', newline='\n')
    out.write(json.dumps(payload, ensure_ascii=False, indent=2))
    out.close()
    print('[OK] Đã tạo %s' % OUT_PATH)
    print('    %d metric (pass=%d · warn=%d · fail=%d) · %d bảng' % (
        payload['summary']['total_metrics'],
        payload['summary']['pass_metrics'],
        payload['summary']['warn_metrics'],
        payload['summary']['fail_metrics'],
        payload['total_tables'],
    ))
    for m_ in payload['metrics']:
        print('    %-24s %6.2f%%  %s  (goal>=%s)' % (m_['label'], m_['percent'], m_['status'], m_['goal']))


if __name__ == '__main__':
    main()