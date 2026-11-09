import os
d = r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\dila_import\biographies.2024-01\nexus_src'
f = 'biQiuNi.nexus.xml'
path = os.path.join(d, f)
with open(path, 'rb') as fh:
    content = fh.read()
    print('Size:', len(content))
    # Try to decode
    try:
        text = content.decode('utf-8')
        print('First 500 chars:', text[:500])
    except:
        print('First 200 bytes hex:', content[:200].hex())