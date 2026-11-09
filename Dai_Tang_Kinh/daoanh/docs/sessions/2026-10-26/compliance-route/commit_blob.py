"""Commit 1 file bang CACH BLOB tren index tam (khong dong vao index that, khong nuot WIP).
Usage: python -X utf8 commit_blob.py <repo-relative-path> <blob-file> "<message>"
Quy trinh: parent=HEAD -> read-tree parent (index tam) -> hash-object -w -> update-index --cacheinfo
-> kiem name-status == 'M <path>' -> write-tree -> commit-tree -> CAS thu cong tren ref (toi da 3 lan).
"""
import os
import subprocess
import sys

ROOT = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
SESS = os.path.join(ROOT, "Dai_Tang_Kinh", "daoanh", "docs", "sessions", "2026-10-26", "compliance-route")
IDX = os.path.join(SESS, "wt_index")
rel, blob_file, msg = sys.argv[1], sys.argv[2], sys.argv[3]
env = dict(os.environ, GIT_INDEX_FILE=IDX)


def git(*args, use_idx=False):
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, env=env if use_idx else None)
    if r.returncode != 0:
        raise SystemExit("git %s failed: %s" % (args, r.stderr.decode("utf-8", "replace")))
    return r.stdout.decode("utf-8", "replace").strip()


def build(parent):
    if os.path.exists(IDX):
        os.remove(IDX)
    git("read-tree", parent, use_idx=True)
    sha = git("hash-object", "-w", blob_file)
    git("update-index", "--add", "--cacheinfo", "100644,%s,%s" % (sha, rel), use_idx=True)
    ns = git("diff", "--cached", "--name-status", use_idx=True)
    print("NAME-STATUS:", repr(ns))
    if ns != "M\t" + rel:
        raise SystemExit("name-status khong dung: %r" % ns)
    tree = git("write-tree", use_idx=True)
    return git("commit-tree", tree, "-p", parent, "-m", msg, use_idx=True)


ref_name = git("symbolic-ref", "HEAD")
gitdir = git("rev-parse", "--git-dir")
ref_path = os.path.join(ROOT, gitdir, ref_name) if not os.path.isabs(gitdir) else os.path.join(gitdir, ref_name)
print("ref:", ref_name, "file:", ref_path, "isfile:", os.path.isfile(ref_path))
assert os.path.isfile(ref_path), "ref khong phai file loose -> dung lai"

parent = git("rev-parse", "HEAD")
for attempt in range(3):
    new = build(parent)
    print("attempt", attempt + 1, "parent", parent, "new", new)
    cur = open(ref_path, encoding="ascii").read().strip()
    if cur == parent:
        # CAS thu cong: ghi tai cho (khong os.replace, khong update-ref)
        with open(ref_path, "wb") as fh:
            fh.write((new + "\n").encode("ascii"))
        print("CAS OK -> HEAD =", new)
        break
    print("HEAD doi (%s != %s), thu lai" % (cur, parent))
    parent = cur
else:
    raise SystemExit("CAS that bai sau 3 lan -> dung")

if os.path.exists(IDX):
    os.remove(IDX)
print("VERIFY HEAD:", git("rev-parse", "HEAD"))
