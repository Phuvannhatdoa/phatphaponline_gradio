#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify revert từng commit mà KHÔNG ghi worktree.

Cách: `git diff <sha>^ <sha>` → patch; `git apply --check --reverse` trên
worktree = kiểm tra patch revert được hay không (chỉ check, không ghi).
"""
import os, subprocess, sys

BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
os.chdir(BASE)

SHAS = ["01ee030f", "2686da0a", "a5d2ec25", "38ffb5f4", "8242fbd1", "32e1d2d7"]
WORK = os.path.join(BASE, "Dai_Tang_Kinh", "daoanh", "docs", "sessions", "2026-10-28-commit")
os.makedirs(WORK, exist_ok=True)

for sha in SHAS:
    # patch = thay đổi của commit; revert = áp ngược
    r = subprocess.run(["git", "diff", sha + "^", sha], capture_output=True, cwd=BASE)
    patch = r.stdout
    pf = os.path.join(WORK, "revert_%s.patch" % sha)
    with open(pf, "wb") as f:
        f.write(patch)
    # apply --check --reverse: nghĩa là worktree đã có thay đổi → revert được
    r2 = subprocess.run(["git", "apply", "--check", "--reverse", pf], capture_output=True, cwd=BASE)
    ok = r2.returncode == 0
    msg = "" if ok else r2.stderr.decode("utf-8", "replace").strip().split("\n")[0][:110]
    files = patch.decode("utf-8", "replace").count("\ndiff --git") + (
        1 if patch.startswith(b"diff --git") else 0)
    print("%s  revert=%-5s  files=%-3d  %s" % (sha, "OK" if ok else "FAIL", files, msg))

print()
print("HEAD:", subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, cwd=BASE).stdout.decode().strip())
