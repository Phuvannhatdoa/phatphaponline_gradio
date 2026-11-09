import os
root = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh"
for dirpath, dirs, files in os.walk(root):
    for f in files:
        if 'bio' in f.lower() or 'biography' in f.lower():
            print(os.path.join(dirpath, f))