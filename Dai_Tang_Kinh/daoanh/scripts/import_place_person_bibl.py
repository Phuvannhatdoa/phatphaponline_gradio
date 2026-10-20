"""
T39 — Import place_person_bibl from DILA Place Authority XML listBibl.

SOURCE: authority_place/Buddhist_Studies_Place_Authority.xml
OUTPUT: place_person_bibl table in lineage.db

Logic:
  Each <bibl> in <listBibl> has the form:
    "( CBETA T50n2060_p0457c16 ) 唐高僧傳: 釋玄奘傳 {少林寺}"
  We extract:
    cbeta_ref       = "T50n2060_p0457c16"
    source_book     = "唐高僧傳"
    person_name_raw = "釋玄奘"  (text before 傳, after the 書名: separator)
    mention_keyword = "少林寺"  (text inside {})
  Then match person_name_raw -> people.name_zh to get person_id.

Run:
    python scripts/import_place_person_bibl.py [--dry-run] [--limit N]
"""
import sys, os, io, re, argparse, sqlite3
import xml.etree.ElementTree as ET

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLACE_XML = os.path.join(BASE_DIR, 'data', 'dila_import', 'Authority-Databases',
                         'authority_place', 'Buddhist_Studies_Place_Authority.xml')
DB_PATH   = os.path.join(BASE_DIR, 'data', 'lineage.db')
LOG_PATH  = os.path.join(BASE_DIR, 'docs', 'sessions', '2026-08-25', 't39_etl.log')

