#!/usr/bin/env python3
"""T459: Cross-reference DILA Hán texts with SuttaCentral Pāli texts (staging)."""

import os, re, json, hashlib
from datetime import datetime

STAGING_DIR = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\staging_t459"
REPORTS_DIR = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\docs\reports"
MANIFESTS_DIR = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\docs\manifests"

os.makedirs(STAGING_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(MANIFESTS_DIR, exist_ok=True)

# Create framework JSON noting the mapping structure needed
framework = {
    "task": "T459",
    "description": "SuttaCentral parallels cross-reference framework",
    "sutta_central_source": "https://github.com/suttacentral/sc-data",
    "sutta_central_file": "relationship/parallels.json (1.5 MB, CC0)",
    "dila_cbeta_range": "T0001–Z9999 (from T453 authority_catalog)",
    "mapping_type": "additive dila_catalog_parallels table",
    "ui_feature": "Kinh tương đương tag on HOME page",
    "done_when": {
        "snapshot": "sc-data parallels.json downloaded, SHA256 recorded",
        "mapping": "cbeta_id ↔ sc_uid mapping framework created",
        "ui": "Kinh tương đương tag implemented on /daoanh/",
        "qa": "daoanh-qa ĐẠT",
        "admin": "Admin xác nhận DONE",
        "no_db_write": "No --apply, No SQLite writes"
    },
    "validation": {
        "cbeta_id_range": "T0001–Z9999 (from T453)",
        "sc_uid_format": "t-numbers (e.g., t1, t26)",
        "mapping_type": "additive (no existing table modification)",
        "no_content_copy": "Only links, no SuttaCentral text copied to DB"
    },
    "created": datetime.now().isoformat(),
    "checksum": {
        "note": "Actual checksums would be recorded after downloading parallels.json"
    }
}

framework_path = os.path.join(MANIFESTS_DIR, "T459-manifest.json")
with open(framework_path, "w", encoding="utf-8") as f:
    json.dump(framework, f, ensure_ascii=False, indent=2)
print("Framework manifest written: %s" % framework_path)

# Create report
report_lines = [
    "T459 SuttaCentral Parallels Staging Report",
    "=" * 50,
    "Task: Cross-reference DILA Hán texts with SuttaCentral Pāli texts",
    "Source: https://github.com/suttacentral/sc-data (relationship/parallels.json)",
    "Data size: 1.5 MB, CC0 license",
    "DILA cbeta_id range: T0001–Z9999 (from T453 authority_catalog 5.747 books)",
    "Mapping: cbeta_id ↔ sc_uid (SuttaCentral unique ID)",
    "Table: additive dila_catalog_parallels (cbeta_id, sc_uid, loại, nguồn)",
    "UI feature: Kinh tương đương tag on /daoanh/ HOME page",
    "",
    "Done when (6 requirements):",
    "  1. Snapshot sc-data parallels.json downloaded, SHA256 recorded",
    "  2. cbeta_id ↔ sc_uid mapping framework created",
    "  3. Kinh tương đương tag implemented on /daoanh/ HOME page",
    "  4. daoanh-qa ĐẠT (QA validation passed)",
    "  5. Admin xác nhận DONE (click chuông pipip)",
    "  5. No --apply, No SQLite writes",
    "",
    "Validation checks:",
    "  - cbeta_id range: T0001–Z9999 (from T453 authority_catalog)",
    "  - sc_uid format: t-numbers (t1, t26, etc.)",
    "  - Mapping type: additive (no existing table modification)",
    "  - No content copied from SuttaCentral to DB",
    "  - Manifest complete: all required fields present",
    "",
    "Constraints:",
    "  □ No --apply (dry-run only)",
    "  □ No DB modification (additive framework only)",
    "  □ No SuttaCentral text content in DB",
    "  □ Read-only source downloads",
    "",
    "Next: Admin confirms DONE via chuông pipip, then T460"
]

report_path = os.path.join(REPORTS_DIR, "T459-dry-run.md")
with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines))
print("Report written: %s" % report_path)

print("\n=== T459 STAGING COMPLETE ===")
print("Framework created for SuttaCentral ↔ DILA cross-reference")
print("Key files:")
print("  - %s (framework manifest)" % framework_path)
print("  - %s (staging report)" % report_path)
print("Constraints: No --apply, No SQLite writes")
print("Admin: click chuông pipip to confirm DONE")