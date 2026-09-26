# -*- coding: utf-8 -*-
"""T169 — Phase 7 BUDDHIST-HAN-VI-BENCH: tests deterministic + thật dữ liệu.

Kiểm tra (additive, KHÔNG đụng DB thật — chỉ READ qua sqlite connect):
  1. select() deterministic: seed cố định + size cố định → cùng tập passage_id.
  2. 500 items đều từ DB thật (total_passages=9316, loc T50n2060).
  3. 10 category, mỗi category ~500//10=50, passage KHÔNG trùng.
  4. Không có passage nào 'features' rỗng / meta.enough.
  5. score() load được validator (importlib), metric deterministic không ném lỗi.
  6. scored items: has_translation đúng, metric human (None) + human_required.
  7. score_all lưu file scored vẫn còn 500 items.

Chạy: python -X utf8 tests/test_t167_benchmark.py
"""
import io
import json
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from scripts.buddhist_han_vi_bench import DB_PATH, CATEGORIES
from scripts.buddhist_han_vi_bench.select import DEFAULT_SIZE
from scripts.buddhist_han_vi_bench.select import DEFAULT_SIZE, select, load_set  # noqa: E402
from scripts.buddhist_han_vi_bench.score import score_all  # noqa: E402

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


def main():
    if not os.path.exists(DB_PATH):
        print('❌ DB thật không tồn tại:', DB_PATH)
        return 1
    if not os.path.exists(os.path.join(BASE, 'scripts', 'translation_validator.py')):
        print('❌ translation_validator.py thiếu — cần validator T166.')
        return 1

    print('=== TEST BUDDHIST-HAN-VI-BENCH (Phase 7) ===')

    # 1) determinism
    print('-- 1) Déterminisme select --')
    items1, meta1 = select(size=DEFAULT_SIZE, seed=20260925)
    items2, meta2 = select(size=DEFAULT_SIZE, seed=20260925)
    ids1 = [i['passage_id'] for i in items1]
    ids2 = [i['passage_id'] for i in items2]
    check('seed cố định → cùng 500 passage', set(ids1) == set(ids2),
          f'độ lệch {len(set(ids1) ^ set(ids2))}')

    # 2) thật dữ liệu
    print('-- 2) Dữ liệu thật --')
    check('đủ 500 items', len(items1) == DEFAULT_SIZE, f'got {len(items1)}')
    check('passage độc nhất', len(set(ids1)) == len(ids1))
    check('đúng 10 category trong set', set(i['category'] for i in items1) == set(CATEGORIES))
    check('mỗi passage có features dict đầy đủ',
          all(isinstance(i.get('features'), dict) and len(i['features']) == 10 for i in items1))
    check('meta tổng passage thật = 9316', meta1.get('total_passages_in_db') == 9316,
          f"got {meta1.get('total_passages_in_db')}")
    check('all items thuộc T50n2060', all('T50n2060' in i['passage_id'] for i in items1))

    # 3) cân bằng category
    print('-- 3) Phân bố category --')
    from collections import Counter
    cnt = Counter(i['category'] for i in items1)
    check('mỗi category ≥ 40', all(v >= 40 for v in cnt.values()), str(dict(cnt)))
    check('tổng = 500', sum(cnt.values()) == DEFAULT_SIZE)

    # 4) khớp DB thật
    print('-- 4) Khớp DB thật --')
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.row_factory = sqlite3.Row
    n_db = con.execute("SELECT COUNT(*) c FROM text_passages WHERE work_id='T50n2060'").fetchone()['c']
    con.close()
    check('số passage trong DB khớp meta', n_db == meta1['total_passages_in_db'],
          f'db {n_db} vs meta {meta1["total_passages_in_db"]}')

    # 5) load_set round-trip
    print('-- 5) load_set / JSON round-trip --')
    d = load_set()
    check('file benchmark tồn tại và 500 items', len(d.get('items', [])) == 500,
          f"got {len(d.get('items', []))}")

    # 6) score_all determinist + không ném lỗi (vào temp)
    print('-- 6) score_all --')
    tmpdir = tempfile.mkdtemp(prefix='t167_bench_')
    scored_path = os.path.join(tmpdir, 'scored_test.json')
    out = score_all(out_path=scored_path)
    check('scored có 500 items', len(out['items']) == 500)
    check('scored meta kế thừa size=500', out['meta'].get('size') == 500)
    sc = out['items']
    for it in sc:
        assert isinstance(it, dict)
    check('human metrics luôn None (không bịa)',
          all(it.get('semantic_fidelity') is None and
              it.get('doctrinal_fidelity') is None and
              it.get('human_acceptance') is None for it in sc))
    # với bản dịch tồn tại (pilot) phải có validator_overall
    with_tr = [it for it in sc if it['has_translation']]
    if with_tr:
        check('item có bản dịch → chạy validator', all('validator_overall' in it for it in with_tr))
    else:
        print('  (skipped) chưa có bản dịch — worker chưa translate benchmark set')

    print()
    print(f'PASS={PASS} FAIL={FAIL}')
    return 1 if FAIL else 0


if __name__ == '__main__':
    sys.exit(main())