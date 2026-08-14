#!/usr/bin/env python3
"""
Download Marcus SNA .gexf file from GitHub
Download: Historical Social Network of Chinese Buddhism v2021-06
"""
import os
import urllib.request
import sys

REPO_URL = "https://raw.githubusercontent.com/mbingenheimer/ChineseBuddhism_SNA/main"
GEXF_FILE = "CB_HSNA_2021-06.gexf"
DATA_DIR = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/chinese_buddhism_sna"

def download_gexf():
    os.makedirs(DATA_DIR, exist_ok=True)
    url = f"{REPO_URL}/{GEXF_FILE}"
    output_path = os.path.join(DATA_DIR, GEXF_FILE)
    
    if os.path.exists(output_path):
        size = os.path.getsize(output_path)
        if size > 20_000_000:
            print(f"✓ File already exists ({size:,} bytes)")
            return output_path
    
    print(f"Downloading {GEXF_FILE}...")
    try:
        urllib.request.urlretrieve(url, output_path)
        size = os.path.getsize(output_path)
        print(f"✓ Downloaded {size:,} bytes")
        return output_path
    except Exception as e:
        print(f"Lỗi download: {e}")
        return None

if __name__ == "__main__":
    result = download_gexf()
    print(f"Output: {result}")