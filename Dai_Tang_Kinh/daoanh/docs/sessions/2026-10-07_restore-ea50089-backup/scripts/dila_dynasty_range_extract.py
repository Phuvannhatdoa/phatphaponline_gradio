"""
dila_dynasty_range_extract.py — T21 Giai đoạn 2f: Dynasty range fallback
=========================================================================
Cho các temple notes chỉ có "唐代建/始建於宋/晉時建" mà KHÔNG có era name
hoặc CE year cụ thể — gán midpoint của dynasty làm founding year approximate.

Confidence: 'dynasty_range' (thấp nhất)
Source: 'dila_dynasty'
Display: "~唐代 (618-907年間)" → midpoint 762 CE

Quy tắc:
  - KHÔNG sửa dữ liệu DILA
  - KHÔNG overwrite data từ wikidata/dila_note/dila_era_name
  - Additive-only. Skip nếu dila_id đã có trong place_timeline_events.
  - Renovation keywords gần founding context → skip

Pattern coverage:
  "始建於唐代"  "唐時建"  "唐代創"  "元末明初"  "建於晉朝"
  "元魏初建"   "北魏時建"  "五代時建"
"""
import sqlite3, re, sys, argparse, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_PATH = 'data/lineage.db'

# Dynasty → (start_CE, end_CE, label) — midpoint = (start+end)//2
DYNASTY_TABLE = {
    # Key: dynasty char(s) as they appear in DILA notes
    '東漢': (25, 220, '東漢'),    '後漢': (25, 220, '漢'),
    '西漢': (-206, 24, '西漢'),   '漢': (25, 220, '漢'),
    '三國': (220, 280, '三國'),   '魏': (220, 265, '魏'),
    '蜀': (221, 263, '蜀'),       '吳': (222, 280, '吳'),
    '西晉': (265, 316, '西晉'),   '東晉': (317, 420, '東晉'),
    '晉': (265, 420, '晉'),
    '劉宋': (420, 479, '劉宋'),   '南朝': (420, 589, '南朝'),
    '南齊': (479, 502, '南齊'),   '齊': (479, 502, '齊'),
    '梁': (502, 557, '梁'),       '陳': (557, 589, '陳'),
    '北魏': (386, 534, '北魏'),   '元魏': (386, 534, '北魏'),  # 元魏=北魏
    '東魏': (534, 550, '東魏'),   '西魏': (535, 557, '西魏'),
    '北周': (557, 581, '北周'),   '北齊': (550, 577, '北齊'),
    '北朝': (386, 581, '北朝'),   '五胡': (304, 439, '五胡'),
    '隋': (581, 618, '隋'),
    '唐': (618, 907, '唐'),
    '五代': (907, 960, '五代'),   '五代十國': (907, 960, '五代'),
    '後梁': (907, 923, '後梁'),   '後唐': (923, 936, '後唐'),
    '後晉': (936, 947, '後晉'),   '後漢': (947, 950, '後漢'),
    '後周': (951, 960, '後周'),
    '北宋': (960, 1127, '北宋'),  '南宋': (1127, 1279, '南宋'),
    '宋': (960, 1279, '宋'),
    '遼': (907, 1125, '遼'),      '西夏': (1038, 1227, '西夏'),
    '金': (1115, 1234, '金'),
    '元': (1271, 1368, '元'),
    '明': (1368, 1644, '明'),
    '清': (1644, 1911, '清'),
    '民國': (1912, 1949, '民國'),
}

# Sort by length desc so longer names match first (元魏 before 魏, 北魏 before 魏)
DYNASTY_NAMES_SORTED = sorted(DYNASTY_TABLE.keys(), key=len, reverse=True)

# Founding keywords
FOUNDING_KW = re.compile(r'[建創立起始興造開]')
# Renovation → skip if adjacent to founding context
RENOVATION = re.compile(r'重[修建葺]|修繕|修復|新修|重葺|敕修|奉修')
# CE year pattern (already handled by other scripts)
YEAR_CE_PAT = re.compile(r'（\d{3,4}）')
# Era name hint (handled by era_name script)
ERA_HINT = re.compile(
    r'貞觀|開元|萬曆|康熙|乾隆|嘉靖|洪武|永樂|順治|雍正|至元|至正|大定|'
    r'天聖|元豐|紹興|咸通|大中|天寶|元和|建炎|淳熙|慶元|嘉定|宣德|成化|'
    r'弘治|正德|天順|景泰|正統|天啟|崇禎|嘉慶|道光|咸豐|同治|光緒|宣統|'
    r'天監|永明|天嘉|太建|大業|武德|永徽|貞元|會昌|大觀|政和|宣和|靖康|'
    r'熙寧|慶曆|嘉祐|治平|元豐|崇寧|淳祐|景定|咸淳|元貞|至大|大德|皇慶|延祐'
)


