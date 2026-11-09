import os
d = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\dila_import\biographies.2024-01\nexus_src"
if os.path.exists(d):
    files = os.listdir(d)
    print(f"nexus_src has {len(files)} files")
    print("First 5:", files[:5])
else:
    print("not found")