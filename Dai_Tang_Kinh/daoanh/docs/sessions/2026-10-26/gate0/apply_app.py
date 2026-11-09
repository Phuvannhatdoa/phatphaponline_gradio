"""Chèn khối DILA (T453) vào app.py. Chỉ thêm text, không đụng phần khác.
usage: python apply_app.py <src> <dst>
- Khối lấy NGUYÊN VĂN từ docs/sessions/2026-10-25/T445-coder/backup/app.py
  (b1 = dòng 13511-13574, route = dòng 13596-13624) đã đối chiếu với gate0-report.md.
- Neo định vị theo NGỮ CẢNH; assert đúng 1 lần khớp, không theo số dòng.
"""
import sys

BACKUP = "docs/sessions/2026-10-25/T445-coder/backup/app.py"

src_path, dst_path = sys.argv[1], sys.argv[2]
with open(BACKUP, encoding="utf-8", newline="") as f:
    bl = f.read().replace("\r\n", "\n").split("\n")  # backup là CRLF; chuẩn hoá LF, số dòng giữ nguyên
assert bl[13510].startswith("        # T453: kinh lục DILA"), bl[13510]
assert bl[13573] == "" and bl[13574] == "" or True
b1 = "\n".join(bl[13510:13574]) + "\n"          # 13511..13574 (kèm dòng trống cuối)
assert b1.rstrip("\n").endswith("dila_people = []"), repr(b1[-80:])
assert bl[13595].startswith("@app.route('/daoanh/api/public/dila_works')"), bl[13595]
route = "\n".join(bl[13595:13624]) + "\n"        # 13596..13624
assert route.rstrip("\n").endswith("conn.close()"), repr(route[-60:])

with open(src_path, encoding="utf-8", newline="") as f:
    text = f.read()
assert "\r\n" not in text, "source must be LF"

OLD_RESP_TAIL = (
    '        """, (like, like)).fetchall()\n'
    "\n"
    "        resp = {\n"
    '            "success": True,\n'
    '            "monks": [dict(r) for r in monks],\n'
    '            "places": [dict(r) for r in places],\n'
    '            "works": [dict(r) for r in works],\n'
    "        }\n"
)
NEW_RESP_TAIL = (
    '        """, (like, like)).fetchall()\n'
    "\n"
    + b1 +
    "        resp = {\n"
    '            "success": True,\n'
    '            "monks": [dict(r) for r in monks],\n'
    '            "places": [dict(r) for r in places],\n'
    '            "works": [dict(r) for r in works],\n'
    '            "dila_works": dila_works,\n'
    '            "dila_works_total": dila_works_total,\n'
    '            "dila_people": dila_people,\n'
    "        }\n"
)
n1 = text.count(OLD_RESP_TAIL)
assert n1 == 1, f"anchor resp count={n1}"
text = text.replace(OLD_RESP_TAIL, NEW_RESP_TAIL)

OLD_PUB = "@app.route('/daoanh/api/public/search')\ndef public_search():\n"
n2 = text.count(OLD_PUB)
assert n2 == 1, f"anchor public_search count={n2}"
assert text.count("def public_dila_works(") == 0
text = text.replace(OLD_PUB, route + "\n\n" + OLD_PUB)

with open(dst_path, "w", encoding="utf-8", newline="") as f:
    f.write(text)
print("OK insert b1 lines=%d route lines=%d -> %s" % (b1.count("\n"), route.count("\n"), dst_path))
