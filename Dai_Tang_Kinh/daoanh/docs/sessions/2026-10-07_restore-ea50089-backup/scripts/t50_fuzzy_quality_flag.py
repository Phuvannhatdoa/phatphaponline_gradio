"""
t50_fuzzy_quality_flag.py — T50a: Flag low-confidence fuzzy matches
====================================================================
cbeta_catalog_place_fuzzy: 61,706 rows — 91% noise (score < 70).
Add low_confidence column and flag rows with score < 80.

Usage:
    python scripts/t50_fuzzy_quality_flag.py           # full run
    python scripts/t50_fuzzy_quality_flag.py --dry-run  # preview only
"""
import sqlite3, sys, argparse, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DB_PATH = 'data/lineage.db'


def main():
    parser = argparse.ArgumentParser(description='T50a: Flag low-confidence fuzzy matches')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)

    # Check if column already exists
    cols = [r[1] for r in conn.execute("PRAGMA table_info(cbeta_catalog_place_fuzzy)").fetchall()]
    if 'low_confidence' not in cols:
        print("Adding low_confidence column...")
        conn.execute("ALTER TABLE cbeta_catalog_place_fuzzy ADD COLUMN low_confidence INTEGER DEFAULT 0")
    else:
        print("low_confidence column already exists")

    # Current distribution
    dist = conn.execute("""
        SELECT score/10*10 as bucket, COUNT(*)
        FROM cbeta_catalog_place_fuzzy GROUP BY bucket ORDER BY bucket
    """).fetchall()
    print("\nBefore flagging:")
    for bucket, count in dist:
        bucket = int(bucket)
        flag = "LOW" if bucket < 80 else "HIGH"
        print(f"  Score {bucket:3d}-{bucket+9}: {count:6d} [{flag}]")

    total = conn.execute("SELECT COUNT(*) FROM cbeta_catalog_place_fuzzy").fetchone()[0]
    low = conn.execute("SELECT COUNT(*) FROM cbeta_catalog_place_fuzzy WHERE score < 80").fetchone()[0]
    high = total - low
    print(f"\n  Total: {total}, Low (<80): {low} ({low*100/total:.1f}%), High (>=80): {high} ({high*100/total:.1f}%)")

    if args.dry_run:
        print("\n[DRY RUN — nothing written]")
        conn.close()
        return

    # Flag low confidence
    conn.execute("UPDATE cbeta_catalog_place_fuzzy SET low_confidence = 1 WHERE score < 80")
    conn.execute("UPDATE cbeta_catalog_place_fuzzy SET low_confidence = 0 WHERE score >= 80")
    conn.commit()

    # Verify
    low_flagged = conn.execute("SELECT COUNT(*) FROM cbeta_catalog_place_fuzzy WHERE low_confidence = 1").fetchone()[0]
    high_flagged = conn.execute("SELECT COUNT(*) FROM cbeta_catalog_place_fuzzy WHERE low_confidence = 0").fetchone()[0]
    print(f"\n✅ Flagged: {low_flagged} low-confidence, {high_flagged} high-confidence")

    conn.close()


if __name__ == '__main__':
    main()
