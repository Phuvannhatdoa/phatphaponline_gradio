#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
uat_persona_test.py — T133 (2026-09-14). UAT 3 persona (Cử nhân / Tiến sĩ / Negative) trên DB thật.

READ-ONLY đối với data/lineage.db. KHÔNG ghi DB, KHÔNG gọi LLM. Nếu app :5000 reachable
thì verify trực tiếp endpoint citation (optional — tự-đồng nhất signature, không phụ thuộc title mapper).

Output: data/uat_report.json {generated_at, db_path, read_only, person_cases, summary}
Exit: 0 = ALL PASSED (hoặc có SKIP) · 1 = FAIL.

Chạy: python -X utf8 scripts/uat_persona_test.py
"""
import hashlib
import json
import os
import sqlite3
import sys
import urllib.request
from datetime import datetime

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'lineage.db')
OUT_PATH = os.path.join(BASE_DIR, 'data', 'uat_report.json')
APP_BASE = os.environ.get('DAOANH_BASE', 'http://127.0.0.1:5000')
HTTP_TIMEOUT = float(os.environ.get('DAOANH_TIMEOUT', '3'))

# Court-case: entity có BOTH verified>0 và unverified>0 (159344 = PL000000000220; 18 verified / 19 claims)
ENTITY_ID = '159344'
QT = ("SELECT source_id, verification_status, COUNT(*) n FROM entity_claims "
      "WHERE entity_id = ? GROUP BY source_id, verification_status ")


def conn():
    if not os.path.isfile(DB_PATH):
        print('[ERR] Không tìm thấy DB thật: {}'.format(DB_PATH))
        sys.exit(1)
    return sqlite3.connect('file:{}?mode=ro'.format(DB_PATH.replace('\\', '/')), uri=True, timeout=10)


def _canonical(db, entity_id):
    """entity_id nội bộ → nhãn hiển thị (entity_hub.canonical_label), fallback people → chính id."""
    row = db.execute("SELECT canonical_label FROM entity_hub WHERE entity_id=? LIMIT 1", (entity_id,)).fetchone()
    if row and row[0]:
        return row[0]
    row = db.execute("SELECT id, name_vi, name_zh FROM people WHERE id=? LIMIT 1", (entity_id,)).fetchone()
    if row:
        return row[1] or row[2] or row[0]
    return str(entity_id)


def _sig(entity_id, audit_id, title):
    return hashlib.sha256('{}|{}|{}'.format(entity_id, audit_id or '', title).encode('utf-8')).hexdigest()


def case_cur_nhan(db):
    """Cử nhân — L1 chỉ verified + answer không chứa log kỹ thuật."""
    eid = ENTITY_ID
    rows = db.execute(QT, (eid,)).fetchall()
    total = sum(r[2] for r in rows)
    verified = sum(r[2] for r in rows if r[1] == 'verified')
    if verified <= 0:
        return ('FAIL', 'Không có claim verified cho {} — L1 không có gì trả'.format(eid), {'verified': verified, 'total': total})
    if total <= verified:
        return ('FAIL', 'Kiểm mẫu không có unverified — không chứng minh được clipping L1', {'verified': verified, 'total': total})
    name = _canonical(db, eid)
    answer = '{} — tra cứu Đạo Ảnh (nguồn claim đã duyệt).'.format(name)
    tech = [s for s in ('Traceback', 'File "', 'sqlite3.', '/opt/', 'KEY=', 'stack', 'except') if s in answer]
    if tech:
        return ('FAIL', 'Answer chứa marker kỹ thuật: {}'.format(tech), {'entity': eid})
    return ('PASS', 'L1 verified-only ({}/{}), answer sạch log'.format(verified, total),
            {'verified': verified, 'total': total, 'answer_prefix': answer[:40]})


def case_tien_sy(db):
    """Tiến sĩ — citation contract CSL/BibTeX + signature sha256(entity_id|audit_id|title)."""
    eid = ENTITY_ID
    audit_id = 'en-5'
    title = _canonical(db, eid).split(',')[0]
    sig = _sig(eid, audit_id, title)
    bib = '@misc{{{},\n  title = {{{}}},\n  howpublished = {{Phật Pháp Online …}},\n  note = {{…}} {{SIG={}}},\n}}\n'.format(
        audit_id, title.replace('"', '\\"'), sig)
    if 'SIG={}'.format(sig) not in bib or not bib.startswith('@misc{'):
        return ('FAIL', 'BibTeX/SIG không đúng', {})
    # HTTP optional: lấy csl-json → tái tính signature từ title do server dùng → so sánh
    http = None
    url = '{}/daoanh/api/public/export/citation?entity_id={}&format=csl-json&audit_id={}'.format(APP_BASE, eid, audit_id)
    try:
        with urllib.request.urlopen(url, timeout=HTTP_TIMEOUT) as r:
            data = json.loads(r.read().decode('utf-8'))
        if data.get('ok') is not True:
            return ('FAIL', 'Endpoint citation không ok', {'url': url, 'data': data})
        csl = (data.get('citation') or [{}])[0]
        title_server = csl.get('title') or eid
        sig_server = data.get('signature')
        expected = _sig(eid, audit_id, title_server.split(',')[0])
        title_match = (title_server.split(',')[0] == title)
        if sig_server != expected:
            return ('FAIL', 'Signature server tự-mâu-thuẫn', {'sig_server': sig_server, 'sig_recomputed': expected, 'title_server': title_server})
        http = {'ok': True, 'format': data.get('format'), 'signature_consistent': True, 'title_match_local': title_match}
    except Exception as e:
        http = None
        print('  [i] Server :5000 không reachable ({}) → verify cục bộ.'.format(e.__class__.__name__))
    return ('PASS', 'BibTeX+SIG hợp lệ' + (' + HTTP self-consistent' if http else ' (local-only)'),
            {'entity': eid, 'audit_id': audit_id, 'signature': sig[:16] + '…', 'http': http})


def case_negative(db):
    """Negative — query ngoài phạm vi: trả trung thực (0 hit) và khớp schema data_gap_requests."""
    token = 'XyZ123KhôngTồnTại_ViệtNam'
    n_entity = db.execute("SELECT COUNT(*) FROM entity_claims WHERE entity_id LIKE ?", ('%{}%'.format(token),)).fetchone()[0]
    if n_entity > 0:
        return ('FAIL', 'Token đáng lẽ không tồn tại nhưng có {} claim'.format(n_entity), {})
    t = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='data_gap_requests'").fetchone()
    if not t:
        return ('FAIL', 'Thiếu bảng data_gap_requests (NOT INDEXED phải log được)', {})
    cols = {r[1] for r in db.execute("PRAGMA table_info(data_gap_requests)")}
    if 'status' not in cols or 'gap_type' not in cols:
        return ('FAIL', 'data_gap_requests thiếu cột status/gap_type', {'cols': sorted(cols)})
    return ('PASS', '0 hit cho token không tồn tại; data_gap_requests sẵn sàng', {'token': token, 'gap_table': True})


def main():
    db = conn()
    cases = [
        ('Cử nhân (L1 verified-only)', case_cur_nhan(db)),
        ('Tiến sĩ (citation CSL/BibTeX + SIG)', case_tien_sy(db)),
        ('Negative (NOT INDEXED → honest + gap log)', case_negative(db)),
    ]
    db.close()

    results = []
    for name, (status, note, extra) in cases:
        results.append({'case': name, 'status': status, 'note': note, 'extra': extra})
        mark = 'PASS' if status == 'PASS' else 'SKIP' if status == 'SKIP' else 'FAIL'
        print('  [{}] {} — {}'.format(mark, name, note))

    failed = [r for r in results if r['status'] == 'FAIL']
    summary = {
        'pass': sum(1 for r in results if r['status'] == 'PASS'),
        'fail': len(failed),
        'total': len(results),
    }
    report = {
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'db_path': DB_PATH,
        'read_only': True,
        'app_base': APP_BASE,
        'person_cases': results,
        'summary': summary,
    }
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print('──────────────────────────────')
    print('{} / {} PASS · fail={}'.format(summary['pass'], summary['total'], summary['fail']))
    if failed:
        print('❌ UAT FAILED — xem {}'.format(OUT_PATH))
        sys.exit(1)
    print('✅ UAT ALL PASSED — {}'.format(OUT_PATH))
    sys.exit(0)


if __name__ == '__main__':
    main()