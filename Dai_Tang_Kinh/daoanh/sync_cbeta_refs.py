#!/usr/bin/env python3
"""One-time sync: scan DILA places_dila for CBETA refs, fill cbeta_ref_passages table.

Usage:
    cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
    python sync_cbeta_refs.py [--place PL000000023255]
    
Without --place: scans ALL places_dila entries.
With --place: only scans that specific place_id.
"""

import sys, os, re, sqlite3, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import get_db_connection, get_cbeta_conn, ensure_cbeta_ref_table, _sync_ref_passage, CBETA_REF_TABLE

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
LINEAGE_DB = os.path.join(DATA_DIR, 'lineage.db')

CBETA_RE = re.compile(r'CBETA\s+([A-Z]\d+n\d+_\w+)')


def collect_refs_from_places(conn, place_id=None):
    """Collect all unique CBETA ref_codes from places_dila.listbibl."""
    refs = set()
    if place_id:
        rows = conn.execute(
            "SELECT listbibl FROM places_dila WHERE id = ? AND listbibl IS NOT NULL",
            (place_id,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT listbibl FROM places_dila WHERE listbibl IS NOT NULL"
        ).fetchall()

    for row in rows:
        for m in CBETA_RE.finditer(row['listbibl']):
            refs.add(m.group(1))
    return sorted(refs)


def main():
    parser = argparse.ArgumentParser(description='Sync CBETA ref passages')
    parser.add_argument('--place', help='Only sync refs for a specific place_id')
    args = parser.parse_args()

    ensure_cbeta_ref_table()

    conn = get_db_connection()
    try:
        refs = collect_refs_from_places(conn, args.place)
    finally:
        conn.close()

    if not refs:
        print("No CBETA refs found.")
        return

    print(f"Found {len(refs)} unique CBETA ref codes.")
    
    stats = {'synced': 0, 'missing': 0, 'skipped': 0}
    for i, ref in enumerate(refs, 1):
        conn = get_db_connection()
        try:
            existing = conn.execute(
                f"SELECT han_text FROM {CBETA_REF_TABLE} WHERE ref_code = ?",
                (ref,)
            ).fetchone()
        finally:
            conn.close()

        if existing and existing['han_text']:
            stats['skipped'] += 1
            if i % 20 == 0:
                print(f"  [{i}/{len(refs)}] {ref} => already synced")
            continue

        result = _sync_ref_passage(ref)
        if result:
            stats['synced'] += 1
            print(f"  [{i}/{len(refs)}] {ref} => synced ({len(result['han_text'])} chars)")
        else:
            stats['missing'] += 1
            print(f"  [{i}/{len(refs)}] {ref} => NOT FOUND in cbeta.db")

    print(f"\nDone: {stats['synced']} synced, {stats['missing']} missing, {stats['skipped']} already synced")


if __name__ == '__main__':
    main()
