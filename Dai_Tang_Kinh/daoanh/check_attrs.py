#!/usr/bin/env python3
"""Quick check: how many nexus blocks have each attribute."""

import os, re

NEXUS_SRC_DIR = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\dila_import\biographies.2024-01\nexus_src"

files = sorted([f for f in os.listdir(NEXUS_SRC_DIR) if f.endswith('.nexus.xml')])

for fname in files[:3]:  # Check first 3 files
    fpath = os.path.join(NEXUS_SRC_DIR, fname)
    with open(fpath, "rb") as fh:
        raw = fh.read()
    text = raw.decode("utf-8", errors="replace")
    
    # Count nexus blocks with each attribute pattern
    nexus_blocks = re.findall(r'<nexus[^>]*>(.*?)</nexus>', text, re.DOTALL)
    
    with_book = 0
    with_seq = 0
    with_from = 0
    with_to = 0
    with_id = 0
    
    for block in nexus_blocks:
        if re.search(r'book="[^"]+"', block):
            with_book += 1
        if re.search(r'seq="\d+"', block):
            with_seq += 1
        if re.search(r'from="[^"]+"', block):
            with_from += 1
        if re.search(r'to="[^"]+"', block):
            with_to += 1
        if re.search(r'id="[A-Z0-9]+"', block):
            with_id += 1
    
    total = len(nexus_blocks)
    print("%s: total=%d, with_book=%d (%d%%), with_seq=%d (%d%%), with_from=%d (%d%%), with_to=%d (%d%%), with_id=%d (%d%%)"
        % (fname, total, with_book, 100*with_book//total if total else 0,
           with_seq, 100*with_seq//total if total else 0,
           with_from, 100*with_from//total if total else 0,
           with_to, 100*with_to//total if total else 0,
           with_id, 100*with_id//total if total else 0))