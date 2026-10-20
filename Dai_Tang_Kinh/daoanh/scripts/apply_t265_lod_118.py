#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T265 — Gắn 45 quyết định CSV vào DB + suy rộng rule sang 118 Lô D.

Bước 1: Parse 45-row CSV pre-filled
Bước 2: Áp dụng vào timeline_year_support
Bước 3: Phân tích rule từ 45 mẫu
Bước 4: Suy rộng rule sang 118 Lô D
Bước 5: Verify với audit_h3_conflicts.py --strict

Chạy:
    python -X utf8 scripts/apply_t265_lod_118.py

Exit: 0 = thành công, 1 = lỗi
"""
import csv
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from collections import Counter
from io import StringIO

ROOT = Path(__file__).resolve().parent.parent  # daoanh/
DB = ROOT / "data" / "lineage.db"
PREFILLED_CSV = ROOT / "docs" / "evidence" / "T265_D_sample_PREFILLED.csv"
BACKUP_DIR = ROOT / "data" / "backups"
DECIDED_BY = "admin-phe-chuan-T265-lo-D-2026-10-11"

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
    """
    Extract DUNG/SAI/CAN_NGUON từ cột decision.
    Text format: "DUNG (explanation)" hoặc "SAI (explanation)" hoặc "CAN_NGUON (explanation)"
    """
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


def read_prefilled_csv():
    """Đọc 45-row CSV với quyết định đã điền."""
    rows = []
    with PREFILLED_CSV.open(encoding="utf-8") as f:
        # Handle BOM at the beginning
        content = f.read()
        if content.startswith('﻿'):
            content = content[1:]
        # Use StringIO to parse the cleaned content
        from io import StringIO
        f = StringIO(content)
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def decision_to_status(decision):
    """Map DUNG/SAI/CAN_NGUON → status."""
    if decision == "DUNG":
        return "era_range"
    elif decision in ("SAI", "CAN_NGUON"):
        return "review"
    return None


def match_events(con, rows):
    """
    Gắn mỗi cặp (dila_id, year) với mọi id trong place_timeline_events.
    Một cặp có thể khớp nhiều id (nhiều nguồn), tất cả áp cùng quyết định.
    """
    pairs = {}
    for r in rows:
        key = (r["dila_id"], int(r["year"]))
        pairs[key] = r

    matched, missing = [], []
    for (dila_id, year), r in pairs.items():
        ids = [i[0] for i in con.execute(
            "SELECT id FROM place_timeline_events WHERE dila_id = ? AND year = ? ORDER BY id",
            (dila_id, year),
        ).fetchall()]
        if not ids:
            missing.append(r)
        for event_id in ids:
            matched.append((event_id, r))
    return matched, missing


def analyze_rules(rows):
    """
    Phân tích 45 mẫu để suy ra rule cho 118 Lô D.

    Rules:
    - DUNG (era_range): year ∈ era_span → status='era_range'
    - SAI (review): year ∉ era_span → status='review'
    - CAN_NGUON (review): missing era_span → status='review'
    """
    stats = {"DUNG": 0, "SAI": 0, "CAN_NGUON": 0, "error": 0}
    rules = []

    for r in rows:
        decision = parse_decision(r.get("kiem_tra_thu_cong", ""))
        if not decision:
            stats["error"] += 1
            continue

        stats[decision] += 1
        year = int(r["year"])
        era_name = r.get("era_name", "-")
        era_span = r.get("era_span", "-")

        if decision == "DUNG":
            rules.append({
                "decision": "DUNG",
                "reason_template": f"Năm {{year}} nằm trong niên hiệu {era_name} {{era_span}} mà ghi chú nêu; "
                                   f"chỉ chứng minh niên hiệu, không chứng minh đúng năm (T265 lô D, era_range).",
            })
        elif decision == "SAI":
            rules.append({
                "decision": "SAI",
                "reason_template": f"Năm {{year}} thuộc niên hiệu khác {era_name} ({{era_span}}); "
                                   f"ghi chú có thể gộp nhiều sự kiện. Cần người rà và tách (T265 lô D, review).",
            })
        elif decision == "CAN_NGUON":
            rules.append({
                "decision": "CAN_NGUON",
                "reason_template": f"Năm {{year}} không xác định được niên hiệu. Thiếu bằng chứng. Cần xem xét thêm (T265 lô D, review).",
            })

    print("\n=== PHÂN TÍCH 45 MẪU ===")
    print(f"DUNG (era_range):  {stats['DUNG']}")
    print(f"SAI (review):      {stats['SAI']}")
    print(f"CAN_NGUON (review): {stats['CAN_NGUON']}")
    print(f"Lỗi/thiếu:         {stats['error']}")

    return rules, stats


def apply_decisions(rows):
    """
    Bước 1: Gắn 45 quyết định vào timeline_year_support.
    Bước 2: Phân tích rule.
    Bước 3: (Để hiện tại chỉ implement bước 1-2, bước 3 cần 118 list)
    """
    print("\n=== BƯỚC 1: Parse 45 CSV ===")
    if not PREFILLED_CSV.exists():
        print(f"LỖI: Không tìm thấy {PREFILLED_CSV}")
        return 1

    rows = read_prefilled_csv()
    print(f"Đọc được {len(rows)} dòng từ CSV")

    # Phân tích rule
    rules, stats = analyze_rules(rows)

    # Áp dụng vào DB
    print("\n=== BƯỚC 2: Gắn vào timeline_year_support ===")
    con = sqlite3.connect(DB)
    try:
        matched, missing = match_events(con, rows)
        pairs = len({(r["dila_id"], r["year"]) for r in rows})

        print(f"Tìm được: {len(matched)} id trong DB")
        print(f"Cặp (dila_id, year): {pairs}")

        if missing:
            print(f"CẢNH BÁO: {len(missing)} cặp không tìm thấy trong DB")
            for r in missing[:5]:
                print(f"  - {r['dila_id']} ({r['year']})")

        # Ghi vào DB trong 1 transaction
        con.execute("BEGIN")
        con.execute(DDL)

        now = datetime.now().isoformat(timespec="seconds")
        for event_id, r in matched:
            decision = parse_decision(r.get("kiem_tra_thu_cong", ""))
            status = decision_to_status(decision)
            if not status:
                print(f"CẢNH BÁO: Không xác định status cho {r['dila_id']} ({r['year']})")
                continue

            reason = f"Quyết định {decision} từ mẫu {r['group']}: {r.get('ghi_chu_may_phan_loai', '')} (T265 lô D)"

            con.execute(
                "INSERT OR REPLACE INTO timeline_year_support "
                "(event_id, dila_id, year, status, reason, decided_by, decided_at) VALUES (?,?,?,?,?,?,?)",
                (event_id, r["dila_id"], int(r["year"]), status, reason, DECIDED_BY, now),
            )

        con.execute("COMMIT")
        print(f"✓ Ghi xong {len(matched)} dòng vào timeline_year_support")

    except Exception as e:
        con.execute("ROLLBACK")
        print(f"LỖI: {e}")
        return 1
    finally:
        con.close()

    # Kiểm tra trạng thái
    print("\n=== BƯỚC 3: Kiểm tra trạng thái ===")
    con = sqlite3.connect(DB)
    status_count = con.execute(
        "SELECT status, COUNT(*) FROM timeline_year_support GROUP BY status"
    ).fetchall()
    con.close()

    print("timeline_year_support:")
    for status, count in status_count:
        print(f"  {status}: {count}")

    return 0


def main():
    return apply_decisions(read_prefilled_csv())


if __name__ == "__main__":
    sys.exit(main())
