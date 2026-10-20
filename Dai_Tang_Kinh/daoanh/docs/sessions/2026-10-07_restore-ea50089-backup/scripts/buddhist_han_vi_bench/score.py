# -*- coding: utf-8 -*-
"""BUDDHIST-HAN-VI-BENCH — score deterministic trên benchmark set.

Load benchmark set (buddhist_han_vi_bench.json) → với MỖI item:
  - Lấy bản dịch hiện hành từ translation_segments (nếu có).
  - Reuse script/translation_validator.py (load qua importlib) để có các layer
    A-G deterministic.
  - Tính metric deterministic:
      terminology_accuracy      : glossary terms trong passage có trong bản dịch? (đếm)
      canonical_names_accuracy  : place/person (places.json + namevi_map) chứa trong bản dịch thành Hán?
      context_consistency       : dùng PREV/NEXT context (alignment/seq) trong bản dịch?
      omission_addition         : layer C (echo, ratio, alignment count)
  - Các metric CẦN NGƯỜI (semantic_fidelity, doctrinal_fidelity,
    human_acceptance) → để null + human_required: true — KHÔNG bịa số.

Output: buddhist_han_vi_bench_scored.json {meta, items, summaries}
"""
import importlib.util
import io
import json
import os
import re
import sqlite3
import sys
from datetime import datetime

from . import BASE, DATA_DIR, DB_PATH, DEFAULT_SET, DEFAULT_SCORED
from .select import load_set

sys.stdout.reconfigure(encoding='utf-8')


