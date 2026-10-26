#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_design_compliance.py — Compliance Meter (T113, doc SCHEMA_DESIGN M7.2).

Đọc-ONLY + Zero-RAM: chỉ dùng COUNT/SELECT aggregate (generator nếu duyệt theo hàng),
KHÔNG sửa database. Sinh data/design_compliance.json để dashboard hiển thị "Data Quality".

Cách chạy:
    python scripts/verify_design_compliance.py            # in summary + ghi JSON
    python scripts/verify_design_compliance.py --json     # in raw JSON ra stdout
    python scripts/verify_design_compliance.py --strict   # mọi fail (contract + coverage) → exit 1

CHÍNH SÁCH EXIT (cổng hai tầng, Admin duyệt 2026-10-26):
    contract  = lỗi cấu trúc/hợp đồng (thiếu bảng/cột, SQL lỗi) → exit 1 luôn (chặn review)
    coverage  = mức phủ dữ liệu chưa đạt goal → exit 0, in khối cảnh báo + ghi báo cáo
    --strict  = mọi fail → exit 1 (dùng khi phát hành / đánh giá dữ liệu)
    Metric sai vẫn ghi status='fail' — chỉ đổi chính sách exit, không đổi nhãn.

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
import argparse
from datetime import datetime

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'lineage.db')
OUT_PATH = os.path.join(DATA_DIR, 'design_compliance.json')

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

# Phân loại cổng hai tầng (Admin duyệt 2026-10-26).
# Mọi metric hiện tại đều là % phủ dữ liệu so với goal → 'coverage' (cảnh báo, không chặn review).
# Lỗi cấu trúc (thiếu bảng/cột, SQL lỗi) được bắt trong compute() → 'contract' (exit 1).
# Nguyên tắc an toàn: metric lưỡng tính → xếp 'contract'. Hiện không có metric nào lưỡng tính.
GATE_CLASS = {m['id']: 'coverage' for m in METRICS}

# Task sở hữu gợi ý để in trong khối cảnh báo (suy ra từ docs/tasktodo.md). Không biết → không ghi.
OWNER_TASK = {
    'claims_assertion_level': 'T113/T133 (HITL: người review điền assertion_level, bot không điền)',
    'claims_reviewed': 'T119 (bulk review)',
    'claims_verified': 'T119 (bulk review)',
    'conflicts_resolved': 'T109/T136 (conflict workflow)',
    'events_provenance': 'T109 (provenance)',
    'claims_with_audit': 'T109 (provenance)',
    'glossary_vi_coverage': 'T110 (glossary VI)',
}


def count(cur, sql):
    """Zero-RAM: aggregate COUNT của SQLite — không nạp hàng vào Python."""
    row = cur.execute(sql).fetchone()
    return int(row[0]) if row else 0


def open_conn():
    conn = sqlite3.connect('file:%s?mode=ro' % DB_PATH.replace('\\', '/'), uri=True)
    conn.execute('PRAGMA query_only = ON')
    return conn


def compute(strict=False):
    conn = open_conn()
    cur = conn.cursor()
    out_metrics = []
    for m in METRICS:
        contract_error = None
        try:
            passed = count(cur, m['passed_sql'])
            total = count(cur, m['total_sql'])
        except sqlite3.Error as e:
            # Lỗi cấu trúc (thiếu bảng/cột) = contract: không tính ratio giả, status = fail, chặn review
            passed, total, contract_error = 0, 0, str(e)
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
            'gate_class': 'contract' if contract_error else GATE_CLASS.get(m['id'], 'coverage'),
            'owner_task': OWNER_TASK.get(m['id']),
            'contract_error': contract_error,
            'note': 'Sau T109/T110' if m['id'] in ('claims_with_audit', 'events_provenance', 'glossary_vi_coverage') else (
                'Bootstrap: %s đã duyệt' % passed if passed else 'Chưa review'
            ),
        })
    total_tables = cur.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchone()[0]
    conn.close()

    # Tách fail thành contract (chặn) và coverage (cảnh báo). status vẫn giữ nguyên 'fail'.
    contract_fail = [m_['id'] for m_ in out_metrics
                     if m_['status'] == 'fail' and m_['gate_class'] == 'contract']
    coverage_fail = [m_['id'] for m_ in out_metrics
                     if m_['status'] == 'fail' and m_['gate_class'] != 'contract']
    summary = {
        'pass_metrics': sum(1 for m_ in out_metrics if m_['status'] == 'pass'),
        'warn_metrics': sum(1 for m_ in out_metrics if m_['status'] == 'warn'),
        'fail_metrics': sum(1 for m_ in out_metrics if m_['status'] == 'fail'),
        'total_metrics': len(out_metrics),
        'contract_fail_metrics': contract_fail,
        'coverage_fail_metrics': coverage_fail,
        'gate_policy': 'strict' if strict else 'two-tier: contract=block, coverage=warn',
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


def _print_coverage_block(payload, strict):
    by_id = {m_['id']: m_ for m_ in payload['metrics']}
    bar = '!' * 72
    head = ('⚠ COVERAGE GAPS — --strict: CHẶN (exit 1)' if strict else
            '⚠ COVERAGE GAPS — dữ liệu chưa đủ, KHÔNG chặn review (theo quy định dự án)')
    print(bar)
    print(head)
    for mid in payload['summary']['coverage_fail_metrics']:
        m_ = by_id[mid]
        owner = m_.get('owner_task') or '(chưa gán task)'
        print('  - %s: %d/%d (%.2f%%)  goal>=%s%%  [task sở hữu: %s]' % (
            mid, m_['passed'], m_['total'], m_['percent'], m_['goal'], owner))
    print('Cổng cứng: npm run test:compliance:strict   (mọi fail → exit 1)')
    print(bar)


def main():
    ap = argparse.ArgumentParser(description='Compliance Meter — cổng hai tầng (contract chặn, coverage cảnh báo)')
    ap.add_argument('--json', action='store_true', help='in raw JSON ra stdout (không ghi file)')
    ap.add_argument('--strict', action='store_true', help='mọi fail (contract + coverage) → exit 1')
    args = ap.parse_args()
    payload = compute(strict=args.strict)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
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
        if payload['summary']['coverage_fail_metrics']:
            _print_coverage_block(payload, args.strict)
    # Chính sách exit (cổng hai tầng). Sau khi đã in/ghi output.
    s = payload['summary']
    if s['contract_fail_metrics']:
        code, verdict = 1, 'BLOCK: contract fail'
    elif args.strict and s['coverage_fail_metrics']:
        code, verdict = 1, 'BLOCK: strict + coverage fail'
    else:
        code = 0
        verdict = 'PASS (có coverage gap — cảnh báo)' if s['coverage_fail_metrics'] else 'PASS'
    if not args.json:
        print('EXIT POLICY [%s]: contract_fail=%d · coverage_fail=%d → exit %d (%s)' % (
            s['gate_policy'], len(s['contract_fail_metrics']), len(s['coverage_fail_metrics']), code, verdict))
    if code:
        sys.exit(code)


if __name__ == '__main__':
    main()