def extract_dynasty_year(note: str) -> tuple[int | None, str, str]:
    """
    Returns (midpoint_year, dynasty_name, dynasty_label).
    """
    if not note:
        return None, '', ''

    # Skip if already has CE year (other scripts handle these)
    if YEAR_CE_PAT.search(note):
        return None, '', ''

    # Special pattern: 元末明初 / 明末清初 (dynasty transitions)
    transition_m = re.search(r'([元明清唐宋])末([明清宋元])初', note)
    if transition_m:
        d1 = transition_m.group(1)
        d2 = transition_m.group(2)
        # Check founding context nearby
        ctx_s = max(0, transition_m.start() - 15)
        ctx_e = min(len(note), transition_m.end() + 15)
        ctx = note[ctx_s:ctx_e]
        if FOUNDING_KW.search(ctx) or re.search(r'建|創|立', note[:transition_m.start()+10]):
            if not RENOVATION.search(ctx):
                # Use exact single-char key to avoid 元→元魏 mismatch
                if d1 in DYNASTY_TABLE:
                    end_year = DYNASTY_TABLE[d1][1]
                    label = DYNASTY_TABLE[d1][2]
                    return end_year, d1+'末'+d2+'初', f'{label}末{d2}初'

    # Main pattern: find dynasty name + founding context
    best = None
    for dyn in DYNASTY_NAMES_SORTED:
        idx = note.find(dyn)
        if idx == -1:
            continue

        start_y, end_y, dyn_label = DYNASTY_TABLE[dyn]

        # Context around dynasty name
        ctx_s = max(0, idx - 15)
        ctx_e = min(len(note), idx + len(dyn) + 20)
        ctx = note[ctx_s:ctx_e]

        # Must have founding keyword in same clause
        clause_s = note.rfind('。', 0, idx)
        clause_s = clause_s + 1 if clause_s >= 0 else 0
        clause_e_m = note.find('。', idx)
        clause_e = clause_e_m if clause_e_m >= 0 else min(len(note), idx + 80)
        clause = note[clause_s:clause_e]

        if not FOUNDING_KW.search(clause):
            continue
        # T32 fix: only skip if era name in the FOUNDING clause, not entire note
        if ERA_HINT.search(clause):
            continue
        if RENOVATION.search(ctx):
            continue

        # Check for dynasty suffix (代/朝/時/初/中/末)
        after = note[idx + len(dyn):]
        suffix_m = re.match(r'^[代朝時初中末]?', after)
        if not suffix_m:
            continue

        # Valid — compute midpoint
        mid = (start_y + end_y) // 2
        label_str = f"{dyn_label} ({start_y}–{end_y}年間)"
        best = (mid, dyn, label_str)
        break  # Longest match wins

    return (best[0], best[1], best[2]) if best else (None, '', '')


def main():
    parser = argparse.ArgumentParser(description='DILA dynasty range founding year extractor (T21)')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    existing = set(r[0] for r in conn.execute(
        'SELECT DISTINCT dila_id FROM place_timeline_events'
    ).fetchall())

    sql = """
        SELECT id, name_zh, note FROM places_dila
        WHERE note IS NOT NULL AND length(note) > 10
          AND note_category LIKE '%寺廟%'
    """
    if args.limit:
        sql += f' LIMIT {args.limit}'

    places = conn.execute(sql).fetchall()

    stats = {'examined': 0, 'skip_existing': 0, 'found': 0, 'skip_none': 0}
    rows = []

    for (dila_id, name_zh, note) in places:
        stats['examined'] += 1
        if dila_id in existing and not args.force:
            stats['skip_existing'] += 1
            continue

        year, dyn, label_str = extract_dynasty_year(note)
        if year is None:
            stats['skip_none'] += 1
            continue

        stats['found'] += 1
        name = (name_zh or '').strip()
        label_zh = f"{name} ~{label_str}".strip()
        rows.append({
            'dila_id': dila_id, 'year': year, 'label_zh': label_zh,
            'source': 'dila_dynasty', 'source_ref': f"{dila_id}·{dyn}·midpoint",
            'confidence': 'dynasty_range'
        })

    print(f'Examined: {stats["examined"]}')
    print(f'Skip (existing): {stats["skip_existing"]}')
    print(f'No dynasty found: {stats["skip_none"]}')
    print(f'Would insert: {stats["found"]}')
    print()
    print('Sample (first 10):')
    for r in rows[:10]:
        print(f'  {r["dila_id"]} | year={r["year"]} | {r["label_zh"][:65]}')

    if args.dry_run:
        print('\n[DRY RUN — nothing written]')
        conn.close()
        return

    inserted = 0
    for r in rows:
        try:
            conn.execute("""
                INSERT OR IGNORE INTO place_timeline_events
                  (dila_id, event_type, year, label_zh, source, source_ref, confidence)
                VALUES (?, 'founding', ?, ?, ?, ?, ?)
            """, (r['dila_id'], r['year'], r['label_zh'],
                  r['source'], r['source_ref'], r['confidence']))
            inserted += 1
        except Exception as e:
            print(f'  Error {r["dila_id"]}: {e}')

    conn.commit()
    total = conn.execute('SELECT COUNT(*) FROM place_timeline_events').fetchone()[0]
    unique = conn.execute('SELECT COUNT(DISTINCT dila_id) FROM place_timeline_events').fetchone()[0]
    total_dila = conn.execute('SELECT COUNT(*) FROM places_dila').fetchone()[0]
    by_src = conn.execute(
        'SELECT source, COUNT(*), COUNT(DISTINCT dila_id) FROM place_timeline_events GROUP BY source'
    ).fetchall()

    print(f'\n✅ Inserted {inserted} rows.')
    print(f'Total: {total} rows / {unique} unique DILA places')
    print(f'Coverage: {unique}/{total_dila} = {unique*100/total_dila:.2f}%')
    for r in by_src:
        print(f'  {r[0]}: {r[1]} rows / {r[2]} places')

    conn.close()


if __name__ == '__main__':
    main()
