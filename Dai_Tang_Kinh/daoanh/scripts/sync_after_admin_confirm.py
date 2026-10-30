# -*- coding: utf-8 -*-
"""Sync worktree 3 task file + tasktodo về HEAD (giữ WIP T500/T486/T485 của session khác)."""
import os, re, subprocess, sys

BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
os.chdir(BASE)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DAO = "Dai_Tang_Kinh/daoanh"

# --- 3 task file: đồng bộ thẳng từ HEAD ---
for rel in ["tasks/T454-namevi-places-suffix-huy-cleanup.md",
            "tasks/T455-person-name-vi-standardize-from-dila-catalog.md",
            "tasks/T457-dila-biographies-nexus-import.md"]:
    path = DAO + "/" + rel
    r = subprocess.run(["git", "show", "HEAD:" + path], capture_output=True, cwd=BASE)
    wt = os.path.join(BASE, path.replace("/", os.sep))
    with open(wt, "wb") as f:
        f.write(r.stdout)
    print("synced %-62s %d bytes" % (rel, len(r.stdout)))

# --- tasktodo: lấy worktree (giữ WIP session khác) + chèn marker T453..T457 từ HEAD ---
TODO = DAO + "/docs/tasktodo.md"
wt = os.path.join(BASE, TODO.replace("/", os.sep))
head = subprocess.run(["git", "show", "HEAD:" + TODO], capture_output=True, cwd=BASE).stdout.decode("utf-8")
with open(wt, encoding="utf-8", errors="replace") as f:
    cur = f.read()
nl = "\r\n" if "\r\n" in cur else "\n"

blocks = []
for tid in ["T453", "T454", "T455", "T456", "T457"]:
    m = re.search(r"<!-- %s:START -->.*?<!-- %s:END -->" % (tid, tid), head, re.DOTALL)
    if not m:
        print("WARN khong thay marker", tid, "trong HEAD"); continue
    blocks.append(m.group(0))

# gỡ marker cũ (nếu có) rồi chèn bản HEAD
for tid in ["T453", "T454", "T455", "T456", "T457"]:
    cur = re.sub(r"\n?<!-- %s:START -->.*?<!-- %s:END -->\n?" % (tid, tid), "\n", cur, flags=re.DOTALL)

anchor = "<!-- T461:END -->"
assert anchor in cur, "khong thay anchor T461:END trong worktree"
cur = cur.replace(anchor, anchor + nl + nl + (nl + nl).join(blocks), 1)
with open(wt, "w", encoding="utf-8", newline="") as f:
    f.write(cur)
print("tasktodo worktree: %d chars, %d marker block(s)" % (len(cur), len(blocks)))
for tid in ["T453", "T454", "T455", "T456", "T457", "T500", "T486", "T485"]:
    print("  %s trong worktree: %s" % (tid, ("<!-- %s:START -->" % tid) in cur))

r = subprocess.run(["git", "status", "--short", "--"] + [TODO] +
                   [DAO + "/tasks/T454-namevi-places-suffix-huy-cleanup.md",
                    DAO + "/tasks/T455-person-name-vi-standardize-from-dila-catalog.md",
                    DAO + "/tasks/T457-dila-biographies-nexus-import.md"],
                   capture_output=True, cwd=BASE)
print("\ngit status:", r.stdout.decode() or "(sach)")
