import subprocess, os, sys
os.chdir(r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app")
files = sys.argv[1:]
for p in files:
    head = subprocess.run(["git", "show", "HEAD:Dai_Tang_Kinh/daoanh/" + p], capture_output=True).stdout
    wt = open("Dai_Tang_Kinh/daoanh/" + p, "rb").read()
    print(("CLEAN " if head == wt else "WIP   ") + p, len(head), len(wt))
