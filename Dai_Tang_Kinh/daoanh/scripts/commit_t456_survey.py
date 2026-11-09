#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Commit báo cáo khảo sát T456 (trùng phạm vi T469) + script khảo sát."""
import os, subprocess, sys, time

BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DAO = "Dai_Tang_Kinh/daoanh"
os.chdir(BASE)
BRANCH_REF = os.path.join(BASE, ".git", "refs", "heads", "truyen-dang-the-pho-clean")
REAL_INDEX = os.path.join(BASE, ".git", "index")
TMP = os.path.join(os.environ.get("TEMP", r"C:\Users\Nam Thien\AppData\Local\Temp"), "opencode", "daoanh-stage")
os.makedirs(TMP, exist_ok=True)
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
    entries = [
        (DAO + "/docs/reports/T456-survey-t469-overlap.md", read(DAO + "/docs/reports/T456-survey-t469-overlap.md")),
        (DAO + "/scripts/t456_timing.py", read(DAO + "/scripts/t456_timing.py")),
        (DAO + "/scripts/t456_http_timing.py", read(DAO + "/scripts/t456_http_timing.py")),
        (DAO + "/scripts/t456_survey_index.py", read(DAO + "/scripts/t456_survey_index.py")),
        (DAO + "/scripts/commit_t455_done.py", read(DAO + "/scripts/commit_t455_done.py")),
        (DAO + "/scripts/sync_after_t455_apply.py", read(DAO + "/scripts/sync_after_t455_apply.py")),
    ]
    parent = git(["rev-parse", "HEAD"]).decode().strip()
    print("PARENT", parent)
    tmp = os.path.join(TMP, "idx.index")
    env = {"GIT_INDEX_FILE": tmp}
    git(["read-tree", parent], env)
    for path, content in entries:
        blob = git(["hash-object", "-w", "--stdin"], inp=content).decode().strip()
        git(["update-index", "--add", "--cacheinfo", "100644,%s,%s" % (blob, path)], env)
    staged = git(["diff", "--cached", "--name-status"], env).decode().replace("\r", "").strip()
    print("STAGED:\n" + staged)
    got = sorted(x.split("\t", 1)[1] for x in staged.splitlines() if x)
    ent = dict(entries)
    for g in got:
        assert g in ent, "staged ngoai danh sach: " + g
    for path, content in entries:
        if path not in got:
            assert git(["rev-parse", "HEAD:" + path]).decode().strip() == \
                   git(["hash-object", "--stdin"], inp=content).decode().strip(), \
                   "chua staged nhung khac HEAD: " + path
    for x in staged.splitlines():
        assert not x.startswith("D\t"), "file bi XOA: " + x
    tree = git(["write-tree"], env).decode().strip()
    new = git(["commit-tree", tree, "-p", parent, "-m",
               "docs(T456): khao sat truoc khi trien khai - phat hien T469 da lam 2/3 nhom (UI+route+cache), do duoc latency cho 3 nguon, de xu 3 phuong an + docs"]).decode().strip()
    os.remove(tmp)

    cur = open(BRANCH_REF, encoding="utf-8").read().strip()
    if cur != parent:
        raise RuntimeError("CAS fail")
    with open(BRANCH_REF, "w", encoding="utf-8", newline="\n") as f:
        f.write(new + "\n")

    tmp2 = os.path.join(TMP, "sync.index")
    git(["read-tree", new], {"GIT_INDEX_FILE": tmp2})
    data = open(tmp2, "rb").read()
    with open(REAL_INDEX, "r+b") as f:
        f.write(data); f.truncate(len(data))
    os.remove(tmp2)

    print("COMMIT", new)
    print(git(["log", "--oneline", "-3"]).decode())


if __name__ == "__main__":
    main()
