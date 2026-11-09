import os
d = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\dila_import\biographies.2024-01"
if os.path.exists(d):
    print("exists", os.listdir(d)[:5])
else:
    print("not found", d)