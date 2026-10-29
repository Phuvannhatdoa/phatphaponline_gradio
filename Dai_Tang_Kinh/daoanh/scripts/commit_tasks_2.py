#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Commit 3 & 4 (T455 classify + T456 status/ROLLBACK) — chạy tiếp sau khi HEAD đã ở commit T457."""
import os, subprocess, sys, time

BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DAO = "Dai_Tang_Kinh/daoanh"
os.chdir(BASE)
BRANCH_REF = os.path.join(BASE, ".git", "refs", "heads", "truyen-dang-the-pho-clean")
REAL_INDEX = os.path.join(BASE, ".git", "index")
WORK = os.path.join(BASE, DAO, "docs", "sessions", "2026-10-28-commit")
STAGE = os.path.join(WORK, "blobs")


def git(args, env=None, inp=None):
    e = os.environ.copy()
    if env:
        e.update(env)
    r = subprocess.run(["git"] + args, capture_output=True, env=e, input=inp)
    if r.returncode != 0:
        raise RuntimeError("git %s rc=%s err=%s" % (args, r.returncode, r.stderr.decode("utf-8", "replace")))
    return r.stdout


def staged_blob(path):
    staged = os.path.join(STAGE, path.replace("/", "__"))
    if os.path.exists(staged):
        with open(staged, "rb") as f:
            return f.read()
    wt = os.path.join(BASE, path.replace("/", os.sep))
    if os.path.exists(wt):
        with open(wt, "rb") as f:
            return f.read()
    raise RuntimeError("khong tim thay noi dung cho " + path)


def make_commit(parent, entries, msg):
    tmp = os.path.join(WORK, "tmp_%s.index" % str(time.time()).replace(".", ""))
    if os.path.exists(tmp):
        os.remove(tmp)
    env = {"GIT_INDEX_FILE": tmp}
    git(["read-tree", parent], env)
    for path, content in entries:
        blob = git(["hash-object", "-w", "--stdin"], inp=content).decode().strip()
        git(["update-index", "--add", "--cacheinfo", "100644,%s,%s" % (blob, path)], env)
    staged = git(["diff", "--cached", "--name-status"], env).decode()
    got_lines = [x for x in staged.replace("\r", "").strip().split("\n") if x]
    got = sorted(x.split("\t", 1)[1] for x in got_lines)
    expect = sorted(p for p, _ in entries)
    if got != expect:
        raise RuntimeError("staged mismatch\n got=%s\n expect=%s" % (got, expect))
    for x in got_lines:
        if x.startswith("D\t"):
            raise RuntimeError("file bi XOA trong staged: " + x)
    print("STAGED (%d):" % len(got))
    for g in got_lines:
        print("   ", g)
    tree = git(["write-tree"], env).decode().strip()
    new = git(["commit-tree", tree, "-p", parent, "-m", msg]).decode().strip()
    os.remove(tmp)
    return new


def cas_ref(parent, new):
    cur = open(BRANCH_REF, encoding="utf-8").read().strip()
    if cur != parent:
        raise RuntimeError("CAS fail: ref=%s expected=%s" % (cur, parent))
    with open(BRANCH_REF, "w", encoding="utf-8", newline="\n") as f:
        f.write(new + "\n")


def sync_real_index(new):
    tmp2 = os.path.join(WORK, "sync.index")
    if os.path.exists(tmp2):
        os.remove(tmp2)
    git(["read-tree", new], {"GIT_INDEX_FILE": tmp2})
    with open(tmp2, "rb") as f:
        data = f.read()
    with open(REAL_INDEX, "r+b") as f:
        f.write(data)
        f.truncate(len(data))
    os.remove(tmp2)
    return len(data)


def commit(parent, entries, msg, label):
    new = make_commit(parent, entries, msg)
    cas_ref(parent, new)
    n = sync_real_index(new)
    print("\n[%s] COMMIT %s (index sync %d bytes)\n" % (label, new, n))
    return new


def main():
    parent = git(["rev-parse", "HEAD"]).decode().strip()
    print("START PARENT", parent)

    e = [
        (DAO + "/tasks/T455-person-name-vi-standardize-from-dila-catalog.md", staged_blob(DAO + "/tasks/T455-person-name-vi-standardize-from-dila-catalog.md")),
        (DAO + "/docs/Handoff-2026-10-28-t455.md", staged_blob(DAO + "/docs/Handoff-2026-10-28-t455.md")),
        (DAO + "/scripts/classify_t455.py", staged_blob(DAO + "/scripts/classify_t455.py")),
        (DAO + "/scripts/t455_check_state.py", staged_blob(DAO + "/scripts/t455_check_state.py")),
    ]
    for rel in ["plan.md", "classify_out.txt", "name_vi_mismatch_A.csv", "name_vi_mismatch_B.csv", "name_vi_mismatch_C.csv"]:
        p = DAO + "/docs/sessions/2026-10-28-t455/" + rel
        e.append((p, staged_blob(p)))
    parent = commit(parent, e,
        "feat(T455): phan loai 794 dong name_vi lech thanh 3 lo A=24/B=534/C=236 (chua ghi DB, cho Admin duyet tung lo) + script + handoff",
        "T455")

    e = [
        (DAO + "/tasks/T456-home-search-autocomplete-dila-catalog.md", staged_blob(DAO + "/tasks/T456-home-search-autocomplete-dila-catalog.md")),
        (DAO + "/docs/ROLLBACK.md", staged_blob(DAO + "/docs/ROLLBACK.md")),
    ]
    parent = commit(parent, e,
        "docs(T456): ghi trang thai cho autocomplete HOME (blocked boi T455) + rollback row T454/T457 trong ROLLBACK.md",
        "T456+ROLLBACK")

    print("=== FINAL ===")
    print("HEAD:", git(["rev-parse", "HEAD"]).decode().strip())
    print(git(["log", "--oneline", "-6"]).decode())


if __name__ == "__main__":
    main()
