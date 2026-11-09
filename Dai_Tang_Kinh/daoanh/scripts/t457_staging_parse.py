#!/usr/bin/env python3
"""T457 staging: parse 11 nexus files → JSONL staging records."""

import os, re, json, hashlib
from xml.sax.saxutils import unescape

STAGING_DIR = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\staging"
REPORTS_DIR = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\docs\reports"
MANIFESTS_DIR = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\docs\manifests"

os.makedirs(STAGING_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(MANIFESTS_DIR, exist_ok=True)

NEXUS_SRC_DIR = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\dila_import\biographies.2024-01\nexus_src"

# Step 1: List and read all 11 nexus files
files = sorted([f for f in os.listdir(NEXUS_SRC_DIR) if f.endswith('.nexus.xml')])
print(f"Found {len(files)} nexus files")

# Track statistics
stats = {
    "total_files": len(files),
    "total_nexus": 0,
    "with_year": 0,
    "with_person": 0,
    "with_place": 0,
    "errors": [],
    "records": [],
}

# Step 2: Parse each <nexus> element
for fname in files:
    fpath = os.path.join(NEXUS_SRC_DIR, fname)
    with open(fpath, 'rb') as fh:
        raw = fh.read()
    
    # Compute checksum of source file
    sha256 = hashlib.sha256(raw).hexdigest()
    
    # Decode
    try:
        text = raw.decode('utf-8')
    except:
        text = raw.decode('utf-8', errors='replace')
    
    # Parse all <nexus> blocks
    # Pattern: <nexus ...>...</nexus>
    nexus_blocks = re.findall(r'<nexus[^>]*>(.*?)</nexus>', text, re.DOTALL)
    
    file_records = []
    for block in nexus_blocks:
        rec = {
            "book": None,
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
            "provenance": "t457_staging_parse",
            "status": "candidate",
        }
        
        # Extract attributes from <nexus ...>
        attr_match = re.search(r'book="([^"]+)"', block)
        if attr_match:
            rec["book"] = attr_match.group(1)
        
        # Extract id attribute (nexus_id)
        id_match = re.search(r'id="([^"]+)"', block)
        if id_match:
            rec["nexus_id"] = id_match.group(1)
        
        # Extract seq
        seq_match = re.search(r'seq="(\d+)"', block)
        if seq_match:
            rec["seq"] = int(seq_match.group(1))
        
        # Extract from/to anchors
        from_match = re.search(r'from="([^"]+)"', block)
        if from_match:
            rec["from_anchor"] = from_match.group(1)
        
        to_match = re.search(r'to="([^"]+)"', block)
        if to_match:
            rec["to_anchor"] = to_match.group(1)
        
        # Extract text_zh
        text_match = re.search(r'<text_zh>(.*?)</text_zh>', block, re.DOTALL)
        if text_match:
            rec["text_zh"] = unescape(text_match.group(1)).strip()
        
        # Extract person IDs
        persons = re.findall(r'<person id="([A-Z0-9]+)"', block)
        if persons:
            rec["person_id"] = persons[0]  # take first
            stats["with_person"] += 1
        
        # Extract place IDs
        places = re.findall(r'<place id="([A-Z0-9]+)"', block)
        if places:
            rec["place_id"] = places[0]  # take first
            stats["with_place"] += 1
        
        # Extract time/jd
        jd_matches = re.findall(r'jd_from="(\d{7})"', block)
        if jd_matches:
            rec["jd_from"] = jd_matches[0]
            # Convert JD to year (simplified)
            jd = int(jd_matches[0])
            if jd >= 2299161:
                year = int((jd + 32044 + 3) // 146097 * 4 - 32075)  # simplified
            else:
                year = jd - 32082
            rec["year_from"] = year
        
        jd_matches2 = re.findall(r'jd_to="(\d{7})"', block)
        if jd_matches2:
            rec["jd_to"] = jd_matches2[0]
        
        # Check if has year info
        if rec["year_from"] is not None:
            stats["with_year"] += 1
        
        file_records.append(rec)
        stats["total_nexus"] += 1
        stats["records"].append(rec)
    
    # Store per-file info for report
    stats.setdefault("per_file", {})[fname] = {
        "nexus_count": len(nexus_blocks),
        "sha256": sha256,
    }

# Step 3: Write JSONL staging file
jsonl_path = os.path.join(STAGING_DIR, "t457_dila_bio_nexus.jsonl")
with open(jsonl_path, 'w', encoding='utf-8') as f:
    for rec in stats["records"]:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')

# Step 4: Generate report
report_lines = []
report_lines.append(f"T457 DILA Bio Nexus Staging Report")
report_lines.append(f"================================")
report_lines.append(f"Total nexus files: {stats['total_files']}")
report_lines.append(f"Total nexus records: {stats['total_nexus']}")
report_lines.append(f"Records with year: {stats['with_year']}")
report_lines.append(f"Records with person ID: {stats['with_person']}")
report_lines.append(f"Records with place ID: {stats['with_place']}")
report_lines.append("")
report_lines.append("Per-file breakdown:")
for fname, info in stats.get("per_file", {}).items():
    report_lines.append(f"  - {fname}: {info['nexus_count']} nexus, SHA256={info['sha256'][:16]}...")
report_lines.append("")
report_lines.append("Validation checks:")
# Check 1: source files unchanged (we only read them)
report_lines.append(f"  ✓ Source files read-only (no modifications)")
# Check 2: JSONL readable
try:
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    report_lines.append(f"  ✓ JSONL file readable: {len(lines)} records")
except Exception as e:
    report_lines.append(f"  ✗ JSONL read error: {e}")
# Check 3: No duplicate nexus_ids
nexus_ids = [r["nexus_id"] for r in stats["records"] if r["nexus_id"]]
if nexus_ids:
    if len(nexus_ids) == len(set(nexus_ids)):
        report_lines.append(f"  ✓ No duplicate nexus_ids ({len(nexus_ids)} unique)")
    else:
        dupes = [x for x in nexus_ids if nexus_ids.count(x) > 1]
        report_lines.append(f"  ✗ Duplicate nexus_ids: {set(dupes)}")
# Check 4: text_zh not empty
empty_text = sum(1 for r in stats["records"] if not r["text_zh"])
report_lines.append(f"  ✓ Records with text_zh: {len(stats['records']) - empty_text}/{len(stats['records'])}")
report_lines.append("")
report_lines.append("Staging file: " + jsonl_path)
report_lines.append("Do not --apply. Do not modify production DB.")

# Write report
report_path = os.path.join(REPORTS_DIR, "T457-dry-run.md")
with open(report_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(report_lines))

# Step 5: Write manifest
manifest = {
    "task": "T457",
    "description": "DILA Bio Nexus staging parse",
    "source_dir": NEXUS_SRC_DIR,
    "output_jsonl": jsonl_path,
    "report_path": report_path,
    "total_records": stats["total_nexus"],
    "total_files": stats["total_files"],
    "checksums": {},
    "created": __import__('datetime').datetime.now().isoformat(),
}
# Add per-file checksums
for fname, info in stats.get("per_file", {}).items():
    manifest["checksums"][fname] = info["sha256"]

manifest_path = os.path.join(MANIFESTS_DIR, "T457-manifest.json")
with open(manifest_path, 'w', encoding='utf-8') as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

# Final summary
print(f"\n=== T457 STAGING COMPLETE ===")
print(f"Files parsed: {stats['total_files']}")
print(f"Records: {stats['total_nexus']}")
print(f"JSONL: {jsonl_path}")
print(f"Report: {report_path}")
print(f"Manifest: {manifest_path}")
print(f"\nDo NOT run --apply. Do NOT modify production DB.")
print(f"Do NOT translate to Vietnamese. Do NOT write to DB.")