def _load_validator():
    path = os.path.join(BASE, 'scripts', 'translation_validator.py')
    spec = importlib.util.spec_from_file_location('translation_validator', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_glossary():
    try:
        with io.open(os.path.join(BASE, 'data', 'glossaries', 'vi-buddhist.json'),
                     'r', encoding='utf-8') as f:
            return json.load(f).get('terms', {})
    except Exception:
        return {}


def load_places_zh():
    p = os.path.join(BASE, 'data', 'places.json')
    try:
        with io.open(p, 'r', encoding='utf-8') as f:
            return {x['nameChinese'] for x in json.load(f).get('places', []) if
                    len((x.get('nameChinese') or '')) >= 2}
    except Exception:
        return set()


def _current_translation(con, passage_id):
    return con.execute(
        "SELECT * FROM translation_segments WHERE passage_id=? AND "
        "translation_status IN ('completed','needs_review','reviewed') "
        "ORDER BY revision_no DESC, created_at DESC LIMIT 1",
        (passage_id,)).fetchone()


def score(item, con, V, glossary, places_zh):
    """Tính metric deterministic cho 1 item. Trả dict metric + metadata."""
    passage_id = item['passage_id']
    zh = item.get('zh') or ''
    seg = _current_translation(con, passage_id)

    res = {
        'passage_id': passage_id,
        'category': item['category'],
        'seq': item['seq'],
        'has_translation': bool(seg),
    }

    if not seg:
        for m in ('terminology_accuracy', 'canonical_names_accuracy',
                  'context_consistency', 'omission_addition'):
            res[m] = None
        res['note'] = 'chưa có bản dịch — chờ worker/job'
        res['human_required'] = True
        return res

    seg = dict(seg)
    vi = seg.get('translation_text') or ''
    res['translation_id'] = seg.get('translation_id')

    # Layer B/C revalidate (deterministic, from validator)
    try:
        vres = V.validate_translation(seg['translation_id'], con)
        layers = {l['layer']: l for l in vres.get('layers', [])}
        res['validator_overall'] = vres.get('overall')
        for l in layers:
            res['layer_' + l] = {'status': layers[l]['status'],
                                 'message': (layers[l]['message'] or '')[:200]}
    except Exception as ve:
        res['validator_error'] = str(ve)[:200]

    # terminology_accuracy: glossary terms xuất hiện trong Hán passage →
    # bản dịch có chứa ít nhất 1 trong các giá trị vi tương ứng không
    hits = totals = 0
    for zh_t, vi_t in glossary.items():
        if zh_t and zh_t in zh:
            totals += 1
            cands = [vi_t] if isinstance(vi_t, str) else list(vi_t)
            if any(c and (c in vi or zh_t in vi) for c in cands):
                hits += 1
    res['terminology_accuracy'] = round(hits / totals, 3) if totals else None
    res['terminology_total'] = totals

    # canonical_names_accuracy: place names (Hán) trong passage → có trong bản dịch?
    phits = ptotals = 0
    for p in places_zh:
        if p in zh:
            ptotals += 1
            if p in vi:
                phits += 1
    res['canonical_names_accuracy'] = round(phits / ptotals, 3) if ptotals else None
    res['canonical_names_total'] = ptotals

    # context_consistency: seq liền kề có bản dịch sinh ra? (định lượng sơ bộ)
    # đo bằng: passage có câu cụt/cần ngữ cảnh nhưng vẫn có bản dịch độc lập →
    # nếu có context_dependent feature + bản dịch ko trống → cho điểm tạm (ko tự bịa)
    cctx = con.execute(
        "SELECT COUNT(*) c FROM passage_translation_alignment "
        "WHERE passage_id=? AND alignment_type='segment_full'",
        (passage_id,)).fetchone()
    res['alignment_count'] = cctx['c'] if cctx else 0
    # metric context: tạm đặt None (cần human) — nhưng ghi lại số liệu thô nguồn
    res['context_consistency'] = None
    res['context_source_zh'] = zh[:60]

    # omission_addition: layer C (echo/ratio/alignment) — deterministic
    lc = res.get('layer_C', {})
    res['omission_addition'] = lc.get('status')
    res['omission_addition_msg'] = (lc.get('message') or '')[:120]
    res['ratio_hint'] = round(len(vi) / max(1, len(zh)), 3)

    # human-required metrics — KHÔNG bịa
    res['semantic_fidelity'] = None
    res['doctrinal_fidelity'] = None
    res['human_acceptance'] = None
    res['human_required'] = True
    res['review_status'] = seg.get('quality_status')
    return res


def score_all(set_path=None, out_path=None):
    data = load_set(set_path)
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.row_factory = sqlite3.Row
    V = _load_validator()
    glossary = load_glossary()
    places_zh = load_places_zh()

    items = [score(it, con, V, glossary, places_zh) for it in data['items']]
    con.close()

    summaries = _summarize(items)
    out = {'meta': data['meta'],
           'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
           'summaries': summaries,
           'items': items}
    op = out_path or DEFAULT_SCORED
    os.makedirs(os.path.dirname(op), exist_ok=True)
    with io.open(op, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f'✅ Scored {len(items)} items → {op}')
    for k, v in summaries.get('overall', {}).items():
        print(f'   {k}: {v}')
    return out


def _summarize(items):
    from functools import reduce
    total = len(items)
    with_tr = sum(1 for i in items if i['has_translation'])
    agg = {}
    for m in ('terminology_accuracy', 'canonical_names_accuracy'):
        vals = [i[m] for i in items if i[m] is not None]
        agg[m + '_avg'] = round(sum(vals) / len(vals), 3) if vals else None
        agg[m + '_n'] = len(vals)
    oa = [i['omission_addition'] for i in items if i['has_translation']]
    agg['omission_addition_dist'] = {
        'PASS': oa.count('PASS'), 'REVIEW': oa.count('REVIEW'), 'FAIL': oa.count('FAIL')}
    by_cat = {}
    for c in sorted({i['category'] for i in items}):
        sub = [i for i in items if i['category'] == c]
        by_cat[c] = {
            'n': len(sub),
            'with_translation': sum(1 for i in sub if i['has_translation']),
            'terminology_avg': agg.__class__(
                {m + '_avg': (round(sum(i[m] for i in sub if i[m] is not None) /
                                     max(1, sum(1 for i in sub if i[m] is not None)), 3)
                               if any(i[m] is not None for i in sub) else None)}),
        }
    return {'overall': {'total': total, 'with_translation': with_tr, **agg},
            'by_category': by_cat}


if __name__ == '__main__':
    score_all()