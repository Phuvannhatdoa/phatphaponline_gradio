#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Commit Handoff tổng chuỗi N4 (1 commit, chỉ 1 file — revert cực gọn)."""
import os, subprocess, sys, time

BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DAO = "Dai_Tang_Kinh/daoanh"
os.chdir(BASE)
BRANCH_REF = os.path.join(BASE, ".git", "refs", "heads", "truyen-dang-the-pho-clean")
REAL_INDEX = os.path.join(BASE, ".git", "index")
WORK = os.path.join(BASE, DAO, "docs", "sessions", "2026-10-28-commit")
PATH = DAO + "/docs/Handoff-2026-10-29-n4-t454-t457-batch.md"


def git(args, env=None, inp=None):
    e = os.environ.copy()
    if env:
        e.update(env)
    r = subprocess.run(["git"] + args, capture_output=True, env=e, input=inp)
    if r.returncode != 0:
        raise RuntimeError("git %s rc=%s err=%s" % (args, r.returncode, r.stderr.decode("utf-8", "replace")))
    return r.stdout


def main():
    content = open(os.path.join(BASE, PATH.replace("/", os.sep)), "rb").read()
    parent = git(["rev-parse", "HEAD"]).decode().strip()
    tmp = os.path.join(WORK, "tmp_%s.index" % str(time.time()).replace(".", ""))
    env = {"GIT_INDEX_FILE": tmp}
    git(["read-tree", parent], env)
    blob = git(["hash-object", "-w", "--stdin"], inp=content).decode().strip()
    git(["update-index", "--add", "--cacheinfo", "100644,%s,%s" % (blob, PATH)], env)
    staged = git(["diff", "--cached", "--name-status"], env).decode().strip()
    print("STAGED:", staged)
    assert staged.endswith(PATH), "staged sai"
    tree = git(["write-tree"], env).decode().strip()
    new = git(["commit-tree", tree, "-p", parent, "-m",
               "docs: handoff tong chuoi N4 T454-T457 (10 muc AGENTS §15, 7 commit, revert 7/7 PASS) + docs"]).decode().strip()
    os.remove(tmp)

    cur = open(BRANCH_REF, encoding="utf-8").read().strip()
    if cur != parent:
        raise RuntimeError("CAS fail: %s != %s" % (cur, parent))
    with open(BRANCH_REF, "w", encoding="utf-8", newline="\n") as f:
        f.write(new + "\n")

    tmp2 = os.path.join(WORK, "sync.index")
    if os.path.exists(tmp2):
        os.remove(tmp2)
    git(["read-tree", new], {"GIT_INDEX_FILE": tmp2})
    data = open(tmp2, "rb").read()
    with open(REAL_INDEX, "r+b") as f:
        f.write(data); f.truncate(len(data))
    os.remove(tmp2)

    print("COMMIT", new)
    print(git(["log", "--oneline", "-3"]).decode())
    print()
    r = subprocess.run(["git", "status", "--short", "--", PATH], capture_output=True, cwd=BASE)
    print("worktree status:", r.stdout.decode().strip() or "(sach)")


if __name__ == "__main__":
    main()
