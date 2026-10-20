# -*- coding: utf-8 -*-
"""
T276 bước 7–10 — thống kê và xuất kết quả side-car T170/T169 cho Admin.

Vì sao có file này:
  - Kết quả tự động (review_status = auto_*) không được coi là cuối. Cờ `provisional`
    được TÍNH KHI ĐỌC: auto_* và admin_checked = 0. Không đổi code ghi kết quả.
  - Admin duyệt mẫu xong thì đánh admin_checked = 1 (cột mới, chỉ ở side-car).

Chỉ đọc khi thống kê/xuất. Ghi duy nhất khi chạy `--migrate` (thêm cột admin_checked
vào 2 side-car, có backup). Không đụng bảng people / places_dila / places_pending.

Usage:
    python -X utf8 scripts/t276_audit_stats.py --stats          # in thống kê (RO)
    python -X utf8 scripts/t276_audit_stats.py --export         # xuất CSV cho Admin (RO)
    python -X utf8 scripts/t276_audit_stats.py --migrate-dry    # xem SQL sẽ chạy (RO)
    python -X utf8 scripts/t276_audit_stats.py --migrate        # backup + ALTER side-car (GHI)
    python -X utf8 scripts/t276_audit_stats.py --revert         # DROP COLUMN admin_checked (GHI)

Env override cho test: T276_DB=<đường dẫn db>
"""
import csv
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # daoanh/
DB_PATH = os.environ.get('T276_DB') or str(ROOT / 'data' / 'lineage.db')
BACK_DIR = ROOT / 'data' / 'backups'
EVID_DIR = ROOT / 'docs' / 'evidence'
TABLES = ('place_groq_audit', 'person_groq_audit')
AUTO_PREFIX = 'auto_%'


def _ro():
    return sqlite3.connect(f'file:{DB_PATH}?mode=ro', uri=True)


def _table_exists(con, name):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def _cols(con, name):
    return [r[1] for r in con.execute(f'PRAGMA table_info({name})')]


def stats_for(con, table):
    """Thống kê một side-car. Trả None nếu bảng chưa có."""
    if not _table_exists(con, table):
        return None
    cols = _cols(con, table)
    has_admin = 'admin_checked' in cols
    admin_expr = 'COALESCE(admin_checked,0)' if has_admin else '0'
    by_status = dict(con.execute(
        f'SELECT review_status, COUNT(*) FROM {table} GROUP BY review_status').fetchall())
    total = sum(by_status.values())
    provisional = con.execute(
        f"SELECT COUNT(*) FROM {table} WHERE review_status LIKE ? AND {admin_expr} = 0",
        (AUTO_PREFIX,)).fetchone()[0]
    needs_review = con.execute(
        f'SELECT COUNT(*) FROM {table} WHERE needs_review = 1').fetchone()[0]
    api_error = by_status.get('api_error', 0)
    last = con.execute(
        f'SELECT batch_id, checked_at FROM {table} WHERE checked_at IS NOT NULL '
        f'ORDER BY checked_at DESC LIMIT 1').fetchone()
    return {
        'table': table,
        'total': total,
        'by_status': by_status,
        'provisional': provisional,
        'needs_review': needs_review,
        'api_error': api_error,
        'admin_checked_col': has_admin,
        'last_batch_id': last[0] if last else None,
        'last_checked_at': last[1] if last else None,
    }


def collect():
    """Gom thống kê cho dashboard. Không ghi gì."""
    if not os.path.exists(DB_PATH):
        return {'ok': False, 'error': f'Không thấy DB: {DB_PATH}', 'tables': {}}
    con = _ro()
    try:
        out = {}
        for t in TABLES:
            s = stats_for(con, t)
            out[t] = s if s is not None else {'table': t, 'missing': True}
        return {'ok': True, 'generated_at': datetime.now().isoformat(timespec='seconds'), 'tables': out}
    finally:
        con.close()


