import os
d = r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\dila_import\biographies.2024-01\extracted'
for root, dirs, files in os.walk(d):
    for f in files[:1]:
        path = os.path.join(root, f)
        print('File:', path)
        with open(path, 'rb') as fh:
            head = fh.read(200)
        print('Header:', head[:100])
        print('Ext:', f.split('.')[-1] if '.' in f else 'no ext')
    break