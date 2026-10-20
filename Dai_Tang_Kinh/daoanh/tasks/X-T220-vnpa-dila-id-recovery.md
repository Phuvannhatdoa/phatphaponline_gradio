---
id: T220
former_ids: [T215]
title: "VNPA DILA-ID Recovery: Khôi phục 33 dila_id từ T206/T207 backup (SUPERSEDED by T215)"
module: Data / Canonical Identity
priority: critical
status: superseded
owner: claudecode
depends_on: [T214, T212, T211]
created: 2026-10-02
updated: 2026-10-12
superseded_by: T215
designed_by: claudecode
handoff_to: Admin
done_when: |
  This task is superseded by T215. The actual recovery was performed under T215.
  See T215-VNPA-DILA-ID-RECOVERY-01.md for the authoritative record.
risk: |
  This is a duplicate task file. The actual recovery was done in T215.
  T216 (ETL UPSERT guard) still needed to prevent future loss.
---

# T220 — VNPA DILA-ID Recovery

> **Admin-authorized data recovery.** Phạm vi: chỉ 33 UPDATE dila_id IS NULL.  
> Artifact: [docs/Mimo-Flash/T220-VNPA-DILA-ID-RECOVERY-01.md](../docs/Mimo-Flash/T220-VNPA-DILA-ID-RECOVERY-01.md)

## Kết quả

- **33/33 dila_ids restored** từ T206/T207 backup (100% match)
- **0 INSERT, 0 DELETE** — T220 scope CLEAN
- **T200 restored**: 6 broken dila_ids (A026824/A030596/A038165/A045400/A045639/A047679) đều working
- **T212 preserved**: 4 alias rows vẫn absent
- **Backup**: `lineage_t215_20261002_172632.db`, SHA256=`813cb17f...`
- **+1 anomaly**: `dien_phuc_tue_thang` inserted by background ETL (không phải T220)

## ETL Root Cause (Section 13)

- `scripts/etl_ttl_person_authority.py` lines 374-378: full `DELETE FROM vn_person_authority` trước khi reinsert
- Dila_id curate thủ công không qua `ttl_mapping` bị mất khi ETL chạy

## Follow-up

- **T216**: ETL UPSERT guard — preserve existing dila_id (cần Admin approval)
- **D3**: A021395 canonical choice (Admin decision)
- **D4**: dam_chau_bao_cai_uoc wrong-person fix
- **T213**: Classification 211 dila_id='' rows
