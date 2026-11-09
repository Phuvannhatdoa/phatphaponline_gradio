import os, subprocess, shutil

ROOT = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
BATCH = os.path.join(ROOT, "Dai_Tang_Kinh", "daoanh", "docs", "sessions", "2026-10-26", "docs-batch")
os.makedirs(BATCH, exist_ok=True)
os.chdir(ROOT)


def git(args, env=None):
    e = os.environ.copy()
    if env:
        e.update(env)
    r = subprocess.run(["git"] + args, capture_output=True, env=e)
    return r.returncode, r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")


# 1. baseline index diff
rc, out, err = git(["diff", "--cached", "--name-status"])
with open(os.path.join(BATCH, "pre-index.txt"), "w", encoding="utf-8", newline="\n") as f:
    f.write(out)
assert os.path.exists(os.path.join(BATCH, "pre-index.txt"))
print("PRE-INDEX:\n" + out)

# 2. temp index from HEAD
tmp = os.path.join(BATCH, "step0.index")
env = {"GIT_INDEX_FILE": tmp}
rc, out, err = git(["read-tree", "HEAD"], env)
print("read-tree rc", rc, err)
assert rc == 0 and os.path.exists(tmp)

# 3. backup real index bytes
shutil.copyfile(os.path.join(ROOT, ".git", "index"), os.path.join(BATCH, "index.before.bak"))
assert os.path.getsize(os.path.join(BATCH, "index.before.bak")) == os.path.getsize(os.path.join(ROOT, ".git", "index"))

# 4. write temp index bytes into real index in place
with open(tmp, "rb") as f:
    data = f.read()
with open(os.path.join(ROOT, ".git", "index"), "r+b") as f:
    f.write(data)
    f.truncate(len(data))
print("index written bytes", len(data))

# 5. verify
rc, out, err = git(["diff", "--cached", "--name-status"])
print("POST diff --cached:", repr(out))
rc2, head, _ = git(["rev-parse", "HEAD"])
print("HEAD", head.strip())
os.remove(tmp)
print("tmp removed")
