import tarfile, os, shutil

tar_path = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\dila_import\biographies.2024-01\biographies-4e82453.tar.gz"
extract_to = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\dila_import\biographies.2024-01\biographies-master"

# Extract if not exists
if not os.path.exists(extract_to):
    os.makedirs(extract_to, exist_ok=True)
    with tarfile.open(tar_path, 'r:gz') as tar:
        tar.extractall(extract_to)
    print("Extracted successfully")
else:
    print("Already extracted")

# List top-level dirs
for d in sorted(os.listdir(extract_to)):
    if os.path.isdir(os.path.join(extract_to, d)):
        files = [f for f in os.listdir(os.path.join(extract_to, d)) if f.endswith('.xml')]
        print(f"{d}: {len(files)} XML files")