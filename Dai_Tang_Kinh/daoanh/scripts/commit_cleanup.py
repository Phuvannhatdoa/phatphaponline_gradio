#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dọn rác + commit công cụ apply T455 (chờ Admin duyệt) + bằng chứng patch.

Xoá:
- scripts/verify_revert.py  (NGUY HIỂM — ghi worktree, KHÔNG nên dùng)
- root scripts/classify_t455.py (đã copy vào daoanh/scripts)
- root update_tasktodo.py (rác)
"""
import os, subprocess, sys, time

BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DAO = "Dai_Tang_Kinh/daoanh"
os.chdir(BASE)
BRANCH_REF = os.path.join(BASE, ".git", "refs", "heads", "truyen-dang-the-pho-clean")
REAL_INDEX = os.path.join(BASE, ".git", "index")
WORK = os.path.join(BASE, DAO, "docs", "sessions", "2026-10-28-commit")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ---------- 1. xoá rác ----------
for rel in [
    DAO + "/scripts/verify_revert.py",
    "scripts/classify_t455.py",
    "update_tasktodo.py",
    DAO + "/update_tasktodo.py",
]:
    p = os.path.join(BASE, rel.replace("/", os.sep))
    if os.path.exists(p):
        os.remove(p)
        print("removed:", rel)

# ---------- 2. commit ----------
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


entries = [(DAO + "/scripts/t455_name_vi_fix.py", read(DAO + "/scripts/t455_name_vi_fix.py"))]
pdir = os.path.join(BASE, DAO, "docs", "sessions", "2026-10-28-commit")
for f in sorted(os.listdir(pdir)):
    if f.endswith(".patch"):
        entries.append((DAO + "/docs/sessions/2026-10-28-commit/" + f, read(DAO + "/docs/sessions/2026-10-28-commit/" + f)))

parent = git(["rev-parse", "HEAD"]).decode().strip()
print("PARENT", parent)
tmp = os.path.join(WORK, "tmp_y.index")
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
assert got == sorted(p for p, _ in entries), "staged mismatch"
tree = git(["write-tree"], env).decode().strip()
new = git(["commit-tree", tree, "-p", parent, "-m",
           "feat(T455): them script apply ten nguoi (backup + --apply/--revert, CHUA chay - cho Admin duyet lo) + 12 file patch revert la bang chung + docs"]).decode().strip()
os.remove(tmp)

cur = open(BRANCH_REF, encoding="utf-8").read().strip()
if cur != parent:
    raise RuntimeError("CAS fail")
with open(BRANCH_REF, "w", encoding="utf-8", newline="\n") as f:
    f.write(new + "\n")

tmp2 = os.path.join(WORK, "sync_y.index")
if os.path.exists(tmp2):
    os.remove(tmp2)
git(["read-tree", new], {"GIT_INDEX_FILE": tmp2})
data = open(tmp2, "rb").read()
with open(REAL_INDEX, "r+b") as f:
    f.write(data); f.truncate(len(data))
os.remove(tmp2)

print("COMMIT", new)
print(git(["log", "--oneline", "-13"]).decode())
