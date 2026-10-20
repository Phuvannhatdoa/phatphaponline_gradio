# -*- coding: utf-8 -*-
"""T167 Phase 8 GOLD — tests exporter dataset training-ready.

Kiểm tra (additive, KHÔNG ghi vào DB thật — chỉ READ + write vào temp):
  1. export_gold với human file rỗng → 0 GOLD rows (KHÔNG bịa, trung thực).
  2. human file có 1 passage đạt acceptance ≥ 4 + có bản dịch completed/reviewed
     → 1 GOLD row với đầy đủ source/provenance/ruleset/review.
  3. passage acceptance < ngưỡng → không vào GOLD.
  4. passage chưa có bản dịch completed/reviewed → không vào GOLD (skip nb).
  5. record GOLD có 4 nhóm: source, final_translation, provenance, ruleset, review.
  6. output JSONL + summary nhất quán.

Chạy: python -X utf8 tests/test_t167_gold.py
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

from scripts.buddhist_han_vi_bench import DB_PATH  # noqa: E402
from scripts.buddhist_han_vi_bench.gold import export_gold, DEFAULT_GOLD  # noqa: E402
from scripts.buddhist_han_vi_bench.select import load_set  # noqa: E402

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


def _pid_with_translation(con):
    """Lấy passage_id trong bench có bản dịch completed/reviewed."""
    from scripts.buddhist_han_vi_bench import DEFAULT_SET
    bench = load_set(DEFAULT_SET)
    pids = [it['passage_id'] for it in bench['items']]
    ph = ','.join('?' * len(pids))
    row = con.execute(
        "SELECT passage_id FROM translation_segments WHERE passage_id IN (" + ph +
        ") AND translation_status IN ('completed','reviewed') LIMIT 1", pids).fetchone()
    return row and row[0]


def _write_human(path, data):
    with io.open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    if not os.path.exists(DB_PATH):
        print('❌ DB thật không tồn tại:', DB_PATH)
        return 1
    bench = load_set()
    if not bench or not bench.get('items'):
        print('❌ Không load được benchmark set (chạy select trước).')
        return 1

    print('=== TEST GOLD EXPORT (Phase 8) ===')
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.row_factory = sqlite3.Row
    pid = _pid_with_translation(con)
    if not pid:
        print('❌ Chưa có passage nào trong bench có bản dịch completed/reviewed '
              '(worker chưa translate benchmark set) — cần ít nhất 1 passage có bản dịch.')
        con.close()
        return 1
    item = next(i for i in bench['items'] if i['passage_id'] == pid)
    print(f'-- fixture thật: {pid} | {item["category"]} | seq {item["seq"]} --')

    tmp = tempfile.mkdtemp(prefix='t167_gold_')

    # 1) không có human score → 0 GOLD (không bịa)
    print('-- 1) no human score --')
    out1 = os.path.join(tmp, 'gold_empty.jsonl')
    n1, s1 = export_gold(human_path=os.path.join(tmp, 'nohuman.json'),
                         out_path=out1, verbose=False)
    check('export 0 GOLD row khi không có human score', n1 == 0, f'got {n1}')
    check('summary ghi nhận skip đúng', s1['skipped'].get('chưa có human score (đủ 3 metric người)') >= 1)
    check('summary consistent', s1['bench_size'] == len(bench['items']))

    # 2) human score đủ + acceptance ≥ 4 + có bản dịch → 1 GOLD row
    print('-- 2) approved passage --')
    hpath = os.path.join(tmp, 'human.json')
    _write_human(hpath, {
        pid: {
            'semantic_fidelity': 4, 'doctrinal_fidelity': 5,
            'human_acceptance': 5, 'reviewer': 'giaotho', 'scored_at': '2026-09-26 12:00:00',
        }
    })
    out2 = os.path.join(tmp, 'gold_ok.jsonl')
    n2, s2 = export_gold(human_path=hpath, out_path=out2, verbose=False)
    check('1 GOLD row cho passage approved', n2 == 1, f'got {n2}')
    lines = [json.loads(l) for l in io.open(out2, encoding='utf-8').read().strip().split('\n') if l.strip()]
    r = lines[0]
    check('record có source', 'source' in r and r['source'] == item['zh'])
    check('record có final_translation (Văn bản Việt không rỗng)',
          bool(r.get('final_translation')))
    check('record có provenance passage_id/seq',
          r['provenance']['passage_id'] == pid and r['provenance']['seq'] == item['seq'])
    check('record có ruleset_id/version', bool(r['ruleset']['ruleset_id'])
          and bool(r['ruleset']['ruleset_version']))
    check('record có review đầy đủ → human_acceptance=5',
          r['review'].get('human_acceptance') == 5 and r['review'].get('semantic_fidelity') == 4)
    check('no draft fields leak (source_type cbeta)',
          r['provenance'].get('source_type') == 'cbeta')

    # 3) acceptance dưới ngưỡng → không vào GOLD (buffer threshold)
    print('-- 3) acceptance < ngưỡng --')
    hpath2 = os.path.join(tmp, 'human_low.json')
    _write_human(hpath2, {pid: {
        'semantic_fidelity': 3, 'doctrinal_fidelity': 3,
        'human_acceptance': 2, 'reviewer': 'giaotho', 'scored_at': '2026-09-26 12:00:00'}})
    n3, s3 = export_gold(human_path=hpath2, out_path=os.path.join(tmp, 'gold_low.jsonl'),
                         verbose=False, min_acceptance=4)
    check('0 GOLD row khi acceptance < ngưỡng', n3 == 0, f'got {n3}')
    check('skip reason nổi rõ', s3['skipped'].get('human_acceptance < ngưỡng') == 1)

    # 4) human score cho passage KHÔNG có bản dịch → skip 'no translation'
    print('-- 4) approved nhưng chưa có bản dịch --')
    no_tr_pid = next(i['passage_id'] for i in bench['items']
                     if i['passage_id'] != pid)
    hpath3 = os.path.join(tmp, 'human_notr.json')
    _write_human(hpath3, {no_tr_pid: {
        'semantic_fidelity': 5, 'doctrinal_fidelity': 5,
        'human_acceptance': 5, 'reviewer': 'giaotho', 'scored_at': '2026-09-26 12:00:00'}})
    n4, s4 = export_gold(human_path=hpath3, out_path=os.path.join(tmp, 'gold_notr.jsonl'),
                         verbose=False)
    check('0 GOLD row cho approved passage chưa có bản dịch', n4 == 0, f'got {n4}')
    check('skip reason có translation chưa có', s4['skipped'].get('chưa có bản dịch completed/reviewed') == 1)

    # 5) đầu ra JSONL parse được + summary nhất quán
    print('-- 5) deterministic --')
    out5 = os.path.join(tmp, 'gold_repeat.jsonl')
    n5a, _ = export_gold(human_path=hpath, out_path=out5, verbose=False)
    n5b, _ = export_gold(human_path=hpath, out_path=out5, verbose=False)
    check('chạy 2 lần cùng kết quả', n5a == n5b == 1)

    con.close()
    print()
    print(f'PASS={PASS} FAIL={FAIL}')
    return 1 if FAIL else 0


if __name__ == '__main__':
    sys.exit(main())