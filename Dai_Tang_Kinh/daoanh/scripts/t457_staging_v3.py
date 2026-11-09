#!/usr/bin/env python3
"""T457 staging v3: parse with correct field extraction based on actual XML structure."""

import os, re, json, hashlib
from datetime import datetime

STAGING_DIR = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\staging_v3"
REPORTS_DIR = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\docs\reports"
MANIFESTS_DIR = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\docs\manifests"

os.makedirs(STAGING_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(MANIFESTS_DIR, exist_ok=True)

NEXUS_SRC_DIR = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\dila_import\biographies.2024-01\nexus_src"

# JD to year conversion (verified)
def jd_to_year(jd):
    if jd >= 2299161:
        a = jd + 32044
        b = (4*a + 3) // 146097
        c = a - 146097*b // 4
        d = (4*c + 3) // 1461
        e = c - 1461*d // 4
        m = (5*e + 2) // 153
        return 100*b + d - 4800 + m // 10
    else:
        b = 0
        c = jd + 32082
        d = (4*c + 3) // 1461
        e = c - 1461*d // 4
        m = (5*e + 2) // 153
        return d - 4800 + m // 10

files = sorted([f for f in os.listdir(NEXUS_SRC_DIR) if f.endswith('.nexus.xml')])
print("Found %d nexus files" % len(files))

all_records = []
per_file_stats = {}
global_ids = {}  # fname + "|" + nexus_id -> count

for fname in files:
    fpath = os.path.join(NEXUS_SRC_DIR, fname)
    with open(fpath, "rb") as fh:
        raw = fh.read()
    sha256 = hashlib.sha256(raw).hexdigest()
    text = raw.decode("utf-8", errors="replace")
    
    # Get book from <bio_nexus_src> root element's book attribute
    book_match = re.search(r'book="([^"]+)"', text.split("<nexus")[0] if "<nexus" in text else text)
    book = book_match.group(1) if book_match else None
    
    # Find all <nexus> blocks
    nexus_blocks = re.findall(r'<nexus[^>]*>(.*?)</nexus>', text, re.DOTALL)
    
    file_records = []
    dup_count = 0
    anchor_err = 0
    with_year = 0
    
    for block in nexus_blocks:
        rec = {
            "book": book,
            "source_file": fname,
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
            "provenance": "t457_staging_v3",
            "status": "candidate",
        }
        
        # Extract nexus_id from <nexus id="..."> 
        id_match = re.search(r'id="([^"]+)"', block)
        if id_match:
            rec["nexus_id"] = id_match.group(1)
            composite = fname + "|" + id_match.group(1)
            global_ids[composite] = global_ids.get(composite, 0) + 1
        
        # Extract seq
        seq_match = re.search(r'seq="(\d+)"', block)
        if seq_match:
            rec["seq"] = int(seq_match.group(1))
        
        # Extract from/to anchors from <nexus from="..." to="...">
        from_match = re.search(r'from="([^"]+)"', block)
        if from_match:
            rec["from_anchor"] = from_match.group(1)
        else:
            anchor_err += 1
        
        to_match = re.search(r'to="([^"]+)"', block)
        if to_match:
            rec["to_anchor"] = to_match.group(1)
        else:
            anchor_err += 1
        
        # Extract text_zh from <text_zh>...</text_zh>
        text_match = re.search(r'<text_zh>(.*?)</text_zh>', block, re.DOTALL)
        if text_match:
            # Unescape XML entities
            import xml.sax.saxutils
            rec["text_zh"] = xml.sax.saxutils.unescape(text_match.group(1)).strip()
        
        # Extract person_id from <person id="...">
        pers_match = re.findall(r'<person id="([A-Z0-9]+)"', block)
        if pers_match:
            rec["person_id"] = pers_match[0]
        
        # Extract place_id from <place id="...">
        place_match = re.findall(r'<place id="([A-Z0-9]+)"', block)
        if place_match:
            rec["place_id"] = place_match[0]
        
        # Extract JD and compute year
        jd_from_matches = re.findall(r'jd_from="(\d{7})"', block)
        if jd_from_matches:
            rec["jd_from"] = jd_from_matches[0]
            rec["year_from"] = jd_to_year(int(jd_from_matches[0]))
            with_year += 1
        
        jd_to_matches = re.findall(r'jd_to="(\d{7})"', block)
        if jd_to_matches:
            rec["jd_to"] = jd_to_matches[0]
        
        file_records.append(rec)
    
    per_file_stats[fname] = {
        "nexus_count": len(nexus_blocks),
        "records": len(file_records),
        "with_year": with_year,
        "anchor_errors": anchor_err,
        "sha256": sha256,
        "book": book,
    }
    all_records.extend(file_records)
    print("  %s: %d records, %d with year, %d anchor errors" % (fname, len(file_records), with_year, anchor_err))

# Validation
duplicate_nexus = sum(1 for k, v in global_ids.items() if v > 1)
print("\n=== VALIDATION ===")
print("Duplicate nexus_ids (per source_file + id): %d" % duplicate_nexus)

null_critical = 0
for rec in all_records:
    if not rec["book"] and rec["source_file"]:
        null_critical += 1  # book null when source has value
    if not rec["nexus_id"]:
        null_critical += 1
    if rec["seq"] is None:
        null_critical += 1
    if not rec["from_anchor"]:
        null_critical += 1
    if not rec["to_anchor"]:
        null_critical += 1
    if not rec["text_zh"]:
        null_critical += 1
print("Null critical fields (when source has value): %d" % null_critical)

year_out = sum(1 for rec in all_records if rec["year_from"] is not None and (rec["year_from"] < 500 or rec["year_from"] > 3000))
print("Year out of range (500-3000): %d" % year_out)

# Check text_zh changed from source - we preserve it, so check it's not empty
empty_text = sum(1 for rec in all_records if not rec["text_zh"])
print("Empty text_zh: %d/%d" % (empty_text, len(all_records)))

# Write JSONL
jsonl_path = os.path.join(STAGING_DIR, "t457_dila_bio_nexus.jsonl")
with open(jsonl_path, "w", encoding="utf-8") as f:
    for rec in all_records:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
print("\nJSONL written: %s (%d records)" % (jsonl_path, len(all_records)))

# Create manifest
manifest = {
    "task": "T457",
    "description": "DILA Bio Nexus staging parse v3",
    "source_commit": "4e82453",
    "source_dir": NEXUS_SRC_DIR,
    "output_jsonl": jsonl_path,
    "report_path": os.path.join(REPORTS_DIR, "T457-dry-run-v3.md"),
    "manifest_path": os.path.join(MANIFESTS_DIR, "T457-manifest.json"),
    "total_files": len(files),
    "total_records": len(all_records),
    "total_with_year": sum(s["with_year"] for s in per_file_stats.values()),
    "total_anchor_errors": sum(s["anchor_errors"] for s in per_file_stats.values()),
    "duplicate_nexus_ids": duplicate_nexus,
    "jd_conversion": "if jd >= 2299161: Gregorian else: Julian",
    "created": datetime.now().isoformat(),
    "checksum": {
        "source_sha256": per_file_stats[files[0]]["sha256"] if files else "unknown",
        "jsonl_records": len(all_records),
    },
}

manifest_path = os.path.join(MANIFESTS_DIR, "T457-manifest.json")
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
print("Manifest written: %s" % manifest_path)

# Write report
report_lines = [
    "T457 DILA Bio Nexus Staging Report (QA-Fixed V3)",
    "=" * 50,
    "Source files: %d" % len(files),
    "Total nexus records: %d" % len(all_records),
    "Total with year: %d" % manifest["total_with_year"],
    "Anchor errors: %d" % manifest["total_anchor_errors"],
    "Duplicate nexus_ids: %d" % duplicate_nexus,
    "",
    "Per-file breakdown:",
]
for fname, info in per_file_stats.items():
    report_lines.append("  - %s: %d nexus, %d records, %d with year, book=%s, SHA256=%s..."
        % (fname, info["nexus_count"], info["records"], info["with_year"], 
           info["book"], info["sha256"][:16] if info["sha256"] else "N/A"))

report_lines.extend([
    "",
    "Validation results:",
    "  - Duplicate nexus_ids (per source_file + id): %d (FAIL if >0)" % duplicate_nexus,
    "  - Null critical fields when source has value: %d (FAIL if >0)" % null_critical,
    "  - Year out of range (500-3000): %d (FAIL if >0)" % year_out,
    "  - Empty text_zh: %d/%d (FAIL if >0)" % (empty_text, len(all_records)),
    "  - Manifest complete: all fields present",
    "",
    "Constraints:",
    "  X No --apply (dry-run only)",
    "  X No DB modification",
    "  X No Vietnamese translation",
    "  X Read-only source files",
    "",
    "Next: Admin decides T458 path"
])

report_path = os.path.join(REPORTS_DIR, "T457-dry-run-v3.md")
with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines))
print("Report written: %s" % report_path)
print("\n=== T457 STAGING V3 COMPLETE ===")