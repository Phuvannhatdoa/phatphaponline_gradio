# -*- coding: utf-8 -*-
"""T169 Phase 2 — unit tests classify_diff (SPEC §3.9 fixture bắt buộc).

Chạy: python -X utf8 tests/test_t169_classify_diff.py   (không cần DB, không cần API key)
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.t169_classify import classify_diff, FIXTURES, TAXONOMY_SUFFIX  # noqa: E402

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


print('=== T169 classify_diff — 3 fixture bắt buộc (SPEC §3.9) ===')
for name_zh, d, g, want in FIXTURES:
    got, reason = classify_diff(name_zh, d, g)
    check(f'fixture {name_zh}: {d} vs {g} → {got}',
          got == want, f'(got {got}, want {want}) · {reason}')

print('\n=== Extra: word-boundary TAXONOMY (P1-2 — không substring) ===')
got, _ = classify_diff('安樂寺', 'An Lạc Tự', 'An Lạc Tự')
check('same text → NONE (không false taxonomy)', got == 'NONE', f'got {got}')

got, _ = classify_diff('安樂寺', 'An Lạc Tự', 'Chùa An Lạc')
check('寺 tự↔chùa → TAXONOMY_VARIANT', got == 'TAXONOMY_VARIANT', f'got {got}')

got, reason = classify_diff('降魔窟', 'Giáng Ma Quật', 'Hàng Ma Quật')
check('POLYPHONIC ưu tiên trước TAXONOMY', got == 'POLYPHONIC_CHAR', f'got {got}')

got, _ = classify_diff('白馬寺', 'Bạch Mã Tự', 'Bạch Mã Chùa')
check('Tự↔Chùa cùng chữ 寺 → TAXONOMY', got == 'TAXONOMY_VARIANT', f'got {got}')

print('\n=== Extra: giữ nguyên cặp nest bị cấm (P1-2) ===')
check('không có cặp nest viện/tự viện', ('viện', 'tự viện') not in TAXONOMY_SUFFIX.values())

print('\n=== Extra: PHONETIC_MISMATCH fallback ===')
got, _ = classify_diff('金山', 'Kim Sơn', 'Kim San')
check('lệch phiên âm (không đa âm) → PHONETIC_MISMATCH', got == 'PHONETIC_MISMATCH', f'got {got}')

got, _ = classify_diff('長安', 'Trường An', 'Tràng An')
check('長 đa âm trường↔tràng → POLYPHONIC_CHAR', got == 'POLYPHONIC_CHAR', f'got {got}')

print('\n=== Extra: validate input ===')
from scripts.t169_classify import classify_diff as cd2  # noqa: F811
try:
    cd2('abc def', 'A B', 'C D')
    check('name_zh không Hán → raise', False)
except ValueError:
    check('name_zh không Hán → raise', True)

print(f'\nT169 classify_diff: {PASS} PASS · {FAIL} FAIL')
sys.exit(1 if FAIL else 0)