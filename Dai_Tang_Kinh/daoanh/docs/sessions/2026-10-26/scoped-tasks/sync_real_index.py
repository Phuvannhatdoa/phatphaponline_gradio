# -*- coding: utf-8 -*-
# Dong bo index that ve HEAD: backup -> index tam (read-tree HEAD) -> ghi byte vao .git/index (r+b + truncate).
import os
import shutil
import subprocess
import sys

REPO = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
OUT = os.path.join(REPO, "Dai_Tang_Kinh", "daoanh", "docs", "sessions", "2026-10-26", "scoped-tasks")
REAL = os.path.join(REPO, ".git", "index")
TMP = os.path.join(OUT, "tmp_index")
BAK = os.path.join(OUT, "index.before-sync.bak")
dry = "--dry" in sys.argv


def git(args, env=None):
    r = subprocess.run(["git"] + args, cwd=REPO, env=env or os.environ, capture_output=True)
    assert r.returncode == 0, r.stderr
    return r.stdout.decode("utf-8")


if not dry:
    shutil.copy2(REAL, BAK)
    print("backup:", BAK, os.path.getsize(BAK), "bytes")
if os.path.exists(TMP):
    os.remove(TMP)
env = dict(os.environ, GIT_INDEX_FILE=TMP)
git(["read-tree", "HEAD"], env=env)
data = open(TMP, "rb").read()
print("tmp index bytes:", len(data))
if dry:
    print("DRY: khong ghi .git/index")
    sys.exit(0)
with open(REAL, "r+b") as f:
    f.write(data)
    f.truncate()
print("wrote .git/index:", len(data), "bytes")
os.remove(TMP)
