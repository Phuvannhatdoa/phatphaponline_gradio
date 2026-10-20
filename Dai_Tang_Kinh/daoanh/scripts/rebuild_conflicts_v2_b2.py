#!/usr/bin/env python3
"""
T157 B-2: Re-snapshot lineage_conflicts_v2 after B-1 ETL + B-3 persons.json fix.

persons.json was globally inverted (teacher/student swapped) → lineage_conflicts_v2
showed ~40,327 spurious conflicts.  After B-3 fix the axes are now canonical, so
re-running the comparison against marcus_networks should dramatically reduce the
conflict count to only genuine DILA↔Marcus disagreements.

Usage:
  python scripts/rebuild_conflicts_v2_b2.py --dry-run   # stats only, no writes
  python scripts/rebuild_conflicts_v2_b2.py --apply     # backup stats + DELETE + INSERT
  python scripts/rebuild_conflicts_v2_b2.py --verify    # show before/after summary
"""
import argparse
import json
import os
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH      = os.path.join(BASE_DIR, "data", "lineage.db")
PERSONS_JSON = os.path.join(BASE_DIR, "data", "persons.json")
BACKUP_DIR   = os.path.join(BASE_DIR, "data", "backups")
BACKUP_LOG   = os.path.join(BACKUP_DIR, "conflicts_v2_b2_pre_snapshot.json")


def load_persons():
    with open(PERSONS_JSON, encoding="utf-8") as f:
        raw = json.load(f)
    return {p["id"]: p for p in raw.get("persons", [])}


def get_marcus_data(conn):
    """teacher→students and student→teachers from marcus_networks."""
    cur = conn.cursor()
    cur.execute("SELECT teacher_id, student_id FROM marcus_networks")
    rows = cur.fetchall()
    teachers_of = defaultdict(list)   # student_id → [teacher_ids]
    students_of = defaultdict(list)   # teacher_id → [student_ids]
    for teacher_id, student_id in rows:
        teachers_of[student_id].append(teacher_id)
        students_of[teacher_id].append(student_id)
    return teachers_of, students_of


def analyze(persons, teachers_of, students_of):
    conflicts = []
    for pid, p in persons.items():
        dila_t = set(x["id"] for x in (p.get("teacher") or []))
        dila_s = set(x["id"] for x in (p.get("student") or []))
        marc_t = set(teachers_of.get(pid, []))
        marc_s = set(students_of.get(pid, []))

        name_zh = ""
        name_vi = ""
        for nm in p.get("names", []):
            if nm.get("type") == "primary":
                name_zh = nm.get("value", "")
            if nm.get("lang") == "vie":
                name_vi = nm.get("value", "")
        if not name_vi:
            for nm in p.get("names", []):
                if nm.get("lang", "").startswith("zho"):
                    name_vi = nm.get("value", "")
                    break

        if dila_t != marc_t:
            conflicts.append(dict(person_id=pid, label=name_zh, name_vi=name_vi,
                                  conflict_type="teacher_set",
                                  dila_data=json.dumps(sorted(dila_t)),
                                  marcus_data=json.dumps(sorted(marc_t)),
                                  dila_count=len(dila_t), marcus_count=len(marc_t)))
        if dila_s != marc_s:
            conflicts.append(dict(person_id=pid, label=name_zh, name_vi=name_vi,
                                  conflict_type="student_set",
                                  dila_data=json.dumps(sorted(dila_s)),
                                  marcus_data=json.dumps(sorted(marc_s)),
                                  dila_count=len(dila_s), marcus_count=len(marc_s)))
    return conflicts


def show_stats(conn, label="Current"):
    cur = conn.cursor()
    total  = cur.execute("SELECT COUNT(*) FROM lineage_conflicts_v2").fetchone()[0]
    t_conf = cur.execute("SELECT COUNT(*) FROM lineage_conflicts_v2 WHERE conflict_type='teacher_set'").fetchone()[0]
    s_conf = cur.execute("SELECT COUNT(*) FROM lineage_conflicts_v2 WHERE conflict_type='student_set'").fetchone()[0]
    res    = cur.execute("SELECT COUNT(*) FROM lineage_conflicts_v2 WHERE resolved=1").fetchone()[0]
    print(f"\n[{label}]")
    print(f"  Total:     {total:,}")
    print(f"  teacher_set: {t_conf:,}  student_set: {s_conf:,}")
    print(f"  Resolved:  {res:,}  Open: {total-res:,}")
    return total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply",   action="store_true")
    parser.add_argument("--verify",  action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if args.verify:
        show_stats(conn, "Post-B2 snapshot")
        conn.close()
        return

    print("Loading persons.json...")
    persons = load_persons()
    print(f"  {len(persons):,} persons loaded")

    print("Loading marcus_networks...")
    teachers_of, students_of = get_marcus_data(conn)
    print(f"  {len(teachers_of):,} persons have Marcus teacher data")

    before = show_stats(conn, "BEFORE rebuild")

    print("\nAnalyzing DILA vs Marcus conflicts...")
    conflicts = analyze(persons, teachers_of, students_of)
    after_count = len(conflicts)
    t_new = sum(1 for c in conflicts if c["conflict_type"] == "teacher_set")
    s_new = sum(1 for c in conflicts if c["conflict_type"] == "student_set")
    print(f"  New conflicts: {after_count:,}  (teacher_set={t_new:,}, student_set={s_new:,})")
    print(f"  Delta: {after_count - before:+,} (was {before:,})")

    if args.dry_run:
        print("\nDRY-RUN: no writes.")
        conn.close()
        return

    if args.apply:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        backup_meta = {
            "timestamp": datetime.now().isoformat(),
            "before_total": before,
            "after_total": after_count,
            "delta": after_count - before,
            "note": "T157 B-2 re-snapshot after B-1 ETL + B-3 persons.json fix"
        }
        with open(BACKUP_LOG, "w", encoding="utf-8") as f:
            json.dump(backup_meta, f, ensure_ascii=False, indent=2)
        print(f"\nMeta backup -> {BACKUP_LOG}")

        cur = conn.cursor()
        cur.execute("DELETE FROM lineage_conflicts_v2")
        deleted = cur.rowcount
        print(f"Deleted {deleted:,} old rows")

        cur.executemany(
            "INSERT INTO lineage_conflicts_v2 (person_id,label,name_vi,conflict_type,dila_data,marcus_data,dila_count,marcus_count) VALUES (:person_id,:label,:name_vi,:conflict_type,:dila_data,:marcus_data,:dila_count,:marcus_count)",
            conflicts
        )
        conn.commit()
        print(f"Inserted {after_count:,} new rows")

        show_stats(conn, "AFTER rebuild")
        print("\nAPPLY DONE. Run --verify anytime to recheck.")
        print("REVERT: restore from lineage.db backup or re-run with old persons.json")

    conn.close()


if __name__ == "__main__":
    main()
