#!/usr/bin/env python3
"""
Check Missing Vietnamese Labels in TTL files
Scans /data/ttl/old/*.ttl for missing skos:prefLabel or rdfs:label@vi
"""
import os
import re
import glob
from collections import defaultdict

TTL_DIR = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/ttl/old"
OUTPUT_LOG = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/chinese_buddhism_sna/missing_vi_labels.log"

def scan_ttl_file(filepath):
    """Scan a single TTL file for labels"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    missing = []
    found_vi = []
    found_other = []
    
    vi_pattern = r'rdfs:label\s+"([^"]+)"@vi'
    other_pattern = r'rdfs:label\s+"([^"]+)"(?!@vi)'
    
    for match in re.finditer(vi_pattern, content):
        found_vi.append(match.group(1))
    
    for match in re.finditer(other_pattern, content):
        found_other.append(match.group(1))
    
    if not found_vi:
        if found_other:
            missing.append({
                "file": os.path.basename(filepath),
                "issue": "only_non_vi_label",
                "labels": found_other[:5]
            })
        else:
            missing.append({
                "file": os.path.basename(filepath),
                "issue": "no_label",
                "labels": []
            })
    
    return missing, found_vi, found_other

def scan_all():
    """Scan all TTL files in directory"""
    all_missing = []
    file_stats = {}
    
    ttl_files = glob.glob(os.path.join(TTL_DIR, "*.ttl"))
    
    for filepath in ttl_files:
        missing, found_vi, found_other = scan_ttl_file(filepath)
        
        all_missing.extend(missing)
        
        file_stats[os.path.basename(filepath)] = {
            "vi_labels": len(found_vi),
            "other_labels": len(found_other)
        }
    
    print(f"✓ Scanned {len(ttl_files)} TTL files")
    
    return all_missing, file_stats

def save_log(missing):
    """Save missing labels log"""
    with open(OUTPUT_LOG, 'w', encoding='utf-8') as f:
        for m in missing:
            f.write(f"{m['file']}: {m['issue']} - {m.get('labels', [])}\n")
    
    print(f"✓ Saved to {OUTPUT_LOG}")

def show_stats(missing, file_stats):
    """Show statistics"""
    print(f"\n=== Label Stats ===")
    print(f"  Files scanned: {len(file_stats)}")
    print(f"  Files with issues: {len(missing)}")
    
    print(f"\n=== Per File ===")
    for fname, stats in file_stats.items():
        print(f"  {fname}: {stats['vi_labels']} VI, {stats['other_labels']} other")
    
    if missing:
        print(f"\n=== Missing VI Labels ===")
        for m in missing[:10]:
            print(f"  {m['file']}: {m['issue']}")

if __name__ == "__main__":
    missing, file_stats = scan_all()
    save_log(missing)
    show_stats(missing, file_stats)