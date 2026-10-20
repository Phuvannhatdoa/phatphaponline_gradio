# -*- coding: utf-8 -*-
"""T172 — unit tests charwise Han-Viet debug pipeline (SPEC §8).

Fixtures: tests/fixtures/t172_hanviet_cases.json (deterministic char_map, KHÔNG cần DB).
Chạy: python -X utf8 tests/test_t172_charwise.py
"""
import json
import os
import sqlite3
import sys
import unicodedata

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT)

from scripts.t172_build_charmap import (  # noqa: E402
    is_ideograph, compute_charwise, validate_status, legacy_compare,
    is_transliteration_flag, LEGACY_EXACT, LEGACY_NORMALIZED,
    LEGACY_DIFFERS, LEGACY_NOT_COMPARABLE,
    STATUS_VALID, STATUS_MISMATCH, STATUS_UNKNOWN, STATUS_EXCEPTION, STATUS_NEEDS_REVIEW,
)
from scripts.t172_hanviet_charwise_migrate import (  # noqa: E402
    process_person, upsert_debug, CREATE_DEBUG, CREATE_EXCEPTION, CREATE_CHAR_MAP,
)

FIX = os.path.join(os.path.dirname(__file__), 'fixtures', 't172_hanviet_cases.json')
with open(FIX, encoding='utf-8') as _f:
    FIXTURE = json.load(_f)

PASS = 0
FAIL = 0


def check(name, cond, detail=''):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f'  ✅ {name}')
    else:
        FAIL += 1
        print(f'  ❌ {name} {detail}')


def build_cmap(case):
    """char_map cho một case: reading từ fixture + override polyphonic
    (kể cả chữ CHỈ có ở polyphonic — không lặp từng tự ngoài name_zh)."""
    cmap = {}
    chars = set(case['name_zh']) | (set(FIXTURE['polyphonic']) & set(case['name_zh']))
    for ch in chars:
        base = FIXTURE['char_map'].get(ch)
        poly = FIXTURE['polyphonic'].get(ch, {})
        if base is None and not poly:
            continue
        cmap[ch] = {
            'reading': poly.get('reading', base),
            'is_polyphonic': 1 if poly else 0,
            'candidates': poly.get('candidates', ''),
        }
    return cmap


def run_case(case):
    cmap = build_cmap(case)
    res = compute_charwise(case['name_zh'], cmap)
    if res['han_count'] == 0:
        return None
    han = [c for c in case['name_zh'] if is_ideograph(c)]
    ex_set = {''.join(han)} if case.get('exception') else set()
    legacy_match = legacy_compare(case['name_vi'], res['charwise'])
    status, reason = validate_status(res['unknown'], ''.join(han) in ex_set,
                                     res['poly'], legacy_match)
    translit = is_transliteration_flag(res['unknown'], legacy_match)
    return {
        'status': status, 'legacy_match': legacy_match, 'is_transliteration': translit,
        'han_count': res['han_count'], 'syll_count': res['syll_count'],
        'unknown': ''.join(res['unknown']),
        'charwise': res['charwise'], 'reason': reason,
    }


