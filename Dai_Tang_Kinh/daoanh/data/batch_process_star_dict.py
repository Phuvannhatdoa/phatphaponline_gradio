#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
batch_process_star_dict.py - QUICK VERSION
Xử lý nhanh 22 file .docx, lọc địa danh theo Bộ lọc kép

Author: Agent Build (2026-04-09)
"""

import os, re, json, glob
import docx

INPUT_DIR = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/dictionaries"
OUTPUT_FILE = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/processed/temples_master_v2.json"

PROVINCE_CODES = {
    "an giang": "VN-36", "bắc giang": "VN-20", "bắc kạn": "VN-05", "bạc liêu": "VN-55",
    "bắc ninh": "VN-20", "bến tre": "VN-50", "bình dương": "VN-58", "bình định": "VN-62",
    "bình phước": "VN-59", "bình thuận": "VN-60", "cà mau": "VN-56", "cần thơ": "VN-65",
    "cao bằng": "VN-04", "đà nẵng": "VN-48", "đắk lắk": "VN-68", "đắk nông": "VN-69",
    "điện biên": "VN-71", "đồng nai": "VN-39", "đồng tháp": "VN-45", "gia lai": "VN-70",
    "hà giang": "VN-02", "hà nam": "VN-36", "hà nội": "VN-01", "hà tĩnh": "VN-47",
    "hải dương": "VN-61", "hải phòng": "VN-31", "hậu giang": "VN-72", "hòa bình": "VN-17",
    "hồ chí minh": "VN-SG", "huế": "VN-26", "hưng yên": "VN-34", "khánh hòa": "VN-34",
    "kiên giang": "VN-67", "kon tum": "VN-74", "lai châu": "VN-12", "lạng sơn": "VN-13",
    "lào cai": "VN-10", "long an": "VN-41", "nam định": "VN-38", "nghệ an": "VN-40",
    "ninh bình": "VN-37", "ninh thuận": "VN-64", "phú thọ": "VN-44", "phú yên": "VN-63",
    "quảng bình": "VN-49", "quảng nam": "VN-49", "quảng ngãi": "VN-51", "quảng ninh": "VN-54",
    "quảng trị": "VN-52", "sóc trăng": "VN-55", "sơn la": "VN-14", "tây ninh": "VN-37",
    "thái bình": "VN-34", "thái nguyên": "VN-69", "thanh hóa": "VN-42", "thừa thiên": "VN-26",
    "tiền giang": "VN-46", "trà vinh": "VN-53", "tuyên quang": "VN-07", "vĩnh long": "VN-54",
    "vĩnh phúc": "VN-70", "yên bái": "VN-15", "nha trang": "VN-34"
}

NAME_START = ["chùa", "tịnh xá", "thiền viện", "tự", "am", "cốc", "quán", "trai", "viện"]
CONTEXT = ["tọa lạc", "ở tại", "thuộc tỉnh", "xây dựng", "núi", "thôn", "xã", "huyện", "tp.", "tỉnh"]

def detect_province(text):
    for p, c in PROVINCE_CODES.items():
        if p in text.lower(): return c
    return "VN-UN"

def is_temple(name):
    n = name.lower().strip()
    for kw in NAME_START:
        if n.startswith(kw): return True
    return False

def has_context(text):
    for kw in CONTEXT:
        if kw in text.lower(): return True
    return False

def norm(name):
    import unicodedata
    n = unicodedata.normalize('NFD', name)
    n = ''.join(c for c in n if unicodedata.category(c) != 'Mn')
    n = re.sub(r'[\s\-]+', '_', n).lower()
    return re.sub(r'[^\w_]', '', n)

# Main
print("🚀 BATCH PROCESSING STAR DICT")
print("=" * 50)

files = glob.glob(os.path.join(INPUT_DIR, "*.docx"))
print(f"📁 Files: {len(files)}")

temples = {}

for idx, fp in enumerate(files, 1):
    fname = os.path.basename(fp)
    print(f"[{idx}/{len(files)}] {fname[:40]}...", end=" ", flush=True)
    
    try:
        doc = docx.Document(fp)
        for para in doc.paragraphs:
            txt = para.text.strip()
            if not txt: continue
            
            # Split by tab
            if '\t' in txt:
                parts = txt.split('\t', 1)
                kw, val = parts[0].strip(), parts[1].strip() if len(parts) > 1 else txt
            else:
                kw, val = txt, txt
            
            # Filter
            if not is_temple(kw): continue
            if val != kw and not has_context(val): continue
            
            # Add
            n = norm(kw)
            if n not in temples:
                temples[n] = {
                    "nameVi": kw,
                    "province": detect_province(val),
                    "description": val,
                    "sources": [fname]
                }
            else:
                if fname not in temples[n]["sources"]:
                    temples[n]["sources"].append(fname)
        
        print("✓")
    except Exception as e:
        print(f"⚠️ {e}")

print(f"\n✅ Temples found: {len(temples)}")

# Assign IDs
results = []
province_counter = {}

for n, info in temples.items():
    prov = info["province"]
    province_counter[prov] = province_counter.get(prov, 0) + 1
    seq = province_counter[prov]
    
    typ = "Chua"
    nl = info["nameVi"].lower()
    if nl.startswith("am "): typ = "Am"
    elif nl.startswith("tự "): typ = "Tu"
    elif nl.startswith("viện "): typ = "Vien"
    
    pid = f"pth:{prov}_{seq:03d}_{typ}_{n}"
    
    # Province name
    pname = next((p.title() for p, c in PROVINCE_CODES.items() if c == prov), "Unknown")
    
    results.append({
        "id": pid,
        "nameVi": info["nameVi"],
        "type": typ,
        "province": prov,
        "provinceName": pname,
        "description": info["description"],
        "sources": info["sources"],
        "lat": "",
        "lon": "",
        "status": "pending",
        "sameAs": []
    })

# Save
output = {"version": "v2.2-Batch", "generated": "2026-04-09", "total": len(results), "temples": results}

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"📄 Saved: {OUTPUT_FILE}")
print("=" * 50)