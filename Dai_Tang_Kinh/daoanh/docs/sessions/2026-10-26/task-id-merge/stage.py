import subprocess, os, sys
ROOT = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
os.chdir(ROOT)
TMPIDX = os.path.join(ROOT, r"Dai_Tang_Kinh\daoanh\docs\sessions\2026-10-26\task-id-merge\tmp.index")
env = dict(os.environ, GIT_INDEX_FILE=TMPIDX)
D = "Dai_Tang_Kinh/daoanh/"

def g(*a, check=True):
    r = subprocess.run(["git", *a], capture_output=True, env=env)
    out = r.stdout.decode("utf-8", "replace")
    err = r.stderr.decode("utf-8", "replace")
    print(">>", " ".join(a), "rc=", r.returncode, "err=", err.strip()[:300])
    if check and r.returncode != 0:
        sys.exit("FAIL " + " ".join(a))
    return out

if os.path.exists(TMPIDX):
    os.remove(TMPIDX)
parent = g("rev-parse", "HEAD").strip()
print("PARENT", parent)
g("read-tree", parent)
for old in ["T432-places-districts-claude-analysis.md", "T433-places-districts-claude-import.md", "T434-places-districts-gemini-batch.md"]:
    g("update-index", "--force-remove", D + "tasks/" + old)
for p in [D + "tasks/T442-places-districts-claude-analysis.md",
          D + "tasks/T443-places-districts-claude-import.md",
          D + "tasks/T444-places-districts-gemini-batch.md",
          D + "docs/Handoff-2026-10-20-places-gemini.md"]:
    g("add", "--", p)
print("=== CACHED NAME-STATUS ===")
print(g("diff", "--cached", "--name-status"))
print("=== CACHED NUMSTAT ===")
print(g("diff", "--cached", "--numstat"))