def main():
    # ── 1. Fixture case assertions ──
    print('=== T172 fixture cases (7) ===')
    for case in FIXTURE['cases']:
        got = run_case(case)
        exp = case['expect']
        tag = f"[{case['id']}] {case['desc']}"
        check(f'{tag} status={exp["status"]}', got['status'] == exp['status'], str(got['status']))
        check(f'{tag} legacy_match={exp["legacy_match"]}', got['legacy_match'] == exp['legacy_match'], str(got['legacy_match']))
        check(f'{tag} is_transliteration={exp["is_transliteration"]}', got['is_transliteration'] == exp['is_transliteration'], str(got['is_transliteration']))
        check(f'{tag} han_count={exp["han_count"]}', got['han_count'] == exp['han_count'], str(got['han_count']))
        check(f'{tag} syll_count={exp["syll_count"]}', got['syll_count'] == exp['syll_count'], str(got['syll_count']))
        check(f'{tag} unknown={exp["unknown"]!r}', got['unknown'] == exp['unknown'], repr(got['unknown']))
        if exp['status'] == STATUS_EXCEPTION:
            check(f'{tag} exception not auto-suae (reason giu exception_list)',
                  'exception_list' in got['reason'], repr(got['reason']))

    # ── 2. Ideograph counter (kể U+279CC, Ext B) ──
    print('\n=== T172 ideograph counter ===')
    check("is_ideograph(U+279CC '𧝌') True", is_ideograph('\U000279cc'))
    res = compute_charwise('\U000279cc一山', {'一': {'reading': 'Nhất', 'is_polyphonic': 0, 'candidates': ''}})
    check('count U+279CC + 一 + 山 = 3', res['han_count'] == 3, str(res['han_count']))
    check('non-CJK không đếm ("A1一行")', compute_charwise('A1一行', {}).get('han_count') == 2)

    # ── 3. Validate order: unknown > exception > needs_review > mismatch > valid ──
    print('\n=== T172 validate order ===')
    st, _ = validate_status(['頔'], True, [], LEGACY_DIFFERS)
    check('unknown thắng exception', st == STATUS_UNKNOWN, st)
    st, _ = validate_status([], False, [], LEGACY_DIFFERS)
    check('differs → mismatch', st == STATUS_MISMATCH, st)
    st, _ = validate_status([], False, [('行', 'hàng')], LEGACY_DIFFERS)
    check('poly + differs → needs_review', st == STATUS_NEEDS_REVIEW, st)
    st, r = validate_status([], False, [('行', 'hàng')], LEGACY_EXACT)
    check('poly + exact → valid nhưng reason chứa needs_review marker', st == STATUS_VALID and 'needs_review' in r, f'{st} / {r}')
    st, _ = validate_status([], False, [], LEGACY_EXACT)
    check('exact → valid', st == STATUS_VALID, st)
    st, _ = validate_status([], True, [], LEGACY_EXACT)
    check('exception → exception', st == STATUS_EXCEPTION, st)

    # ── 4. Legacy compare (NFC/lowercase/whitespace; not_comparable) ──
    print('\n=== T172 legacy compare ===')
    check("whitespace collapse: 'nhất  sơn' vs 'Nhất Sơn'", legacy_compare('nhất  sơn', 'Nhất Sơn') == LEGACY_EXACT)
    check("NFC: decomposed 'Hô\u0300' ≡ composed 'Hồ'", legacy_compare('Hô\u0300', 'Hồ') == LEGACY_EXACT)
    check("toneless: 'Tây Ho' vs 'Tây Hồ' → normalized", legacy_compare('Tây Ho', 'Tây Hồ') == LEGACY_NORMALIZED)
    check("'Vu 頔' vs 'vu [?頔]' → not_comparable (legacy còn Hán tự)",
          legacy_compare('Vu 頔', 'vu [?頔]') == LEGACY_NOT_COMPARABLE)
    check("hoàn toàn khác → differs", legacy_compare('Mã Tổ', 'Bồ Đề Đạt Ma') == LEGACY_DIFFERS)
    check('legacy rỗng + charwise rỗng → not_comparable', legacy_compare('', ' ') == LEGACY_NOT_COMPARABLE)

    # ── 5. Không placeholder cho chữ có reading ──
    print('\n=== T172 placeholder rule ===')
    cmap = build_cmap(FIXTURE['cases'][1])
    res = compute_charwise('一行', cmap)
    check("'一行' charwise không chứa '[?'", res['charwise'] == 'Nhất Hành' and '[?' not in res['charwise'], repr(res['charwise']))
    res = compute_charwise('于頔', build_cmap(FIXTURE['cases'][4]))
    check("'頔' chưa biết → placeholder '[?頔]'", '[?頔]' in res['charwise'] and res['unknown'] == ['頔'], repr(res['charwise']))

    # ── 6. process_person deterministic (idempotency proxy) ──
    print('\n=== T172 process_person determinism ===')
    row = ('A000008', '一行', 'Nhất Hàng')
    cmap = build_cmap(FIXTURE['cases'][1])
    ex_set = set()
    r1 = process_person(row, cmap, ex_set)
    r2 = process_person(row, cmap, ex_set)
    check('2 lần cho cùng dict (idempotent)', r1 == r2, repr(r1))
    check('reason chứa needs_review', 'needs_review' in (r1['han_viet_validation_reason'] or ''), repr(r1['han_viet_validation_reason']))

    # ── 7. people immutability (in-memory sqlite, INSERT OR REPLACE 2×) ──
    print('\n=== T172 people immutability + upsert 2× (sqlite in-memory) ===')
    con = sqlite3.connect(':memory:')
    try:
        con.execute(CREATE_CHAR_MAP)
        con.execute(CREATE_EXCEPTION)
        con.execute(CREATE_DEBUG)
        con.execute("CREATE TABLE people (id TEXT PRIMARY KEY, name_zh TEXT, name_vi TEXT)")
        people = [('A000008', '一行', 'Nhất Hàng'), ('A000047', '于頔', 'Vu 頔')]
        con.executemany('INSERT INTO people(id,name_zh,name_vi) VALUES(?,?,?)', people)
        cmap2 = {}
        for ch, reading in FIXTURE['char_map'].items():
            poly = FIXTURE['polyphonic'].get(ch, {})
            cmap2[ch] = {'reading': poly.get('reading', reading),
                         'is_polyphonic': 1 if poly else 0,
                         'candidates': poly.get('candidates', '')}
        before = con.execute('SELECT COUNT(*) FROM people').fetchone()[0]
        for _ in range(2):
            rows = [process_person((pid, zh, vi), cmap2, set()) for pid, zh, vi in people]
            upsert_debug(con, [r for r in rows if r])
            con.commit()
        after = con.execute('SELECT COUNT(*) FROM people').fetchone()[0]
        n_debug = con.execute('SELECT COUNT(*) FROM person_hanviet_debug').fetchone()[0]
        check('people COUNT(*) trước = sau', before == after and before == 2, f'{before}→{after}')
        check('sidecar đủ 2 row (INSERT OR REPLACE không nhân đôi)', n_debug == 2, str(n_debug))
    finally:
        con.close()

    print(f'\nT172 charwise: {PASS} PASS · {FAIL} FAIL')
    sys.exit(1 if FAIL else 0)


if __name__ == '__main__':
    main()