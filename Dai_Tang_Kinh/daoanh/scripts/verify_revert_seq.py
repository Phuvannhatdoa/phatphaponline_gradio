#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify revert theo THỨ TỰ NGƯỢC (newest → oldest) trong worktree cô lập.

Đây là cách revert chuẩn khi nhiều commit đụng cùng file: revert từ trên xuống,
mỗi bước context khớp vì đã hoàn tác các commit con.
"""
import os, subprocess, sys, shutil

BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
TMP = r"C:\Users\Nam Thien\AppData\Local\Temp\opencode\revert-seq"
os.chdir(BASE)

# thứ tự ngược: 873e7dcc → 32e1d2d7 → 8242fbd1 → 38ffb5f4 → a5d2ec25 → 2686da0a → 01ee030f
SEQ = ["873e7dcc", "32e1d2d7", "8242fbd1", "38ffb5f4", "a5d2ec25", "2686da0a", "01ee030f"]
LABEL = {
    "873e7dcc": "fix UTF-16 logs -> UTF-8",
    "32e1d2d7": "tasktodo markers T454-T457",
    "8242fbd1": "ROLLBACK backup path fix",
    "38ffb5f4": "T456 status + ROLLBACK rows",
    "a5d2ec25": "T455 - phan loai 794 dong",
    "2686da0a": "T457 - import DILA bio nexus",
    "01ee030f": "T454 - lam sach hau to",
}


def git(args, cwd=None):
    r = subprocess.run(["git"] + args, capture_output=True, cwd=cwd or BASE)
    return r.returncode, r.stdout, r.stderr


if os.path.isdir(TMP):
    git(["worktree", "remove", "--force", TMP])
    shutil.rmtree(TMP, ignore_errors=True)

rc, out, err = git(["worktree", "add", "--detach", TMP, "HEAD"])
if rc != 0:
    print("WORKTREE ADD FAIL:", err.decode("utf-8", "replace")[:300]); sys.exit(1)

print("=== Revert theo thu tu nguoc (newest -> oldest) ===")
failed = []
for sha in SEQ:
    rc, out, err = git(["revert", "--no-commit", "-n", sha], cwd=TMP)
    if rc != 0:
        msg = err.decode("utf-8", "replace").strip().split("\n")[0][:120]
        failed.append(sha)
        print("  %s  %-32s FAIL  %s" % (sha, LABEL[sha], msg))
        git(["revert", "--abort"], cwd=TMP)
        break
    rc2, out2, _ = git(["status", "--porcelain"], cwd=TMP)
    n = len([x for x in out2.decode("utf-8", "replace").splitlines() if x])
    print("  %s  %-32s OK    %d file" % (sha, LABEL[sha], n))

# kiểm tra trạng thái cuối: có giống bản trước 01ee030f (tức trước cả chuỗi N4) không
if not failed:
    rc, out, _ = git(["diff", "--stat", "01ee030f^"], cwd=TMP)
    diff = out.decode("utf-8", "replace").strip()
    print("\nTrang thai sau khi revert ca chuoi so voi HEAD truoc chuoi (01ee030f^):")
    print("  " + (diff if diff else "(TUONG DOI - khop voi trang thai truoc chuoi N4)"))

git(["revert", "--abort"], cwd=TMP)
git(["worktree", "remove", "--force", TMP])
shutil.rmtree(TMP, ignore_errors=True)

print("\nHEAD khong doi:", git(["rev-parse", "HEAD"])[1].decode().strip())
print("Ket qua: %s" % ("tat ca OK" if not failed else "FAIL tai " + failed[0]))
