#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T252 — dump các dòng FAIL H3 ra TSV (đầu ra chuẩn để so sánh 4 mốc đo).

    python -X utf8 scripts/t252_h3_dump.py [kieu]
      kieu = all | none | out | mid | w1    (mac dinh: all)

Cùng bộ luật với h3() trong scripts/audit_data_honesty.py — in thêm cột loai
để đối chiếu "dòng nào được mốc nào sửa". Dùng chung để:
  baseline 132  ->  sau W1 (43)  ->  sau W3  ->  sau W4 (=0)
"""
import csv
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audit_data_honesty as A  # noqa: E402

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                  "data", "lineage.db")


def classify(conn, era_map):
    """Yield (dila_id, year, loai, sref, label, note) cho tung dong FAIL H3."""
    rows = conn.execute(
        "SELECT p.dila_id, p.year, p.source_ref, p.label_zh, pd.note "
        "FROM place_timeline_events p "
        "LEFT JOIN places_dila pd ON pd.id = p.dila_id "
        "WHERE p.year IS NOT NULL").fetchall()
    for did, year, sref, label, note in rows:
        note = note or ""
        label = label or ""
        sref = sref or ""
        if str(year) in note or str(year) in note.replace("（", "(").replace("）", ")"):
            continue
        r = A.era_year_in_text(note, era_map, year)
        if r is not None and r >= 0:
            continue
        if A.era_year_exact(note, era_map, year):
            continue
        if A.era_year_exact(label, era_map, year):
            continue
        if re.match(r"^Q\d+", sref):
            continue
        if sref.endswith("midpoint"):
            rng = A.label_range(label)
            if rng is None:
                yield did, year, "mid-norange", sref, label, note
                continue
            if rng[0] <= year <= rng[1]:
                continue
            yield did, year, "mid-out", sref, label, note
            continue
        if A.era_mid_hit(note, era_map, year) or A.era_mid_hit(label, era_map, year):
            continue
        if A.era_range_hit(note, era_map, year) or A.era_range_hit(label, era_map, year):
            continue
        yield did, year, ("out" if (r is not None and r < 0) else "none"), \
            sref, label, note


def main():
    kind = sys.argv[1] if len(sys.argv) > 1 else "all"
    want = {"all": None,
            "none": {"none"},
            "out": {"out"},
            "mid": {"mid-norange", "mid-out"},
            "w1": {"none", "out"}}.get(kind)
    if want is None and kind != "all":
        print("kieu khong ro (all|none|out|mid|w1): %s" % kind, file=sys.stderr)
        sys.exit(2)
    conn = sqlite3.connect(DB)
    era_map = A.load_era_map(conn)
    w = csv.writer(sys.stdout, delimiter="\t", lineterminator="\n",
                   quoting=csv.QUOTE_NONE, escapechar=None)
    w.writerow(["dila_id", "year", "loai", "sref", "label", "note"])
    n = 0
    for did, year, loai, sref, label, note in classify(conn, era_map):
        if want and loai not in want:
            continue
        n += 1
        w.writerow([did, year, loai, sref, label,
                    " ".join((note or "").split())[:400]])
    print("# rows=%d kieu=%s" % (n, kind), file=sys.stderr)


if __name__ == "__main__":
    main()
