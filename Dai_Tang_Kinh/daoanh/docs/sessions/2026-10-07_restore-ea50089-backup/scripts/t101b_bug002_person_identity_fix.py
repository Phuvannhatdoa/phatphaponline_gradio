"""
T101b — BUG-002 Migration: Person Identity Fix
place_person_bibl rows 7326/7340/7343/7346 for PL000000023255

Vấn đề: ETL gán nhầm person_id → UI show sai người lịch sử.
Fix: person_id=NULL, confidence=0.0, ghi note đầy đủ, giữ person_name_raw.

Usage:
  python scripts/t101b_bug002_person_identity_fix.py --dry-run
  python scripts/t101b_bug002_person_identity_fix.py --apply
  python scripts/t101b_bug002_person_identity_fix.py --revert
"""

import sqlite3, json, sys, os
from datetime import datetime

DB_PATH  = os.path.join(os.path.dirname(__file__), '..', 'data', 'lineage.db')
SNAPSHOT = os.path.join(os.path.dirname(__file__), '..', 'data',
                        'bug002_person_identity_snapshot.json')

# 4 rows cần fix — verified 2026-09-08
FIXES = [
    {
        'ppb_id': 7326,
        'raw_name': '釋辯相',
        'wrong_person_id': 'A002000',
        'wrong_name_zh': '淨影慧遠',
        'reason': 'ETL mismatch: 釋辯相 ≠ 淨影慧遠 (523-592 Bắc Tề/Tùy). Hai người khác nhau.',
    },
    {
        'ppb_id': 7340,
        'raw_name': '恒月',
        'wrong_person_id': 'A009319',
        'wrong_name_zh': '釋普寂',
        'reason': 'ETL mismatch: 恒月 ≠ 釋普寂 (651-739 đệ tử Thần Tú). Hai người khác nhau.',
    },
    {
        'ppb_id': 7343,
        'raw_name': '智常',
        'wrong_person_id': 'A009365',
        'wrong_name_zh': '李萬卷',
        'reason': 'ETL mismatch: 智常 ≠ 李萬卷 (quan văn, không phải thiền sư). Hai người khác nhau.',
    },
    {
        'ppb_id': 7346,
        'raw_name': '思睿',
        'wrong_person_id': 'A008784',
        'wrong_name_zh': '大智禪師',
        'reason': 'ETL mismatch: 思睿 ≠ 大智禪師. Hai người khác nhau.',
    },
]


def get_db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def load_current(con, ppb_id):
    return con.execute(
        'SELECT * FROM place_person_bibl WHERE id = ?', (ppb_id,)
    ).fetchone()


def dry_run():
    con = get_db()
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[DRY-RUN] BUG-002 Person Identity Fix — {ts}")
    print(f"DB: {DB_PATH}\n")

    for fix in FIXES:
        row = load_current(con, fix['ppb_id'])
        if not row:
            print(f"  ppb.id={fix['ppb_id']} — NOT FOUND (đã fix rồi?)")
            continue
        cur_pid = row['person_id']
        cur_conf = row['confidence']
        print(f"  ppb.id={fix['ppb_id']} | raw={fix['raw_name']}")
        print(f"    person_id:  {cur_pid!r}  →  NULL")
        print(f"    confidence: {cur_conf}  →  0.0")
        print(f"    reason:     {fix['reason'][:90]}...")
        print()

    con.close()
    print("[DRY-RUN] Không có gì thay đổi. Chạy --apply để áp dụng.")


def load_nexus_rows(con, wrong_ids, place_dila_id='PL000000023255'):
    placeholders = ','.join('?' * len(wrong_ids))
    return con.execute(
        f"SELECT * FROM nexus_events WHERE person_dila_id IN ({placeholders}) AND place_dila_id = ?",
        wrong_ids + [place_dila_id]
    ).fetchall()


def save_snapshot(con):
    ppb_rows = []
    for fix in FIXES:
        row = load_current(con, fix['ppb_id'])
        if row:
            ppb_rows.append(dict(row))

    wrong_ids = [f['wrong_person_id'] for f in FIXES]
    nexus_rows = [dict(r) for r in load_nexus_rows(con, wrong_ids)]

    with open(SNAPSHOT, 'w', encoding='utf-8') as f:
        json.dump({
            'created': datetime.now().isoformat(),
            'place_person_bibl': ppb_rows,
            'nexus_events': nexus_rows
        }, f, ensure_ascii=False, indent=2)
    print(f"[SNAPSHOT] Đã lưu {len(ppb_rows)} ppb + {len(nexus_rows)} nexus_events → {SNAPSHOT}")


