#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T290 — Test cho `scripts/build_credits.py` (sinh credits.html từ `data_sources`).

Dùng DB FIXTURE trong thư mục tạm (không đụng `data/lineage.db`, không ghi DB thật).
Chạy: python -m pytest tests/test_t290_credits_generator.py -v
  hoặc python -X utf8 tests/test_t290_credits_generator.py
"""
import os
import re
import sqlite3
import sys
import tempfile

DAOANH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, DAOANH)
sys.path.insert(0, os.path.join(DAOANH, 'scripts'))

import build_credits as bc  # noqa: E402

# 4 nguồn: 2 đang dùng (DILA giấy phép chưa xác minh, CBETA đã xác minh),
# 2 bị chặn (BDRC active=0/BLOCKED, SAT BLOCKED).
FIXTURE_ROWS = [
    dict(source_id=1, source_code='DILA', source_name='DILA Authority',
         organization='DILA (Dharma Drum)', legal_status='AUDITING',
         integration_mode='INGEST', license_verified=0, license_spdx=None,
         data_license=None, active=1, origin_url='https://authority.dila.edu.tw',
         license_url=None, claims=100),
    dict(source_id=3, source_code='CBETA', source_name='CBETA Buddhist Canon',
         organization='CBETA 中華電子佛典協會', legal_status='AUDITING',
         integration_mode='INGEST', license_verified=1, license_spdx='CC-BY-NC-SA-4.0',
         data_license='CC-BY-NC-SA-4.0', active=1, origin_url='https://cbeta.org',
         license_url='https://cbeta.org/license', claims=50),
    dict(source_id=2, source_code='BDRC', source_name='Buddhist Digital Resource Center',
         organization='BDRC', legal_status='UNKNOWN', integration_mode='BLOCKED',
         license_verified=0, license_spdx=None, data_license=None, active=0,
         origin_url=None, license_url=None, claims=0),
    dict(source_id=7, source_code='SAT', source_name='SAT Daizōkyō Text Database',
         organization=None, legal_status='UNKNOWN', integration_mode='BLOCKED',
         license_verified=0, license_spdx=None, data_license=None, active=1,
         origin_url=None, license_url=None, claims=0),
]


def make_fixture_db(path):
    """Tạo DB fixture tối thiểu (schema rút gọn của lineage.db) + nạp 4 nguồn."""
    conn = sqlite3.connect(path)
    conn.executescript('''
        CREATE TABLE data_sources (
            source_id INTEGER PRIMARY KEY, source_code TEXT, source_name TEXT,
            organization TEXT, legal_status TEXT, integration_mode TEXT,
            license_verified INTEGER, license_spdx TEXT, data_license TEXT,
            active INTEGER, origin_url TEXT, license_url TEXT);
        CREATE TABLE entity_claims (claim_id INTEGER PRIMARY KEY, source_id INTEGER);
        CREATE TABLE source_authority (source_id INTEGER, authority_score INTEGER);
    ''')
    for r in FIXTURE_ROWS:
        conn.execute(
            'INSERT INTO data_sources (source_id, source_code, source_name, organization, '
            'legal_status, integration_mode, license_verified, license_spdx, data_license, '
            'active, origin_url, license_url) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
            (r['source_id'], r['source_code'], r['source_name'], r['organization'],
             r['legal_status'], r['integration_mode'], r['license_verified'],
             r['license_spdx'], r['data_license'], r['active'], r['origin_url'],
             r['license_url']))
    # claims: DILA 3, CBETA 2 (đếm thật từ entity_claims, không lấy cột fixture)
    conn.executemany('INSERT INTO entity_claims (source_id) VALUES (?)',
                     [(1,), (1,), (1,), (3,), (3,)])
    conn.execute('INSERT INTO source_authority (source_id, authority_score) VALUES (1, 100)')
    conn.commit()
    conn.close()


def fixture_rows():
    tmpdir = tempfile.mkdtemp(prefix='t290_fixture_')
    path = os.path.join(tmpdir, 'fixture.db')
    make_fixture_db(path)
    return path, bc.load_rows_from_db(path)


def card_segment(html_text, code):
    """Lấy đúng đoạn thẻ của 1 nguồn (không lấn sang thẻ/danh sách kế tiếp)."""
    marker = 'data-source-code="%s"' % code
    parts = html_text.split(marker, 1)
    if len(parts) < 2:
        return ''
    rest = parts[1]
    for stop in ('data-source-code="', '<h2 class="section"', '<footer>'):
        idx = rest.find(stop)
        if idx != -1:
            rest = rest[:idx]
    return rest


def test_load_db_counts_claims_and_authority():
    path, rows = fixture_rows()
    by_code = {r['source_code']: r for r in rows}
    assert len(rows) == 4
    assert by_code['DILA']['claims'] == 3       # đếm từ entity_claims
    assert by_code['CBETA']['claims'] == 2
    assert by_code['DILA']['authority_score'] == 100
    assert by_code['SAT']['authority_score'] is None


def test_select_groups_rule():
    _, rows = fixture_rows()
    in_use, blocked = bc.select_groups(rows)
    assert [r['source_code'] for r in in_use] == ['DILA', 'CBETA']
    assert [r['source_code'] for r in blocked] == ['BDRC', 'SAT']


def test_render_entries_equal_sql_rows():
    """Kiểm chứng §4 của task: số mục trên trang = số dòng SQL."""
    path, rows = fixture_rows()
    html_text = bc.render(rows, generated_at='2026-11-01 00:00')
    codes = re.findall(r'data-source-code="([^"]+)"', html_text)
    assert len(codes) == len(rows) == 4, codes
    assert len(set(codes)) == len(codes)  # mỗi nguồn đúng 1 mục
    assert 't290:total=4 in_use=2 blocked=2' in html_text


def test_check_page_passes_on_generated_page():
    _, rows = fixture_rows()
    html_text = bc.render(rows, generated_at='2026-11-01 00:00')
    assert bc.check_page(html_text, rows) == []


def test_check_page_fails_on_handwritten_page():
    """Trang tĩnh gõ tay (bản cũ) phải bị bắt là không khớp DB."""
    _, rows = fixture_rows()
    stale = ('<html><body><div class="source-card"><h2>DILA</h2>'
             '<span class="badge sa">CC BY-SA 3.0</span></div>'
             '<div class="source-card"><h2>CBETA</h2></div></body></html>')
    problems = bc.check_page(stale, rows)
    assert problems, 'phải phát hiện trang gõ tay không khớp DB'
    joined = ' '.join(problems)
    assert 'Thiếu marker' in joined
    assert 'BDRC' in joined and 'SAT' in joined


def test_unverified_license_is_not_asserted():
    _, rows = fixture_rows()
    html_text = bc.render(rows, generated_at='2026-11-01 00:00')
    seg = card_segment(html_text, 'DILA')
    assert 'chưa xác minh' in seg.lower()
    assert 'license_verified=0' in seg


def test_unverified_source_shows_no_license_term_note():
    """Sửa 1: nguồn license_verified=0 không được thấy câu về điều khoản."""
    _, rows = fixture_rows()
    html_text = bc.render(rows, generated_at='2026-11-01 00:00')
    seg = card_segment(html_text, 'DILA')
    assert 'chia sẻ tương tự' not in seg.lower()
    notes = bc.NOTE_BLOCK_RE.findall(seg)
    assert notes, 'phải có ghi chú biên tập để kiểm'
    for note_html in notes:
        assert bc.find_license_claims(note_html) == [], note_html
    # Không có khối ghi chú nào là điều khoản bị render cho DILA
    assert '<div class="note term">' not in seg


def test_verified_source_shows_license_term_note():
    """Câu điều khoản của LICENSE_TERM_NOTES chỉ hiện khi license_verified=1."""
    _, rows = fixture_rows()
    html_text = bc.render(rows, generated_at='2026-11-01 00:00')
    seg = card_segment(html_text, 'CBETA')
    assert 'phi thương mại' in seg.lower()
    assert '<div class="note term">' in seg


def test_editorial_notes_have_no_license_terms():
    """EDITORIAL_NOTES chỉ mô tả vai trò — không được chứa từ khóa giấy phép."""
    offenders = {code: bc.find_license_claims(note)
                 for code, note in bc.EDITORIAL_NOTES.items()
                 if bc.find_license_claims(note)}
    assert offenders == {}, offenders


def test_check_page_flags_hardcoded_license_note():
    """Sửa 2: --check phải bắt ghi chú cứng nêu giấy phép cho nguồn chưa xác minh."""
    _, rows = fixture_rows()
    html_text = bc.render(rows, generated_at='2026-11-01 00:00')
    assert bc.check_page(html_text, rows) == []
    injected = html_text.replace(
        'data-source-code="DILA"',
        'data-source-code="DILA"><div class="note">Bản phái sinh phải cùng giấy phép '
        'chia sẻ tương tự.</div>', 1)
    problems = bc.check_page(injected, rows)
    joined = ' '.join(problems)
    assert 'DILA' in joined
    assert 'điều khoản' in joined and 'share-alike' in joined, problems


def test_check_page_flags_hardcoded_license_note_term_class():
    """Sửa 2 (vòng 3): ghi chú cứng dạng <div class="note term"> cũng bị bắt."""
    _, rows = fixture_rows()
    html_text = bc.render(rows, generated_at='2026-11-01 00:00')
    assert bc.check_page(html_text, rows) == []
    injected = html_text.replace(
        'data-source-code="DILA"',
        'data-source-code="DILA"><div class="note term">Bản phái sinh phải cùng giấy phép '
        'chia sẻ tương tự.</div>', 1)
    problems = bc.check_page(injected, rows)
    joined = ' '.join(problems)
    assert 'DILA' in joined, problems
    assert 'điều khoản' in joined, problems


def test_check_page_flags_hardcoded_license_note_p_tag():
    """Sửa 2 (vòng 3): ghi chú cứng dạng <p class="note"> cũng bị bắt."""
    _, rows = fixture_rows()
    html_text = bc.render(rows, generated_at='2026-11-01 00:00')
    assert bc.check_page(html_text, rows) == []
    injected = html_text.replace(
        'data-source-code="DILA"',
        'data-source-code="DILA"><p class="note">Theo CC BY-SA 3.0, phải ghi nguồn.</p>', 1)
    problems = bc.check_page(injected, rows)
    joined = ' '.join(problems)
    assert 'DILA' in joined, problems
    assert 'điều khoản' in joined, problems


def test_verified_license_shown_from_db():
    _, rows = fixture_rows()
    html_text = bc.render(rows, generated_at='2026-11-01 00:00')
    seg = card_segment(html_text, 'CBETA')
    assert 'CC-BY-NC-SA-4.0' in seg
    assert 'chưa xác minh' not in seg.lower()
    assert 'badge nc' in seg          # NC → nhãn vàng


def test_blocked_sources_listed_with_explanation():
    _, rows = fixture_rows()
    html_text = bc.render(rows, generated_at='2026-11-01 00:00')
    assert 'Nguồn đang chặn hoặc chưa xác minh (2)' in html_text
    assert 'BDRC' in html_text and 'active: tắt' in html_text


def test_cli_check_exit_codes():
    path, _ = fixture_rows()
    tmpdir = tempfile.mkdtemp(prefix='t290_out_')
    out = os.path.join(tmpdir, 'credits.html')
    assert bc.main(['--db', path, '--out', out, '--generated-at', '2026-11-01 00:00']) == 0
    assert bc.main(['--db', path, '--out', out, '--check']) == 0
    # sửa tay để mất 1 nguồn → check phải FAIL
    text = open(out, encoding='utf-8').read()
    open(out, 'w', encoding='utf-8').write(text.replace('data-source-code="SAT"', 'data-x="SAT"'))
    assert bc.main(['--db', path, '--out', out, '--check']) == 1


def test_load_rejects_empty_db_placeholder():
    tmpdir = tempfile.mkdtemp(prefix='t290_empty_')
    empty = os.path.join(tmpdir, 'lineage.db')
    open(empty, 'wb').close()          # 0 byte, giống placeholder trong worktree
    try:
        bc.load_rows_from_db(empty)
    except RuntimeError as exc:
        assert '0 byte' in str(exc)
    else:
        raise AssertionError('phải từ chối DB 0 byte')


if __name__ == '__main__':
    failed = 0
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith('test_') and callable(f)]
    for name, fn in tests:
        try:
            fn()
            print(f'PASS {name}')
        except AssertionError as exc:
            failed += 1
            print(f'FAIL {name}: {exc}')
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f'ERROR {name}: {type(exc).__name__}: {exc}')
    print(f'\n{len(tests) - failed}/{len(tests)} PASS')
    sys.exit(1 if failed else 0)
