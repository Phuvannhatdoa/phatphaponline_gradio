import os, re

NEXUS_SRC_DIR = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\dila_import\biographies.2024-01\nexus_src"
fname = "biQiuNi.nexus.xml"
fpath = os.path.join(NEXUS_SRC_DIR, fname)
with open(fpath, "rb") as fh:
    raw = fh.read()
text = raw.decode("utf-8", errors="replace")

blocks = re.findall(r"<nexus[^>]*>(.*?)</nexus>", text, re.DOTALL)
print("File: %s, Total nexus blocks: %d" % (fname, len(blocks)))
for i, block in enumerate(blocks[:1]):
    # Print first 200 chars as raw bytes hex to avoid encoding issues
    block_bytes = block[:200].encode("utf-8", errors="replace")
    print("Block %d first 200 bytes hex: %s" % (i+1, block_bytes.hex()))
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

    print("  book: %s" % (b_match.group(1) if b_match else None))
    print("  id: %s" % (id_match.group(1) if id_match else None))
    print("  seq: %s" % (seq_match.group(1) if seq_match else None))
    print("  from: %s" % (from_match.group(1) if from_match else None))
    print("  to: %s" % (to_match.group(1) if to_match else None))
    print("  text_zh present: %s" % (text_match is not None))
    if text_match:
        txt = text_match.group(1)
        print("  text_zh first 80: %s" % (txt[:80]))
    print("  persons: %s" % (pers[:3]))
    print("  places: %s" % (place[:3]))
    print("  jd_from: %s" % (jd_from[:3]))
    print("  jd_to: %s" % (jd_to[:3]))