"""Dong bo index THAT ve HEAD (chi khi diff --cached hien tai chi gom file cua minh).
- backup .git/index truoc (vao thu muc session)
- index tam (trong session) = read-tree HEAD
- ghi byte index tam vao .git/index bang open('r+b') + truncate (tranh rename bi chan tren may nay)
- verify: git diff --cached --name-status rong
Usage: python -X utf8 sync_index.py <expected_name_status_line_or_EMPTY>
"""
import os
import shutil
import subprocess
import sys
import time

ROOT = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
SESS = os.path.join(ROOT, "Dai_Tang_Kinh", "daoanh", "docs", "sessions", "2026-10-26", "compliance-route")
REAL = os.path.join(ROOT, ".git", "index")
TMP = os.path.join(SESS, "wt_index_sync")
expect = sys.argv[1] if len(sys.argv) > 1 else "EMPTY"


def git(*args, idx=None):
    env = dict(os.environ)
    if idx:
        env["GIT_INDEX_FILE"] = idx
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, env=env)
    if r.returncode != 0:
        raise SystemExit("git %s rc=%s: %s" % (args, r.returncode, r.stderr.decode("utf-8", "replace")))
    return r.stdout.decode("utf-8", "replace").strip()


print("before:", repr(git("diff", "--cached", "--name-status")))
if os.path.exists(REAL + ".lock"):
    raise SystemExit("index.lock ton tai -> dung")
bak = os.path.join(SESS, "index.backup-%s" % time.strftime("%Y%m%d-%H%M%S"))
shutil.copy2(REAL, bak)
print("backup:", bak, os.path.getsize(bak))

if os.path.exists(TMP):
    os.remove(TMP)
git("read-tree", "HEAD", idx=TMP)
print("tmp index vs HEAD:", repr(git("diff", "--cached", "--name-status", idx=TMP)))
data = open(TMP, "rb").read()
with open(REAL, "r+b") as fh:
    fh.write(data)
    fh.truncate()
os.remove(TMP)
after = git("diff", "--cached", "--name-status")
print("after:", repr(after))
if expect == "EMPTY":
    assert after == "", "index that chua rong"
print("HEAD:", git("rev-parse", "HEAD"))
