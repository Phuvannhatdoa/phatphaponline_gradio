T459 SuttaCentral Parallels Staging Report
==================================================
Task: Cross-reference DILA Hán texts with SuttaCentral Pāli texts
Source: https://github.com/suttacentral/sc-data (relationship/parallels.json)
Data size: 1.5 MB, CC0 license
DILA cbeta_id range: T0001–Z9999 (from T453 authority_catalog 5.747 books)
Mapping: cbeta_id ↔ sc_uid (SuttaCentral unique ID)
Table: additive dila_catalog_parallels (cbeta_id, sc_uid, loại, nguồn)
UI feature: Kinh tương đương tag on /daoanh/ HOME page

Done when (6 requirements):
  1. Snapshot sc-data parallels.json downloaded, SHA256 recorded
  2. cbeta_id ↔ sc_uid mapping framework created
  3. Kinh tương đương tag implemented on /daoanh/ HOME page
  4. daoanh-qa ĐẠT (QA validation passed)
  5. Admin xác nhận DONE (click chuông pipip)
  5. No --apply, No SQLite writes

Validation checks:
  - cbeta_id range: T0001–Z9999 (from T453 authority_catalog)
  - sc_uid format: t-numbers (t1, t26, etc.)
  - Mapping type: additive (no existing table modification)
  - No content copied from SuttaCentral to DB
  - Manifest complete: all required fields present

Constraints:
  □ No --apply (dry-run only)
  □ No DB modification (additive framework only)
  □ No SuttaCentral text content in DB
  □ Read-only source downloads

Next: Admin confirms DONE via chuông pipip, then T460