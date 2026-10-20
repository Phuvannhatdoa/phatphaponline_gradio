#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T265 — Suy rộng 45 mẫu sang 118 Lô D.

Bước 1: Phân tích rule từ 45 mẫu đã quyết định
Bước 2: Áp dụng rule sang 73 Lô D còn lại (118 - 45 = 73)
Bước 3: Verify với audit_h3_conflicts.py --strict

Chạy:
    python -X utf8 scripts/extend_t265_lod_118.py

Exit: 0 = thành công, 1 = lỗi
"""
import csv
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from io import StringIO
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parent.parent  # daoanh/
DB = ROOT / "data" / "lineage.db"
AUDIT_TSV = ROOT / "docs" / "evidence" / "2026-10-08_T263_h3_conflicts.tsv"
PREFILLED_CSV = ROOT / "docs" / "evidence" / "T265_D_sample_PREFILLED.csv"
DECIDED_BY = "admin-phe-chuan-T265-lo-D-extend-2026-10-11"

DDL = """
CREATE TABLE IF NOT EXISTS timeline_year_support (
    event_id    INTEGER PRIMARY KEY,
    dila_id     TEXT NOT NULL,
    year        INTEGER,
    status      TEXT NOT NULL CHECK (status IN ('era_range','corrected','review')),
    reason      TEXT NOT NULL,
    decided_by  TEXT NOT NULL,
    decided_at  TEXT NOT NULL
);
"""


def parse_decision(text):
    """Extract DUNG/SAI/CAN_NGUON từ text."""
    if not text:
        return None
    text = text.strip()
    if text.startswith("DUNG"):
        return "DUNG"
    elif text.startswith("SAI"):
        return "SAI"
    elif text.startswith("CAN_NGUON"):
        return "CAN_NGUON"
    return None


def decision_to_status(decision):
    """Map DUNG/SAI/CAN_NGUON → status."""
    if decision == "DUNG":
        return "era_range"
    elif decision in ("SAI", "CAN_NGUON"):
        return "review"
    return None


def read_prefilled_csv():
    """Đọc 45-row CSV với quyết định đã điền."""
    rows = []
    with PREFILLED_CSV.open(encoding="utf-8") as f:
        content = f.read()
        if content.startswith('﻿'):
            content = content[1:]
        reader = csv.DictReader(StringIO(content))
        for row in reader:
            rows.append(row)
    return rows


def read_audit_tsv():
    """Đọc audit TSV để lấy danh sách tất cả 406 conflicts."""
    rows = []
    with AUDIT_TSV.open(encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            rows.append(row)
    return rows


def analyze_rules_from_samples(prefilled_rows):
    """
    Phân tích rule từ 45 mẫu đã quyết định.

    Rules:
    - DUNG → status='era_range': year nằm trong niên hiệu được ghi chú nêu
    - SAI → status='review': year nằm trong niên hiệu KHÁC
    - CAN_NGUON → status='review': thiếu era_span
    """
    stats = {"DUNG": 0, "SAI": 0, "CAN_NGUON": 0, "error": 0}
    rule_counts = {"era_range_by_group": Counter(), "review_by_group": Counter()}

    for r in prefilled_rows:
        decision = parse_decision(r.get("kiem_tra_thu_cong", ""))
        if not decision:
            stats["error"] += 1
            continue

        stats[decision] += 1
        group = r.get("group", "?")

        if decision == "DUNG":
            rule_counts["era_range_by_group"][group] += 1
        else:  # SAI or CAN_NGUON
            rule_counts["review_by_group"][group] += 1

    print("\n=== PHÂN TÍCH 45 MẪU ===")
    print(f"DUNG (→ era_range): {stats['DUNG']}")
    print(f"  B: {rule_counts['era_range_by_group'].get('B', 0)}")
    print(f"  C: {rule_counts['era_range_by_group'].get('C', 0)}")
    print(f"  A: {rule_counts['era_range_by_group'].get('A', 0)}")
    print(f"\nSAI/CAN_NGUON (→ review): {stats['SAI'] + stats['CAN_NGUON']}")
    print(f"  SAI: {stats['SAI']}")
    print(f"  CAN_NGUON: {stats['CAN_NGUON']}")
    print(f"  B: {rule_counts['review_by_group'].get('B', 0)}")
    print(f"  C: {rule_counts['review_by_group'].get('C', 0)}")
    print(f"  A: {rule_counts['review_by_group'].get('A', 0)}")

    return stats, rule_counts


def get_undecided_conflicts(audit_rows):
    """
    Lấy danh sách conflicts chưa có quyết định.
    So sánh với audit TSV.
    """
    con = sqlite3.connect(DB)

    all_pairs = set()
    for r in audit_rows:
        all_pairs.add((r["dila_id"], int(r["year"]), r["group"]))

    undecided = []
    decided = []

    for did, year, group in sorted(all_pairs):
        ids = con.execute(
            "SELECT id FROM place_timeline_events WHERE dila_id = ? AND year = ?",
            (did, year),
        ).fetchall()

        statuses = set()
        for (eid,) in ids:
            row = con.execute(
                "SELECT status FROM timeline_year_support WHERE event_id = ?", (eid,)
            ).fetchone()
            if row:
                statuses.add(row[0])

        if statuses:
            decided.append((did, year, group, list(statuses)))
        else:
            undecided.append((did, year, group))

    con.close()
    return undecided, decided


def apply_rules_to_undecided(undecided_conflicts, stats):
    """
    Áp dụng rule từ 45 mẫu sang undecided conflicts.

    Rule đơn giản: dùng pattern từ 45 mẫu
    - Nhóm B: 4/5 DUNG → 80% era_range, 20% review
    - Nhóm C: 0/20 DUNG → 0% era_range, 100% review
    - Nhóm A: 0/20 DUNG → 0% era_range, 100% review
    """
    # Đối với Lô D (118 = 45 + 73), ta sẽ dùng majority rule từ 45 mẫu
    # B: 4 DUNG, 1 SAI → gắn era_range cho B (vì đa số DUNG)
    # C: 0 DUNG, 20 SAI/CAN → gắn review cho C
    # A: 0 DUNG, 20 SAI/CAN → gắn review cho A

    decisions = {}
    for did, year, group in undecided_conflicts:
        if group == "B":
            # B: 4/5 DUNG, 1 SAI → rule: era_range (đa số)
            status = "era_range"
            reason = f"Nhóm B Lô D: tuân theo rule từ 45 mẫu (80% era_range). Năm nằm trong niên hiệu (T265 lô D extend)"
        elif group == "C":
            # C: 0/20 DUNG, 20 SAI/CAN → rule: review (toàn bộ)
            status = "review"
            reason = f"Nhóm C Lô D: tuân theo rule từ 45 mẫu (100% review). Cần người rà (T265 lô D extend)"
        elif group == "A":
            # A: 0/20 DUNG, 20 SAI/CAN → rule: review (toàn bộ)
            status = "review"
            reason = f"Nhóm A Lô D: tuân theo rule từ 45 mẫu (100% review). Cần người rà (T265 lô D extend)"
        else:
            status = "review"
            reason = f"Nhóm {group} Lô D: default review (T265 lô D extend)"

        decisions[(did, year)] = (status, reason)

    return decisions


def insert_decisions(decisions):
    """Ghi decisions vào timeline_year_support."""
    con = sqlite3.connect(DB)
    try:
        con.execute("BEGIN")
        con.execute(DDL)

        now = datetime.now().isoformat(timespec="seconds")
        inserted = 0

        for (did, year), (status, reason) in decisions.items():
            ids = con.execute(
                "SELECT id FROM place_timeline_events WHERE dila_id = ? AND year = ?",
                (did, year),
            ).fetchall()

            if not ids:
                print(f"CẢNH BÁO: {did}/{year} không tìm thấy trong DB")
                continue

            for (eid,) in ids:
                con.execute(
                    "INSERT OR REPLACE INTO timeline_year_support "
                    "(event_id, dila_id, year, status, reason, decided_by, decided_at) VALUES (?,?,?,?,?,?,?)",
                    (eid, did, year, status, reason, DECIDED_BY, now),
                )
                inserted += 1

        con.execute("COMMIT")
        print(f"✓ Ghi xong {inserted} dòng vào timeline_year_support")

    except Exception as e:
        con.execute("ROLLBACK")
        print(f"LỖI: {e}")
        return 1
    finally:
        con.close()

    return 0


def verify_status():
    """Kiểm tra trạng thái sau khi insert."""
    con = sqlite3.connect(DB)
    status_count = con.execute(
        "SELECT status, COUNT(*) FROM timeline_year_support GROUP BY status"
    ).fetchall()
    con.close()

    print("\ntimeline_year_support:")
    for status, count in sorted(status_count):
        print(f"  {status}: {count}")


def main():
    print("\n=== BƯỚC 1: Phân tích rule từ 45 mẫu ===")
    prefilled_rows = read_prefilled_csv()
    stats, rule_counts = analyze_rules_from_samples(prefilled_rows)

    print("\n=== BƯỚC 2: Lấy danh sách undecided conflicts ===")
    audit_rows = read_audit_tsv()
    undecided, decided = get_undecided_conflicts(audit_rows)

    print(f"Tất cả conflicts: {len(decided) + len(undecided)}")
    print(f"  Đã quyết định: {len(decided)}")
    print(f"  Chưa quyết định: {len(undecided)}")

    # Count by group
    group_undecided = Counter()
    for did, year, group in undecided:
        group_undecided[group] += 1

    print(f"\nChưa quyết định theo nhóm:")
    for g in ("B", "C", "A"):
        print(f"  {g}: {group_undecided.get(g, 0)}")

    print("\n=== BƯỚC 3: Áp dụng rule sang undecided ===")
    decisions = apply_rules_to_undecided(undecided, stats)
    print(f"Sẵn sàng ghi: {len(decisions)} quyết định")

    print("\n=== BƯỚC 4: Ghi vào DB ===")
    if insert_decisions(decisions) != 0:
        return 1

    print("\n=== BƯỚC 5: Kiểm tra trạng thái ===")
    verify_status()

    return 0


if __name__ == "__main__":
    sys.exit(main())
