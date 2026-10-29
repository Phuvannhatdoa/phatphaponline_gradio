#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify revert chuỗi N4 trong worktree cô lập (KHÔNG đụng worktree chính).

2 cách:
  A) 1 LỆNH (khuyến nghị cho Admin):
     git revert --no-commit 01ee030f^..d73fbc7b
     → kết quả phải khớp chính xác trạng thái trước chuỗi (`git diff --stat 01ee030f^` = rỗng)
  B) TỪNG COMMIT theo thứ tự ngược (mới → cũ):
     d58ac475 → bdcf4fa4 → 873e7dcc → 32e1d2d7 → 8242fbd1 → 38ffb5f4 → a5d2ec25 → 2686da0a → 01ee030f
"""
import os, subprocess, sys, shutil

BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
TMP = r"C:\Users\Nam Thien\AppData\Local\Temp\opencode\revert-seq"
os.chdir(BASE)

CHAIN = ["d58ac475", "bdcf4fa4", "873e7dcc", "32e1d2d7", "8242fbd1",
         "38ffb5f4", "a5d2ec25", "2686da0a", "01ee030f"]
BASE_COMMIT = "01ee030f"          # commit đầu chuỗi
LABEL = {
    "d58ac475": "pipeline log + known-failing-gates",
    "bdcf4fa4": "handoff tong chuoi N4",
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


def reset_worktree():
    git(["reset", "--hard", "HEAD"], cwd=TMP)
    git(["clean", "-fd"], cwd=TMP)


def cleanup():
    git(["revert", "--abort"], cwd=TMP)
    git(["worktree", "remove", "--force", TMP])
    shutil.rmtree(TMP, ignore_errors=True)


if os.path.isdir(TMP):
    git(["worktree", "remove", "--force", TMP])
    shutil.rmtree(TMP, ignore_errors=True)

rc, out, err = git(["worktree", "add", "--detach", TMP, "HEAD"])
if rc != 0:
    print("WORKTREE ADD FAIL:", err.decode("utf-8", "replace")[:300]); sys.exit(1)
print("worktree: %s\n" % TMP)

# ---------- A) revert 1 lệnh cả range ----------
print("=== A) REVERT 1 LENH (ca range) ===")
# HEAD động — không hardcode, để script dùng được sau mọi commit mới
HEAD_SHA = git(["rev-parse", "HEAD"])[1].decode().strip()[:8]
rng = "%s^..%s" % (BASE_COMMIT, HEAD_SHA)
rc, out, err = git(["revert", "--no-commit", "-n", rng], cwd=TMP)
if rc != 0:
    print("  RANGE REVERT FAIL:", err.decode("utf-8", "replace").strip().split("\n")[0][:150])
    cleanup(); sys.exit(1)
rc2, diff, _ = git(["diff", "--stat", BASE_COMMIT + "^"], cwd=TMP)
same = not diff.decode("utf-8", "replace").strip()
print("  git revert --no-commit %s  →  rc=0" % rng)
print("  diff vs trang thai truoc chuoi (%s^): %s" % (BASE_COMMIT, "RONG - khop chinh xac" if same else "KHONG RONG"))
if not same:
    print(diff.decode("utf-8", "replace")[:800])
reset_worktree()

# ---------- B) từng commit ngược ----------
print("\n=== B) REVERT TUNG COMMIT (thu tu nguoc) ===")
failed = []
for sha in CHAIN:
    rc, out, err = git(["revert", "--no-commit", "-n", sha], cwd=TMP)
    if rc != 0:
        # conflict modify/delete: file bị commit này ADD nhưng commit sau đã sửa.
        # Ý định revert = đưa về trạng thái trước commit ⇒ XOÁ file đó.
        rc_u, unmerged, _ = git(["diff", "--name-only", "--diff-filter=U"], cwd=TMP)
        paths = [x for x in unmerged.decode("utf-8", "replace").splitlines() if x]
        if paths:
            for pth in paths:
                git(["rm", "--ignore-unmatch", "-q", pth], cwd=TMP)
            git(["add", "-A"], cwd=TMP)
            rc2, st, _ = git(["status", "--porcelain"], cwd=TMP)
            n = len([x for x in st.decode("utf-8", "replace").splitlines() if x])
            print("  %s  %-32s OK*   %d file (tu giai quyet modify/delete: %d file)" % (
                sha, LABEL.get(sha, ""), n, len(paths)))
            continue
        msg = err.decode("utf-8", "replace").strip().split("\n")[0][:130]
        failed.append(sha)
        print("  %s  %-32s FAIL  %s" % (sha, LABEL.get(sha, ""), msg))
        git(["revert", "--abort"], cwd=TMP)
        reset_worktree()
        continue
    rc2, st, _ = git(["status", "--porcelain"], cwd=TMP)
    n = len([x for x in st.decode("utf-8", "replace").splitlines() if x])
    print("  %s  %-32s OK    %d file" % (sha, LABEL.get(sha, ""), n))

cleanup()

print("\n=== TOM TAT ===")
print("  A) revert 1 lenh ca range: %s" % ("PASS" if same else "FAIL"))
print("  B) revert tung commit: %d/%d PASS%s" % (
    len(CHAIN) - len(failed), len(CHAIN),
    "" if not failed else "  (FAIL: " + ", ".join(failed) + " — dung cach A)"))
print("\nHEAD khong doi:", git(["rev-parse", "HEAD"])[1].decode().strip())
