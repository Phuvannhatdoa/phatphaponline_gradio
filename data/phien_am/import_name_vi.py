#!/usr/bin/env python3
"""Nạp name_vi từ XML (người / địa danh / đơn vị hành chính) vào bảng SQLite chỉ định.

Mặc định CHẠY THỬ (không ghi). Chỉ cập nhật dòng ĐÃ có dila_id; mặc định nạp cả 4 tầng (tầng 3-4 là bản tạm chờ admin duyệt).
  --apply           ghi thật (tự sao lưu file DB thành <db>.bak trước)
  --tiers 1,2,3     chọn tầng (tầng 3 = còn chữ đa âm/lệch từ điển, cần người duyệt)
  --overwrite       ghi đè cả name_vi đã có (mặc định chỉ điền ô trống)
  --element person|place|unit   loại phần tử trong XML (mặc định person)
  --table / --id-col            bảng và cột khóa (mặc định vn_person_authority / dila_id)
  --district-column <cột>       (place) ghi thêm district_vi vào cột này
"""
import argparse, shutil, sqlite3, sys
import xml.etree.ElementTree as ET

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--db", required=True)
ap.add_argument("--element", default="person", choices=["person","place","unit"])
ap.add_argument("--table", default="vn_person_authority")
ap.add_argument("--id-col", default="dila_id")
ap.add_argument("--district-column")
ap.add_argument("--xml", default="vn_person_name_vi.xml")
ap.add_argument("--tiers", default="1,2,3,4")
ap.add_argument("--tier-column", help="nếu có: ghi thêm tầng (1-4) vào cột này để admin lọc dòng cần duyệt")
ap.add_argument("--overwrite", action="store_true")
ap.add_argument("--apply", action="store_true")
a = ap.parse_args()
tiers = set(a.tiers.split(","))

items = []
for _, el in ET.iterparse(a.xml, events=("end",)):
    if el.tag == a.element:
        vi = (el.findtext("name_vi") or "").strip()
        if el.get("tier") in tiers and vi:
            items.append((el.get("dila_id"), vi, el.get("tier"), (el.findtext("district_vi") or "").strip()))
        el.clear()

con = sqlite3.connect(a.db)
have = dict(con.execute(f"SELECT {a.id_col}, COALESCE(name_vi,'') FROM {a.table}"))
todo = [(vi, i, t, _d) for i, vi, t, _d in items if i in have and (a.overwrite or not have[i].strip())]
print(f"XML hợp lệ: {len(items)} | có dila_id trong DB: {sum(i in have for i,_,_,_ in items)} | sẽ cập nhật: {len(todo)}")
print(f"không có dila_id trong DB (bỏ qua): {sum(i not in have for i,_,_,_ in items)}")
if not a.apply:
    print("CHẠY THỬ — không ghi gì. Thêm --apply để ghi thật."); sys.exit(0)
con.close(); shutil.copyfile(a.db, a.db + ".bak")
con = sqlite3.connect(a.db)
with con:
    con.executemany(f"UPDATE {a.table} SET name_vi=? WHERE {a.id_col}=?", [(v, i) for v, i, _, _ in todo])
    if a.tier_column:
        con.executemany(f"UPDATE {a.table} SET {a.tier_column}=? WHERE {a.id_col}=?", [(t, i) for _, i, t, _ in todo])
    if a.district_column:
        con.executemany(f"UPDATE {a.table} SET {a.district_column}=? WHERE {a.id_col}=?", [(d, i) for _, i, _, d in todo if d])
print(f"đã cập nhật {len(todo)} dòng (bản sao lưu: {a.db}.bak)")
