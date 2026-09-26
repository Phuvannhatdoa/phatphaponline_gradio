"""
Seed catalog_mapping from CBETA refs in places_dila.listbibl.

Extracts ( CBETA T50n2060_p0435a23 ) patterns → matches sigla (T50n2060)
against cbeta_catalog_vn.cbeta_ref → inserts approved mapping rows.
"""

import sqlite3
import re
import sys
import os

DB = os.path.join(os.path.dirname(__file__), '..', 'data', 'lineage.db')

CBETA_RE = re.compile(r'CBETA\s+([A-Z]\d+n\d+)(?:_p[a-z0-9]+)?')

def get_connection():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def extract_refs_from_listbibl(listbibl):
    """Extract (sigla, full_ref) tuples from a listbibl string."""
    matches = CBETA_RE.findall(listbibl)
    return set(matches)


def load_catalog_ref_map(conn):
    """Build {cbeta_ref: sh_number} from catalog."""
    rows = conn.execute(
        "SELECT cbeta_ref, sh_number FROM cbeta_catalog_vn WHERE cbeta_ref IS NOT NULL AND cbeta_ref != ''"
    ).fetchall()
    return {r['cbeta_ref']: r['sh_number'] for r in rows}


def load_existing_mappings(conn):
    """Get set of (place_id, catalog_id) already in catalog_mapping."""
    rows = conn.execute(
        "SELECT place_id, catalog_id FROM catalog_mapping"
    ).fetchall()
    return {(r['place_id'], r['catalog_id']) for r in rows}


def seed_mappings(conn, catalog_map, existing, source='auto_seed_from_cbeta_ref'):
    """Insert catalog_mapping rows for all places with matching CBETA refs."""
    places = conn.execute(
        """SELECT DISTINCT id, listbibl FROM places_dila
           WHERE listbibl IS NOT NULL AND listbibl != '' AND listbibl LIKE '%CBETA%'"""
    ).fetchall()

    inserted = 0
    skipped_dup = 0
    skipped_no_match = 0
    refs_found = set()

    for place in places:
        place_id = place['id']
        listbibl = place['listbibl']
        siglas = extract_refs_from_listbibl(listbibl)

        for sigla in siglas:
            refs_found.add(sigla)
            if sigla not in catalog_map:
                skipped_no_match += 1
                continue

            catalog_id = catalog_map[sigla]
            if (place_id, catalog_id) in existing:
                skipped_dup += 1
                continue

            conn.execute(
                """INSERT OR IGNORE INTO catalog_mapping
                   (place_id, catalog_id, source, status, created_at, updated_at, note)
                   VALUES (?, ?, ?, 'approved', datetime('now'), datetime('now'), ?)""",
                (place_id, catalog_id, source,
                 f"Seed mapping từ ref {sigla}")
            )
            inserted += 1
            existing.add((place_id, catalog_id))

    conn.commit()
    return inserted, skipped_dup, skipped_no_match, refs_found


def main():
    conn = get_connection()

    catalog_map = load_catalog_ref_map(conn)
    print(f"  Catalog ref map: {len(catalog_map)} entries (cbeta_ref → sh_number)")
    for k, v in sorted(catalog_map.items()):
        print(f"    {k} → {v}")

    existing = load_existing_mappings(conn)
    print(f"  Existing mappings: {len(existing)} rows")

    inserted, skipped_dup, skipped_no_match, refs_found = seed_mappings(
        conn, catalog_map, existing
    )

    print(f"\n  CBETA siglas found in listbibl: {len(refs_found)}")
    print(f"  Mappings inserted: {inserted}")
    print(f"  Skipped (dup):     {skipped_dup}")
    print(f"  Skipped (no match): {skipped_no_match}")

    conn.close()

    # Summary for Vương Tự
    if inserted > 0:
        print(f"\n  ✅ Seeded {inserted} new catalog_mapping rows")
    else:
        print("\n  ℹ️  No new mappings to add")

    return 0 if inserted >= 0 else 1


if __name__ == '__main__':
    sys.exit(main())
