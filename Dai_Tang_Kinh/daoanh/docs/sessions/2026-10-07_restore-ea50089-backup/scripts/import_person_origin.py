"""T41 — Person placeOfOrigin ETL.

Reads <note type='placeOfOrigin'><placeName><ref>PL...</ref></placeName></note>
from DILA Person Authority XML, inserts into person_origin_link table.

Key fix: PL ID is in ref.text, NOT in ref.get('target').
"""
import sys, os, io, time, sqlite3, xml.etree.ElementTree as ET
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERSON_XML = os.path.join(BASE, 'data', 'dila_import', 'Authority-Databases',
                           'authority_person', 'Buddhist_Studies_Person_Authority.xml')
DB_PATH = os.path.join(BASE, 'data', 'lineage.db')
NS = {'tei': 'http://www.tei-c.org/ns/1.0'}
XML_ID = '{http://www.w3.org/XML/1998/namespace}id'

LOG_DIR = os.path.join(BASE, 'docs', 'sessions', '2026-08-25')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, 't41_etl.log')

log_lines = []


def log(msg):
    ts = time.strftime('%H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    log_lines.append(line)


def flush_log():
    with open(LOG_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(log_lines))


def setup_db(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS person_origin_link (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id TEXT NOT NULL,
        place_id TEXT NOT NULL,
        confidence REAL DEFAULT 1.0,
        created_at TEXT DEFAULT (datetime('now')),
        UNIQUE(person_id, place_id)
    );
    CREATE INDEX IF NOT EXISTS idx_pol_place ON person_origin_link(place_id);
    CREATE INDEX IF NOT EXISTS idx_pol_person ON person_origin_link(person_id);
    """)
    conn.commit()
    log("DB schema ready: person_origin_link")


def get_valid_place_ids(conn):
    rows = conn.execute("SELECT id FROM places_dila").fetchall()
    return {r[0] for r in rows}


def extract_pl_from_note(note_el):
    """Extract PL ID from note — PL ID is in ref.text, not ref.target."""
    ref_el = note_el.find('.//tei:ref', NS)
    if ref_el is None:
        return None
    text = (ref_el.text or '').strip()
    if text.startswith('PL'):
        return text
    return None


def run_etl():
    log(f"=== T41 Person placeOfOrigin ETL ===")
    log(f"XML: {PERSON_XML}")
    log(f"DB:  {DB_PATH}")

    tree = ET.parse(PERSON_XML)
    root = tree.getroot()
    persons = root.findall('.//tei:person', NS)
    log(f"Total persons in XML: {len(persons)}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    setup_db(conn)

    valid_places = get_valid_place_ids(conn)
    log(f"Valid place IDs in DB: {len(valid_places)}")

    inserted = 0
    skipped_no_pl = 0
    skipped_not_in_db = 0
    skipped_duplicate = 0
    persons_with_origin = 0

    for p in persons:
        pid = p.get(XML_ID)
        if not pid:
            continue
        note_el = p.find("tei:note[@type='placeOfOrigin']", NS)
        if note_el is None:
            skipped_no_pl += 1
            continue
        pl_id = extract_pl_from_note(note_el)
        if not pl_id:
            skipped_no_pl += 1
            continue
        persons_with_origin += 1
        if pl_id not in valid_places:
            skipped_not_in_db += 1
            continue
        try:
            conn.execute(
                "INSERT OR IGNORE INTO person_origin_link (person_id, place_id, confidence) VALUES (?,?,1.0)",
                (pid, pl_id)
            )
            if conn.total_changes > 0:
                inserted += 1
            else:
                skipped_duplicate += 1
        except Exception as e:
            log(f"  Error inserting {pid}/{pl_id}: {e}")

    conn.commit()

    # verify
    total_rows = conn.execute("SELECT COUNT(*) FROM person_origin_link").fetchone()[0]
    unique_places = conn.execute("SELECT COUNT(DISTINCT place_id) FROM person_origin_link").fetchone()[0]
    unique_persons = conn.execute("SELECT COUNT(DISTINCT person_id) FROM person_origin_link").fetchone()[0]

    log("=== ETL Results ===")
    log(f"Persons with placeOfOrigin note:  {persons_with_origin}")
    log(f"Persons without origin/no PL ID:  {skipped_no_pl}")
    log(f"Origin PL not in places_dila:     {skipped_not_in_db}")
    log(f"Inserted new links:               {inserted}")
    log(f"Skipped (duplicate):              {skipped_duplicate}")
    log(f"--- person_origin_link table ---")
    log(f"Total rows:                       {total_rows}")
    log(f"Unique places with origin persons:{unique_places}")
    log(f"Unique persons with origin link:  {unique_persons}")

    # sample
    samples = conn.execute("""
        SELECT pol.person_id, pol.place_id, pd.name_zh
        FROM person_origin_link pol
        JOIN places_dila pd ON pd.id = pol.place_id
        LIMIT 10
    """).fetchall()
    log("Sample rows:")
    for s in samples:
        log(f"  {s['person_id']} → {s['place_id']} ({s['name_zh']})")

    conn.close()
    flush_log()
    log(f"Log saved to: {LOG_PATH}")
    return total_rows


if __name__ == '__main__':
    total = run_etl()
    sys.exit(0 if total > 0 else 1)
