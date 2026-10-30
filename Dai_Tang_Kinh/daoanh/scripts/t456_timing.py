# -*- coding: utf-8 -*-
"""T456 — đo hiệu năng các nguồn gợi ý + kiểm tra route autocomplete (places) có sẵn."""
import os, sqlite3, sys, time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh"
DB = os.path.join(BASE, "data", "lineage.db")
conn = sqlite3.connect("file:" + DB + "?mode=ro", uri=True)
conn.row_factory = sqlite3.Row


def t(fn, n=3):
    best = 1e9
    for _ in range(n):
        t0 = time.perf_counter()
        r = fn()
        best = min(best, (time.perf_counter() - t0) * 1000)
    return best, r


print("=== kích thước bảng ===")
for tb in ["dila_catalog_works", "dila_catalog_contributors", "dila_catalog_places",
           "cbeta_catalog_vn", "people", "places_pending", "namevi_map_places"]:
    try:
        n = conn.execute("SELECT COUNT(*) FROM %s" % tb).fetchone()[0]
        print("   %-28s %8d" % (tb, n))
    except Exception as e:
        print("   %-28s LỖI %s" % (tb, e))

print()
print("=== đo latency (ms), 3 lần lấy min ===")
QUERIES = ["Huyền", "Thi", "Long", "Bát", "Tâm Kinh", "Khuy Cơ", "Thiếu L", "Nghĩa Huyền"]
for q in QUERIES:
    like = q + "%"
    sub = "%" + q + "%"

    def f_works():
        return conn.execute(
            "SELECT cbeta_id, title_vi, title_zh FROM dila_catalog_works "
            "WHERE title_vi LIKE ? OR title_zh LIKE ? LIMIT 8", (like, like)).fetchall()

    def f_works_sub():
        return conn.execute(
            "SELECT cbeta_id, title_vi, title_zh FROM dila_catalog_works "
            "WHERE title_vi LIKE ? OR title_zh LIKE ? OR byline_zh LIKE ? OR byline_vi LIKE ? LIMIT 8",
            (like, like, like, like)).fetchall()

    def f_people():
        return conn.execute(
            "SELECT id, name_vi, name_zh FROM people WHERE name_vi LIKE ? OR name_zh LIKE ? LIMIT 8",
            (like, like)).fetchall()

    def f_people_sub():
        return conn.execute(
            "SELECT id, name_vi, name_zh FROM people WHERE name_vi LIKE ? OR name_zh LIKE ? LIMIT 8",
            (sub, sub)).fetchall()

    def f_works_cbeta():
        return conn.execute(
            "SELECT id, title_vi FROM cbeta_catalog_vn WHERE title_vi LIKE ? OR title_zh LIKE ? LIMIT 8",
            (like, like)).fetchall()

    row = []
    for label, fn in [("works(prefix)", f_works), ("works+byline", f_works_sub),
                      ("cbeta(prefix)", f_works_cbeta), ("people(prefix)", f_people),
                      ("people(substr)", f_people_sub)]:
        ms, res = t(fn)
        row.append("%s=%.1f(%d)" % (label, ms, len(res)))
    print("   q=%-12s %s" % (q, "  ".join(row)))

print()
print("=== EXPLAIN QUERY PLAN: works prefix ===")
for r in conn.execute(
        "EXPLAIN QUERY PLAN SELECT cbeta_id FROM dila_catalog_works "
        "WHERE title_vi LIKE ? OR title_zh LIKE ? LIMIT 8", ("A%", "A%")):
    print("   ", r[3])

print()
print("=== FTS có sẵn cho places? ===")
fts = [r[0] for r in conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%fts%'")]
print("   ", fts)
if "places_pending_fts" in fts:
    for q in ["Thiếu L", "Nghĩa Huyền", "Khuy Cơ"]:
        terms = [x + "*" for x in q.split()]
        try:
            ms, res = t(lambda: conn.execute(
                "SELECT id FROM places_pending_fts WHERE places_pending_fts MATCH ? LIMIT 8",
                (" ".join(terms),)).fetchall())
            print("   FTS q=%-14s %.1f ms (%d hit)" % (q, ms, len(res)))
        except Exception as e:
            print("   FTS q=%-14s LỖI %s" % (q, e))
conn.close()
