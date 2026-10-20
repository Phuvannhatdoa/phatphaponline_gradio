# -*- coding: utf-8 -*-
"""test_t200_vnpa_tiebreak.py — [T200] tie-break `vn_person_authority` theo `dila_id`.

Bối cảnh: `vn_person_authority.dila_id` KHÔNG unique (33 nhóm 2–3 dòng). Call site cũ
dùng `... WHERE dila_id=? LIMIT 1` **không `ORDER BY`** ⇒ dòng trả về phụ thuộc thứ tự quét
của SQLite ⇒ **không xác định**. Admin chốt (2026-10-01): ưu tiên **theo status**.

Chạy: python -X utf8 tests/test_t200_vnpa_tiebreak.py
"""
import os
import sqlite3
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DAOANH = os.path.dirname(HERE)
if DAOANH not in sys.path:
    sys.path.insert(0, DAOANH)

import vnpa_lookup as vl  # noqa: E402

DB_PATH = os.path.join(DAOANH, 'data', 'lineage.db')

_pass = 0
_fail = []


def check(name, cond, extra=""):
    global _pass
    if cond:
        _pass += 1
        print("   OK   %s" % name)
    else:
        _fail.append(name)
        print("   FAIL %s %s" % (name, extra))


def _mk(conn):
    conn.executescript("""
        CREATE TABLE vn_person_authority (
            id TEXT, ttl_filename TEXT, name_vi TEXT, name_zh TEXT,
            dharma_title TEXT, dharma_lineage TEXT, generation_order INTEGER,
            is_lineage_founder INTEGER, gender TEXT, biographical_note_vi TEXT,
            birth_year INTEGER, death_year INTEGER, appellations TEXT,
            dila_id TEXT, status TEXT, created_at TEXT);
    """)


def _row(i, vi, zh, did, st):
    return ("INSERT INTO vn_person_authority (id,name_vi,name_zh,dila_id,status)"
            " VALUES (?,?,?,?,?)", (i, vi, zh, did, st))


# --------------------------------------------------------------------------
print("=== 1) Thu tu uu tien status dung chu ky te ===")
RANK = [("verified", 0), ("pending", 1), ("auto_ttl", 2),
        ("alias_vi_suffix", 3), ("alias_zh_match", 4)]
for st, want in RANK:
    got = vl.VNPA_ORDER_BY.find("WHEN '%s' THEN %d" % (st, want))
    check("rank %s = %d" % (st, want), got > 0, "(khong tim thay trong SQL)")
check("ORDER BY co tie-break id ASC", vl.VNPA_ORDER_BY.rstrip().endswith("id ASC"))

# --------------------------------------------------------------------------
print()
print("=== 2) lookup chon dung dong theo thu tu status ===")
ORDER = ["verified", "pending", "auto_ttl", "alias_vi_suffix", "alias_zh_match"]
for want_st, want_rank in RANK:
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    _mk(con)
    # Chi insert target + cac status KE hon (rank >= want_rank) => target phai thang
    for st, rk in RANK:
        if rk < want_rank:
            continue
        sql, args = _row("d_%02d_%s" % (rk, st), "T\u00ean " + st,
                         "\u6f22", "A1", st)
        con.execute(sql, args)
    got = vl.lookup_by_dila(con, "A1")
    check("A1 -> dong status=%s" % want_st,
          got is not None and got["id"] == "d_%02d_%s" % (want_rank, want_st),
          "(got %s)" % (got["id"] if got else None))
    con.close()

# --------------------------------------------------------------------------
print()
print("=== 3) TIE-BREAK: cung status -> phai chon theo id ASC (deterministic) ===")
con = sqlite3.connect(":memory:")
con.row_factory = sqlite3.Row
_mk(con)
for s in ("zz", "aa", "mm", "bb"):
    sql, args = _row("id_" + s, "T\u00ean " + s.upper(), "\u540c", "A2", "pending")
    con.execute(sql, args)
got = vl.lookup_by_dila(con, "A2")
check("4 dong cung status -> id nho nhat (id_aa)",
      got is not None and got["id"] == "id_aa",
      "(got %s)" % (got["id"] if got else None))
con.close()

