# -*- coding: utf-8 -*-
"""BUDDHIST-HAN-VI-BENCH — Phase 8 GOLD DATASET export.

Tạo training-ready dataset từ benchmark đã được NGƯỜI duyệt:
  source (Hán) + final translation (Việt) + provenance + ruleset version + review metadata.

Quy tắc (T167 § PHASE 8):
  - Chỉ passage đạt **L3 human-approved** mới vào GOLD: passage phải có **đủ**
    metric người (semantic_fidelity, doctrinal_fidelity, human_acceptance) TRONG
    file `buddhist_han_vi_bench_human.json` VÀ `human_acceptance >= ngưỡng`
    (default 4/5).
  - Bản dịch final lấy từ `translation_segments` (completed/reviewed, revision mới nhất).
  - Output JSONL, separable khỏi drafts (chỉ chứa approved final).
  - KHÔNG fine-tune trong T167 — chỉ export dataset cho future fine-tune task.
  - KHÔNG BỊA điểm: nếu chưa có human score → 0 dòng GOLD (trung thực).

Usage:
  python -m scripts.buddhist_han_vi_bench gold [--human PATH] [--set PATH]
      [--out PATH] [--min-acceptance 4] [--db PATH]
"""
import io
import json
import os
import sqlite3
import sys
from datetime import datetime

from . import (BASE, DATA_DIR, DB_PATH, DEFAULT_SET, DEFAULT_HUMAN,
               HUMAN_METRICS)
from .select import load_set

sys.stdout.reconfigure(encoding='utf-8')

# tương ứng DEFAULT_RULESET_ID = 't167-constitution-v1' trong app.py (T167). Để
# bench package tự đủ (không import app.py nặng). Given per task doc line 164.
DEFAULT_RULESET_ID = 't167-constitution-v1'

DEFAULT_GOLD = os.path.join(DATA_DIR, 'buddhist_han_vi_bench_gold.jsonl')
MIN_ACCEPTANCE_DEFAULT = 4

# quality_status coi là đã được review (L3) — bản dịch trong bench được người duyệt
# qua `human` CLI (human file), nên L3 = human score đủ + acceptance ≥ ngưỡng.
GOLD_TRANSLATION_STATUSES = ('completed', 'reviewed')


def load_human(human_path=None):
    """Đọc file human scores (dict passage_id → {metric: value}). Thiếu → {}."""
    path = human_path or DEFAULT_HUMAN
    if not os.path.exists(path):
        return {}
    try:
        with io.open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _latest_translation(con, passage_id):
    """Bản dịch final mới nhất cho passage (completed/reviewed)."""
    return con.execute(
        "SELECT translation_id, translation_text, quality_status, ruleset_id, "
        "created_at FROM translation_segments "
        "WHERE passage_id=? AND translation_status IN ('completed','reviewed') "
        "ORDER BY revision_no DESC, created_at DESC LIMIT 1",
        (passage_id,)).fetchone()


def _ruleset_version(con):
    """ruleset_version của ruleset canonical (t167-constitution-v1) — mặc định DEFAULT."""
    row = con.execute(
        "SELECT ruleset_version FROM translation_rulesets WHERE is_canonical=1 "
        "ORDER BY updated_at DESC LIMIT 1").fetchone()
    return row and row[0] or DEFAULT_RULESET_ID


def export_gold(human_path=None, set_path=None, out_path=None, db_path=None,
                min_acceptance=MIN_ACCEPTANCE_DEFAULT, verbose=True):
    """Xuất GOLD JSONL. Trả (record_count, summary dict). Không bịa điểm."""
    bench = load_set(set_path)
    humans = load_human(human_path)
    db = db_path or DB_PATH
    con = sqlite3.connect(db, timeout=30)
    con.row_factory = sqlite3.Row
    ruleset_ver = _ruleset_version(con)

    def scoring_newest(first, second):
        if first is None:
            return second
        if second is None:
            return first
        return first if (first[1] or '') >= (second[1] or '') else second

    records = []
    skipped = {
        'chưa có human score (đủ 3 metric người)': 0,
        'human_acceptance < ngưỡng': 0,
        'chưa có bản dịch completed/reviewed': 0,
    }
    for item in bench['items']:
        pid = item['passage_id']
        hs = humans.get(pid)
        if not hs:
            skipped['chưa có human score (đủ 3 metric người)'] += 1
            continue
        have_all = all(hs.get(m) is not None for m in HUMAN_METRICS)
        if not have_all:
            skipped['chưa có human score (đủ 3 metric người)'] += 1
            continue
        if (hs.get('human_acceptance') or 0) < min_acceptance:
            skipped['human_acceptance < ngưỡng'] += 1
            continue

        seg = _latest_translation(con, pid)
        if not seg:
            skipped['chưa có bản dịch completed/reviewed'] += 1
            continue

        rec = {
            'source': item.get('zh') or '',
            'final_translation': seg['translation_text'] or '',
            'provenance': {
                'passage_id': pid,
                'category': item.get('category'),
                'seq': item.get('seq'),
                'loc_ref': item.get('loc_ref'),
                'juan': item.get('juan'),
                'translation_id': seg['translation_id'],
                'source_type': item.get('source_type', 'cbeta'),
            },
            'ruleset': {
                'ruleset_id': seg['ruleset_id'] or DEFAULT_RULESET_ID,
                'ruleset_version': ruleset_ver,
            },
            'review': {},
        }
        for m in HUMAN_METRICS:
            rec['review'][m] = hs.get(m)
        rec['review']['human_acceptance'] = hs.get('human_acceptance')
        if hs.get('reviewer'):
            rec['review']['reviewer'] = hs['reviewer']
        if hs.get('scored_at'):
            rec['review']['scored_at'] = hs['scored_at']
        records.append(rec)

    con.close()

    op = out_path or DEFAULT_GOLD
    os.makedirs(os.path.dirname(op), exist_ok=True)
    with io.open(op, 'w', encoding='utf-8') as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')

    summary = {
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'min_acceptance': min_acceptance,
        'bench_size': len(bench['items']),
        'human_scored': len(humans),
        'gold_rows': len(records),
        'ruleset_version': ruleset_ver,
        'skipped': skipped,
    }
    if verbose:
        print(f'=== GOLD export — {op} ===')
        print(f'  bench: {summary["bench_size"]} · human scored: {summary["human_scored"]} '
              f'· GOLD: {summary["gold_rows"]} rows (acceptance ≥ {min_acceptance})')
        for why, n in skipped.items():
            print(f'    skip {n:<4} {why}')
    return len(records), summary