import subprocess, os, shutil
ROOT = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
os.chdir(ROOT)
BK = "Dai_Tang_Kinh/daoanh/docs/sessions/2026-10-26/task-id-merge/backup"
os.makedirs(BK, exist_ok=True)
olds = [
 "Dai_Tang_Kinh/daoanh/tasks/T432-places-districts-claude-analysis.md",
 "Dai_Tang_Kinh/daoanh/tasks/T433-places-districts-claude-import.md",
 "Dai_Tang_Kinh/daoanh/tasks/T434-places-districts-gemini-batch.md",
]
for p in olds:
    name = os.path.basename(p)
    # sao lưu: nội dung worktree + blob HEAD (để chắc chắn)
    raw = open(p, "rb").read()
    head = subprocess.run(["git", "show", "HEAD:" + p], capture_output=True).stdout
    with open(os.path.join(BK, name), "wb") as f:
        f.write(raw)
    with open(os.path.join(BK, name + ".HEAD"), "wb") as f:
        f.write(head)
    print("backup", name, len(raw), "worktree==HEAD:", raw == head)
for p in olds:
    os.remove(p)
    print("removed", p, os.path.exists(p))
