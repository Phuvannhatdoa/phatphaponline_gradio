import subprocess, os, sys
ROOT = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
os.chdir(ROOT)
TMPIDX = os.path.join(ROOT, r"Dai_Tang_Kinh\daoanh\docs\sessions\2026-10-26\task-id-merge\tmp.index")
env = dict(os.environ, GIT_INDEX_FILE=TMPIDX)
D = "Dai_Tang_Kinh/daoanh/"
EXPECT = {
 "D\t" + D + "tasks/T432-places-districts-claude-analysis.md",
 "D\t" + D + "tasks/T433-places-districts-claude-import.md",
 "D\t" + D + "tasks/T434-places-districts-gemini-batch.md",
 "A\t" + D + "tasks/T442-places-districts-claude-analysis.md",
 "A\t" + D + "tasks/T444-places-districts-gemini-batch.md",
 "M\t" + D + "docs/Handoff-2026-10-20-places-gemini.md",
}
def g(*a, e=None, check=True):
    r = subprocess.run(["git", *a], capture_output=True, env=e)
    out = r.stdout.decode("utf-8", "replace")
    if check and r.returncode != 0:
        sys.exit("FAIL git " + " ".join(a) + " :: " + r.stderr.decode("utf-8", "replace"))
    return out

parent_now = g("rev-parse", "HEAD").strip()
parent_idx = open(os.path.join(ROOT, r"Dai_Tang_Kinh\daoanh\docs\sessions\2026-10-26\task-id-merge\parent.txt")).read().strip()
print("parent_now", parent_now, "parent_idx", parent_idx)
if parent_now != parent_idx:
    sys.exit("HEAD moved; rebuild index")
ns = g("diff", "--cached", "--no-renames", "--name-status", e=env)
got = set(l.replace(" ", "\t") if False else l for l in ns.splitlines() if l.strip())
print("CACHED (no-renames):")
print(ns)
if got != EXPECT:
    print("MISMATCH. extra:", got - EXPECT, "missing:", EXPECT - got)
    sys.exit(2)
print("NAME-STATUS MATCH EXPECT")
tree = g("write-tree", e=env).strip()
print("TREE", tree)
msg = "chore: gop 3 task trung ID (T432/T433/T434 -> T442/T443/T444, former_ids giu nguyen) + docs"
new = g("commit-tree", tree, "-p", parent_now, "-m", msg).strip()
print("NEW", new)
ref_path = os.path.join(ROOT, r".git\refs\heads\truyen-dang-the-pho-clean")
sym = g("symbolic-ref", "HEAD").strip()
print("symbolic HEAD", sym)
cur = open(ref_path).read().strip()
print("ref file", cur)
if cur != parent_now:
    sys.exit("CAS FAIL: ref != parent")
open(ref_path, "w").write(new + "\n")
print("REF WRITTEN")
print("rev-parse HEAD =", g("rev-parse", "HEAD").strip())
open(os.path.join(ROOT, r"Dai_Tang_Kinh\daoanh\docs\sessions\2026-10-26\task-id-merge\new.txt"), "w").write(new + "\n")
