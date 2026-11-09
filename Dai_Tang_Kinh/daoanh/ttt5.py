import tarfile, os

tar_path = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\dila_import\biographies.2024-01\biographies-4e82453.tar.gz"
# Extract to temp
extract_to = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\dila_import\biographies.2024-01\extracted"

if os.path.exists(extract_to):
    import shutil
    shutil.rmtree(extract_to)

os.makedirs(extract_to, exist_ok=True)
with tarfile.open(tar_path, 'r:gz') as tar:
    tar.extractall(extract_to)

# List structure
root = extract_to
for dirpath, dirs, files in os.walk(root):
    dirs.sort()
    level = dirpath.replace(root, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f'{indent}{os.path.basename(dirpath)}/')
    subindent = ' ' * 2 * (level + 1)
    for f in sorted(files)[:3]:
        print(f'{subindent}{f}')
    if level > 3:
        break