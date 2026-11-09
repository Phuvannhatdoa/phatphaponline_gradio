"""Commit 2 file (app.py, index.html) dựng từ blob HEAD + khối DILA — KHÔNG nuốt WIP.
Index tạm riêng (GIT_INDEX_FILE trong gate0/), không đụng .git/index thật.
CAS thủ công lên file ref (không update-ref, không os.replace).
usage: python commit_dila.py            (mặc định: thực hiện commit)
       python commit_dila.py --dry-run  (chỉ dựng index tạm + kiểm, không commit)
"""
import os, subprocess, sys

DRY = "--dry-run" in sys.argv
BRANCH = "truyen-dang-the-pho-clean"
PREFIX = "Dai_Tang_Kinh/daoanh/"
GATE = os.path.join("Dai_Tang_Kinh", "daoanh", "docs", "sessions", "2026-10-26", "gate0")  # tương đối gốc repo
MSG = "fix: khoi phuc phan DILA tren HOME (route dila_works + search keys + index.html) (T453 Gate 0) + docs"

root = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True).stdout.strip()
os.chdir(root)
IDX = os.path.abspath(os.path.join(GATE, "wt_index"))
ENV = dict(os.environ, GIT_INDEX_FILE=IDX)


def git(*args, env=None):
    r = subprocess.run(["git", *args], capture_output=True, env=env)
    if r.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {r.stderr.decode('utf-8', 'replace')}")
    return r.stdout.decode("utf-8", "replace").strip()


def rb(p):
    with open(p, "rb") as f:
        return f.read()


parent = git("rev-parse", "HEAD")
print("PARENT", parent)

# 1) Kiểm: blob HEAD còn đúng bản đã dùng để dựng khối (HEAD không đổi).
head_app = subprocess.run(["git", "show", f"{parent}:{PREFIX}app.py"], capture_output=True, check=True).stdout
head_idx = subprocess.run(["git", "show", f"{parent}:{PREFIX}index.html"], capture_output=True, check=True).stdout
assert head_app == rb(os.path.join(GATE, "app_head_ref.py")), "HEAD app.py đã đổi — dựng lại trước"
assert head_idx == rb(os.path.join(GATE, "index_head_ref.html")), "HEAD index.html đã đổi — dựng lại trước"

# 2) Blob mới (LF, không filter).
blob_app = git("hash-object", "-w", os.path.join(GATE, "app_head_new.py"))
blob_idx = git("hash-object", "-w", os.path.join(GATE, "index_head_new.html"))
print("BLOB_APP", blob_app)
print("BLOB_INDEX", blob_idx)

# 3) Index tạm = HEAD + 2 blob.
if os.path.exists(IDX):
    os.remove(IDX)
git("read-tree", parent, env=ENV)
git("update-index", "--add", "--cacheinfo", f"100644,{blob_app},{PREFIX}app.py", env=ENV)
git("update-index", "--add", "--cacheinfo", f"100644,{blob_idx},{PREFIX}index.html", env=ENV)

# 4) Xác minh index tạm.
ns = git("diff", "--cached", "--name-status", env=ENV)
print("NAME-STATUS:\n" + ns)
expect = f"M\t{PREFIX}app.py\nM\t{PREFIX}index.html"
assert ns == expect, f"name-status lệch:\n{ns}"
print("NUMSTAT:\n" + git("diff", "--cached", "--numstat", env=ENV))

# 5) Không được có WIP của phiên khác lọt vào diff.
diff_txt = git("diff", "--cached", "-U0", env=ENV)
added = [l[1:] for l in diff_txt.split("\n") if l.startswith("+") and not l.startswith("+++")]
for bad in ["codex_place_name", "ai_place_name", "_lexicon_han_lookup", "/daoanh/api/admin/backup",
            "api_monk_ancestor_spine", "is_primary"]:
    hits = [l for l in added if bad in l]
    assert not hits, f"WIP lọt vào diff ({bad}): {hits[:2]}"
print("WIP-marker check: OK (không có token WIP)")

if DRY:
    print("DRY-RUN: dừng trước khi commit.")
    os.remove(IDX)
    raise SystemExit(0)

# 6) Tree + commit object.
tree = git("write-tree", env=ENV)
chk = git("diff-tree", "--name-status", "-r", parent, tree)
print("DIFF-TREE:\n" + chk)
assert chk == expect.replace("\t", "\t"), f"diff-tree lệch:\n{chk}"
new = git("commit-tree", tree, "-p", parent, "-m", MSG)
print("NEW", new)

# 7) CAS thủ công lên file ref.
ref = os.path.join(".git", "refs", "heads", BRANCH)
cur = open(ref, encoding="ascii").read().strip()
if cur != parent:
    raise SystemExit(f"CAS FAIL: ref={cur} != parent={parent} — KHÔNG ghi; chạy lại từ đầu")
with open(ref, "w", encoding="ascii", newline="") as f:
    f.write(new + "\n")

os.remove(IDX)
print("HEAD after:", git("rev-parse", "HEAD"))
