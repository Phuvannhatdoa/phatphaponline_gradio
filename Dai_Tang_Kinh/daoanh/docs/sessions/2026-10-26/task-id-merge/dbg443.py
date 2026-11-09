import subprocess, os, hashlib
ROOT = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
os.chdir(ROOT)
TMPIDX = os.path.join(ROOT, r"Dai_Tang_Kinh\daoanh\docs\sessions\2026-10-26\task-id-merge\tmp.index")
env = dict(os.environ, GIT_INDEX_FILE=TMPIDX)
P = "Dai_Tang_Kinh/daoanh/tasks/T443-places-districts-claude-import.md"
def g(*a, e=None):
    r = subprocess.run(["git", *a], capture_output=True, env=e)
    return r.stdout.decode("utf-8", "replace") + r.stderr.decode("utf-8", "replace")
print("HEAD ls-tree:", g("ls-tree", "HEAD", "--", P))
print("tmp ls-files:", g("ls-files", "-s", "--", P, e=env))
print("real index ls-files:", g("ls-files", "-s", "--", P))
print("hash worktree:", g("hash-object", "--", P))
print("check-ignore:", g("check-ignore", "-v", P))
print("attr:", g("check-attr", "-a", "--", P))
print("ls-files -v real (flags):", g("ls-files", "-v", "--", P))
print("ls-files -v tmp:", g("ls-files", "-v", "--", P, e=env))
