#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T83 — Bootstrap Review Script (Zero-ALTER, Zero-RAM, additive-only)

Tự động review claims chất lượng cao (entity xuất hiện ở ≥2 nguồn active).
Viết vào columns đã có: entity_claims.verification_status, reviewed_by, reviewed_at.
Mỗi review ghi en_audit_log. 0 ALTER, 0 INSERT bảng mới.

Usage:
  python t83_bootstrap_review.py --auto --dry-run        # in plan, không ghi DB
  python t83_bootstrap_review.py --auto --review          # ghi ≥limit claims
  python t83_bootstrap_review.py --auto --revert          # undo tất cả review của T83
  python t83_bootstrap_review.py --seed entities.txt --review  # review entities cụ thể
  python t83_bootstrap_review.py --stats                  # in thống kê review hiện tại
"""

import argparse
import io
import os
import sqlite3
import sys
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "lineage.db")

# Active sources by authority_score DESC (DILA > CBETA > MARCUS > ZQLOCAL)
ACTIVE_SOURCES = ["DILA", "CBETA", "MARCUS", "ZQLOCAL"]

# Priority claim_types (by volume + importance)
PRIORITY_CLAIM_TYPES = ["NAME", "COORDINATE", "ADMIN_UNIT", "NETWORK_EVIDENCE", "TEXT_EVIDENCE"]

REVIEWED_BY = "T83_auto"


def get_conn(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def query_candidates(conn, limit=5000, seed_ids=None):
    """Zero-RAM: yield (entity_id, source_id, claim_id, claim_type, subject, object_text) tuples."""
    if seed_ids:
        placeholders = ",".join("?" for _ in seed_ids)
        sql = """
            SELECT c.claim_id, c.entity_id, c.source_id, c.claim_type, c.subject, c.object_text
            FROM entity_claims c
            WHERE c.entity_id IN ({ph})
              AND c.verification_status = 'unverified'
            ORDER BY c.source_id, c.claim_type
            LIMIT ?
        """.format(ph=placeholders)
        params = seed_ids + [limit]
    else:
        sql = """
            SELECT c.claim_id, c.entity_id, c.source_id, c.claim_type, c.subject, c.object_text
            FROM entity_claims c
            JOIN source_authority sa ON sa.source_id = c.source_id
            WHERE c.claim_type IN ({types})
              AND c.verification_status = 'unverified'
              AND sa.implemented = 1
              AND c.entity_id IN (
                  SELECT c2.entity_id FROM entity_claims c2
                  JOIN source_authority sa2 ON sa2.source_id = c2.source_id
                  WHERE c2.verification_status = 'unverified' AND sa2.implemented = 1
                  GROUP BY c2.entity_id
                  HAVING COUNT(DISTINCT c2.source_id) >= 2
              )
            ORDER BY c.entity_id, c.source_id, c.claim_type
            LIMIT ?
        """.format(types=",".join("?" for _ in PRIORITY_CLAIM_TYPES))
        params = PRIORITY_CLAIM_TYPES + [limit]

    cursor = conn.execute(sql, params)
    batch_size = 1000
    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            break
        for r in rows:
            yield dict(r)


def stats(conn):
    """Print current review stats."""
    total = conn.execute("SELECT COUNT(*) n FROM entity_claims").fetchone()["n"]
    reviewed = conn.execute("SELECT COUNT(*) n FROM entity_claims WHERE reviewed_by IS NOT NULL").fetchone()["n"]
    verified = conn.execute("SELECT COUNT(*) n FROM entity_claims WHERE verification_status='verified'").fetchone()["n"]
    unverified = conn.execute("SELECT COUNT(*) n FROM entity_claims WHERE verification_status='unverified'").fetchone()["n"]
    t83_reviewed = conn.execute(
        "SELECT COUNT(*) n FROM entity_claims WHERE reviewed_by=?", (REVIEWED_BY,)
    ).fetchone()["n"]
    audit_count = conn.execute(
        "SELECT COUNT(*) n FROM en_audit_log WHERE action='review'"
    ).fetchone()["n"]

    print("== T83 Bootstrap Review Stats ==")
    print("  Total claims:          %d" % total)
    print("  Verified:              %d (%.2f%%)" % (verified, verified * 100 / total))
    print("  Reviewed (any):        %d (%.2f%%)" % (reviewed, reviewed * 100 / total))
    print("  Unverified:            %d (%.2f%%)" % (unverified, unverified * 100 / total))
    print("  T83_auto reviewed:     %d" % t83_reviewed)
    print("  Audit log (review):    %d" % audit_count)

    if t83_reviewed > 0:
        print("  Compliance:            claims_reviewed=%.2f%% claims_verified=%.2f%%" % (
            reviewed * 100 / total, verified * 100 / total
        ))
    else:
        print("  Compliance:            No T83 reviews yet")


def do_review(conn, limit=5000, seed_ids=None, dry_run=False):
    """Review claims: UPDATE verification_status + INSERT en_audit_log. Zero-ALTER."""
    ts = datetime.now().isoformat(timespec="seconds")
    reviewed = 0
    batch_log = []

    for claim in query_candidates(conn, limit=limit, seed_ids=seed_ids):
        claim_id = claim["claim_id"]
        entity_id = claim["entity_id"]
        source_id = claim["source_id"]
        claim_type = claim["claim_type"]
        subject = claim["subject"]
        object_text = claim["object_text"]

        if dry_run:
            reviewed += 1
            if reviewed <= 20:
                print("  [DRY] claim_id=%s entity=%s src=%s type=%s subject=%s" % (
                    claim_id, entity_id, source_id, claim_type, (subject or "")[:40]
                ))
            continue

        # 1) UPDATE entity_claims
        conn.execute(
            "UPDATE entity_claims SET verification_status='verified', reviewed_by=?, reviewed_at=? WHERE claim_id=?",
            (REVIEWED_BY, ts, claim_id)
        )

        # 2) INSERT en_audit_log
        conn.execute(
            """INSERT INTO en_audit_log
               (entity_ref, action, field_name, old_value, new_value, evidence_sources, editor, created_at)
               VALUES (?, 'review', 'verification_status', 'unverified', 'verified', ?, ?, ?)""",
            (entity_id, source_id, REVIEWED_BY, ts)
        )

        reviewed += 1
        if reviewed % 500 == 0:
            conn.commit()
            print("  ... reviewed %d claims" % reviewed)

    if not dry_run:
        conn.commit()

    return reviewed


def do_revert(conn, dry_run=False):
    """Revert all T83_auto reviews: UPDATE unverified + DELETE audit log. Zero-ALTER."""
    t83_count = conn.execute(
        "SELECT COUNT(*) n FROM entity_claims WHERE reviewed_by=?", (REVIEWED_BY,)
    ).fetchone()["n"]

    if t83_count == 0:
        print("  Nothing to revert (0 T83 reviews)")
        return 0

    print("  Reverting %d T83 reviews..." % t83_count)

    if dry_run:
        print("  [DRY] Would revert %d claims" % t83_count)
        return t83_count

    # Revert entity_claims
    conn.execute(
        "UPDATE entity_claims SET verification_status='unverified', reviewed_by=NULL, reviewed_at=NULL WHERE reviewed_by=?",
        (REVIEWED_BY,)
    )

    # Revert en_audit_log
    log_ids = [
        r["log_id"] for r in
        conn.execute("SELECT log_id FROM en_audit_log WHERE action='review' AND editor=?", (REVIEWED_BY,))
    ]
    if log_ids:
        placeholders = ",".join("?" for _ in log_ids)
        conn.execute("DELETE FROM en_audit_log WHERE log_id IN ({ph})".format(ph=placeholders), log_ids)

    conn.commit()
    print("  Reverted %d claims + %d audit log entries" % (t83_count, len(log_ids)))
    return t83_count


def load_seed(filepath):
    """Load entity_ids from file (one per line, strip, skip # comments)."""
    ids = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                ids.append(line)
    return ids


def main():
    parser = argparse.ArgumentParser(description="T83 Bootstrap Review (Zero-ALTER)")
    parser.add_argument("--db", default=DB_PATH)
    parser.add_argument("--auto", action="store_true", help="Auto-select top entities by multi-source")
    parser.add_argument("--seed", help="File with entity_ids (one per line)")
    parser.add_argument("--review", action="store_true", help="Review claims (write DB)")
    parser.add_argument("--revert", action="store_true", help="Revert T83 reviews")
    parser.add_argument("--dry-run", action="store_true", help="Print plan, no DB writes")
    parser.add_argument("--stats", action="store_true", help="Print current review stats")
    parser.add_argument("--limit", type=int, default=5000, help="Max claims to review")
    args = parser.parse_args()

    if not os.path.exists(args.db):
        print("ERROR: DB not found:", args.db)
        sys.exit(1)

    conn = get_conn(args.db)

    if args.stats:
        stats(conn)
        conn.close()
        return

    if args.revert:
        do_revert(conn, dry_run=args.dry_run)
        stats(conn)
        conn.close()
        return

    if not args.review and not args.dry_run:
        print("ERROR: specify --review or --dry-run or --revert or --stats")
        parser.print_help()
        conn.close()
        sys.exit(1)

    seed_ids = None
    if args.seed:
        seed_ids = load_seed(args.seed)
        print("Loaded %d entity_ids from %s" % (len(seed_ids), args.seed))
    elif not args.auto:
        print("ERROR: specify --auto or --seed <file>")
        parser.print_help()
        conn.close()
        sys.exit(1)

    print("== T83 Bootstrap Review ==")
    print("  Mode: %s" % ("DRY-RUN" if args.dry_run else "REVIEW"))
    print("  Sources: %s (by authority_score DESC)" % ", ".join(ACTIVE_SOURCES))
    print("  Limit: %d claims" % args.limit)
    print()

    reviewed = do_review(conn, limit=args.limit, seed_ids=seed_ids, dry_run=args.dry_run)
    print()
    print("  Reviewed: %d claims" % reviewed)
    stats(conn)
    conn.close()


if __name__ == "__main__":
    main()
