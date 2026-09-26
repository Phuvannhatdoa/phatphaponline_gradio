# -*- coding: utf-8 -*-
"""BUDDHIST-HAN-VI-BENCH — thanh chọn 500 real CBETA passages + tag category.

Thanh chọn DETERMINISTIC: không dùng random — mỗi passage được đo bằng rules có
thật (glossary + places + cấu trúc Hán văn), sau đó gán KHÔNG-trùng-lặp vào 100%
1 category theo thứ tự ưu tiên (verse → ... → ordinary). Mỗi category chọn filter
đã được validate thật trên DB (feasibility pools đều ≥ 335 trừ những pool nhỏ hơn
được ưu tiên trước).

10 category (spec Phase 7): ordinary_classical, buddhist_terminology,
person_names, place_names, titles, long_syntax, repetitive_canonical, polysemy,
verse, context_dependent.

Output: JSON {meta, categories, items: [{passage_id, seq, category,
features, zh, loc_ref, juan}]} — KHÔNG bịa passage.
"""
import io
import json
import os
import re
import sqlite3
import sys

from . import BASE, DATA_DIR, DB_PATH

sys.stdout.reconfigure(encoding='utf-8')

DEFAULT_SIZE = 500
DEFAULT_SEED = 20260925

ZH = re.compile(r'[\u4e00-\u9fff]')

# Thứ tự ưu tiên gán category (không trùng lặp). Category hiếm đi trước
# (verse, repetitive, title) để không bị category phổ biến nuốt mất passages.
PRIORITY = [
    'verse', 'repetitive_canonical', 'titles', 'context_dependent',
    'long_syntax', 'person_names', 'place_names', 'buddhist_terminology',
    'polysemy', 'ordinary_classical',
]

# Regex detector — đã kiểm feasibility (pool thật trên DB):
PERSON_SUFFIX = re.compile(r'[\u4e00-\u9fff]{1,4}(?:禪師|法師|沙門|比丘|尊者|羅漢|論師|律師)')
PERSON_LIST = re.compile('|'.join([
    '釋迦', '牟尼', '如來', '世尊', '觀音', '文殊', '普賢', '地藏', '彌勒',
    '阿彌陀', '維摩', '羅睺羅', '舍利弗', '目犍連', '迦葉', '阿難', '優波離',
    '富樓那', '須菩提', '龍樹', '提婆', '馬鳴', '世親', '鳩摩羅什', '佛圖澄',
    '道安', '慧遠', '僧肇', '竺法護', '康僧會', '安世高', '支婁迦讖',
    '曇無讖', '法顯', '玄奘', '義淨', '道宣', '智顗', '善導', '慧能', '神秀']))
TITLE_RE = re.compile('|'.join([
    '皇帝', '天子', '陛下', '太后', '皇后', '太子', '丞相', '太尉',
    '太守', '刺史', '將軍', '尚書']))
VERSE_TRIG = re.compile(r'偈|頌')
REP_TRIG = re.compile(r'爾時|如是我聞|一時|有[\u4e00-\u9fff]{1,4}者')


def load_places():
    """places.json → dict nameChinese → [records] (thật từ DILA)."""
    p = os.path.join(BASE, 'data', 'places.json')
    try:
        with io.open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
        out = {}
        for x in data.get('places', []):
            zh = (x.get('nameChinese') or '').strip()
            if len(zh) >= 2:
                out.setdefault(zh, []).append(x)
        return out
    except Exception:
        return {}


def load_glossary_terms():
    """vi-buddhist.json terms → dict Hán → Vi (dùng category terminology)."""
    p = os.path.join(BASE, 'data', 'glossaries', 'vi-buddhist.json')
    try:
        with io.open(p, 'r', encoding='utf-8') as f:
            return json.load(f).get('terms', {})
    except Exception:
        return {}


def _detect(zh, terms, places):
    f = {
        'verse': bool(VERSE_TRIG.search(zh)),
        'repetitive_canonical': bool(REP_TRIG.search(zh)),
        'titles': bool(TITLE_RE.search(zh)),
        'context_dependent': (bool(re.search(r'[之其此彼]', zh)) and not zh.rstrip().endswith('。')) or
                             bool(re.match(r'^(之|其|此|彼|斯)', zh)),
        'long_syntax': len(zh) >= 70,
        'person_names': bool(PERSON_SUFFIX.search(zh)) or bool(PERSON_LIST.search(zh)),
        'place_names': any(k in zh for k in places),
        'buddhist_terminology': any(t and t in zh for t in terms),
        'polysemy': sum(1 for p in ('道', '法', '經', '師', '行', '為', '見', '得', '說', '入', '受', '坐', '白') if p in zh) >= 3,
        'ordinary_classical': False,  # set sau
    }
    return f


