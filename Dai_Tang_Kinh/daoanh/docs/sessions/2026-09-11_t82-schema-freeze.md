# Session — T82 Schema Freeze + Data Lock (read-only, 2026-09-11)

> Thuần read-only: 0 ALTER, 0 INSERT/UPDATE/DELETE, 0 sửa app.py/HTML. Chỉ query DB + ghi docs.
> Không đụng file agent ngoài (app.py/places.html...) — tránh conflict staged-index.

## Mục tiêu phiên

Tasktodo T82 = "Đóng băng schema + audit toàn bộ data trước release". Audit data-lock phiên trước
(`t82_data_lock_audit.json`) đã cover orphan/admin_approved. Phiên này bổ sung **đóng băng schema**:
snapshot toàn bộ schema + phân lớp freeze + checksum baseline + expected-change registry.

## Thực hiện (read-only)

### 1. Checksum baseline
`python scripts/t82_checksum.py` (streaming zero-RAM, ShA-256 từng row) → `data/checksums.json`:
| bảng | rows |
|------|-----:|
| people | 48,673 |
| places | 59,161 |
| places_dila | 59,167 |
| place_timeline_events | 3,688 |
| vn_person_events | 5,351 |
| place_person_bibl | 13,933 |
| entity_claims | 447,885 |

SHA-256 đầy đủ trong file (gitignored).

### 2. Schema snapshot
Quét `sqlite_master` → **137 tables + 4 views**, phân lớp freeze:
- **RAW 5** (places_dila, people_full, marcus_reference, marcus_networks, dila_reference)
- **CORE 15** (entity_claims 447,885 · entity_source_ids 182,715 · entity_hub 167,006 · lexicon 166,278 ...)
- **MAPPING 70**
- **DERIVED 44** (glossary_vi 248,095 · entity_claims_audit 447,885 · places_pending 176,783 ...)
- **AUDIT 2** (en_audit_log 3 · text_reading_log 0)
- **VIEW 4** (v_assertions · v_entity_places · v_events_full · v_place_cbeta_vn)

Lưu `data/schema_snapshot.json` (gitignored).

### 3. Docs
- `docs/SCHEMA_FREEZE.md` — khóa sổ: tổng quan 137/4, quy tắc đóng băng,
  **Expected-Change Registry** (§5: person_bio_vi_draft 0/2,093 · place_desc_vi_draft 0/14,000 ·
  geo_cross_ref candidate 9 · text_reading_log · en_audit_log · lineage_conflicts_v2),
  release gate (T113 compliance + checksum verify).
- `tasks/T82-schema-freeze-data-lock.md` (task mới, khác `tasks/backup/T82-consolidation-data-lock.md` đã done).
- `docs/tasktodo.md` dòng T82 → DONE.

### 4. Commit
Build commit (docs + task file + tasktodo) qua `b4_commit.py` temp-index → hash-fill. Revert: `git revert a8336fb4`.

## Files
- `docs/SCHEMA_FREEZE.md` (committed)
- `tasks/T82-schema-freeze-data-lock.md` (committed)
- `docs/sessions/2026-09-11_t82-schema-freeze.md` (file này, committed)
- `docs/tasktodo.md` (committed)
- `data/checksums.json`, `data/schema_snapshot.json` (gitignored, trên disk)

## Revert
`git revert <build hash>` + nếu muốn xóa file docs bổ sung từ 6500be9 .. build.