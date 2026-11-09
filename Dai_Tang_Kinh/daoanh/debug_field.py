import os, re

NEXUS_SRC_DIR = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\dila_import\biographies.2024-01\nexus_src"
files = sorted([f for f in os.listdir(NEXUS_SRC_DIR) if f.endswith('.nexus.xml')])

fname = files[0]
fpath = os.path.join(NEXUS_SRC_DIR, fname)
with open(fpath, "rb") as fh:
    raw = fh.read()
text = raw.decode("utf-8", errors="replace")

root_book = re.search(r'book="([^"]+)"', text.split("<nexus")[0] if "<nexus" in text else text)
book = root_book.group(1) if root_book else None

m = __import__('re').finditer(r'<nexus[^>]*>.*?</nexus>', text, re.DOTALL)
first = next(m).group()
print("First nexus first 300 chars: %s" % first[:300])

id_m = re.search(r'id="([^"]+)"', first)
seq_m = re.search(r'seq="(\d+)"', first)
from_m = re.search(r'from="([^"]+)"', first)
to_m = re.search(r'to="([^"]+)"', first)
pers = re.findall(r'<person id="([A-Z0-9]+)"', first)
place = re.findall(r'<place id="([A-Z0-9]+)"', first)
text_zh_m = re.search(r'<text_zh>(.*?)</text_zh>', first, re.DOTALL)
jd_from = re.findall(r'jd_from="(\d{7})"', first)
jd_to = re.findall(r'jd_to="(\d{7})"', first)

print("id: %s" % (id_m.group(1) if id_m else None))
print("seq: %s" % (seq_m.group(1) if seq_m else None))
print("from: %s" % (from_m.group(1) if from_m else None))
print("to: %s" % (to_m.group(1) if to_m else None))
print("persons: %s" % pers[:3])
print("places: %s" % place[:3])
print("text_zh present: %s" % (text_zh_m is not None))
if text_zh_m:
    txt = text_zh_m.group(1)
    print("text_zh first 40: %s" % (txt[:40]))
print("jd_from: %s" % str(jd_from[:1]))
print("jd_to: %s" % str(jd_to[:1]))