#!/usr/bin/env python3
"""Check attribute presence across all files."""

import os, re

NEXUS_SRC_DIR = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\dila_import\biographies.2024-01\nexus_src"

files = sorted([f for f in os.listdir(NEXUS_SRC_DIR) if f.endswith('.nexus.xml')])

# Check root element book attribute
for fname in files:
    fpath = os.path.join(NEXUS_SRC_DIR, fname)
    with open(fpath, "rb") as fh:
        raw = fh.read()
    text = raw.decode("utf-8", errors="replace")
    
    # Get book from root
    root_book = re.search(r'book="([^"]+)"', text.split("<nexus")[0] if "<nexus" in text else text)
    
    # Check nexus blocks for seq, from, to
    nexus_blocks = re.findall(r'<nexus[^>]*>(.*?)</nexus>', text, re.DOTALL)
    
    with_seq = sum(1 for b in nexus_blocks if re.search(r'seq="\d+"', b))
    with_from = sum(1 for b in nexus_blocks if re.search(r'from="[^"]+"', b))
    with_to = sum(1 for b in nexus_blocks if re.search(r'to="[^"]+"', b))
    
    print("%s: root_book=%s, total_nexus=%d, with_seq=%d (%), with_from=%d (%), with_to=%d (%), with_id=100%%"
        % (fname, root_book.group(1) if root_book else None, len(nexus_blocks), with_seq, 100*with_seq//len(nexus_blocks) if nexus_blocks else 0, with_from, 100*with_from//len(nexus_blocks) if nexus_blocks else 0, with_to, 100*with_to//len(nexus_blocks) if nexus_blocks else 0))