#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Commit: Admin xác nhận DONE (T453/T454/T457) + báo cáo phân tích T455 + script phân tích."""
import os, subprocess, sys, time

BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DAO = "Dai_Tang_Kinh/daoanh"
os.chdir(BASE)
BRANCH_REF = os.path.join(BASE, ".git", "refs", "heads", "truyen-dang-the-pho-clean")
REAL_INDEX = os.path.join(BASE, ".git", "index")
WORK = os.path.join(BASE, DAO, "docs", "sessions", "2026-10-30-t455-analysis")
STAGE = os.path.join(WORK, "blobs")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def git(args, env=None, inp=None):
    e = os.environ.copy()
    if env:
        e.update(env)
    r = subprocess.run(["git"] + args, capture_output=True, env=e, input=inp)
    if r.returncode != 0:
        raise RuntimeError("git %s rc=%s err=%s" % (args, r.returncode, r.stderr.decode("utf-8", "replace")))
    return r.stdout


def read(rel):
    with open(os.path.join(BASE, rel.replace("/", os.sep)), "rb") as f:
        return f.read()


def main():
    entries = []
    # blob đã chuẩn bị (tasktodo + 3 task file)
    for f in sorted(os.listdir(STAGE)):
        path = f.replace("__", "/")
        entries.append((path, open(os.path.join(STAGE, f), "rb").read()))
    # báo cáo + script phân tích
    for rel in [
        DAO + "/docs/reports/T455-analysis-794-mismatch.md",
        DAO + "/scripts/t455_examples.py",
        DAO + "/scripts/t455_diff_analysis.py",
        DAO + "/scripts/t455_charmap_check.py",
        DAO + "/scripts/t455_polyphonic_check.py",
        DAO + "/scripts/prepare_admin_confirm.py",
        DAO + "/scripts/fix_t455_marker.py",
    ]:
        entries.append((rel, read(rel)))

    parent = git(["rev-parse", "HEAD"]).decode().strip()
    print("PARENT", parent)
    tmp = os.path.join(WORK, "tmp.index")
    if os.path.exists(tmp):
        os.remove(tmp)
    env = {"GIT_INDEX_FILE": tmp}
    git(["read-tree", parent], env)
    for path, content in entries:
        blob = git(["hash-object", "-w", "--stdin"], inp=content).decode().strip()
        git(["update-index", "--add", "--cacheinfo", "100644,%s,%s" % (blob, path)], env)
    staged = git(["diff", "--cached", "--name-status"], env).decode().replace("\r", "").strip()
    print("STAGED:\n" + staged)
    got = sorted(x.split("\t", 1)[1] for x in staged.splitlines() if x)
    assert got == sorted(p for p, _ in entries), "staged mismatch:\n%s\n%s" % (got, sorted(p for p, _ in entries))
    for x in staged.splitlines():
        assert not x.startswith("D\t"), "file bi XOA: " + x
    tree = git(["write-tree"], env).decode().strip()
    new = git(["commit-tree", tree, "-p", parent, "-m",
               "feat(T455): bao cao phan tich 794 dong (3 lo A24/B534/C236, chung minh charmap) + 3 phuong an cho Admin + Admin xac nhan DONE T453/T454/T457 + docs"]).decode().strip()
    os.remove(tmp)

    cur = open(BRANCH_REF, encoding="utf-8").read().strip()
    if cur != parent:
        raise RuntimeError("CAS fail")
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


if __name__ == "__main__":
    main()