def export_csv(table, out_path):
    """Xuất side-car ra CSV (RO). Cột provisional được tính thêm."""
    con = _ro()
    try:
        if not _table_exists(con, table):
            print(f'Không có bảng {table}.')
            return 0
        cols = _cols(con, table)
        has_admin = 'admin_checked' in cols
        sel = ', '.join(cols)
        prov = ("CASE WHEN review_status LIKE 'auto_%' AND COALESCE(admin_checked,0)=0 THEN 1 ELSE 0 END"
                if has_admin else
                "CASE WHEN review_status LIKE 'auto_%' THEN 1 ELSE 0 END")
        cur = con.execute(f'SELECT {sel}, {prov} AS provisional FROM {table} ORDER BY id')
        header = [d[0] for d in cur.description]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        n = 0
        with out_path.open('w', encoding='utf-8', newline='') as f:
            w = csv.writer(f)
            w.writerow(header)
            for row in cur:
                w.writerow(row)
                n += 1
        return n
    finally:
        con.close()


MIGRATE_SQL = {
    t: f'ALTER TABLE {t} ADD COLUMN admin_checked INTEGER DEFAULT 0' for t in TABLES
}


def migrate_plan():
    con = _ro()
    try:
        plan = []
        for t in TABLES:
            if not _table_exists(con, t):
                plan.append((t, 'BỎ QUA: bảng chưa tồn tại'))
            elif 'admin_checked' in _cols(con, t):
                plan.append((t, 'BỎ QUA: đã có cột admin_checked'))
            else:
                plan.append((t, MIGRATE_SQL[t]))
        return plan
    finally:
        con.close()


def migrate_apply():
    plan = migrate_plan()
    if all(p[1].startswith('BỎ QUA') for p in plan):
        print('Không có gì để thêm:', plan)
        return 0
    BACK_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    bak = BACK_DIR / f'lineage.T276-audit-{ts}.db'
    src = sqlite3.connect(DB_PATH)
    dst = sqlite3.connect(bak)
    with dst:
        src.backup(dst)
    dst.close()
    chk = sqlite3.connect(bak).execute('PRAGMA quick_check').fetchone()[0]
    src.close()
    if chk != 'ok':
        print('❌ Backup không đạt quick_check:', chk, '— dừng, không ALTER.')
        return 1
    print(f'Backup OK ({chk}): {bak}')
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.execute('PRAGMA busy_timeout=10000')
    try:
        for t, sql in plan:
            if sql.startswith('BỎ QUA'):
                print(f'  {t}: {sql}')
                continue
            con.execute(sql)
            print(f'  {t}: đã thêm admin_checked')
        con.commit()
    except Exception as ex:
        con.rollback()
        print('❌ Lỗi, đã rollback:', ex)
        return 1
    finally:
        con.close()
    return 0


def migrate_revert():
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.execute('PRAGMA busy_timeout=10000')
    try:
        for t in TABLES:
            if _table_exists(con, t) and 'admin_checked' in _cols(con, t):
                con.execute(f'ALTER TABLE {t} DROP COLUMN admin_checked')
                print(f'  {t}: đã DROP COLUMN admin_checked')
        con.commit()
    finally:
        con.close()
    return 0


def _print_stats(res):
    if not res['ok']:
        print(res['error'])
        return
    for t, s in res['tables'].items():
        if s.get('missing'):
            print(f'{t}: chưa có bảng')
            continue
        print(f"{t}: tổng {s['total']} · provisional {s['provisional']} · "
              f"chờ duyệt {s['needs_review']} · api_error {s['api_error']} · "
              f"admin_checked col={s['admin_checked_col']}")
        print('   theo trạng thái:', s['by_status'])


def main(argv):
    if '--stats' in argv:
        _print_stats(collect())
        return 0
    if '--export' in argv:
        for t in TABLES:
            n = export_csv(t, EVID_DIR / f'2026-10-10_T276_{t}.csv')
            print(f'{t}: {n} dòng -> {EVID_DIR / f"2026-10-10_T276_{t}.csv"}')
        return 0
    if '--migrate-dry' in argv:
        for t, sql in migrate_plan():
            print(f'{t}: {sql}')
        return 0
    if '--migrate' in argv:
        return migrate_apply()
    if '--revert' in argv:
        return migrate_revert()
    print(__doc__)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
