import tarfile, os
tar_path = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\dila_import\biographies.2024-01\biographies-4e82453.tar.gz"
with tarfile.open(tar_path, 'r:gz') as tar:
    members = tar.getmembers()
    for m in sorted(members, key=lambda x: x.name)[:30]:
        print(m.name, m.size)
    print(f"Total: {len(members)} files")