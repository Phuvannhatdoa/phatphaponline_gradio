"""
t32_expansion.py — T32 Phase 2: Insert high-confidence founding dates missed by rule-based scripts.

Two classes of extractions:
1. NOTE-FOUNDING: places with clear CE year + founding KW but blocked by buggy sentence-boundary check
   - Only inserts manually-vetted cases
2. DYNASTY-RENOVATION: places founded in named dynasty, but later renovation CE year caused dynasty script to skip

Usage:
    python scripts/t32_expansion.py --dry-run
    python scripts/t32_expansion.py
"""
import sqlite3, sys, re, argparse, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_PATH = 'data/lineage.db'

# ── Manually vetted high-confidence insertions (CLASS 1: note-founding) ──────
# Each: (dila_id, year_ce, label_zh, source_ref)
NOTE_FOUNDING_ROWS = [
    ('PL000000000452', 1093, '建於遼大安九年（1093），為石雕八角形三層密簷式塔', 'PL000000000452·note·regex'),
    ('PL000000013181', 300,  '西晉永康元年（300）建，為紹興城區最早的寺院', 'PL000000013181·note·regex'),
    ('PL000000017218', 924,  '五代後唐同光二年（924）建有仙宗寺', 'PL000000017218·note·regex'),
    ('PL000000042270', 684,  '文明元年（684）高宗崩後百日，立為大獻福寺', 'PL000000042270·note·regex'),
    ('PL000000056287', 913,  '梁乾化三年（913）建寺', 'PL000000056287·note·regex'),
]

# ── Dynasty + renovation-CE places (CLASS 2: dila_dynasty via renovation-CE notes) ──
DYNASTY_TABLE = {
    '北魏': (386, 534), '東魏': (534, 550), '西魏': (535, 557),
    '北周': (557, 581), '北齊': (550, 577), '南齊': (479, 502),
    '劉宋': (420, 479), '北宋': (960, 1127), '南宋': (1127, 1279),
    '五代': (907, 960), '前秦': (351, 394),
    '漢': (25, 220), '魏': (220, 265), '晉': (265, 420),
    '隋': (581, 618), '唐': (618, 907), '梁': (502, 557),
    '陳': (557, 589), '遼': (907, 1125), '金': (1115, 1234),
    '宋': (960, 1279), '元': (1271, 1368),
    '明': (1368, 1644), '清': (1644, 1911),
    '東漢': (25, 220), '西漢': (-206, 24), '三國': (220, 280),
}
DYN_SORTED = sorted(DYNASTY_TABLE.keys(), key=len, reverse=True)

CE_PAT = re.compile(r'（(\d{3,4})）')
RENO_KW = re.compile(r'重[修建葺]|修繕|修復|新修|重葺|敕修|賜[額名]|改[為名]|重建|重造')
FOUNDING_PHRASE = re.compile(
    r'(始建|創建|建立|開山|始創|創寺|建寺|建廟|建塔|始開|肇建|建自|創自|建於|創於|始於|建立|創立|始于|建于|創于)'
)
UNKNOWN_PAT = re.compile(r'不詳|不明|無考|年代不明|建寺時期')


def extract_dynasty_founding(note: str):
    """Find dynasty name in founding context from notes that also have renovation CE years."""
    if not CE_PAT.search(note):
        return None, None  # handled by note-founding script

    sentences = re.split(r'[。；]', note)
    for sent in sentences[:3]:
        m = FOUNDING_PHRASE.search(sent)
        if not m:
            continue
        if RENO_KW.search(sent):
            continue
        if UNKNOWN_PAT.search(sent):
            continue
        for dyn in DYN_SORTED:
            if dyn not in sent:
                continue
            dyn_idx = sent.find(dyn)
            if dyn_idx >= m.start() - 5:
                s, e = DYNASTY_TABLE[dyn]
                mid = (s + e) // 2
                if 100 <= mid <= 1950:
                    return mid, dyn
    return None, None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    existing = set(
        r[0] for r in conn.execute('SELECT DISTINCT dila_id FROM place_timeline_events').fetchall()
    )

    rows_to_insert = []

    # CLASS 1: manually vetted note-founding rows
    for (dila_id, year, label_zh, source_ref) in NOTE_FOUNDING_ROWS:
        if dila_id in existing:
            print(f'  SKIP (exists): {dila_id}')
            continue
        rows_to_insert.append((dila_id, year, label_zh, 'dila_note', source_ref, 0.7))

    # CLASS 2: dynasty-renovation places — find dynamically from DB
    places = conn.execute("""
        SELECT pd.id, pd.name_zh, pd.note
        FROM places_dila pd
        WHERE pd.note_category LIKE '%寺廟%'
        AND pd.note IS NOT NULL AND length(pd.note) > 30
        AND NOT EXISTS (SELECT 1 FROM place_timeline_events pt WHERE pt.dila_id = pd.id)
    """).fetchall()

    for r in places:
        dila_id = r['id']
        if dila_id in existing:
            continue
        # Skip places already queued from CLASS 1
        if any(row[0] == dila_id for row in rows_to_insert):
            continue
        note = r['note'] or ''
        year, dyn = extract_dynasty_founding(note)
        if year is None:
            continue
        name_zh = r['name_zh'] or dila_id
        # Build label from founding sentence
        sentences = re.split(r'[。；]', note)
        label = ''
        for s in sentences[:2]:
            if FOUNDING_PHRASE.search(s) and dyn in s:
                label = s.strip()[:80]
                break
        if not label:
            label = name_zh
        rows_to_insert.append((dila_id, year, label, 'dila_dynasty', f'{dila_id}·dynasty·{dyn}', 0.5))

    print(f'\nReady to insert: {len(rows_to_insert)} rows')
    print(f'  CLASS 1 (note-founding): {sum(1 for r in rows_to_insert if r[3]=="dila_note")}')
    print(f'  CLASS 2 (dynasty-renovation): {sum(1 for r in rows_to_insert if r[3]=="dila_dynasty")}')
    print()
    for r in rows_to_insert:
        print(f'  {r[0]} | year={r[1]} | source={r[3]} | {r[2][:60]}')

    if args.dry_run:
        print(f'\n[DRY RUN] Would insert {len(rows_to_insert)} rows.')
        conn.close()
        return

    inserted = 0
    for (dila_id, year, label_zh, source, source_ref, confidence) in rows_to_insert:
        try:
            conn.execute("""
                INSERT OR IGNORE INTO place_timeline_events
                  (dila_id, event_type, year, label_zh, source, source_ref, confidence)
                VALUES (?, 'founding', ?, ?, ?, ?, ?)
            """, (dila_id, year, label_zh, source, source_ref, confidence))
            inserted += 1
        except Exception as e:
            print(f'  ERROR {dila_id}: {e}')

    conn.commit()

    total_tl = conn.execute('SELECT COUNT(*) FROM place_timeline_events').fetchone()[0]
    total_dila = conn.execute('SELECT COUNT(DISTINCT dila_id) FROM place_timeline_events').fetchone()[0]
    total_places = conn.execute('SELECT COUNT(*) FROM places_dila').fetchone()[0]
    pct = total_dila / total_places * 100

    print(f'\n✅ Inserted {inserted} rows.')
    print(f'place_timeline_events: {total_tl} rows, {total_dila} unique places ({pct:.2f}% of {total_places})')

    conn.close()


if __name__ == '__main__':
    main()
