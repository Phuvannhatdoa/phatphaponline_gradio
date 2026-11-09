import os
d = r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\dila_import\biographies.2024-01\nexus_src'
f = 'biQiuNi.nexus.xml'
path = os.path.join(d, f)
with open(path, 'r', encoding='utf-8') as fh:
    text = fh.read()
# find first nexus element
import re
nexus = re.search(r'<nexus[^>]+>', text)
if nexus:
    print('First nexus start:', nexus.start(), 'end:', nexus.end())
    print('Attributes:', re.findall(r'(\w+)=",', text[nexus.start():nexus.end()+200]))
    # print inner content up to </nexus>
    close = text.find('</nexus>', nexus.start())
    if close > 0:
        print('First nexus full:', text[nexus.start():close+8])