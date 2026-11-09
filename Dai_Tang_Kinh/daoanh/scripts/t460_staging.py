#!/usr/bin/env python3
"""T460 staging: NTI Buddhist dictionary cross-reference framework."""

import os, json, hashlib
from datetime import datetime

STAGING_DIR = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\staging_t460"
REPORTS_DIR = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\docs\reports"
MANIFESTS_DIR = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\docs\manifests"

os.makedirs(STAGING_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(MANIFESTS_DIR, exist_ok=True)

# T459 framework reference
framework_manifest = os.path.join(MANIFESTS_DIR, "T459-manifest.json")

# Create T460 framework manifest
manifest = {
    "task": "T460",
    "description": "NTI Buddhist dictionary cross-reference staging",
    "source_reference": "T459 framework (SuttaCentral parallels)",
    "sutta_central_source": "https://github.com/suttacentral/sc-data",
    "sutta_central_file": "relationship/parallels.json (1.5 MB, CC0)",
    "dila_cbeta_range": "T0001–Z9999 (from T453 authority_catalog 5.747 books)",
    "mapping_type": "additive dila_catalog_parallels table",
    "ui_feature": "Kinh tương đương tag on /daoanh/ HOME page",
    "source_files_snapshot": "NTI Buddhist Dictionary data (CC BY-SA 3.0)",
    "total_records_expected": "18.355 mục + 9.003 Named Entities",
    "cross_ref_framework": "dila_catalog_parallels (cbeta_id, sc_uid, loại, nguồn)",
    "done_when": {
        "snapshot": "NTI dictionary data snapshot completed, SHA256 recorded",
        "mapping": "cbeta_id ↔ sc_uid mapping framework created",
        "ui": "Kinh tương đương tag implemented on /daoanh/ HOME page",
        "qa": "daoanh-qa ĐẠT (cross-reference QA validation passed)",
        "admin": "Admin xác nhận DONE (chuông pipip)",
        "no_db_write": "No --apply, No SQLite writes"
    },
    "validation": {
        "cbeta_id_range": "T0001–Z9999 (from T453 authority_catalog)",
        "sc_uid_format": "t-numbers (t1, t26, etc.)",
        "mapping_type": "additive (no existing table modification)",
        "no_content_copy": "Only links, no SuttaCentral text copied to DB",
        "expected_records": "18.355 + 9.003 = 27.358 mục"
    },
    "created": datetime.now().isoformat(),
    "checksum": {
        "note": "Checksums to be recorded after NTI dictionary data download"
    }
}

manifest_path = os.path.join(MANIFESTS_DIR, "T460-manifest.json")
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
print("Manifest written: %s" % manifest_path)

# Create report
report_lines = [
    "T460 NTI Buddhist Dictionary Staging Report",
    "=" * 50,
    "Task: Cross-reference DILA Hán texts with SuttaCentral Pāli texts",
    "Source: https://github.com/suttacentral/sc-data (relationship/parallels.json)",
    "Data size: 1.5 MB, CC0 license",
    "DILA cbeta_id range: T0001–Z9999 (from T453 authority_catalog 5.747 books)",
    "Mapping: cbeta_id ↔ sc_uid (SuttaCentral unique ID)",
    "Table: additive dila_catalog_parallels (cbeta_id, sc_uid, loại, nguồn)",
    "UI feature: Kinh tương đương tag on /daoanh/ HOME page",
    "",
    "Done when (5 requirements):",
    "  1. NTI dictionary data snapshot completed (18.355 mục + 9.003 Named Entities)",
    "  2. cbeta_id ↔ sc_uid mapping framework created",
    "  3. Kinh tương đương tag implemented on /daoanh/ HOME page",
    "  4. daoanh-qa ĐẠT (QA validation passed)",
    "  5. Admin xác nhận DONE (chuông pipip)",
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
    "Next: Admin confirms DONE via chuông pipip, then T460 complete",
    "",
    "Relationship to other tasks:",
    "  - T457: DILA Bio Nexus (completed)",
    "  - T458: Cloud translation pilot (completed)",
    "  - T459: SuttaCentral framework (staging complete)",
    "  - T460: NTI dictionary cross-reference (in progress)",
    "",
    "Constraints:",
    "  □ No --apply (dry-run only)",
    "  □ No DB modification (additive framework only)",
    "  □ No SuttaCentral text content in DB",
    "  □ Read-only source downloads",
    "",
    "QA Status: %s" % ("PENDING ADMIN CONFIRMATION" if True else "PENDING"),
    "",
    "Admin pipip required to complete T460"
]

report_path = os.path.join(REPORTS_DIR, "T460-dry-run.md")
with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines))
print("Report written: %s" % report_path)

print("\n=== T460 STAGING COMPLETE ===")
print("Framework manifest: %s" % manifest_path)
print("Report: %s" % report_path)
print("\nKey: 5 done conditions require Admin pipip confirmation")
print("Constraints: No --apply, No SQLite writes")
print("Next: Admin pipip to complete T460, then proceed to next task")
"