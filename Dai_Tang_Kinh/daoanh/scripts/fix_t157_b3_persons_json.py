#!/usr/bin/env python3
"""
T157 B-3: Fix inverted teacher/student in data/persons.json

Root cause: persons.json generator swaps teacher/student axes —
  persons.json teacher=[student's id]  student=[teacher's id]  (WRONG)
  lineage_edge_assertions uses subject_person_id → object_person_id = teacher→student (CANONICAL)

Strategy: for each person in persons.json, rebuild teacher[] and student[]
from lineage_edge_assertions (canonical DB, already fixed by T157 B-1 ETL).
Only replace entries that have DB ground-truth. Leave untouched if no DB data.

Usage:
  python scripts/fix_t157_b3_persons_json.py --dry-run    # show stats, write nothing
  python scripts/fix_t157_b3_persons_json.py --apply      # backup + fix in place
  python scripts/fix_t157_b3_persons_json.py --verify     # verify A008874 + stats after apply
  python scripts/fix_t157_b3_persons_json.py --revert     # restore from backup
"""
import argparse
import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERSONS_JSON = os.path.join(BASE_DIR, "data", "persons.json")
DB_PATH = os.path.join(BASE_DIR, "data", "lineage.db")
BACKUP_DIR = os.path.join(BASE_DIR, "data", "backups")
BACKUP_PATH = os.path.join(BACKUP_DIR, "persons_b3_20260922.json")


def build_db_lookup():
    """Build {person_id: {teachers: [{id, name}], students: [{id, name}]}} from DB."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # teachers of X = rows where object_person_id=X  (someone teaches X)
    # students of X = rows where subject_person_id=X (X teaches someone)
    # Only use MARCUS (L1, most reliable) + DILA (L2) assertions, status=active
    cur.execute("""
        SELECT lea.subject_person_id, lea.object_person_id,
               p_subj.name_zh AS subj_name, p_obj.name_zh AS obj_name
        FROM lineage_edge_assertions lea
        LEFT JOIN people p_subj ON p_subj.id = lea.subject_person_id
        LEFT JOIN people p_obj  ON p_obj.id  = lea.object_person_id
        WHERE lea.status = 'active'
          AND lea.source_code IN ('MARCUS', 'DILA')
        ORDER BY lea.trust_level ASC, lea.source_code ASC
    """)
    rows = cur.fetchall()
    conn.close()

    lookup = {}  # person_id → {teachers: set of (id, name), students: set of (id, name)}
    seen_pairs = set()  # dedupe (subject, object) across MARCUS/DILA

    for r in rows:
        subj = r["subject_person_id"]
        obj  = r["object_person_id"]
        pair = (subj, obj)
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)

        subj_name = r["subj_name"] or ""
        obj_name  = r["obj_name"] or ""

        # subj is teacher of obj
        if subj not in lookup:
            lookup[subj] = {"teachers": [], "students": [], "_seen_t": set(), "_seen_s": set()}
        if obj not in lookup:
            lookup[obj] = {"teachers": [], "students": [], "_seen_t": set(), "_seen_s": set()}

        # For subj: obj is a student
        if obj not in lookup[subj]["_seen_s"]:
            lookup[subj]["students"].append({"id": obj, "name": obj_name})
            lookup[subj]["_seen_s"].add(obj)

        # For obj: subj is a teacher
        if subj not in lookup[obj]["_seen_t"]:
            lookup[obj]["teachers"].append({"id": subj, "name": subj_name})
            lookup[obj]["_seen_t"].add(subj)

    # Clean up internal sets
    for v in lookup.values():
        del v["_seen_t"], v["_seen_s"]

    return lookup


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--revert", action="store_true")
    args = parser.parse_args()

    if args.revert:
        if not os.path.exists(BACKUP_PATH):
            print(f"ERROR: backup not found at {BACKUP_PATH}")
            sys.exit(1)
        shutil.copy2(BACKUP_PATH, PERSONS_JSON)
        print(f"REVERTED: restored {PERSONS_JSON} from {BACKUP_PATH}")
        return

    if args.verify:
        with open(PERSONS_JSON, encoding="utf-8") as f:
            data = json.load(f)
        persons = data["persons"]
        a8 = next((p for p in persons if p.get("id") == "A008874"), None)
        if a8:
            print(f"A008874 teacher: {a8.get('teacher')}")
            print(f"A008874 student: {a8.get('student')}")
            t_ids = [x["id"] for x in (a8.get("teacher") or [])]
            s_ids = [x["id"] for x in (a8.get("student") or [])]
            if "A001707" in t_ids and "A009491" in s_ids:
                print("VERIFY PASS: A008874 teacher=慧忠(A001707) student=慧寂(A009491) — CORRECT")
            elif "A009491" in t_ids and "A001707" in s_ids:
                print("VERIFY FAIL: still inverted — teacher=慧寂 student=慧忠")
            else:
                print(f"VERIFY UNKNOWN: teacher_ids={t_ids} student_ids={s_ids}")
        else:
            print("A008874 not found")
        return

    print("Loading persons.json...")
    with open(PERSONS_JSON, encoding="utf-8") as f:
        data = json.load(f)
    persons = data["persons"]

    print("Building DB lookup from lineage_edge_assertions...")
    lookup = build_db_lookup()
    print(f"  DB lookup: {len(lookup)} persons with teacher/student data")

    stats = {"fixed": 0, "skipped_no_db": 0, "unchanged": 0, "total": len(persons)}
    changed = []

    for p in persons:
        pid = p.get("id")
        if not pid:
            continue

        old_t = p.get("teacher") or []
        old_s = p.get("student") or []

        if pid not in lookup:
            if old_t or old_s:
                stats["skipped_no_db"] += 1
            continue

        db = lookup[pid]
        new_t = db["teachers"]
        new_s = db["students"]

        old_t_ids = sorted(x["id"] for x in old_t)
        old_s_ids = sorted(x["id"] for x in old_s)
        new_t_ids = sorted(x["id"] for x in new_t)
        new_s_ids = sorted(x["id"] for x in new_s)

        if old_t_ids == new_t_ids and old_s_ids == new_s_ids:
            stats["unchanged"] += 1
            continue

        stats["fixed"] += 1
        changed.append({
            "id": pid,
            "old_teacher_ids": old_t_ids, "new_teacher_ids": new_t_ids,
            "old_student_ids": old_s_ids, "new_student_ids": new_s_ids,
        })
        if args.apply:
            p["teacher"] = new_t
            p["student"] = new_s

    print(f"\nStats:")
    print(f"  Total persons:       {stats['total']}")
    print(f"  Fixed (DB override): {stats['fixed']}")
    print(f"  Unchanged (matched): {stats['unchanged']}")
    print(f"  Skipped (no DB):     {stats['skipped_no_db']}")

    if changed:
        print("\nSample changes (first 5):")
        for c in changed[:5]:
            print("  %s: teacher %s -> %s" % (c['id'], c['old_teacher_ids'], c['new_teacher_ids']))
            print("         student %s -> %s" % (c['old_student_ids'], c['new_student_ids']))

    if args.dry_run:
        print("\nDRY-RUN: no files written.")
        return

    if args.apply:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        shutil.copy2(PERSONS_JSON, BACKUP_PATH)
        print(f"\nBacked up → {BACKUP_PATH}")
        with open(PERSONS_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        print(f"Written   → {PERSONS_JSON}")
        print("\nAPPLY DONE. Run --verify to confirm A008874.")
        print(f"REVERT:  python scripts/fix_t157_b3_persons_json.py --revert")


if __name__ == "__main__":
    main()
