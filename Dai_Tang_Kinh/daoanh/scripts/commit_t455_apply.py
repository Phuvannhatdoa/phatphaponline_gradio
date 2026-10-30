#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Commit apply T455 phương án A: ROLLBACK row + task file + tasktodo + báo cáo + script.

Staging blob đọc vào RAM rồi XOÁ thư mục `docs/.../blobs/` TRƯỚC khi commit
(nếu để lại → `npm run dup:ids` FAIL vì thấy 2 file cùng `id:`).
"""
import os, shutil, subprocess, sys, time

BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DAO = "Dai_Tang_Kinh/daoanh"
os.chdir(BASE)
BRANCH_REF = os.path.join(BASE, ".git", "refs", "heads", "truyen-dang-the-pho-clean")
REAL_INDEX = os.path.join(BASE, ".git", "index")
WORK = os.path.join(BASE, DAO, "docs", "sessions", "2026-10-30-t455-apply")
STAGE = os.path.join(WORK, "blobs")
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
    entries = []
    # 1) đọc blob staged vào RAM
    for f in sorted(os.listdir(STAGE)):
        path = f.replace("__", "/")
        entries.append((path, open(os.path.join(STAGE, f), "rb").read()))
    # 2) XOÁ staging trong docs/ TRƯỚC khi commit
    shutil.rmtree(STAGE)
    print("đã xoá staging docs/.../blobs/ (tránh FAIL dup:ids)")

    # 3) báo cáo + script
    for rel in [
        DAO + "/docs/reports/T455-apply-planA-report.md",
        DAO + "/docs/sessions/2026-10-30-t455-apply/t455_proposal_planA.csv",
        DAO + "/scripts/t455_apply_planA.py",
        DAO + "/scripts/t455_verify_apply.py",
        DAO + "/scripts/t455_propose.py",
        DAO + "/scripts/t455_verify_lotA.py",
        DAO + "/scripts/t455_diff_check.py",
        DAO + "/scripts/t455_diff_analysis.py",
        DAO + "/scripts/t455_charmap_check.py",
        DAO + "/scripts/t455_polyphonic_check.py",
        DAO + "/scripts/t455_examples.py",
        DAO + "/scripts/t455_schema_probe.py",
        DAO + "/scripts/t455_schema_probe2.py",
        DAO + "/scripts/t455_claim_probe.py",
        DAO + "/scripts/t455_claims_and_lotA.py",
        DAO + "/scripts/t455_fix_skipped_row.py",
        DAO + "/scripts/prepare_t455_apply_docs.py",
        DAO + "/docs/sessions/2026-10-28-commit/pipeline.log",
    ]:
        entries.append((rel, read(rel)))

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
    ent_map = dict(entries)
    # mọi file staged phải nằm trong entries
    for g in got:
        assert g in ent_map, "file staged ngoài danh sách: " + g
    # file KHÔNG staged => nội dung phải giống HEAD (đã commit trước đó)
    for path, content in entries:
        if path in got:
            continue
        head_blob = git(["rev-parse", "HEAD:" + path]).decode().strip()
        cur_blob = git(["hash-object", "--stdin"], inp=content).decode().strip()
        assert head_blob == cur_blob, "file chưa staged nhưng nội dung khác HEAD: " + path
    for x in staged.splitlines():
        assert not x.startswith("D\t"), "file bi XOA: " + x
    tree = git(["write-tree"], env).decode().strip()
    new = git(["commit-tree", tree, "-p", parent, "-m",
               "feat(T455): apply phuong an A - chuan hoa 258 ten nguoi (lo A 22 + lo C 236), 534 alias ghi chu, "
               "bang lich su people_name_vi_history (794 dong) + rollback row + bao cao + docs"]).decode().strip()
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
