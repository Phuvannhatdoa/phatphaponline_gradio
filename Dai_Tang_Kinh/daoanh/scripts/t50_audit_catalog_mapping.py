"""
t50_audit_catalog_mapping.py — T50d: Audit catalog_mapping for orphaned entries
================================================================================
Flag catalog_mapping rows where sh_number doesn't exist in cbeta_catalog_vn.

Usage:
    python scripts/t50_audit_catalog_mapping.py           # full run
    python scripts/t50_audit_catalog_mapping.py --dry-run  # preview only
"""
import sqlite3, sys, argparse, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DB_PATH = 'data/lineage.db'


def main():
    parser = argparse.ArgumentParser(description='T50d: Audit catalog_mapping')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)

    # Check if quality_flag column exists
    cols = [r[1] for r in conn.execute("PRAGMA table_info(catalog_mapping)").fetchall()]
    if 'quality_flag' not in cols:
        print("Adding quality_flag column...")
        conn.execute("ALTER TABLE catalog_mapping ADD COLUMN quality_flag TEXT DEFAULT NULL")
    else:
        print("quality_flag column already exists")

    # Find orphaned mappings (catalog_id not in cbeta_catalog_vn.sh_number)
    orphaned = conn.execute("""
        SELECT cm.id, cm.place_id, cm.catalog_id, cm.source
        FROM catalog_mapping cm
        LEFT JOIN cbeta_catalog_vn cv ON cm.catalog_id = cv.sh_number
        WHERE cv.sh_number IS NULL
    """).fetchall()

    total = conn.execute("SELECT COUNT(*) FROM catalog_mapping").fetchone()[0]
    valid = total - len(orphaned)

    print(f"\nCatalog Mapping Audit:")
    print(f"  Total mappings: {total}")
    print(f"  Valid (sh_number exists): {valid}")
    print(f"  Orphaned (sh_number missing): {len(orphaned)}")

    if orphaned:
        print(f"\nOrphaned samples (first 10):")
        for row in orphaned[:10]:
            print(f"  id={row[0]} place={row[1]} catalog_id={row[2]} source={row[3]}")

    # Source distribution of orphaned
    src_dist = conn.execute("""
        SELECT cm.source, COUNT(*)
        FROM catalog_mapping cm
        LEFT JOIN cbeta_catalog_vn cv ON cm.catalog_id = cv.sh_number
        WHERE cv.sh_number IS NULL
        GROUP BY cm.source
    """).fetchall()
    if src_dist:
        print(f"\nOrphaned by source:")
        for src, cnt in src_dist:
            print(f"  {src}: {cnt}")

    if args.dry_run:
        print(f"\n[DRY RUN] Would flag {len(orphaned)} orphaned rows")
        conn.close()
        return

    # Flag orphaned
    conn.execute("""
        UPDATE catalog_mapping SET quality_flag = 'orphaned'
        WHERE id IN (
            SELECT cm.id FROM catalog_mapping cm
            LEFT JOIN cbeta_catalog_vn cv ON cm.catalog_id = cv.sh_number
            WHERE cv.sh_number IS NULL
        )
    """)
    # Mark valid ones
    conn.execute("""
        UPDATE catalog_mapping SET quality_flag = 'verified'
        WHERE quality_flag IS NULL OR quality_flag != 'orphaned'
    """)
    conn.commit()

    print(f"\n✅ Flagged {len(orphaned)} orphaned, {valid} verified")

    conn.close()


if __name__ == '__main__':
    main()