def select(size=None, seed=None, out_path=None):
    """Chọn size passage THẬT deterministically → list item dict + meta."""
    size = size or DEFAULT_SIZE
    seed = seed or DEFAULT_SEED
    out_path = out_path or os.path.join(DATA_DIR, 'buddhist_han_vi_bench.json')

    con = sqlite3.connect(DB_PATH, timeout=30)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT passage_id, sequence_no, original_zh, juan, loc_ref FROM text_passages "
        "WHERE work_id='T50n2060' ORDER BY sequence_no").fetchall()
    n_total = len(rows)
    con.close()

    glossary = load_glossary_terms()
    places = load_places()

    # 1) gán KHÔNG-trùng: mỗi passage → 1 category (category hiếm đi trước)
    buckets = {c: [] for c in PRIORITY}
    for r in rows:
        zh = r['original_zh']
        f = _detect(zh, glossary, places)
        f['ordinary_classical'] = not any(f[k] for k in PRIORITY if k != 'ordinary_classical')
        assigned = False
        for c in PRIORITY:
            if f[c]:
                buckets[c].append({
                    'passage_id': r['passage_id'], 'seq': r['sequence_no'],
                    'zh': zh[:100], 'juan': r['juan'], 'loc_ref': r['loc_ref'],
                    'features': {k: bool(v) for k, v in f.items()}})
                assigned = True
                break
        if not assigned:  # không khớp gì (xưa rồi) → ordinary
            buckets['ordinary_classical'].append({
                'passage_id': r['passage_id'], 'seq': r['sequence_no'],
                'zh': zh[:100], 'juan': r['juan'], 'loc_ref': r['loc_ref'],
                'features': {k: False for k in PRIORITY}})
            buckets['ordinary_classical'][-1]['features']['ordinary_classical'] = True

    # 2) chọn stratified: mỗi category lấy gần bằng nhau (round-robin theo tỉ lệ pool)
    per_target = max(size // len(PRIORITY), 1)

    def _spread(ids, k):
        if not ids:
            return []
        step = max(1, len(ids) / max(1, k))
        return [ids[int(i * step)] for i in range(min(k, len(ids)))]

    picked = []
    seen = set()
    # mỗi category: lấy spread các item chưa dùng (đảm bảo trải rộng khắp văn bản)
    for c in PRIORITY:
        cand = [it for it in buckets[c] if it['passage_id'] not in seen]
        chosen = _spread(cand, per_target)
        for it in chosen:
            if len(picked) >= size:
                break
            if it['passage_id'] in seen:
                continue
            seen.add(it['passage_id'])
            item = dict(it)
            item['category'] = c
            picked.append(item)
    # nếu chưa đủ 500 → bổ sung tuần tự (ưu tiên category nào còn thiếu nhiều)
    if len(picked) < size:
        for c in PRIORITY:
            for it in buckets[c]:
                if len(picked) >= size:
                    break
                if it['passage_id'] in seen:
                    continue
                seen.add(it['passage_id'])
                item = dict(it)
                item['category'] = c
                picked.append(item)

    meta = {
        'name': 'buddhist-han-vi-bench-v1',
        'description': '500 real CBETA T50n2060 passages, category-tagged, deterministic',
        'size': size, 'seed': seed, 'total_passages_in_db': n_total,
        'category_pools': {c: len(buckets[c]) for c in PRIORITY},
        'selected_by_category': _count_by_cat(picked),
        'built_at': __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'db': DB_PATH,
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with io.open(out_path, 'w', encoding='utf-8') as f:
        json.dump({'meta': meta, 'items': picked}, f, ensure_ascii=False, indent=2)
    print(f'✅ Chọn {len(picked)}/{size} passage thật (seed={seed}) → {out_path}')
    print('   Phân bố:', _count_by_cat(picked))
    return picked, meta


def _count_by_cat(items):
    d = {}
    for it in items:
        d[it['category']] = d.get(it['category'], 0) + 1
    return dict(sorted(d.items(), key=lambda kv: -kv[1]))


def load_set(path=None):
    path = path or os.path.join(DATA_DIR, 'buddhist_han_vi_bench.json')
    with io.open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


if __name__ == '__main__':
    select()