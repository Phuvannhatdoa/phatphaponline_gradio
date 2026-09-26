"""
Import people.bio from DILA Person Authority XML.

SOURCE: authority_person/Buddhist_Studies_Person_Authority.xml
FIELD:  <note type='concise'> → people.bio

Run:
    python scripts/import_person_bio.py [--dry-run] [--limit N]
"""
import sys, os, io, argparse, sqlite3
import xml.etree.ElementTree as ET

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XML_PATH = os.path.join(BASE_DIR, 'data', 'dila_import', 'Authority-Databases',
                        'authority_person', 'Buddhist_Studies_Person_Authority.xml')
DB_PATH  = os.path.join(BASE_DIR, 'data', 'lineage.db')

NS = {'tei': 'http://www.tei-c.org/ns/1.0'}
XML_ID  = '{http://www.w3.org/XML/1998/namespace}id'


def get_text(el):
    """Concatenate all text content of an element (strips whitespace)."""
    return ' '.join(''.join(el.itertext()).split()) if el is not None else None


def parse_person(p):
    """Return (person_id, bio_text, wikidata_qid, place_of_origin_pl_id) from a <person> element."""
    pid = p.get(XML_ID) or ''
    if not pid:
        return None

    # bio = note[type='concise']
    bio_el = p.find("tei:note[@type='concise']", NS)
    bio = get_text(bio_el)

    # Wikidata QID
    wk_el = p.find("tei:idno[@type='Wikidata']", NS)
    wikidata_qid = get_text(wk_el)

    # Place of origin DILA ID
    origin_el = p.find("tei:note[@type='placeOfOrigin']//tei:ref", NS)
    origin_pl = None
    if origin_el is not None:
        target = (origin_el.get('target') or '').strip()
        if target.startswith('PL'):
            origin_pl = target
        elif '/' in target:
            last = target.rstrip('/').split('/')[-1]
            if last.startswith('PL'):
                origin_pl = last

    return (pid, bio, wikidata_qid, origin_pl)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--limit', type=int, default=0)
    args = parser.parse_args()

    print(f'=== import_person_bio.py ===')
    print(f'XML: {XML_PATH}')
    print(f'DB : {DB_PATH}')

    print('\n[1] Parsing XML...')
    tree = ET.parse(XML_PATH)
    root = tree.getroot()
    persons = root.findall('.//tei:person', NS)
    print(f'    Total <person> elements: {len(persons)}')
    if args.limit:
        persons = persons[:args.limit]
        print(f'    Limited to first {args.limit}')

    parsed = []
    for p in persons:
        row = parse_person(p)
        if row and row[1]:   # only those with non-empty bio
            parsed.append(row)
    print(f'    Persons with non-empty bio: {len(parsed)}')

    print('\n[2] Updating DB...')
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    updated = 0
    skipped_no_match = 0
    for pid, bio, wikidata_qid, origin_pl in parsed:
        exists = conn.execute('SELECT 1 FROM people WHERE id=?', (pid,)).fetchone()
        if not exists:
            skipped_no_match += 1
            continue
        if not args.dry_run:
            conn.execute('UPDATE people SET bio=? WHERE id=?', (bio, pid))
        updated += 1

    if not args.dry_run:
        conn.commit()
        print(f'    Updated: {updated}')
        print(f'    Skipped (not in people table): {skipped_no_match}')
    else:
        print(f'    [DRY RUN] Would update: {updated}')
        print(f'    [DRY RUN] Skipped: {skipped_no_match}')
        # Show sample
        print('\n    Sample (first 3):')
        for pid, bio, wq, op in parsed[:3]:
            print(f'      {pid}: bio={bio[:80] if bio else None}... wikidata={wq} origin={op}')

    conn.close()
    print('\n=== Done ===')


if __name__ == '__main__':
    main()
