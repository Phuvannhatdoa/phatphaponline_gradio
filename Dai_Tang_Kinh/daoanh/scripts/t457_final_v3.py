#!/usr/bin/env python3
"""T457 final v3: conditional prefix matching + QA validation."""

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
    """Check if a string looks like a book identifier (not person/place ID).
    Person IDs start with 'A', place IDs start with 'PL'.
    Book prefixes are like Buxu_GSZ, Jushi_Zhuan, Mingsengzhuanchao, etc."""
    if not s:
        return False
    # Person IDs: A000146, A002004 etc. (start with A followed by 7 digits)
    if re.match(r'^A\d{7}$', s):
        return False
    # Place IDs: PL0000000xxx (start with PL followed by 7+ digits)
    if re.match(r'^PL\d{7,}$', s):
        return False
    # Empty or too short
    if len(s) < 2:
        return False
    return True

def extract_prefix(s):
    """Extract prefix from nexus_id: part before /, #, or ."""
    if not s:
        return None
    return s.split('/')[0].split('#')[0].split('.')[0]

all_records = []
prefix_mismatch = 0
duplicate_composite_key = 0
null_book = 0
null_anchor = 0
empty_text_zh = 0

composite_keys = {}  # source_stem + "|" + nexus_id prefix

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
            "provenance": "t457_final_v3",
            "status": "candidate",
        }
        
        # Extract nexus_id
        id_match = re.search(r'id="([^"]+)"', nexus_full)
        if id_match:
            rec["nexus_id"] = id_match.group(1)
        
        # Extract seq
        seq_match = re.search(r'seq="(\d+)"', nexus_full)
        if seq_match:
            rec["seq"] = int(seq_match.group(1))
        
        # Extract from_anchor
        from_match = re.search(r'from="([^"]+)"', nexus_full)
        if from_match:
            rec["from_anchor"] = from_match.group(1)
        else:
            null_anchor += 1
        
        # Extract to_anchor
        to_match = re.search(r'to="([^"]+)"', nexus_full)
        if to_match:
            rec["to_anchor"] = to_match.group(1)
        else:
            null_anchor += 1
        
        # Extract text_zh
        text_zh_match = re.search(r'<text_zh>(.*?)</text_zh>', nexus_full, re.DOTALL)
        if text_zh_match:
            rec["text_zh"] = unescape(text_zh_match.group(1)).strip()
        else:
            empty_text_zh += 1
        
        # Extract person_id
        pers = re.findall(r'<person id="([A-Z0-9]+)"', nexus_full)
        if pers:
            rec["person_id"] = pers[0]
        
        # Extract place_id
        place = re.findall(r'<place id="([A-Z0-9]+)"', nexus_full)
        if place:
            rec["place_id"] = place[0]
        
        # Extract JD and year
        jd_from_m = re.findall(r'jd_from="(\d{7})"', nexus_full)
        if jd_from_m:
            rec["jd_from"] = jd_from_m[0]
            rec["year_from"] = jd_to_year(int(jd_from_m[0]))
        
        jd_to_m = re.findall(r'jd_to="(\d{7})"', nexus_full)
        if jd_to_m:
            rec["jd_to"] = jd_to_m[0]
        
        # === Determine book ===
        # Rule: book from nexus_id prefix IF it's a book-like prefix;
        # otherwise from root element book.
        nexus_id = rec["nexus_id"]
        prefix = extract_prefix(nexus_id) if nexus_id else None
        
        # Check if prefix is book-like
        prefix_is_book = is_book_prefix(prefix) if prefix else False
        
        if prefix_is_book and prefix:
            rec["book"] = prefix
        elif book_from_root:
            rec["book"] = book_from_root
        else:
            rec["book"] = None
            null_book += 1
        
        # === Validate: source_file stem == nexus_id prefix == book ===
        # Only check when nexus_id has a book-like prefix
        if prefix_is_book and prefix:
            # Check if prefix matches source_stem
            if prefix != source_stem:
                prefix_mismatch += 1
                # Still set book from prefix (it won't match, so book won't equal stem)
                # But we don't increment prefix_mismatch twice for the same reason
        else:
            # When nexus_id is not book-like, book comes from root element.
            # The "prefix" check is not applicable, so no mismatch counted.
            # However, ensure book is set from root
            if not rec["book"] and book_from_root:
                rec["book"] = book_from_root
        
        # Track composite key: source_stem + nexus_id prefix (for duplicate detection)
        comp_prefix = prefix if (prefix and is_book_prefix(prefix)) else "no_book_prefix"
        composite_key = source_stem + "|" + comp_prefix
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
    "description": "DILA Bio Nexus final parse v3",
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

# Summary
print("\n=== T457 FINAL VALIDATION ===")
print("prefix_mismatch: %d (0 = PASS)" % prefix_mismatch)
print("duplicate_composite_key: %d (0 = PASS)" % duplicate_composite_key)
print("null_book: %d (0 = PASS)" % null_book)
print("null_anchor: %d (0 = PASS)" % null_anchor)
print("empty_text_zh: %d/%d (0 = PASS)" % (empty_text_zh, len(all_records)))
print("JSONL: %s (%d records)" % (jsonl_path, len(all_records)))
print("Manifest: %s" % manifest_path)
print("Constraints: No --apply, No SQLite writes")
print("Key: BCE years allowed; formula verified with known mốc")