import difflib, os
os.chdir(r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\docs\sessions\2026-10-26\task-id-merge\backup")
names = ["T432-places-districts-claude-analysis.md", "T433-places-districts-claude-import.md", "T434-places-districts-gemini-batch.md"]
for n in names:
    wt = open(n, encoding="utf-8").read().splitlines()
    hd = open(n + ".HEAD", encoding="utf-8").read().splitlines()
    print("=====", n)
    for l in difflib.unified_diff(hd, wt, "HEAD", "WORKTREE", lineterm="", n=0):
        print(l)
