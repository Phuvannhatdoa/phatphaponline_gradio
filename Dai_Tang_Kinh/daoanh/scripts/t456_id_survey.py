# -*- coding: utf-8 -*-
"""T455/T456 — khảo sát ID task hiện có (để cấp ID mới đúng quy trình AGENTS §16)."""
import os, re, subprocess, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DAO = os.path.join(BASE, "Dai_Tang_Kinh", "daoanh")
os.chdir(BASE)

ids = {}
for root, dirs, files in os.walk(os.path.join(DAO, "tasks")):
    dirs[:] = [d for d in dirs if d not in ("archive_done", "backup")]
    for f in files:
        if not f.endswith(".md"):
            continue
        p = os.path.join(root, f)
        t = open(p, encoding="utf-8", errors="replace").read()
        m = re.search(r"^id:\s*(T\d+)", t, re.M)
        tid = m.group(1) if m else f[:4]
        st = re.search(r"^status:\s*(\S+)", t, re.M)
        ids.setdefault(tid, []).append((os.path.relpath(p, BASE), st.group(1) if st else "?"))

nums = sorted(int(k[1:]) for k in ids if re.fullmatch(r"T\d+", k))
print("ID cao nhất trong tasks/:", "T%d" % nums[-1])
print("10 ID cao nhất:", ["T%d" % n for n in nums[-10:]])
print()
print("ID đang in_progress / blocked (không được dùng lại):")
for k in sorted(ids):
    for path, st in ids[k]:
        if st in ("in_progress", "blocked"):
            print("   %-8s %-12s %s" % (k, st, path))
print()
print("T455 / T456 / T457 hiện tại:")
for k in ["T453", "T454", "T455", "T456", "T457"]:
    for path, st in ids.get(k, []):
        print("   %-6s %-12s %s" % (k, st, path))

# thư mục task khác (docs/, root) có nhắc ID cao nhất chưa?
print()
print("=== ID trùng (file nào khai 1 ID) ===")
for k in sorted(ids):
    if len(ids[k]) > 1:
        print("   %-8s %d file: %s" % (k, len(ids[k]), [x[0] for x in ids[k]]))
