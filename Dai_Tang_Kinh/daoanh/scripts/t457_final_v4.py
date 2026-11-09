#!/usr/bin/env python3
"""T457 final v4: fix duplicate tracking + all QA checks."""

import os, re, json, hashlib
from xml.sax.saxutils import unescape
from datetime import datetime

STAGING_DIR = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\staging_final"
REPORTS_DIR = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\docs\reports"
MANIFESTS_DIR = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\docs\manifests"

os.makedirs(STAGING_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(MANIFESTS_DIR, exist_ok=True)

NEXUS_SRC_DIR = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\dila_import\biographies.2024-01\nexus_src"

def jd_to_year(jd):
    if jd >= 2299161:
        a = jd + 32044
        b = (4 * a + 3) // 146097
        c = a - 146097 * b // 4
        d = (4 * c + 3) // 1461
        e = c - 1461 * d // 4
        m = (5 * e + 2) // 153
        return 100 * b + d - 4800 + m // 10
    else:
        b = 0
        c = jd + 32082
        d = (4 * c + 3) // 1461
        e = c - 1461 * d // 4
        m = (5 * e + 2) // 153
        return d - 4800 + m // 10

files = sorted([f for f in os.listdir(NEXUS_SRC_DIR) if f.endswith('.nexus.xml')])
print("Found %d nexus files" % len(files))

file_data = {}
for fname in files:
    fpath = os.path.join(NEXUS_SRC_DIR, fname)
    with open(fpath, "rb") as fh:
        raw = fh.read()
    text = raw.decode("utf-8", errors="replace")
    sha256 = hashlib.sha256(raw).hexdigest()
    stem = fname.replace('.nexus.xml', '')
    file_data[fname] = {"text": text, "sha256": sha256, "stem": stem}

all_text = "".join(d["text"] for d in file_data.values())
root_book_match = re.search(r'book="([^"]+)"', all_text)
book_from_root = root_book_match.group(1) if root_book_match else None
print("Book from root: %s" % book_from_root)

all_nexus = []
for fname in files:
    text = file_data[fname]["text"]
    for m in re.finditer(r'<nexus[^>]*>.*?</nexus>', text, re.DOTALL):
        all_nexus.append((fname, m.group()))

print("Total nexus: %d" % len(all_nexus))

def is_book_prefix(s):
    if not s: return False
    if re.match(r'^A\d{7}$', s): return False  # person ID
    if re.match(r'^PL\d{7,}$', s): return False  # place ID
    return len(s) >= 2

def extract_prefix(s):
    if not s: return None
    return s.split('/')[0].split('#')[0].split('.')[0]

all_records = []
prefix_mismatch = 0
null_book = 0
null_anchor = 0
empty_text_zh = 0

# Track: nexus_id values and their source_file occurrences
nexus_id_source_map = {}  # nexus_id -> set of source_filenames
book_from_root_count = 0

for fname in files:
    text = file_data[fname]["text"]
    source_stem = file_data[fname]["stem"]
    
    file_nexus = re.finditer(r'<nexus[^>]*>.*?</nexus>', text, re.DOTALL)
    
    for m in file_nexus:
        nexus_full = m.group()
        rec = {
            "book": None,
            "source_file": fname,
            "source_stem": source_stem,
            "nexus_id": None,
            "seq": None,
            "from_anchor": None,
            "to_anchor": None,
            "text_zh": None,
            "person_id": None,
            "place_id": None,
            "jd_from": None,
            "jd_to": None,
            "year_from": None,
            "year_to": None,
            "provenance": "t457_final_v4",
            "status": "candidate",
        }
        
        id_match = re.search(r'id="([^"]+)"', nexus_full)
        if id_match:
            rec["nexus_id"] = id_match.group(1)
        
        seq_match = re.search(r'seq="(\d+)"', nexus_full)
        if seq_match:
            rec["seq"] = int(seq_match.group(1))
        
        from_match = re.search(r'from="([^"]+)"', nexus_full)
        if from_match:
            rec["from_anchor"] = from_match.group(1)
        else:
            null_anchor += 1
        
        to_match = re.search(r'to="([^"]+)"', nexus_full)
        if to_match:
            rec["to_anchor"] = to_match.group(1)
        else:
            null_anchor += 1
        
        text_zh_match = re.search(r'<text_zh>(.*?)</text_zh>', nexus_full, re.DOTALL)
        if text_zh_match:
            rec["text_zh"] = unescape(text_zh_match.group(1)).strip()
        else:
            empty_text_zh += 1
        
        pers = re.findall(r'<person id="([A-Z0-9]+)"', nexus_full)
        if pers:
            rec["person_id"] = pers[0]
        
        place = re.findall(r'<place id="([A-Z0-9]+)"', nexus_full)
        if place:
            rec["place_id"] = place[0]
        
        jd_from_m = re.findall(r'jd_from="(\d{7})"', nexus_full)
        if jd_from_m:
            rec["jd_from"] = jd_from_m[0]
            rec["year_from"] = jd_to_year(int(jd_from_m[0]))
        
        jd_to_m = re.findall(r'jd_to="(\d{7})"', nexus_full)
        if jd_to_m:
            rec["jd_to"] = jd_to_m[0]
        
        # Determine book
        nexus_id = rec["nexus_id"]
        prefix = extract_prefix(nexus_id) if nexus_id else None
        
        # is_book_prefix check
        prefix_is_book = is_book_prefix(prefix) if prefix else False
        
        if prefix_is_book and prefix:
            rec["book"] = prefix
        elif book_from_root:
            rec["book"] = book_from_root
            book_from_root_count += 1
        else:
            rec["book"] = None
            null_book += 1
        
        # Validate: prefix_mismatch check
        # Only when nexus_id has a book-like prefix, check if it matches source_stem
        if prefix_is_book and prefix:
            if prefix != source_stem:
                prefix_mismatch += 1
        
        all_records.append(rec)

print("Total records: %d" % len(all_records))
print("prefix_mismatch: %d" % prefix_mismatch)
print("null_book: %d" % null_book)
print("null_anchor: %d" % null_anchor)
print("empty_text_zh: %d/%d" % (empty_text_zh, len(all_records)))

# === Compute duplicate_composite_key ===
# Count how many nexus_id values appear in multiple source files
nexus_id_to_sources = {}
for rec in all_records:
    nid = rec["nexus_id"]
    if nid:
        if nid not in nexus_id_to_sources:
            nexus_id_to_sources[nid] = set()
        nexus_id_to_sources[nid].add(rec["source_file"])

duplicate_composite_key = sum(1 for nid, sources in nexus_id_to_sources.items() if len(sources) > 1)
print("duplicate_composite_key (nexus_id in multiple source files): %d" % duplicate_composite_key)

# Write JSONL
jsonl_path = os.path.join(STAGING_DIR, "t457_dila_bio_nexus.jsonl")
with open(jsonl_path, "w", encoding="utf-8") as f:
    for rec in all_records:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
print("JSONL written: %s (%d records)" % (jsonl_path, len(all_records)))

# Create manifest
with open(jsonl_path, "rb") as f:
    jsonl_bytes = f.read()
jsonl_checksum = hashlib.sha256(jsonl_bytes).hexdigest()

file_sha256_dict = {}
for fname in files:
    file_sha256_dict[fname] = file_data[fname]["sha256"]

manifest = {
    "task": "T457",
    "description": "DILA Bio Nexus final parse v4",
    "source_commit": "4e82453",
    "source_dir": NEXUS_SRC_DIR,
    "output_jsonl": jsonl_path,  # ← duy nhất trỏ tới staging_final JSONL
    "total_files": len(files),
    "total_records": len(all_records),
    "prefix_mismatch": prefix_mismatch,
    "duplicate_composite_key": duplicate_composite_key,
    "null_book": null_book,
    "null_anchor": null_anchor,
    "empty_text_zh": empty_text_zh,
    "total_with_year": sum(1 for r in all_records if r["year_from"] is not None),
    "jd_conversion": "if jd >= 2299161: Gregorian else: Julian (BCE allowed, no hard fail on 60 CE or -974)",
    "created": datetime.now().isoformat(),
    "checksum": {
        "source_files": file_sha256_dict,
        "jsonl": jsonl_checksum,
    },
    "validation": {
        "prefix_mismatch": prefix_mismatch,
        "duplicate_composite_key": duplicate_composite_key,
        "null_book": null_book,
        "null_anchor": null_anchor,
        "empty_text_zh": empty_text_zh,
        "prefix_mismatch_zero": prefix_mismatch == 0,
        "duplicate_zero": duplicate_composite_key == 0,
        "null_book_zero": null_book == 0,
        "null_anchor_zero": null_anchor == 0,
        "empty_text_zh_zero": empty_text_zh == 0,
    }
}

manifest_path = os.path.join(MANIFESTS_DIR, "T457-manifest.json")
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
print("Manifest written: %s" % manifest_path)

# Summary (encoding-safe output via file)
print("\n=== T457 FINAL VALIDATION ===")
print("prefix_mismatch: %d (0 = PASS)" % prefix_mismatch)
print("duplicate_composite_key: %d (0 = PASS)" % duplicate_composite_key)
print("null_book: %d (0 = PASS)" % null_book)
print("null_anchor: %d (0 = PASS)" % null_anchor)
print("empty_text_zh: %d/%d (0 = PASS)" % (empty_text_zh, len(all_records)))
print("JSONL: %s (%d records)" % (jsonl_path, len(all_records)))
print("Manifest: %s" % manifest_path)
print("Constraints: No --apply, No SQLite writes")
print("Key: all 5 checks PASS = ready for T458")