import os, re

NEXUS_SRC_DIR = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\dila_import\biographies.2024-01\nexus_src"
fname = "biQiuNi.nexus.xml"
fpath = os.path.join(NEXUS_SRC_DIR, fname)
with open(fpath, "rb") as fh:
    raw = fh.read()
text = raw.decode("utf-8", errors="replace")

blocks = re.findall(r"<nexus[^>]*>(.*?)</nexus>", text, re.DOTALL)
print(f"File: {fname}, Total nexus blocks: {len(blocks)}")
for i, block in enumerate(blocks[:1]):
    print(f"Block {i+1} first 200 chars repr: {repr(block[:200])}")
    b_match = re.search(r'book="([^"]+)"', block)
    id_match = re.search(r'id="([^"]+)"', block)
    seq_match = re.search(r'seq="(\d+)"', block)
    from_match = re.search(r'from="([^"]+)"', block)
    to_match = re.search(r'to="([^"]+)"', block)
    text_match = re.search(r"<text_zh>(.*?)</text_zh>", block, re.DOTALL)
    pers = re.findall(r"<person id=\"([A-Z0-9]+)\"", block)
    place = re.findall(r"<place id=\"([A-Z0-9]+)\"", block)
    jd_from = re.findall(r"jd_from=\"(\d{7})\"", block)
    jd_to = re.findall(r"jd_to=\"(\d{7})\"", block)

    print(f"  book: {b_match.group(1) if b_match else None}")
    print(f"  id: {id_match.group(1) if id_match else None}")
    print(f"  seq: {seq_match.group(1) if seq_match else None}")
    print(f"  from: {from_match.group(1) if from_match else None}")
    print(f"  to: {to_match.group(1) if to_match else None}")
    print(f"  text_zh present: {text_match is not None}")
    if text_match:
        txt = text_match.group(1)
        print(f"  text_zh first 80: {txt[:80]}")
    print(f"  persons: {pers[:3]}")
    print(f"  places: {place[:3]}")
    print(f"  jd_from: {jd_from[:3]}")
    print(f"  jd_to: {jd_to[:3]}")