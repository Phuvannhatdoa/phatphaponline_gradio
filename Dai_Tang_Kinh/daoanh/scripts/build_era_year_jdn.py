#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_era_year_jdn.py
======================
Nexus Commit 3 — TIME NORMALIZED LAYER (`era_year_jdn`).

Cung cấp một tầng JDN (Julian Day Number — proleptic Gregorian) để chuẩn hoá
mọi mốc thời gian trong hệ thống. Era = tầng hiển thị (nhân văn), JDN = tầng
số hoá (máy tính) — có thể so sánh/thứ tự tuyến tính giữa các niên đại khác
nhau, kể cả năm âm (TCN).

Nguồn: `place_timeline_events.year` (3,351 rows — founding/dissolved) →
nhóm theo năm, lưu era_name (label_zh niên đại liên quan) + JDN(01-01 năm đó).

JDN công thức proleptic Gregorian (đã kiểm chứng: 2000-01-01 → 2451545):
    a  = (14 - 1) // 12 = 1
    y2 = year + 4800 - a
    m2 = 1 + 12*a - 3 = 10
    jdn = 1 + (153*m2 + 2)//5 + 365*y2 + y2//4 - y2//100 + y2//400 - 32045
Dùng phép chia sàn Python nên năm âm (TCN) xử lý đúng.

Bảng `era_year_jdn` (additive — KHÔNG đụng bảng nguồn):
    era_year_jdn(
        id       INTEGER PK,
        year     INTEGER NOT NULL UNIQUE,   -- năm (âm = TCN, vd -1599)
        era_name TEXT,                       -- tên niên đại liên quan (hiển thị)
        jdn      INTEGER,                    -- JDN(01-01) chuẩn hoá
        year_bce INTEGER,                    -- 1 nếu âm lịch TCN
        source   TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )

Chạy (từ root daoanh):
  python scripts/build_era_year_jdn.py             # apply
  python scripts/build_era_year_jdn.py --dry-run   # chỉ xem
"""
import io
import os
import sqlite3
import sys
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, '..', 'data', 'lineage.db')
DRY_RUN = '--dry-run' in sys.argv


def to_jdn(year):
    """JDN cho 00:00 ngày 01-01 của năm (proleptic Gregorian). Kiểm chứng 2000→2451545."""
    a = (14 - 1) // 12
    y2 = year + 4800 - a
    m2 = 1 + 12 * a - 3
    return 1 + (153 * m2 + 2) // 5 + 365 * y2 + y2 // 4 - y2 // 100 + y2 // 400 - 32045


def main():
    mode = 'DRY-RUN' if DRY_RUN else 'APPLY'
    print(f'=== Nexus Commit 3 — Build era_year_jdn (TIME mirror) [{mode}] ===')
    print(f'DB: {DB_PATH}')
    print(f'Date: {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    print(f'Sanity: to_jdn(2000) = {to_jdn(2000)} (expect 2451545)')

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Distinct năm + era_name (label_zh) từ timeline
    rows = conn.execute("""
        SELECT year,
               GROUP_CONCAT(DISTINCT label_zh) AS eras,
               COUNT(*) AS n
        FROM place_timeline_events
        WHERE year IS NOT NULL
        GROUP BY year
        ORDER BY year
    """).fetchall()
    print(f'  distinct years: {len(rows):,}')

    built = []
    for r in rows:
        yr = r['year']
        built.append((
            yr, r['eras'] or '', to_jdn(yr), 1 if yr < 0 else 0,
            'place_timeline_events',
        ))

    # Preview
    print('  year range:', built[0][0], '→', built[-1][0] if built else None)
    for b in built[:5]:
        print(f'    year={b[0]} era={b[1]!r} jdn={b[2]} bce={b[3]}')
    print('  ...')
    for b in built[-3:]:
        print(f'    year={b[0]} era={b[1]!r} jdn={b[2]} bce={b[3]}')

    if DRY_RUN:
        print('[DRY-RUN] Không thay đổi DB.')
        conn.close()
        return

    conn.execute("""
        CREATE TABLE IF NOT EXISTS era_year_jdn (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL UNIQUE,
            era_name TEXT,
            jdn INTEGER,
            year_bce INTEGER,
            source TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_era_year_jdn_year ON era_year_jdn(year)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_era_year_jdn_jdn ON era_year_jdn(jdn)")

    conn.executemany(
        "INSERT OR REPLACE INTO era_year_jdn (year, era_name, jdn, year_bce, source) "
        "VALUES (?,?,?,?,?)",
        built,
    )
    conn.commit()

    total = conn.execute('SELECT COUNT(*) FROM era_year_jdn').fetchone()[0]
    bce = conn.execute('SELECT COUNT(*) FROM era_year_jdn WHERE year_bce = 1').fetchone()[0]
    print(f'  era_year_jdn total: {total:,} (BCE years: {bce})')
    print('[DONE]')
    conn.close()


if __name__ == '__main__':
    main()