# --------------------------------------------------------------------------
print()
print("=== 4) DETERMINISM: chay 50 lan phai ra cung ket qua ===")
con = sqlite3.connect(":memory:")
con.row_factory = sqlite3.Row
_mk(con)
rows = []
for g in range(5):
    for s in ("auto_ttl", "pending", "alias_vi_suffix", "alias_zh_match"):
        rows.append(("g%d_%s" % (g, s), "T\u00ean g%d" % g, "\u6f22",
                     "A%d" % g, s))
con.executemany(
    "INSERT INTO vn_person_authority (id,name_vi,name_zh,dila_id,status)"
    " VALUES (?,?,?,?,?)", rows)
sigs = set()
for _ in range(50):
    for g in range(5):
        r = vl.lookup_by_dila(con, "A%d" % g)
        sigs.add((g, r["id"] if r else None))
check("50 lan x 5 nhom -> chi 1 ket qua duy nhat", len(sigs) == 5,
      "(got %d)" % len(sigs))
con.close()

# --------------------------------------------------------------------------
print()
print("=== 5) map_dila_to_name: 1 nhom nhieu dong -> chi giu 1 dong ===")
con = sqlite3.connect(":memory:")
con.row_factory = sqlite3.Row
_mk(con)
con.executemany(
    "INSERT INTO vn_person_authority (id,name_vi,name_zh,dila_id,status)"
    " VALUES (?,?,?,?,?)",
    [("x1", "Alias Full", "\u6f22", "A3", "alias_vi_suffix"),
     ("x2", "Pending Name", "\u6f22", "A3", "pending"),
     ("x3", "Auto Name", "\u6f22", "A3", "auto_ttl"),
     ("y1", "Lon", "\u6f22", "A4", "pending"),
     ("y2", "", "\u6f22", "A4", "pending"),
     ("z1", "NoDila", "\u6f22", "", "pending")])
m = vl.map_dila_to_name(con)
check("A3 -> 'Pending Name' (pending > auto_ttl > alias)",
      m.get("A3") == "Pending Name", "(got %r)" % m.get("A3"))
check("A4 -> 'Lon' (bo dong rong)", m.get("A4") == "Lon", "(got %r)" % m.get("A4"))
check("dila_id rong bi lo", "" not in m and None not in m)
m2 = vl.map_dila_to_name(con)
check("map deterministic", m == m2)
con.close()

# --------------------------------------------------------------------------
print()
print("=== 6) Bien edge: input rong / khong ton tai / bang thieu cot ===")
con = sqlite3.connect(":memory:")
con.row_factory = sqlite3.Row
check("dila_id=None -> None", vl.lookup_by_dila(con, None) is None)
check("dila_id='' -> None", vl.lookup_by_dila(con, "") is None)
check("bang khong ton tai -> None (khong nem)",
      vl.lookup_by_dila(con, "A1") is None)
check("map tren bang khong ton tai -> {} rong", vl.map_dila_to_name(con) == {})
check("has_duplicate_dila tren bang khong ton tai -> (False, 0)",
      vl.has_duplicate_dila(con) == (False, 0))
con.close()

print()
print("=== 7) DB that (read-only): A001984 + dem nhom trung ===")
if os.path.exists(DB_PATH):
    con = sqlite3.connect("file:" + DB_PATH.replace("\\", "/") + "?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    r = vl.lookup_by_dila(con, "A001984")
    check("A001984 tra dung (chi 1 dong)",
          r is not None and r["name_vi"] == "Quy S\u01a1n Linh H\u1ef1u",
          "(got %r)" % (r["name_vi"] if r else None))
    dup, n = vl.has_duplicate_dila(con)
    print("   info: con %d nhom dila_id trung (tie-break da xac dinh)" % n)
    m1 = vl.map_dila_to_name(con)
    m2 = vl.map_dila_to_name(con)
    check("map_dila_to_name tren DB that deterministic", m1 == m2)
    check("map khong rong", len(m1) > 1000, "(got %d)" % len(m1))
    con.close()
else:
    print("   skip (khong co DB)")

# --------------------------------------------------------------------------
print()
print("=" * 60)
if _fail:
    print("T200 tie-break test: %d PASS, %d FAIL" % (_pass, len(_fail)))
    for f in _fail:
        print("   FAIL:", f)
    sys.exit(1)
print("T200 tie-break test: %d/%d PASS" % (_pass, _pass))
print("=" * 60)