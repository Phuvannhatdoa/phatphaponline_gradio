"""
T51d — Build CBETA Aggregate Mention Stats
Compute cbeta_place_mention_stats from passage_entity (378K links).

Usage:
    python scripts/t51d_build_aggregates.py           # dry-run
    python scripts/t51d_build_aggregates.py --apply   # apply
"""
import sqlite3
import io
import os
import sys
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, '..', 'data', 'lineage.db')
DRY_RUN = '--apply' not in sys.argv


def normalize_dila_id(raw_id: str) -> str:
    """Normalize PL000319 → PL000000000319 (14 chars total)."""
    if not raw_id or not raw_id.startswith('PL'):
        return raw_id
    suffix = raw_id[2:]
    if suffix.isdigit() and len(suffix) < 12:
        return 'PL' + suffix.zfill(12)
    return raw_id


def main():
    mode = 'DRY-RUN' if DRY_RUN else 'APPLY'
    print(f'=== T51d CBETA Aggregate Mention Stats [{mode}] ===')
    print(f'DB: {DB_PATH}')
    print(f'Date: {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    print()

    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.row_factory = sqlite3.Row

    # Step 1: Load all passage_entity rows
    print('Step 1: Load passage_entity...')
    rows = conn.execute('SELECT passage_id, entity_id FROM passage_entity').fetchall()
    print(f'  {len(rows):,} total links')

    # Normalize IDs and aggregate
    from collections import defaultdict
    place_passages = defaultdict(list)  # normalized_id → [passage_id, ...]
    for r in rows:
        norm_id = normalize_dila_id(r['entity_id'])
        place_passages[norm_id].append(r['passage_id'])

    print(f'  {len(place_passages):,} unique place IDs after normalization')
    print()

    # Step 2: Get passage → text_id mapping
    print('Step 2: Build passage → text mapping...')
    pass_rows = conn.execute('SELECT passage_id, text_id FROM passage').fetchall()
    passage_text = {r['passage_id']: r['text_id'] for r in pass_rows}
    print(f'  {len(passage_text):,} passages mapped')
    print()

    # Step 3: Get Vietnamese names
    print('Step 3: Load Vietnamese names...')
    vi_rows = conn.execute('SELECT dila_id, name_vi FROM namevi_map_places').fetchall()
    vi_map = {r['dila_id']: r['name_vi'] for r in vi_rows}
    print(f'  {len(vi_map):,} Vietnamese names')
    print()

    # Step 4: Build stats
    print('Step 4: Compute stats...')
    stats = []
    for norm_id, pids in sorted(place_passages.items(), key=lambda x: -len(x[1])):
        mention_count = len(pids)
        # Get top texts (most frequent)
        text_counts = defaultdict(int)
        for pid in pids:
            tid = passage_text.get(pid)
            if tid:
                text_counts[tid] += 1
        top_texts = ','.join(t for t, _ in sorted(text_counts.items(), key=lambda x: -x[1])[:5])
        vi_name = vi_map.get(norm_id) or ''
        stats.append((norm_id, mention_count, top_texts, vi_name, datetime.now().isoformat()))

    print(f'  Computed stats for {len(stats):,} places')
    print()

    # Step 5: Preview top 20
    print('Top 20 places by CBETA mention count:')
    for rank, (pid, cnt, texts, vi, _) in enumerate(stats[:20], 1):
        print(f'  {rank:2}. {pid} | {cnt:4} mentions | {vi or "[no vi name]"} | {texts[:60]}')
    print()

    if DRY_RUN:
        print('[DRY-RUN] Không thay đổi DB.')
        print('Chạy lại với --apply để tạo bảng và insert data.')
        conn.close()
        return

    # Step 6: Create table and insert
    print('Step 6: Create cbeta_place_mention_stats and insert...')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS cbeta_place_mention_stats (
            place_id   TEXT PRIMARY KEY,
            mention_count INTEGER,
            top_texts  TEXT,
            vi_name    TEXT,
            last_updated TEXT
        )
    ''')
    conn.execute('DELETE FROM cbeta_place_mention_stats')
    conn.executemany(
        'INSERT OR REPLACE INTO cbeta_place_mention_stats VALUES (?,?,?,?,?)',
        stats
    )
    conn.commit()
    print(f'  Inserted {len(stats):,} rows into cbeta_place_mention_stats')

    # Verify
    n = conn.execute('SELECT COUNT(*) FROM cbeta_place_mention_stats').fetchone()[0]
    top5 = conn.execute(
        'SELECT place_id, mention_count, vi_name FROM cbeta_place_mention_stats ORDER BY mention_count DESC LIMIT 5'
    ).fetchall()
    print()
    print('=== cbeta_place_mention_stats ===')
    print(f'  Total rows: {n:,}')
    print('  Top 5:')
    for r in top5:
        print(f'    {r[0]} | {r[1]} mentions | {r[2] or "[no vi]"}')

    print()
    print(f'[DONE] {len(stats):,} place mention stats computed')
    conn.close()


if __name__ == '__main__':
    main()
