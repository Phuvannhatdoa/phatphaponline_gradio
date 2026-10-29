#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify revert thật bằng git worktree cô lập (KHÔNG đụng worktree chính).

Mỗi commit: tạo worktree tại HEAD → `git revert --no-commit <sha>` → kiểm tra
→ xoá worktree. Đây là cách kiểm chứng revert thật (git apply --check quá
chặt: binary patch + context đã đổi).
"""
import os, subprocess, sys, shutil

BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
TMP = r"C:\Users\Nam Thien\AppData\Local\Temp\opencode\revert-test"
os.chdir(BASE)

SHAS = [
    ("01ee030f", "T454 - lam sach hau to"),
    ("2686da0a", "T457 - import DILA bio nexus"),
    ("a5d2ec25", "T455 - phan loai 794 dong"),
    ("38ffb5f4", "T456 status + ROLLBACK rows"),
    ("8242fbd1", "ROLLBACK backup path fix"),
    ("32e1d2d7", "tasktodo markers T454-T457"),
    ("873e7dcc", "fix UTF-16 logs -> UTF-8"),
]


def git(args, cwd=None, inp=None):
    e = os.environ.copy()
    r = subprocess.run(["git"] + args, capture_output=True, cwd=cwd or BASE, input=inp, env=e)
    return r.returncode, r.stdout, r.stderr


if os.path.isdir(TMP):
    git(["worktree", "remove", "--force", TMP])
    shutil.rmtree(TMP, ignore_errors=True)

rc, out, err = git(["worktree", "add", "--detach", TMP, "HEAD"])
if rc != 0:
    print("WORKTREE ADD FAIL:", err.decode("utf-8", "replace")[:400])
    sys.exit(1)
print("worktree: %s\n" % TMP)

results = []
for sha, label in SHAS:
    git(["reset", "--hard", "HEAD"], cwd=TMP)
    git(["clean", "-fd"], cwd=TMP)
    rc, out, err = git(["revert", "--no-commit", "-n", sha], cwd=TMP)
    if rc != 0:
        msg = err.decode("utf-8", "replace").strip().split("\n")[0][:120]
        results.append((sha, label, "FAIL", msg))
        print("%s  %-34s REVERT FAIL  %s" % (sha, label, msg))
        continue
    rc2, out2, _ = git(["status", "--porcelain"], cwd=TMP)
    lines = [x for x in out2.decode("utf-8", "replace").splitlines() if x]
    adds = sum(1 for x in lines if x[:2].strip() == "A" or x.startswith("A"))
    dels = sum(1 for x in lines if x.startswith(" D") or x[:1] == "D")
    mods = sum(1 for x in lines if x.startswith("M") or "M" == x[:1].strip())
    results.append((sha, label, "OK", "%d file (A=%d D=%d M=%d)" % (len(lines), adds, dels, mods)))
    print("%s  %-34s REVERT OK    %d file bi doi" % (sha, label, len(lines)))

git(["revert", "--abort"], cwd=TMP)
git(["worktree", "remove", "--force", TMP])
shutil.rmtree(TMP, ignore_errors=True)

print("\n=== TOM TAT ===")
ok = sum(1 for r in results if r[2] == "OK")
for sha, label, st, info in results:
    print("  %s  %-34s %-4s  %s" % (sha, label, st, info))
print("\n%d/%d commit revert duoc doc lap" % (ok, len(results)))
print("HEAD khong doi:", git(["rev-parse", "HEAD"])[1].decode().strip())
