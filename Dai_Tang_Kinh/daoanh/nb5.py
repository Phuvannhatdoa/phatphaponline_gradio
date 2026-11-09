import os
d = r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\dila_import\biographies.2024-01\nexus_src'
f = 'biQiuNi.nexus.xml'
path = os.path.join(d, f)
with open(path, 'rb') as fh:
    data = fh.read()
print('Size:', len(data))
print('First 500 bytes:', data[:500])