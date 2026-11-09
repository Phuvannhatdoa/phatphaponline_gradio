with open(r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\core.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

import re
for m in re.finditer(r'def _t158_neighbors_consensus', content):
    pos = m.start()
    snippet = content[pos:pos+3000]
    with open('t158_func.txt', 'w', encoding='utf-8') as out:
        out.write(snippet)
    break