#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sync worktree tasktodo.md: giữ WIP session khác (T500/T486/T485) + chèn 4 marker T454-T457 từ HEAD.

Cách: đọc worktree, chèn ngay sau `<!-- T461:END -->` (vị trí giống HEAD),
       bỏ các marker T454..T457 cũ nếu có (tránh trùng).
"""
import os, re, subprocess, sys

BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
os.chdir(BASE)
TODO = "Dai_Tang_Kinh/daoanh/docs/tasktodo.md"
WT = os.path.join(BASE, TODO.replace("/", os.sep))

head = subprocess.run(["git", "show", "HEAD:" + TODO], capture_output=True, cwd=BASE).stdout.decode("utf-8")
with open(WT, encoding="utf-8", errors="replace") as f:
    wt = f.read()

nl = "\r\n" if "\r\n" in wt else "\n"

# lấy 4 khối marker từ HEAD
blocks = []
for tid in ["T454", "T455", "T456", "T457"]:
    m = re.search(r"<!-- %s:START -->.*?<!-- %s:END -->" % (tid, tid), head, re.DOTALL)
    if not m:
        print("WARN: khong tim thay marker %s trong HEAD" % tid); continue
    blocks.append(m.group(0))

# gỡ marker cũ (nếu worktree đã có) — tránh trùng
for tid in ["T454", "T455", "T456", "T457"]:
    wt = re.sub(r"\n?<!-- %s:START -->.*?<!-- %s:END -->\n?" % (tid, tid), "\n", wt, flags=re.DOTALL)

# chèn sau T461:END
anchor = "<!-- T461:END -->"
assert anchor in wt, "khong tim thay anchor T461:END trong worktree"
wt = wt.replace(anchor, anchor + nl + nl + (nl + nl).join(blocks), 1)

with open(WT, "w", encoding="utf-8", newline="") as f:
    f.write(wt)

print("worktree tasktodo.md: %d chars, %d marker block(s) chen" % (len(wt), len(blocks)))
for tid in ["T454", "T455", "T456", "T457"]:
    print("  %s trong worktree: %s" % (tid, ("<!-- %s:START -->" % tid) in wt))
print()
r = subprocess.run(["git", "status", "--short", "--", TODO], capture_output=True, cwd=BASE)
print("git status:", r.stdout.decode().strip() or "(sach)")
r2 = subprocess.run(["git", "diff", "--numstat", "--", TODO], capture_output=True, cwd=BASE)
print("diff vs HEAD:", r2.stdout.decode().strip())
