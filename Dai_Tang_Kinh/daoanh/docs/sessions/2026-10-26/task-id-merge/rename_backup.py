import os
BK = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\docs\sessions\2026-10-26\task-id-merge\backup"
for n in os.listdir(BK):
    if n.endswith(".md"):
        os.rename(os.path.join(BK, n), os.path.join(BK, n + ".txt"))
        print("renamed", n, "->", n + ".txt")
print(sorted(os.listdir(BK)))
