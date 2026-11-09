#!/usr/bin/env python3
"""Check attribute presence across all files."""

import os, re

NEXUS_SRC_DIR = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\dila_import\biographies.2024-01\nexus_src"

files = sorted([f for f in os.listdir(NEXUS_SRC_DIR) if f.endswith('.nexus.xml')])

for fname in files:
    fpath = os.path.join(NEXUS_SRC_DIR, fname)
    with open(fpath, "rb") as fh:
        raw = fh.read()
    text = raw.decode("utf-8", errors="replace")
    
    root_book = re.search(r'book="([^"]+)"', text.split("<nexus")[0] if "<nexus" in text else text)
    
    nexus_blocks = re.findall(r'<nexus[^>]*>(.*?)</nexus>', text, re.DOTALL)
    
    with_seq = sum(1 for b in nexus_blocks if re.search(r'seq="\d+"', b))
    with_from = sum(1 for b in nexus_blocks if re.search(r'from="[^"]+"', b))
    with_to = sum(1 for b in nexus_blocks if re.search(r'to="[^"]+"', b))
    
    total = len(nexus_blocks)
    pct_seq = 100 * with_seq / total if total else 0
    pct_from = 100 * with_from / total if total else 0
    pct_to = 100 * with_to / total if total else 0
    
    rb = root_book.group(1) if root_book else None
    print("%s: root_book=%s, total=%d, with_seq=%d (%.1%%), with_from=%d (%.1%%), with_to=%d (%.1%%)"
        % (fname, rb, total, with_seq, pct_seq, with_from, pct_from, with_to, pct_to))