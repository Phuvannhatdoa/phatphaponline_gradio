#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chuyển 3 file log UTF-16 (PowerShell redirect) → UTF-8 + commit lại.

File bị UTF-16:
- docs/sessions/2026-10-28-t457/staging_output.txt
- docs/sessions/2026-10-28-t457/staging_v4_output.txt
- docs/sessions/2026-10-28-t455/classify_out.txt
"""
import os, subprocess, sys, time

BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DAO = "Dai_Tang_Kinh/daoanh"
os.chdir(BASE)
BRANCH_REF = os.path.join(BASE, ".git", "refs", "heads", "truyen-dang-the-pho-clean")
REAL_INDEX = os.path.join(BASE, ".git", "index")
WORK = os.path.join(BASE, DAO, "docs", "sessions", "2026-10-28-commit")

FILES = [
    "docs/sessions/2026-10-28-t457/staging_output.txt",
    "docs/sessions/2026-10-28-t457/staging_v4_output.txt",
    "docs/sessions/2026-10-28-t455/classify_out.txt",
]


def git(args, env=None, inp=None):
    e = os.environ.copy()
    if env:
        e.update(env)
    r = subprocess.run(["git"] + args, capture_output=True, env=e, input=inp)
    if r.returncode != 0:
        raise RuntimeError("git %s rc=%s err=%s" % (args, r.returncode, r.stderr.decode("utf-8", "replace")))
    return r.stdout


def to_utf8(rel):
    p = os.path.join(BASE, DAO, rel.replace("/", os.sep))
    raw = open(p, "rb").read()
    if raw.startswith(b"\xff\xfe"):
        txt = raw.decode("utf-16")
    elif raw.startswith(b"\xfe\xff"):
        txt = raw.decode("utf-16")
    else:
        txt = raw.decode("utf-8", "replace")
    txt = txt.replace("\r\n", "\n")
    out = txt.encode("utf-8")
    with open(p, "wb") as f:
        f.write(out)
    print("converted %-62s %d -> %d bytes (NUL %d -> 0)" % (
        rel, len(raw), len(out), raw.count(b"\x00")))
    return out


def main():
    entries = []
    for rel in FILES:
        entries.append((DAO + "/" + rel, to_utf8(rel)))

    parent = git(["rev-parse", "HEAD"]).decode().strip()
    print("PARENT", parent)
    tmp = os.path.join(WORK, "tmp_%s.index" % str(time.time()).replace(".", ""))
    if os.path.exists(tmp):
        os.remove(tmp)
    env = {"GIT_INDEX_FILE": tmp}
    git(["read-tree", parent], env)
    for path, content in entries:
        blob = git(["hash-object", "-w", "--stdin"], inp=content).decode().strip()
        git(["update-index", "--add", "--cacheinfo", "100644,%s,%s" % (blob, path)], env)
    staged = git(["diff", "--cached", "--name-status"], env).decode()
    print("STAGED:", staged.replace("\r", "").strip())
    tree = git(["write-tree"], env).decode().strip()
    new = git(["commit-tree", tree, "-p", parent, "-m",
               "fix: chuyen 3 file log tu UTF-16 (PowerShell redirect) sang UTF-8 de git patch/revert khong bi binary"]).decode().strip()
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
