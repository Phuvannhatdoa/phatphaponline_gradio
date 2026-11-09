#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Commit cuối: pipeline.log + known-failing-gates (pipeline XANH) + script helper.

1 commit — revert cực gọn (chỉ docs + logs, không đụng code runtime).
"""
import os, subprocess, sys, time

BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DAO = "Dai_Tang_Kinh/daoanh"
os.chdir(BASE)
BRANCH_REF = os.path.join(BASE, ".git", "refs", "heads", "truyen-dang-the-pho-clean")
REAL_INDEX = os.path.join(BASE, ".git", "index")
WORK = os.path.join(BASE, DAO, "docs", "sessions", "2026-10-28-commit")


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
        (DAO + "/docs/known-failing-gates.md", read(DAO + "/docs/known-failing-gates.md")),
        (DAO + "/docs/sessions/2026-10-28-commit/pipeline.log", read(DAO + "/docs/sessions/2026-10-28-commit/pipeline.log")),
        (DAO + "/docs/sessions/2026-10-28-commit/dupids.log", read(DAO + "/docs/sessions/2026-10-28-commit/dupids.log")),
        (DAO + "/scripts/run_pipeline_log.py", read(DAO + "/scripts/run_pipeline_log.py")),
        (DAO + "/scripts/update_known_gates.py", read(DAO + "/scripts/update_known_gates.py")),
        (DAO + "/scripts/verify_revert_worktree.py", read(DAO + "/scripts/verify_revert_worktree.py")),
        (DAO + "/scripts/verify_revert_seq.py", read(DAO + "/scripts/verify_revert_seq.py")),
        (DAO + "/scripts/verify_revert_safe.py", read(DAO + "/scripts/verify_revert_safe.py")),
        (DAO + "/scripts/restore_deleted_files.py", read(DAO + "/scripts/restore_deleted_files.py")),
        (DAO + "/scripts/sync_worktree_tasks.py", read(DAO + "/scripts/sync_worktree_tasks.py")),
        (DAO + "/scripts/sync_tasktodo_worktree.py", read(DAO + "/scripts/sync_tasktodo_worktree.py")),
        (DAO + "/scripts/fix_rollback_dup.py", read(DAO + "/scripts/fix_rollback_dup.py")),
        (DAO + "/scripts/fix_utf16_logs.py", read(DAO + "/scripts/fix_utf16_logs.py")),
        (DAO + "/scripts/commit_handoff.py", read(DAO + "/scripts/commit_handoff.py")),
        (DAO + "/scripts/commit_tasks.py", read(DAO + "/scripts/commit_tasks.py")),
        (DAO + "/scripts/commit_tasks_2.py", read(DAO + "/scripts/commit_tasks_2.py")),
        (DAO + "/scripts/commit_tasks_3.py", read(DAO + "/scripts/commit_tasks_3.py")),
        (DAO + "/scripts/prepare_task_updates.py", read(DAO + "/scripts/prepare_task_updates.py")),
    ]

    parent = git(["rev-parse", "HEAD"]).decode().strip()
    print("PARENT", parent)
    tmp = os.path.join(WORK, "tmp_final.index")
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
    expect = sorted(p for p, _ in entries)
    assert got == expect, "staged mismatch"
    for x in staged.splitlines():
        assert not x.startswith("D\t"), "file bi XOA: " + x
    tree = git(["write-tree"], env).decode().strip()
    new = git(["commit-tree", tree, "-p", parent, "-m",
               "docs: npm run pipeline XANH (exit 0, 1804 dong log) + so cung cap nhat 5 cong da go + script helper"]).decode().strip()
    os.remove(tmp)

    cur = open(BRANCH_REF, encoding="utf-8").read().strip()
    if cur != parent:
        raise RuntimeError("CAS fail")
    with open(BRANCH_REF, "w", encoding="utf-8", newline="\n") as f:
        f.write(new + "\n")

    tmp2 = os.path.join(WORK, "sync_final.index")
    if os.path.exists(tmp2):
        os.remove(tmp2)
    git(["read-tree", new], {"GIT_INDEX_FILE": tmp2})
    data = open(tmp2, "rb").read()
    with open(REAL_INDEX, "r+b") as f:
        f.write(data); f.truncate(len(data))
    os.remove(tmp2)

    print("COMMIT", new)
    print(git(["log", "--oneline", "-10"]).decode())


if __name__ == "__main__":
    main()