NS     = {'tei': 'http://www.tei-c.org/ns/1.0'}
XML_ID = '{http://www.w3.org/XML/1998/namespace}id'

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS place_person_bibl (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    place_id        TEXT NOT NULL,
    person_id       TEXT,
    person_name_raw TEXT,
    cbeta_ref       TEXT,
    source_book     TEXT,
    mention_keyword TEXT,
    confidence      REAL DEFAULT 1.0,
    created_at      TEXT DEFAULT (datetime('now')),
    UNIQUE(place_id, cbeta_ref)
);
CREATE INDEX IF NOT EXISTS idx_ppb_place  ON place_person_bibl(place_id);
CREATE INDEX IF NOT EXISTS idx_ppb_person ON place_person_bibl(person_id);
"""


def parse_bibl(bibl_text):
    """
    Parse one <bibl> text string.
    Returns (cbeta_ref, source_book, person_name_raw, mention_keyword) or None.

    Examples handled:
      "( CBETA T50n2060_p0551b08 ) 唐高僧傳: 佛陀禪師傳 {少林}"
      "T50n2060_p0551b08 唐高僧傳: 佛陀禪師傳 {少林}"
      "( CBETA T50n2060_p0480b14 ) 唐高僧傳: 釋安廩傳"  (no keyword)
    """
    txt = ' '.join(bibl_text.split())

    # CBETA ref: T\d+n\d+_p\d+[a-z]\d+  or  similar
    cbeta_m = re.search(r'\b(T\d+n\d+[_p]+\d+[a-z]\d+)\b', txt)
    if not cbeta_m:
        return None
    cbeta_ref = cbeta_m.group(1)

    # mention_keyword: text inside {}
    kw_m = re.search(r'\{([^}]{1,30})\}', txt)
    mention_keyword = kw_m.group(1).strip() if kw_m else None

    # source_book + person_name: pattern "書名: 某人傳" or "書名：某人傳"
    # The book name is before the colon, person is after until 傳
    book_person_m = re.search(
        r'[\)）]\s*([^\(：:]{2,20})[：:]\s*([^\(：:{]{2,20})傳', txt
    )
    if not book_person_m:
        # Fallback: simpler search for "書名" then "人名傳" anywhere
        book_m = re.search(r'[\)）]\s*([^\(：:\s\{]{2,15})[：:]', txt)
        person_m = re.search(r'[：:]\s*([^\(：:{]{2,15})傳', txt)
        if book_m and person_m:
            source_book     = book_m.group(1).strip()
            person_name_raw = person_m.group(1).strip()
        else:
            return None
    else:
        source_book     = book_person_m.group(1).strip()
        person_name_raw = book_person_m.group(2).strip()

    # Sanity: person_name_raw should be ≥2 chars and mostly CJK
    if len(person_name_raw) < 2:
        return None
    cjk_ratio = sum(1 for c in person_name_raw if '一' <= c <= '鿿') / len(person_name_raw)
    if cjk_ratio < 0.5:
        return None

    return cbeta_ref, source_book, person_name_raw, mention_keyword


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--limit', type=int, default=0, help='Max places to process')
    args = parser.parse_args()

    log_lines = []
    def log(msg):
        print(msg)
        log_lines.append(msg)

    log('=== T39 import_place_person_bibl.py ===')
    log(f'XML : {PLACE_XML}')
    log(f'DB  : {DB_PATH}')
    log(f'Mode: {"DRY RUN" if args.dry_run else "WRITE"}')

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Ensure table exists
    if not args.dry_run:
        for stmt in CREATE_TABLE.strip().split(';'):
            stmt = stmt.strip()
            if stmt:
                conn.execute(stmt)
        conn.commit()
        log('[DB] Table place_person_bibl ensured.')

    # Build people name lookup  name_zh -> id  (and name without 釋/尼 prefix)
    log('\n[1] Building people name lookup...')
    name_exact  = {}   # name_zh -> person_id
    name_strip  = {}   # name_zh_stripped -> person_id  (for "釋玄奘" -> "玄奘")
    for row in conn.execute("SELECT id, name_zh FROM people WHERE name_zh IS NOT NULL"):
        nm = row['name_zh']
        person_id = row['id']
        name_exact[nm] = person_id
        stripped = re.sub(r'^[釋尼俗沙弥]', '', nm).strip()
        if stripped and stripped not in name_exact:
            name_strip[stripped] = person_id
    log(f'    exact entries: {len(name_exact)}')
    log(f'    strip entries: {len(name_strip)}')

    # Load DB place IDs
    db_place_ids = set(r['id'] for r in conn.execute("SELECT id FROM places_dila"))
    log(f'    DB places: {len(db_place_ids)}')

    # Parse XML
    log('\n[2] Parsing Place Authority XML...')
    tree = ET.parse(PLACE_XML)
    root = tree.getroot()
    all_places = root.findall('.//tei:place', NS)
    log(f'    Total places in XML: {len(all_places)}')

    stats = {
        'places_processed': 0,
        'places_with_bibl': 0,
        'bibl_total': 0,
        'bibl_parsed': 0,
        'matched_exact': 0,
        'matched_strip': 0,
        'unmatched': 0,
        'inserted': 0,
        'skipped_dup': 0,
    }
    unmatched_names = {}

    log('\n[3] Processing...')
    for place_el in all_places:
        place_id = place_el.get(XML_ID) or ''
        if place_id not in db_place_ids:
            continue
        stats['places_processed'] += 1

        bibls = place_el.findall('.//tei:bibl', NS)
        if not bibls:
            continue
        stats['places_with_bibl'] += 1
        stats['bibl_total'] += len(bibls)

        for bibl in bibls:
            bibl_text = ' '.join(''.join(bibl.itertext()).split())
            parsed = parse_bibl(bibl_text)
            if not parsed:
                continue
            cbeta_ref, source_book, person_name_raw, mention_keyword = parsed
            stats['bibl_parsed'] += 1

            # Match person
            person_id   = None
            confidence  = 0.0
            stripped    = re.sub(r'^[釋尼俗沙弥]', '', person_name_raw).strip()
            if person_name_raw in name_exact:
                person_id  = name_exact[person_name_raw]
                confidence = 1.0
                stats['matched_exact'] += 1
            elif stripped in name_exact:
                person_id  = name_exact[stripped]
                confidence = 0.9
                stats['matched_strip'] += 1
            elif stripped in name_strip:
                person_id  = name_strip[stripped]
                confidence = 0.9
                stats['matched_strip'] += 1
            else:
                stats['unmatched'] += 1
                unmatched_names[person_name_raw] = unmatched_names.get(person_name_raw, 0) + 1

            if not args.dry_run:
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO place_person_bibl
                            (place_id, person_id, person_name_raw, cbeta_ref,
                             source_book, mention_keyword, confidence)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (place_id, person_id, person_name_raw, cbeta_ref,
                          source_book, mention_keyword, confidence))
                    if conn.total_changes > 0:
                        stats['inserted'] += 1
                    else:
                        stats['skipped_dup'] += 1
                except Exception as e:
                    log(f'    [WARN] insert error {place_id}/{cbeta_ref}: {e}')

        if args.limit and stats['places_processed'] >= args.limit:
            log(f'    [limit] Stopped at {args.limit} places.')
            break

    if not args.dry_run:
        conn.commit()

    log('\n=== Results ===')
    for k, v in stats.items():
        log(f'    {k}: {v}')

    if stats['bibl_parsed'] > 0:
        match_rate = (stats['matched_exact'] + stats['matched_strip']) / stats['bibl_parsed'] * 100
        log(f'    match_rate: {match_rate:.1f}%')

    log('\nTop 20 unmatched person names:')
    for nm, cnt in sorted(unmatched_names.items(), key=lambda x: -x[1])[:20]:
        log(f'    "{nm}": {cnt}x')

    # Write log file
    if not args.dry_run:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, 'w', encoding='utf-8') as f:
            f.write('\n'.join(log_lines))
        print(f'\nLog saved: {LOG_PATH}')

    conn.close()
    log('\n=== Done ===')


if __name__ == '__main__':
    main()
