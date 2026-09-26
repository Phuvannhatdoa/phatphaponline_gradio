"""
T73 — Copy approved bio_vi_draft → people.bio_vi

Usage:
  python t73_copy_approved_bio_vi.py              # dry-run: count rows to copy
  python t73_copy_approved_bio_vi.py --apply      # copy approved drafts → people.bio_vi
  python t73_copy_approved_bio_vi.py --stats      # stats by source + approval status
"""
import sqlite3, json, os, argparse
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'lineage.db')
LOG_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 't73_copy_log.json')


def ensure_bio_vi(conn):
    cols = [r[1] for r in conn.execute("PRAGMA table_info(people)").fetchall()]
    if 'bio_vi' not in cols:
        conn.execute("ALTER TABLE people ADD COLUMN bio_vi TEXT")
        conn.commit()
        print("Added bio_vi column to people table")


def run(apply=False, stats=False):
    conn = sqlite3.connect(DB_PATH)
    ensure_bio_vi(conn)
    c = conn.cursor()

    if stats:
        c.execute("SELECT admin_approved, COUNT(*) FROM person_bio_vi_draft GROUP BY admin_approved")
        for r in c.fetchall():
            label = {0: 'pending', 1: 'approved', -1: 'rejected'}.get(r[0], str(r[0]))
            print(f"  {label}: {r[1]}")
        c.execute("SELECT COUNT(*) FROM people WHERE bio_vi IS NOT NULL AND bio_vi != ''")
        print(f"  people.bio_vi already set: {c.fetchone()[0]}")
        conn.close()
        return

    c.execute(
        "SELECT person_id, bio_vi_draft FROM person_bio_vi_draft WHERE admin_approved = 1"
    )
    approved = c.fetchall()
    print(f"Approved drafts ready to copy: {len(approved)}")

    if not apply:
        print("Dry-run: use --apply to write to people.bio_vi")
        conn.close()
        return

    # Ensure bio_vi column exists
    cols = [r[1] for r in conn.execute("PRAGMA table_info(people)").fetchall()]
    if 'bio_vi' not in cols:
        conn.execute("ALTER TABLE people ADD COLUMN bio_vi TEXT")
        conn.commit()
        print("Added bio_vi column to people table")

    updated = 0
    skipped = 0
    for person_id, draft in approved:
        if not draft:
            skipped += 1
            continue
        c.execute("UPDATE people SET bio_vi = ? WHERE id = ?", (draft, person_id))
        if c.rowcount > 0:
            updated += 1
        else:
            skipped += 1

    conn.commit()

    log = {
        'run_at': datetime.utcnow().isoformat(),
        'approved_drafts': len(approved),
        'updated_people': updated,
        'skipped': skipped,
    }
    with open(LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

    print(f"Updated people.bio_vi: {updated} rows")
    print(f"Skipped (no match or empty): {skipped}")
    print(f"Log: {LOG_PATH}")
    conn.close()


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--apply', action='store_true')
    p.add_argument('--stats', action='store_true')
    args = p.parse_args()
    run(apply=args.apply, stats=args.stats)
