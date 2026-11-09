import os
agents_dir = r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\.opencode\agents'
print('Agents dir exists:', os.path.exists(agents_dir))
if os.path.exists(agents_dir):
    files = os.listdir(agents_dir)
    print('Files:', files)
    for f in files:
        if 'tester' in f.lower():
            fpath = os.path.join(agents_dir, f)
            print(f'--- {f} ---')
            with open(fpath, 'r', encoding='utf-8') as fh:
                content = fh.read()
                # Print first 500 chars
                print(content[:500])
"