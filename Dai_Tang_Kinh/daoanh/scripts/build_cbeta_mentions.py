#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_cbeta_mentions.py
=======================
Commit 1 — NEXUS POINT: ETL passage-level CBETA mentions (PERSON/PLACE in text).

Populate `cbeta_person_mentions` / `cbeta_place_mentions` từ bảng trung gian
`passage` + `passage_entity` (378,483 links đã có sẵn — additive, KHÔNG quét text).

Nguồn:
  - passage          : passage_id, text_id(=CBETA sigla), loc_ref (dạng "0-0196c-"), raw_text
  - passage_entity   : passage_id → entity_id (A... = person, PL... = place)

Đích:
  - cbeta_person_mentions(id, cbeta_text_sigla, dila_person_id, person_name_zh, juan, page, context_snippet)
  - cbeta_place_mentions (id, cbeta_text_sigla, dila_place_id,  place_name_zh,  juan, page, context_snippet)

Tên lấy từ `people` (name_zh) và `places_dila` (name_zh). Place ID chuẩn hóa về dạng dài
PLxxxxxxxxxxxx (14 ký tự). context_snippet = raw_text cắt còn ~200 ký tự.

Chạy (từ root daoanh):
  python scripts/build_cbeta_mentions.py             # apply
  python scripts/build_cbeta_mentions.py --dry-run   # chỉ xem
"""
import io
import os
import re
import sqlite3
import sys
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, '..', 'data', 'lineage.db')
DRY_RUN = '--dry-run' in sys.argv
SNIPPET_LEN = 200


def normalize_place_id(raw):
    if not raw:
        return None
    s = str(raw).strip()
    if s.startswith('PL') and len(s) < 15:
        num = s[2:]
        if num.isdigit():
            return 'PL' + num.zfill(12)
    return s


def main():
    mode = 'DRY-RUN' if DRY_RUN else 'APPLY'
    print(f'=== Nexus Commit 1 — Build CBETA person/place mentions [{mode}] ===')
    print(f'DB: {DB_PATH}')
    print(f'Date: {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # 1) passage → (sigla, loc_ref, raw_text)
    print('Step 1: load passage...')
    passages = {}
    for r in conn.execute('SELECT passage_id, text_id, loc_ref, raw_text FROM passage'):
        passages[r['passage_id']] = (r['text_id'], r['loc_ref'] or '', r['raw_text'] or '')
    print(f'  {len(passages):,} passages')

    # 2) names
    print('Step 2: load names...')
    person_name = {r['id']: r['name_zh'] for r in conn.execute("SELECT id, name_zh FROM people WHERE id LIKE 'A%'")}
    try:
        place_name = {r['id']: r['name_zh'] for r in conn.execute("SELECT id, name_zh FROM places_dila")}
    except Exception:
        place_name = {}
    print(f'  person names: {len(person_name):,} | place names: {len(place_name):,}')

    # 3) passage_entity → person/place mentions
    print('Step 3: build mentions...')
    person_mentions = []
    place_mentions = {}
    page_re = re.compile(r'\d+-(\d+[a-z]?)-')
    for r in conn.execute('SELECT passage_id, entity_id FROM passage_entity'):
        pid = r['passage_id']
        ent = r['entity_id']
        base = passages.get(pid)
        if not base:
            continue
        sigla, loc_ref, raw = base
        m = page_re.search(loc_ref)
        page = m.group(1) if m else ''
        snippet = raw.replace('\n', ' ').strip()[:SNIPPET_LEN]
        if ent.startswith('A'):
            person_mentions.append((sigla, ent, person_name.get(ent, ''), '', page, snippet))
        elif ent.startswith('PL'):
            norm = normalize_place_id(ent)
            if norm:
                place_mentions[norm] = (sigla, norm, place_name.get(norm, ''), '', page, snippet)

    print(f'  person mention rows: {len(person_mentions):,}')
    print(f'  place  mention rows: {len(place_mentions):,}')

    # Preview top counts
    from collections import Counter
    pc = Counter(x[0] for x in person_mentions)
    print('  persons per text:', dict(pc))
    if DRY_RUN:
        print('[DRY-RUN] Không thay đổi DB. Run again without --dry-run to apply.')
        conn.close()
        return

    # 4) Apply — idempotent: DELETE rồi INSERT (nguồn passage_entity là SSOT).
    print('Step 4: apply...')
    conn.execute("DELETE FROM cbeta_person_mentions")
    conn.execute("DELETE FROM cbeta_place_mentions")
    conn.executemany(
        "INSERT INTO cbeta_person_mentions "
        "(cbeta_text_sigla, dila_person_id, person_name_zh, juan, page, context_snippet) "
        "VALUES (?,?,?,?,?,?)",
        person_mentions,
    )
    conn.executemany(
        "INSERT INTO cbeta_place_mentions "
        "(cbeta_text_sigla, dila_place_id, place_name_zh, juan, page, context_snippet) "
        "VALUES (?,?,?,?,?,?)",
        place_mentions.values(),
    )
    conn.commit()

    np_ = conn.execute('SELECT COUNT(*) FROM cbeta_person_mentions').fetchone()[0]
    npl = conn.execute('SELECT COUNT(*) FROM cbeta_place_mentions').fetchone()[0]
    print(f'  cbeta_person_mentions: {np_:,}')
    print(f'  cbeta_place_mentions : {npl:,}')
    print('[DONE]')
    conn.close()


if __name__ == '__main__':
    main()
