#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Commit cuối: Handoff (3 phương án T455 + Admin OK) + script sync + pipeline log.

Staging blob đặt NGOÀI repo (theo T2 T457: tmp) để không làm FAIL `dup:ids`.
"""
import os, subprocess, sys, time

BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DAO = "Dai_Tang_Kinh/daoanh"
os.chdir(BASE)
BRANCH_REF = os.path.join(BASE, ".git", "refs", "heads", "truyen-dang-the-pho-clean")
REAL_INDEX = os.path.join(BASE, ".git", "index")
TMP = os.path.join(os.environ.get("TEMP", r"C:\Users\Nam Thien\AppData\Local\Temp"),
                   "opencode", "daoanh-stage")
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
        (DAO + "/docs/Handoff-2026-10-29-n4-t454-t457-batch.md",
         read(DAO + "/docs/Handoff-2026-10-29-n4-t454-t457-batch.md")),
        (DAO + "/scripts/sync_after_admin_confirm.py", read(DAO + "/scripts/sync_after_admin_confirm.py")),
        (DAO + "/scripts/commit_admin_confirm.py", read(DAO + "/scripts/commit_admin_confirm.py")),
        (DAO + "/scripts/update_handoff_t455_options.py", read(DAO + "/scripts/update_handoff_t455_options.py")),
        (DAO + "/docs/sessions/2026-10-28-commit/pipeline.log",
         read(DAO + "/docs/sessions/2026-10-28-commit/pipeline.log")),
    ]
    parent = git(["rev-parse", "HEAD"]).decode().strip()
    print("PARENT", parent)
    tmp = os.path.join(TMP, "index_%s" % str(time.time()).replace(".", ""))
    env = {"GIT_INDEX_FILE": tmp}
    git(["read-tree", parent], env)
    for path, content in entries:
        blob = git(["hash-object", "-w", "--stdin"], inp=content).decode().strip()
        git(["update-index", "--add", "--cacheinfo", "100644,%s,%s" % (blob, path)], env)
    staged = git(["diff", "--cached", "--name-status"], env).decode().replace("\r", "").strip()
    print("STAGED:\n" + staged)
    got = sorted(x.split("\t", 1)[1] for x in staged.splitlines() if x)
    assert got == sorted(p for p, _ in entries), "staged mismatch"
    for x in staged.splitlines():
        assert not x.startswith("D\t"), "file bi XOA: " + x
    tree = git(["write-tree"], env).decode().strip()
    new = git(["commit-tree", tree, "-p", parent, "-m",
               "docs: handoff cap nhat T455 (3 phuong an A/B/C + bang chung do duoc) + Admin xac nhan DONE T453/T454/T457 + canh bao staging blob + pipeline log + docs"]).decode().strip()
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
    print(git(["log", "--oneline", "-4"]).decode())


if __name__ == "__main__":
    main()
