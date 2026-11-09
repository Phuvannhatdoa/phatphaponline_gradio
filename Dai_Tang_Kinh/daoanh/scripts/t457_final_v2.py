#!/usr/bin/env python3
"""T457 final: parse with correct book extraction from nexus_id prefix + QA validation."""

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
    """Convert Julian Day Number to year.
    Allows BCE/early CE years. No hard fail on out-of-range years."""
    if jd >= 2299161:  # 1582-10-15 Gregorian
        a = jd + 32044
        b = (4 * a + 3) // 146097
        c = a - 146097 * b // 4
        d = (4 * c + 3) // 1461
        e = c - 1461 * d // 4
        m = (5 * e + 2) // 153
        return 100 * b + d - 4800 + m // 10
    else:
        # Julian calendar (before 1582-10-15) - allows BCE years
        b = 0
        c = jd + 32082
        d = (4 * c + 3) // 1461
        e = c - 1461 * d // 4
        m = (5 * e + 2) // 153
        return d - 4800 + m // 10

files = sorted([f for f in os.listdir(NEXUS_SRC_DIR) if f.endswith('.nexus.xml')])
print("Found %d nexus files" % len(files))

# Read all files with SHA256
file_data = {}
for fname in files:
    fpath = os.path.join(NEXUS_SRC_DIR, fname)
    with open(fpath, "rb") as fh:
        raw = fh.read()
    text = raw.decode("utf-8", errors="replace")
    sha256 = hashlib.sha256(raw).hexdigest()
    # Extract "stem" from filename (without .nexus.xml extension)
    stem = fname.replace('.nexus.xml', '')
    file_data[fname] = {"text": text, "sha256": sha256, "stem": stem}

# Extract book from root element <bio_nexus_src book="..."> 
all_text = "".join(d["text"] for d in file_data.values())
root_book_match = re.search(r'book="([^"]+)"', all_text)
book_from_root = root_book_match.group(1) if root_book_match else None
print("Book from root element: %s" % book_from_root)

# Find all <nexus> elements using finditer
all_nexus = []
for fname in files:
    text = file_data[fname]["text"]
    for m in re.finditer(r'<nexus[^>]*>.*?</nexus>', text, re.DOTALL):
        all_nexus.append((fname, m.group()))

print("Total nexus elements: %d" % len(all_nexus))

all_records = []
# Tracking keys
prefix_mismatch = 0
duplicate_composite_key = 0
null_book = 0
null_anchor = 0
empty_text_zh = 0

# Composite key tracker: source_file_stem + nexus_id
composite_keys = {}

