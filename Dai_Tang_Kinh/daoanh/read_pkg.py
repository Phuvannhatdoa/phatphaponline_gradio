import json
with open('E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\package.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
for k in data:
    if 'test' in k.lower() or 'lint' in k.lower() or 'e2e' in k.lower() or 'run' in k.lower():
        print(k + ': ' + str(data[k]))
"