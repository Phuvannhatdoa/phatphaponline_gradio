# -*- coding: utf-8 -*-
"""probe_t207_fts.py — kiem chung FTS5 index sau khi T207 cap nhat 443 row.

CÁCH KIỂM ĐỊNH DANH: FTS5 có lệnh
    INSERT INTO <fts>(<fts>, rank) VALUES('integrity-check', 1);
rank=1 ⇒ soát index có khớp BẢNG NỘI DUNG (external-content) hay không; lệch thì
SQLite ném lỗi. Đây là bằng chứng mạnh nhất, mạnh hơn đếm row hay thử MATCH.

Lệnh này GHI nên cần chạy trên bản sao DB tạm, không đụng DB thật.
"""
import json
import os
import shutil
import sqlite3
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import t207_fix_db_mojibake as T   # noqa: E402

DB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(HERE), 'data', 'lineage.db')


def main():
    print('=' * 78)
    print('T207 FTS5 INTEGRITY CHECK — %s' % os.path.basename(DB))
    print('=' * 78)

    # FTS5 integrity-check la lenh GHI => chay tren ban sao tam
    tmp = os.path.join(tempfile.gettempdir(), '_t207_fts_check.db')
    for suf in ('', '-wal', '-shm'):
        if os.path.exists(tmp + suf):
            os.remove(tmp + suf)
    shutil.copy2(DB, tmp)
    con = sqlite3.connect(tmp)
    con.row_factory = sqlite3.Row

    print('\n1) FTS5 external-content integrity-check (rank=1)')
    try:
        con.execute("INSERT INTO lexicon_fts(lexicon_fts, rank) "
                    "VALUES('integrity-check', 1)")
        con.commit()
        print('   [OK] index lexicon_fts KHỚP hoàn toàn bảng nội dung lexicon')
        fts_ok = True
    except sqlite3.DatabaseError as e:
        print('   [FAIL] index LỆCH: %s' % e)
        fts_ok = False

    print('\n2) FTS5 integrity-check nội bộ (rank=0) — cấu trúc index')
    try:
        con.execute("INSERT INTO lexicon_fts(lexicon_fts, rank) "
                    "VALUES('integrity-check', 0)")
        con.commit()
        print('   [OK] cau truc index khong loi')
    except sqlite3.DatabaseError as e:
        print('   [WARN] %s' % e)

    print('\n3) kiem tra khong con ky tu Ð trong index')
    n = con.execute('SELECT count(*) FROM lexicon_fts WHERE term LIKE ? '
                    'OR definition LIKE ?', ('%' + T.ETH + '%',) * 2).fetchone()[0]
    print('   lexicon_fts con Ð: %d' % n)

    print('\n4) doi chieu rowid co trong index voi bang goc')
    a = con.execute('SELECT count(DISTINCT rowid) FROM lexicon_fts').fetchone()[0]
    b = con.execute('SELECT count(*) FROM lexicon').fetchone()[0]
    print('   distinct rowid trong index = %d ; lexicon rows = %d ; %s'
          % (a, b, 'KHOP' if a == b else 'LECH'))

    print('\n5) rowid ghi trung trong index (mong doi 0)')
    dup = con.execute('SELECT count(*) FROM (SELECT rowid FROM lexicon_fts '
                      'GROUP BY rowid HAVING count(*) > 1)').fetchone()[0]
    print('   rowid trung: %d' % dup)

    print('\n6) tra cuu FTS bang MATCH — vi du khoa da sua')
    for kw in ('Đại', 'Đễ', 'Đề'):
        try:
            rows = con.execute(
                'SELECT rowid FROM lexicon_fts WHERE lexicon_fts MATCH ? '
                'LIMIT 5', (kw,)).fetchall()
            print('   MATCH %-8r -> %d dòng (mẫu: %s)'
                  % (kw, len(rows), [r['rowid'] for r in rows[:3]]))
        except sqlite3.OperationalError as e:
            print('   MATCH %-8r -> loi cú pháp FTS: %s' % (kw, e))

    con.close()
    for suf in ('', '-wal', '-shm'):
        if os.path.exists(tmp + suf):
            try:
                os.remove(tmp + suf)
            except OSError:
                pass

    print()
    print('   => %s' % ('PASS' if (fts_ok and n == 0 and dup == 0) else 'FAIL'))
    return 0 if (fts_ok and n == 0 and dup == 0) else 1


if __name__ == '__main__':
    sys.exit(main())