"""Đồng bộ .git/index thật về HEAD: backup trước, rồi ghi byte index tạm (read-tree HEAD) vào index thật bằng r+b + truncate."""
import os
import shutil
import subprocess
import sys

REPO = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DIR = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(DIR, "wt_tmp_index")
sys.stdout.reconfigure(encoding="utf-8")


def git(*args, env=None):
    r = subprocess.run(["git", *args], cwd=REPO, env=env, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SystemExit("git %s failed: %s" % (" ".join(args), r.stderr.strip()))
    return r.stdout


real = os.path.join(REPO, git("rev-parse", "--git-path", "index").strip())
shutil.copy2(real, os.path.join(DIR, "index.bak"))
print("backup:", os.path.getsize(os.path.join(DIR, "index.bak")), "bytes")

if os.path.exists(TMP):
    os.remove(TMP)
env = dict(os.environ, GIT_INDEX_FILE=TMP)
git("read-tree", "HEAD", env=env)
data = open(TMP, "rb").read()
with open(real, "r+b") as f:
    f.write(data)
    f.truncate()
os.remove(TMP)
print("synced index bytes:", len(data))
print("HEAD", git("rev-parse", "HEAD").strip())
print("cached diff:", repr(git("diff", "--cached", "--name-status")))