for fname, nexus_full in all_nexus:
    rec = {
        "book": None,
        "source_file": fname,
        "source_stem": file_data[fname]["stem"],
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
        "provenance": "t457_final_v2",
        "status": "candidate",
    }
    
    # 1. Extract nexus_id from id="..." in the full nexus tag
    id_match = re.search(r'id="([^"]+)"', nexus_full)
    if id_match:
        rec["nexus_id"] = id_match.group(1)
    
    # 2. Extract seq from seq="..." in the full nexus tag
    seq_match = re.search(r'seq="(\d+)"', nexus_full)
    if seq_match:
        rec["seq"] = int(seq_match.group(1))
    
    # 3. Extract from_anchor from from="..." in the full nexus tag
    from_match = re.search(r'from="([^"]+)"', nexus_full)
    if from_match:
        rec["from_anchor"] = from_match.group(1)
    else:
        null_anchor += 1
    
    # 4. Extract to_anchor to to="..." in the full nexus tag
    to_match = re.search(r'to="([^"]+)"', nexus_full)
    if to_match:
        rec["to_anchor"] = to_match.group(1)
    else:
        null_anchor += 1
    
    # 5. Extract text_zh - MUST be preserved exactly
    text_zh_match = re.search(r'<text_zh>(.*?)</text_zh>', nexus_full, re.DOTALL)
    if text_zh_match:
        rec["text_zh"] = unescape(text_zh_match.group(1)).strip()
    else:
        empty_text_zh += 1
    
    # 6. Extract person_id from <person id="...">
    pers = re.findall(r'<person id="([A-Z0-9]+)"', nexus_full)
    if pers:
        rec["person_id"] = pers[0]
    
    # 7. Extract place_id from <place id="..."> 
    place = re.findall(r'<place id="([A-Z0-9]+)"', nexus_full)
    if place:
        rec["place_id"] = place[0]
    
    # 8. Extract JD and compute year (no hard fail on range)
    jd_from_m = re.findall(r'jd_from="(\d{7})"', nexus_full)
    if jd_from_m:
        rec["jd_from"] = jd_from_m[0]
        rec["year_from"] = jd_to_year(int(jd_from_m[0]))
    
    jd_to_m = re.findall(r'jd_to="(\d{7})"', nexus_full)
    if jd_to_m:
        rec["jd_to"] = jd_to_m[0]
    
    # 9. Determine book:
    #    Rule: source_file stem == nexus_id prefix == book
    #    nexus_id format typically: A000146 or Buxu_GSZ/1520tianXiZai.xml#1
    #    If nexus_id starts with a stem-like prefix, use that as book;
    #    otherwise fall back to root element book.
    
    nexus_id = rec["nexus_id"]
    source_stem = rec["source_stem"]
    
    # Determine book from nexus_id prefix
    # nexus_id can be like: "A000146" or "Buxu_GSZ/1520tianXiZai.xml#1"
    # The prefix before "/" or before non-alphanumeric chars is the book candidate
    book_from_id = None
    if nexus_id:
        # Take the part before "/" or before "#" or first segment
        prefix_candidate = nexus_id.split('/')[0].split('#')[0].split('.')[0]
        # If prefix is all alphanumeric and not too long, it's a candidate book
        if prefix_candidate and prefix_candidate.isalnum():
            book_from_id = prefix_candidate
    
    # Validate: source_file stem == nexus_id prefix == book
    # Check if they match
    prefix_match = (book_from_id == source_stem) if (book_from_id and source_stem) else False
    
    if not prefix_match:
        prefix_mismatch += 1
    
    # Set book: prefer nexus_id prefix, fall back to root element
    if book_from_id:
        rec["book"] = book_from_id
    elif book_from_root:
        rec["book"] = book_from_root
    else:
        rec["book"] = None
        null_book += 1
    
    # Track composite key uniqueness: source_stem + nexus_id
    composite_key = source_stem + "|" + nexus_id if nexus_id else source_stem
    if composite_key in composite_keys:
        duplicate_composite_key += 1
    else:
        composite_keys[composite_key] = 1
    
    all_records.append(rec)

print("Total records: %d" % len(all_records))
print("prefix_mismatch: %d" % prefix_mismatch)
print("duplicate_composite_key: %d" % duplicate_composite_key)
print("null_book: %d" % null_book)
print("null_anchor: %d" % null_anchor)
print("empty_text_zh: %d/%d" % (empty_text_zh, len(all_records)))

# Write JSONL
jsonl_path = os.path.join(STAGING_DIR, "t457_dila_bio_nexus.jsonl")
with open(jsonl_path, "w", encoding="utf-8") as f:
    for rec in all_records:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
print("JSONL written: %s (%d records)" % (jsonl_path, len(all_records)))

# Create manifest - MUST point only to staging_final JSONL
with open(jsonl_path, "rb") as f:
    jsonl_bytes = f.read()
jsonl_checksum = hashlib.sha256(jsonl_bytes).hexdigest()

file_sha256_dict = {}
for fname in files:
    file_sha256_dict[fname] = file_data[fname]["sha256"]

manifest = {
    "task": "T457",
    "description": "DILA Bio Nexus final parse v2 (source_stem == nexus_id prefix == book)",
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

# Summary output (encoding-safe - print to file via redirect)
print("=== T457 FINAL VALIDATION SUMMARY ===")
print("prefix_mismatch: %d (FAIL if >0)" % prefix_mismatch)
print("duplicate_composite_key: %d (FAIL if >0)" % duplicate_composite_key)
print("null_book: %d (FAIL if >0)" % null_book)
print("null_anchor: %d (FAIL if >0)" % null_anchor)
print("empty_text_zh: %d/%d (FAIL if >0)" % (empty_text_zh, len(all_records)))
print("JSONL: %s (%d records)" % (jsonl_path, len(all_records)))
print("Manifest: %s" % manifest_path)
print("Constraints: No --apply, No SQLite writes")
print("Key: source_file stem == nexus_id prefix == book = QA PASS" if prefix_mismatch == 0 and duplicate_composite_key == 0 and null_book == 0 else "Key: SOME CHECKS FAIL - review needed")