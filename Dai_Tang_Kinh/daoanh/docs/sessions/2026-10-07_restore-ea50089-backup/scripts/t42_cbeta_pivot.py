"""T42 — CBETA Ref Pivot: resolve person_id=NULL rows in place_person_bibl.

Builds index from Person Authority XML: cbeta_ref → [person_id, ...]
Then matches unresolved place_person_bibl rows by cbeta_ref.

Confidence:
  0.8 = unambiguous (1 person per cbeta_ref)
  0.7 = ambiguous (multiple persons), fuzzy name match applied

Run idempotently — only updates rows still having person_id IS NULL.
"""
import sys, os, io, re, time, sqlite3, xml.etree.ElementTree as ET
from collections import defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERSON_XML = os.path.join(BASE, 'data', 'dila_import', 'Authority-Databases',
                           'authority_person', 'Buddhist_Studies_Person_Authority.xml')
DB_PATH = os.path.join(BASE, 'data', 'lineage.db')
NS = {'tei': 'http://www.tei-c.org/ns/1.0'}
XML_ID = '{http://www.w3.org/XML/1998/namespace}id'

LOG_DIR = os.path.join(BASE, 'docs', 'sessions', '2026-08-25')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, 't42_etl.log')

log_lines = []


def log(msg):
    ts = time.strftime('%H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    log_lines.append(line)


def flush_log():
    with open(LOG_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(log_lines))


_CBETA_PATTERN = re.compile(r'([A-Z]\d+n\d+[a-zA-Z]?\d*(?:_[a-z]\d+)?)', re.IGNORECASE)


def extract_cbeta_ref(text):
    """Extract T50n2060_p0457c16 style refs from bibl text.

    Returns the full ref including page suffix (e.g. T50n2060_p0457c16).
    Keeps page suffix for precision: same book, different pages = different persons.
    """
    if not text:
        return None
    # Match full ref including page: T50n2060_p0457c16
    # Pattern: LETTER + digits + n + digits + optional letter + digits + optional _pDIGITSletterDIGITS
    m = re.search(r'([A-Z]\d+n\d+[a-zA-Z]?\d*(?:_p\d+[a-z]\d+)?)', text)
    if m:
        return m.group(1)
    return None


def strip_honorific(name):
    """Strip 釋/尼/俗 prefixes for fuzzy matching."""
    return re.sub(r'^[釋尼俗竺求那]', '', name).strip()


def fuzzy_name_match(raw_name, candidates_with_names):
    """
    candidates_with_names = [(person_id, name_zh), ...]
    Returns best person_id or None.
    Criteria: exact match OR exact after strip OR substring containment.
    """
    if not raw_name:
        return None
    stripped_raw = strip_honorific(raw_name)
    # Try exact
    for pid, name in candidates_with_names:
        if name and name == raw_name:
            return pid
    # Try strip
    for pid, name in candidates_with_names:
        if name and strip_honorific(name) == stripped_raw:
            return pid
    # Try substring (raw_name contains name or vice versa)
    for pid, name in candidates_with_names:
        if name and (raw_name in name or name in raw_name):
            return pid
    return None


def build_cbeta_index(persons):
    """Build dict: cbeta_ref → list of (person_id, name_zh)."""
    log("Building CBETA ref index from Person Authority XML...")
    idx = defaultdict(list)
    persons_with_bibl = 0
    total_bibl = 0
    for p in persons:
        pid = p.get(XML_ID)
        if not pid:
            continue
        name_el = p.find('tei:persName', NS)
        name_zh = (name_el.text or '').strip() if name_el is not None else ''
        bibls = p.findall('.//tei:bibl', NS)
        if bibls:
            persons_with_bibl += 1
        for bibl in bibls:
            text = ''.join(bibl.itertext()).strip()
            ref = extract_cbeta_ref(text)
            if ref:
                idx[ref].append((pid, name_zh))
                total_bibl += 1
    log(f"  Persons with bibl: {persons_with_bibl}")
    log(f"  Total cbeta refs indexed: {total_bibl}")
    log(f"  Unique cbeta refs: {len(idx)}")
    return idx


def run_pivot(conn, cbeta_index):
    """Match unresolved place_person_bibl rows via CBETA ref pivot."""
    unmatched = conn.execute(
        "SELECT id, cbeta_ref, person_name_raw FROM place_person_bibl WHERE person_id IS NULL AND cbeta_ref IS NOT NULL"
    ).fetchall()
    log(f"Unmatched rows with cbeta_ref: {len(unmatched)}")

    unambiguous = 0
    fuzzy_matched = 0
    still_unmatched = 0
    no_ref_in_index = 0

    for row in unmatched:
        cbeta_ref = row[1]
        person_name_raw = row[2] or ''
        row_id = row[0]

        # Both index and DB now use full ref (e.g. T50n2060_p0447c17)
        candidates = cbeta_index.get(cbeta_ref, [])
        if not candidates:
            no_ref_in_index += 1
            still_unmatched += 1
            continue

        if len(candidates) == 1:
            # Unambiguous pivot
            pid, _ = candidates[0]
            conn.execute(
                "UPDATE place_person_bibl SET person_id=?, confidence=0.8 WHERE id=?",
                (pid, row_id)
            )
            unambiguous += 1
        else:
            # Multiple candidates → fuzzy name match
            best = fuzzy_name_match(person_name_raw, candidates)
            if best:
                conn.execute(
                    "UPDATE place_person_bibl SET person_id=?, confidence=0.7 WHERE id=?",
                    (best, row_id)
                )
                fuzzy_matched += 1
            else:
                still_unmatched += 1

    conn.commit()
    return unambiguous, fuzzy_matched, still_unmatched, no_ref_in_index


def spot_check(conn):
    """Spot-check: 鳩摩羅什, 釋智顗, 竺佛圖澄."""
    famous = ['鳩摩羅什', '釋智顗', '竺佛圖澄', '道安', '玄奘']
    log("Spot check for famous monks:")
    for name in famous:
        rows = conn.execute(
            "SELECT person_id, confidence FROM place_person_bibl WHERE person_name_raw=? AND person_id IS NOT NULL LIMIT 3",
            (name,)
        ).fetchall()
        if rows:
            log(f"  {name}: person_id={rows[0][0]}, confidence={rows[0][1]:.1f} ({len(rows)} rows)")
        else:
            log(f"  {name}: still unresolved")


def run_etl():
    log("=== T42 CBETA Ref Pivot ===")
    log(f"XML: {PERSON_XML}")
    log(f"DB:  {DB_PATH}")

    tree = ET.parse(PERSON_XML)
    root = tree.getroot()
    persons = root.findall('.//tei:person', NS)
    log(f"Total persons in XML: {len(persons)}")

    cbeta_index = build_cbeta_index(persons)

    conn = sqlite3.connect(DB_PATH)

    # Before stats
    before_matched = conn.execute("SELECT COUNT(*) FROM place_person_bibl WHERE person_id IS NOT NULL").fetchone()[0]
    before_total = conn.execute("SELECT COUNT(*) FROM place_person_bibl").fetchone()[0]
    log(f"Before: {before_matched}/{before_total} matched ({before_matched/before_total*100:.1f}%)")

    unambiguous, fuzzy_matched, still_unmatched, no_ref_in_index = run_pivot(conn, cbeta_index)

    after_matched = conn.execute("SELECT COUNT(*) FROM place_person_bibl WHERE person_id IS NOT NULL").fetchone()[0]
    log("=== T42 Results ===")
    log(f"Unambiguous matched (conf=0.8): {unambiguous}")
    log(f"Fuzzy name matched (conf=0.7):  {fuzzy_matched}")
    log(f"Still unmatched:               {still_unmatched}")
    log(f"  (no cbeta_ref in person idx: {no_ref_in_index})")
    log(f"After: {after_matched}/{before_total} matched ({after_matched/before_total*100:.1f}%)")
    log(f"Coverage improvement: {before_matched/before_total*100:.1f}% → {after_matched/before_total*100:.1f}%")

    spot_check(conn)

    conn.close()
    flush_log()
    log(f"Log saved to: {LOG_PATH}")
    return after_matched


if __name__ == '__main__':
    total = run_etl()
    sys.exit(0 if total > 0 else 1)
