---
id: T214
title: "READ-ONLY Forensic Audit: 33 vn_person_authority rows dila_id=NULL"
module: Data / Canonical Identity
priority: critical
status: done
owner: claudecode
depends_on: [T212, T211, T208]
created: 2026-10-02
updated: 2026-10-02
designed_by: claudecode
handoff_to: Admin
done_when: |
  Forensic report hoàn chỉnh: T212 exonerated, root cause identified,
  33 historical dila_ids recovered, T200 impact analyzed.
  T166 18/18 PASS. T200 25/25 PASS.
  Artifact: docs/Mimo-Flash/T214-DB-DILA-NULL-FORENSIC-01.md
risk: |
  13 T200 lookups broken (6 unique dila_ids: A026824/A030596/A038165/A045400/A045639/A047679).
  A047679 (D2) critical: cả 2 rows mất dila_id.
  Recovery path clear: tất cả 33 historical values đã biết từ T206 backup.
---

# T214 — READ-ONLY DB DILA-NULL Forensic Audit

> **READ-ONLY task.** 0 DB mutation. 0 code change.  
> Artifact: [docs/Mimo-Flash/T214-DB-DILA-NULL-FORENSIC-01.md](../docs/Mimo-Flash/T214-DB-DILA-NULL-FORENSIC-01.md)

## Kết quả

- **T212 EXONERATED**: T212 backup pre-apply đã có 33 NULL rows → T212 không gây ra anomaly
- **Root cause**: `etl_ttl_person_authority.py` (INSERT OR REPLACE) chạy sau T211 commit (15:09), overwrite rows với NULL dila_id
- **Timeline**: Window B (11:25-15:30) = 32 rows; Window A (08:38-11:25) = 1 row (nguyet_chuong_tri_uyen)
- **Recovery**: 33/33 historical dila_ids recovered từ T206/T207 backups

## Next: T215

Restore 33 dila_ids từ T206 backup. SQL ở mục 8 của forensic artifact.
