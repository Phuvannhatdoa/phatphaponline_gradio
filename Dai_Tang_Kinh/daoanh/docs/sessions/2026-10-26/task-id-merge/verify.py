import subprocess, difflib, os
ROOT = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
os.chdir(ROOT)
def git(*a):
    return subprocess.run(["git", *a], capture_output=True).stdout
print("HEAD", git("rev-parse", "HEAD").decode().strip())
pairs = [
 ("Dai_Tang_Kinh/daoanh/tasks/T432-places-districts-claude-analysis.md", "Dai_Tang_Kinh/daoanh/tasks/T442-places-districts-claude-analysis.md"),
 ("Dai_Tang_Kinh/daoanh/tasks/T433-places-districts-claude-import.md", "Dai_Tang_Kinh/daoanh/tasks/T443-places-districts-claude-import.md"),
 ("Dai_Tang_Kinh/daoanh/tasks/T434-places-districts-gemini-batch.md", "Dai_Tang_Kinh/daoanh/tasks/T444-places-districts-gemini-batch.md"),
]
for old, new in pairs:
    ob = git("show", "HEAD:" + old).decode("utf-8")
    nb = open(new, encoding="utf-8").read()
    ol = ob.splitlines(); nl = nb.splitlines()
    only_old = [l for l in ol if l.strip() and l not in nl]
    print("=====", old, "->", new, "old lines", len(ol), "new lines", len(nl))
    print("tracked in HEAD: old blob len", len(ob))
    print("--- dòng chỉ có ở bản CŨ (không có trong bản mới):", len(only_old))
    for l in only_old:
        print("  OLD-ONLY:", l)
    print("--- diff (new vs old), 60 dòng đầu:")
    d = list(difflib.unified_diff(ol, nl, "old", "new", lineterm="", n=0))
    print("\n".join(d[:60]))
print("status cached:", git("diff", "--cached", "--name-status").decode())
