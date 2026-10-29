#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sync worktree 4 task file về nội dung đã commit (HEAD).
Không đụng ROLLBACK.md (còn WIP của session khác: T482/T470/T379).
"""
import os, subprocess, sys

BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
os.chdir(BASE)
DAO = "Dai_Tang_Kinh/daoanh"

FILES = [
    DAO + "/tasks/T454-namevi-places-suffix-huy-cleanup.md",
    DAO + "/tasks/T455-person-name-vi-standardize-from-dila-catalog.md",
    DAO + "/tasks/T456-home-search-autocomplete-dila-catalog.md",
    DAO + "/tasks/T457-dila-biographies-nexus-import.md",
]

for path in FILES:
    r = subprocess.run(["git", "show", "HEAD:" + path], capture_output=True, cwd=BASE)
    if r.returncode != 0:
        print("FAIL show", path, r.stderr.decode()[:200]); continue
    wt = os.path.join(BASE, path.replace("/", os.sep))
    with open(wt, "wb") as f:
        f.write(r.stdout)
    print("synced %-70s %d bytes" % (path, len(r.stdout)))

print()
print("=== git status (4 task file) ===")
r = subprocess.run(["git", "status", "--short"] + FILES, capture_output=True, cwd=BASE)
print(r.stdout.decode() or "  (sach - khong con modified)")