def apply_fix():
    con = get_db()
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[APPLY] BUG-002 Person Identity Fix — {ts}")
    print(f"DB: {DB_PATH}\n")

    # Save snapshot trước khi sửa
    save_snapshot(con)

    changed = 0
    for fix in FIXES:
        row = load_current(con, fix['ppb_id'])
        if not row:
            print(f"  ppb.id={fix['ppb_id']} — NOT FOUND, bỏ qua")
            continue
        if row['person_id'] is None and row['confidence'] == 0.0:
            print(f"  ppb.id={fix['ppb_id']} — ĐÃ FIX RỒI, bỏ qua")
            continue

        con.execute(
            'UPDATE place_person_bibl SET person_id=NULL, confidence=0.0 WHERE id=?',
            (fix['ppb_id'],)
        )
        print(f"  ✓ ppb.id={fix['ppb_id']} | {fix['wrong_person_id']}→NULL | conf→0.0 | raw={fix['raw_name']}")
        changed += 1

    # Fix nexus_events
    wrong_ids = [f['wrong_person_id'] for f in FIXES]
    nexus_rows = load_nexus_rows(con, wrong_ids)
    nexus_changed = 0
    for nr in nexus_rows:
        con.execute(
            'UPDATE nexus_events SET person_dila_id = NULL WHERE id = ?', (nr['id'],)
        )
        print(f"  ✓ nexus_events.id={nr['id']} | {nr['person_dila_id']}→NULL | conf={nr['confidence']} | {nr['source_book']}")
        nexus_changed += 1

    con.commit()
    con.close()
    print(f"\n[APPLY] Đã sửa {changed} ppb + {nexus_changed} nexus_events. Snapshot: {SNAPSHOT}")

    # Verify
    con2 = get_db()
    print("\n[VERIFY] Trạng thái sau fix:")
    for fix in FIXES:
        row = load_current(con2, fix['ppb_id'])
        if row:
            ok = '✓' if row['person_id'] is None and row['confidence'] == 0.0 else '✗'
            print(f"  {ok} ppb.id={fix['ppb_id']} | person_id={row['person_id']} | conf={row['confidence']} | raw={row['person_name_raw']}")
    remaining = load_nexus_rows(con2, wrong_ids)
    if remaining:
        print(f"  ✗ nexus_events: còn {len(remaining)} rows chưa fix!")
    else:
        print(f"  ✓ nexus_events: 4 wrong rows đã NULL hoàn toàn")
    con2.close()


def revert():
    if not os.path.exists(SNAPSHOT):
        print(f"[REVERT] Không tìm thấy snapshot: {SNAPSHOT}")
        sys.exit(1)

    with open(SNAPSHOT, encoding='utf-8') as f:
        data = json.load(f)

    print(f"[REVERT] Snapshot tạo lúc: {data['created']}")
    print(f"[REVERT] Khôi phục {len(data['rows'])} rows...\n")

    con = get_db()
    restored_ppb = 0
    for orig in data.get('place_person_bibl', data.get('rows', [])):
        con.execute(
            'UPDATE place_person_bibl SET person_id=?, confidence=? WHERE id=?',
            (orig['person_id'], orig['confidence'], orig['id'])
        )
        print(f"  ← ppb.id={orig['id']} | person_id={orig['person_id']} | conf={orig['confidence']}")
        restored_ppb += 1

    restored_nexus = 0
    for orig in data.get('nexus_events', []):
        con.execute(
            'UPDATE nexus_events SET person_dila_id=? WHERE id=?',
            (orig['person_dila_id'], orig['id'])
        )
        print(f"  ← nexus_events.id={orig['id']} | person_dila_id={orig['person_dila_id']}")
        restored_nexus += 1

    con.commit()
    con.close()
    print(f"\n[REVERT] Khôi phục {restored_ppb} ppb + {restored_nexus} nexus_events.")


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else '--dry-run'
    if mode == '--dry-run':
        dry_run()
    elif mode == '--apply':
        apply_fix()
    elif mode == '--revert':
        revert()
    else:
        print(f"Usage: python {sys.argv[0]} [--dry-run | --apply | --revert]")
        sys.exit(1)
