# -*- coding: utf-8 -*-
"""CLI BUDDHIST-HAN-VI-BENCH (T167 Phase 7).

python -m scripts.buddhist_han_vi_bench select [--size 500] [--seed 20260925] [--out PATH]
python -m scripts.buddhist_han_vi_bench score  [--set PATH] [--out PATH]
python -m scripts.buddhist_han_vi_bench report [--set PATH] [--out PATH]
python -m scripts.buddhist_han_vi_bench human  <passage_id> --sf 4 --dr 5 --cf 3 --te 4 --cp 5 --df 4 --cs 3 --oa 5 --hs 4 [--reviewer NAM]
python -m scripts.buddhist_han_vi_bench show   [--set PATH] [--limit 10]
"""
import argparse
import io
import json
import os
import sys
from datetime import datetime

from . import (BASE, DATA_DIR, DEFAULT_SET, DEFAULT_SCORED, DEFAULT_HUMAN,
               AUTO_METRICS, HUMAN_METRICS)
from .select import select, load_set
from .score import score_all

sys.stdout.reconfigure(encoding='utf-8')

HUMAN_LABELS = {
    'sf': 'semantic_fidelity',
    'dr': 'doctrinal_fidelity',
    'cf': 'context_consistency',
    'te': 'terminology_accuracy',
    'cp': 'canonical_names_accuracy',
    'df': 'doctrinal_fidelity',
    'cs': 'context_consistency',
    'oa': 'omission_addition',
    'hs': 'human_acceptance',
}

HUMAN_SCALE = {
    'semantic_fidelity': (1, 5), 'doctrinal_fidelity': (1, 5),
    'context_consistency': (1, 5), 'terminology_accuracy': (1, 5),
    'canonical_names_accuracy': (1, 5), 'omission_addition': (1, 5),
    'human_acceptance': (1, 5),
}


def cmd_select(args):
    out = os.path.join(DATA_DIR, args.out or 'buddhist_han_vi_bench.json')
    select(size=args.size or 500, seed=args.seed or 20260925, out_path=out)


def cmd_score(args):
    score_all(set_path=args.set, out_path=args.out)


def _fmt(items, limit=None):
    lines = [f"{'passage_id':<40} {'cat':<20} {'tr':<3} term  canon  oa"]
    for i in items[:limit if limit else len(items)]:
        t = i.get('terminology_accuracy')
        c = i.get('canonical_names_accuracy')
        oa = i.get('omission_addition') or ''
        lines.append(f"{i['passage_id']:<40} {i.get('category',''):<20} "
                     f"{'Y' if i.get('has_translation') else 'N':<3} "
                     f"{str(t):<6} {str(c):<6} {oa}")
    return '\n'.join(lines)


def cmd_report(args):
    data = load_set(args.set)
    scored_path = args.out or DEFAULT_SCORED
    if os.path.exists(scored_path):
        scored = json.load(io.open(scored_path, encoding='utf-8'))
    else:
        scored = score_all(set_path=args.set, out_path=scored_path)
    print(f'=== BUDDHIST-HAN-VI-BENCH report — {data["meta"]["name"]} ===')
    for k, v in scored['summaries']['overall'].items():
        print(f'  {k}: {v}')
    print('--- by category ---')
    for c, sub in scored['summaries']['by_category'].items():
        print(f"  {c:<22} n={sub['n']:<4} tr={sub['with_translation']:<4} "
              f"term_avg={sub.get('terminology_avg', {}).get('terminology_accuracy_avg')}")
    print()
    print(_fmt(scored['items'], limit=10))


def cmd_human(args):
    """Ghi điểm CON NGƯỜI cho 1 passage vào human file (benchmark review, 1-5)."""
    human_path = args.out or DEFAULT_HUMAN
    existing = {}
    if os.path.exists(human_path):
        existing = json.load(io.open(human_path, encoding='utf-8'))
    # validate passage_id thuộc benchmark set
    bench = load_set(args.set)
    pid = args.passage_id
    item = next((i for i in bench['items'] if i['passage_id'] == pid), None)
    if not item:
        print(f'❌ {pid} không nằm trong benchmark set.'); return 1
    rec = existing.get(pid) or {}
    for key, label in HUMAN_LABELS.items():
        v = getattr(args, key, None)
        if v is not None:
            if not (1 <= v <= 5):
                print(f'❌ {label} ngoài khoảng 1-5.'); return 1
            rec[label] = v
    rec['reviewer'] = args.reviewer or 'admin'
    rec['scored_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    existing[pid] = rec
    with io.open(human_path, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    print(f'✅ Đã ghi human score cho {pid} → {human_path}')
    for k, v in rec.items():
        print(f'   {k}: {v}')
    return 0


def cmd_show(args):
    bench = load_set(args.set)
    print(f'=== {bench["meta"]["name"]} — {len(bench["items"])} items, seed {bench["meta"]["seed"]} ===')
    for c, n in bench['meta']['selected_by_category'].items():
        print(f'  {c:<22} {n}')
    if args.limit:
        for it in bench['items'][:args.limit]:
            print(f"  {it['passage_id']:<40} {it['category']}")


def main(argv=None):
    p = argparse.ArgumentParser(prog='buddhist_han_vi_bench')
    sub = p.add_subparsers(dest='cmd')

    ps = sub.add_parser('select')
    ps.add_argument('--size', type=int)
    ps.add_argument('--seed', type=int)
    ps.add_argument('--out')
    ps.set_defaults(fn=cmd_select)

    pc = sub.add_parser('score')
    pc.add_argument('--set', default=DEFAULT_SET)
    pc.add_argument('--out')
    pc.set_defaults(fn=cmd_score)

    pr = sub.add_parser('report')
    pr.add_argument('--set', default=DEFAULT_SET)
    pr.add_argument('--out')
    pr.set_defaults(fn=cmd_report)

    ph = sub.add_parser('human')
    ph.add_argument('passage_id')
    for k in HUMAN_LABELS:
        ph.add_argument('--' + k, type=int)
    ph.add_argument('--reviewer', default='admin')
    ph.add_argument('--set', default=DEFAULT_SET)
    ph.add_argument('--out')
    ph.set_defaults(fn=cmd_human)

    pshow = sub.add_parser('show')
    pshow.add_argument('--set', default=DEFAULT_SET)
    pshow.add_argument('--limit', type=int, default=10)
    pshow.set_defaults(fn=cmd_show)

    args = p.parse_args(argv)
    if not hasattr(args, 'fn'):
        p.print_help(); return 1
    return args.fn(args)


if __name__ == '__main__':
    sys.exit(main())