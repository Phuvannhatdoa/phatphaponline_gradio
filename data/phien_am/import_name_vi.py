#!/usr/bin/env python3
"""Nạp name_vi từ vn_person_name_vi.xml vào vn_person_authority (SQLite).

Mặc định CHẠY THỬ (không ghi). Chỉ cập nhật dòng ĐÃ có dila_id; mặc định nạp cả 4 tầng (tầng 3-4 là bản tạm chờ admin duyệt).
  --apply           ghi thật (tự sao lưu file DB thành <db>.bak trước)
  --tiers 1,2,3     chọn tầng (tầng 3 = còn chữ đa âm/lệch từ điển, cần người duyệt)
  --overwrite       ghi đè cả name_vi đã có (mặc định chỉ điền ô trống)
"""
import argparse, shutil, sqlite3, sys
import xml.etree.ElementTree as ET

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--db", required=True)
ap.add_argument("--xml", default="vn_person_name_vi.xml")
ap.add_argument("--tiers", default="1,2,3,4")
ap.add_argument("--tier-column", help="nếu có: ghi thêm tầng (1-4) vào cột này để admin lọc dòng cần duyệt")
ap.add_argument("--overwrite", action="store_true")
ap.add_argument("--apply", action="store_true")
a = ap.parse_args()
tiers = set(a.tiers.split(","))

items = []
for _, el in ET.iterparse(a.xml, events=("end",)):
    if el.tag == "person":
        vi = (el.findtext("name_vi") or "").strip()
        if el.get("tier") in tiers and vi:
            items.append((el.get("dila_id"), vi, el.get("tier")))
        el.clear()

con = sqlite3.connect(a.db)
have = dict(con.execute("SELECT dila_id, COALESCE(name_vi,'') FROM vn_person_authority"))
todo = [(vi, i, t) for i, vi, t in items if i in have and (a.overwrite or not have[i].strip())]
print(f"XML hợp lệ: {len(items)} | có dila_id trong DB: {sum(i in have for i,_,_ in items)} | sẽ cập nhật: {len(todo)}")
print(f"không có dila_id trong DB (bỏ qua): {sum(i not in have for i,_,_ in items)}")
if not a.apply:
    print("CHẠY THỬ — không ghi gì. Thêm --apply để ghi thật."); sys.exit(0)
con.close(); shutil.copyfile(a.db, a.db + ".bak")
con = sqlite3.connect(a.db)
with con:
    con.executemany("UPDATE vn_person_authority SET name_vi=? WHERE dila_id=?", [(v, i) for v, i, _ in todo])
    if a.tier_column:
        con.executemany(f"UPDATE vn_person_authority SET {a.tier_column}=? WHERE dila_id=?", [(t, i) for _, i, t in todo])
print(f"đã cập nhật {len(todo)} dòng (bản sao lưu: {a.db}.bak)")
