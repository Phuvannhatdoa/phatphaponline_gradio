import os, re

NEXUS_SRC_DIR = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\dila_import\biographies.2024-01\nexus_src"
files = sorted([f for f in os.listdir(NEXUS_SRC_DIR) if f.endswith('.nexus.xml')])

for fname in files[:3]:
    fpath = os.path.join(NEXUS_SRC_DIR, fname)
    with open(fpath, "rb") as fh:
        raw = fh.read()
    text = raw.decode("utf-8", errors="replace")
    
    stem = fname.replace('.nexus.xml', '')
    id_matches = re.findall(r'id="([^"]+)"', text)
    
    prefixes = set()
    for id_val in id_matches[:10]:
        prefix = id_val.split('/')[0].split('#')[0].split('.')[0]
        prefixes.add(prefix)
    
    print("%s: stem=%s, nexus_id prefixes (first 10): %s" % (fname, stem, list(prefixes)[:5]))