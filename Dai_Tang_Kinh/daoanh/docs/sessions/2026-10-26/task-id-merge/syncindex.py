import subprocess, os, sys
ROOT = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
os.chdir(ROOT)
SESS = os.path.join(ROOT, r"Dai_Tang_Kinh\daoanh\docs\sessions\2026-10-26\task-id-merge")
TMPIDX = os.path.join(SESS, "tmp.index")
REALIDX = os.path.join(ROOT, r".git\index")
BAK = os.path.join(SESS, "index.bak")
tmp_bytes = open(TMPIDX, "rb").read()
real_bytes = open(REALIDX, "rb").read()
open(BAK, "wb").write(real_bytes)
print("backup index bytes", len(real_bytes), "tmp bytes", len(tmp_bytes))
with open(REALIDX, "r+b") as f:
    f.write(tmp_bytes)
    f.truncate(len(tmp_bytes))
print("real index now", os.path.getsize(REALIDX))
r = subprocess.run(["git", "diff", "--cached", "--name-status"], capture_output=True)
print("cached after sync (must be empty):", repr(r.stdout.decode("utf-8", "replace")), "rc", r.returncode)
print("HEAD", subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True).stdout.decode().strip())
