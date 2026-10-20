#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_bug025_026.py — Verify DB fixes BUG-025 + BUG-026 (READ-ONLY).

BUG-025: SEARCH_QUY_SON_LINH_HUU_WRONG_PERSON_001
  - A021462 name_vi phải = 'Kính Đường Giác Viên' (không còn 'Quy Sơn Linh Hựu')
  - A001984 name_vi phải = 'Quy Sơn Linh Hựu' (không còn 'Đại Viên Thiền Sư')

BUG-026: SEARCH_THACH_DAU_HY_THIEN_WRONG_PERSON_001
  - A010291 name_vi phải = 'Thạch Đầu Hy Thiên' (đúng)
  - A001744 name_vi phải = 'Tuệ Biện' (không còn 'Thạch Đầu Hy Thiên')

Chạy: python -X utf8 scripts/verify_bug025_026.py
Không ghi DB — chỉ SELECT. Exit 0 = PASS, 1 = FAIL.
"""
import os
import sqlite3
import sys

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(PROJECT, 'data', 'lineage.db')

EXPECT = {
    # id: (name_vi mong đợi, tên bug, ghi chú cũ)
    'A021462': ('Kính Đường Giác Viên', 'BUG-025', 'cũ SAI = Quy Sơn Linh Hựu'),
    'A001984': ('Quy Sơn Linh Hựu', 'BUG-025', 'cũ SAI = Đại Viên Thiền Sư'),
    'A010291': ('Thạch Đầu Hy Thiên', 'BUG-026', 'đúng, giữ nguyên'),
    'A001744': ('Tuệ Biện', 'BUG-026', 'cũ SAI = Thạch Đầu Hy Thiên'),
}


def main():
    if not os.path.exists(DB):
        print(f'❌ KHÔNG TÌM THẤY DB: {DB}')
        return 1
    conn = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    ids = ','.join(f"'{i}'" for i in EXPECT)
    rows = cur.execute(
        f"SELECT id, name_vi, name_zh, bio FROM people WHERE id IN ({ids})"
    ).fetchall()
    found = {r['id']: r for r in rows}
    all_ok = True
    print(f'DB: {DB}')
    print(f'Kiểm tra {len(EXPECT)} people …\n')
    for pid, (want, bug, note) in EXPECT.items():
        r = found.get(pid)
        if r is None:
            print(f'❌ {bug} {pid}: KHÔNG tồn tại trong DB')
            all_ok = False
            continue
        ok = r['name_vi'] == want
        mark = '✅' if ok else '❌'
        if not ok:
            all_ok = False
        print(f'{mark} {bug} {pid} name_vi={r["name_vi"]!r} '
              f'(mong đợi {want!r}) · name_zh={r["name_zh"]!r} · {note}')
    # Kiểm tra trùng name_vi theo từng bug (BUG-026: chỉ còn 1 'Thạch Đầu Hy Thiên')
    dup = cur.execute(
        "SELECT COUNT(*) FROM people WHERE name_vi='Thạch Đầu Hy Thiên'"
    ).fetchone()[0]
    dup_ok = dup == 1
    if not dup_ok:
        all_ok = False
        print(f'{"❌" if not dup_ok else "✅"} People còn {dup} row name_vi="Thạch Đầu Hy Thiên" (mong đợi đúng 1 = A010291)')
    else:
        print('✅ Chỉ 1 row "Thạch Đầu Hy Thiên" (A010291) — hết trùng BUG-026')
    q = cur.execute(
        "SELECT COUNT(*) FROM people WHERE name_vi='Quy Sơn Linh Hựu'"
    ).fetchone()[0]
    if q != 1:
        all_ok = False
        print(f'❌ People còn {q} row name_vi="Quy Sơn Linh Hựu" (mong đợi đúng 1 = A001984)')
    else:
        print('✅ Chỉ 1 row "Quy Sơn Linh Hựu" (A001984) — hết trùng BUG-025')
    conn.close()
    print()
    if all_ok:
        print('🎉 VERIFY PASS — BUG-025 + BUG-026 DONE (đã fix ứng với dữ liệu khớp)')
        return 0
    print('❌ VERIFY FAIL — còn row sai. KHÔNG app/commit DONE.')
    return 1


if __name__ == '__main__':
    sys.exit(main())