# -*- coding: utf-8 -*-
"""Sync worktree sau apply T455: task file T455 từ HEAD; tasktodo giữ WIP session khác + marker HEAD."""
import os, re, subprocess, sys

BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
os.chdir(BASE)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DAO = "Dai_Tang_Kinh/daoanh"

T455 = DAO + "/tasks/T455-person-name-vi-standardize-from-dila-catalog.md"
r = subprocess.run(["git", "show", "HEAD:" + T455], capture_output=True, cwd=BASE)
with open(os.path.join(BASE, T455.replace("/", os.sep)), "wb") as f:
    f.write(r.stdout)
print("synced T455 task file:", len(r.stdout), "bytes")

TODO = DAO + "/docs/tasktodo.md"
wt = os.path.join(BASE, TODO.replace("/", os.sep))
head = subprocess.run(["git", "show", "HEAD:" + TODO], capture_output=True, cwd=BASE).stdout.decode("utf-8")
with open(wt, encoding="utf-8", errors="replace") as f:
    cur = f.read()
nl = "\r\n" if "\r\n" in cur else "\n"

blocks = []
for tid in ["T453", "T454", "T455", "T456", "T457"]:
    m = re.search(r"<!-- %s:START -->.*?<!-- %s:END -->" % (tid, tid), head, re.DOTALL)
    if m:
        blocks.append(m.group(0))
for tid in ["T453", "T454", "T455", "T456", "T457"]:
    cur = re.sub(r"\n?<!-- %s:START -->.*?<!-- %s:END -->\n?" % (tid, tid), "\n", cur, flags=re.DOTALL)
anchor = "<!-- T461:END -->"
assert anchor in cur
cur = cur.replace(anchor, anchor + nl + nl + (nl + nl).join(blocks), 1)
with open(wt, "w", encoding="utf-8", newline="") as f:
    f.write(cur)
print("tasktodo worktree: %d chars, %d marker(s)" % (len(cur), len(blocks)))
for tid in ["T453", "T454", "T455", "T456", "T457", "T500", "T486", "T485"]:
    print("   %s: %s" % (tid, ("<!-- %s:START -->" % tid) in cur))

r2 = subprocess.run(["git", "status", "--short", "--", TODO, T455], capture_output=True, cwd=BASE)
print("\ngit status:", r2.stdout.decode() or "(sach)")
