---
id: T380
title: Khôi phục chọn lọc 4 bảng từ bản 11/10 10:11 + Thêm entity_type column
status: done
created: 2026-10-13T14:30:00Z
updated: 2026-10-13T14:30:00Z
owner: daoanh-debugger
plan_approved_at: 2026-10-13T15:45:00Z
revert: docs/ROLLBACK.md
outcome: null
---

## Scope

Khôi phục **4 bảng chính** từ bản 11/10 10:11 (xác minh safe bởi T379):
- `ai_person_name`: 0 → 39.269 (Gemini transliterations)
- `passage`: 7.563 → 44.820 (TTL passages + dịch)
- `vn_person_authority`: 1.074 → 1.511 (1.507 + 4 alias_*)
- `vn_person_relations`: 84 → 2.013 (teacher-student relations)

**Thêm cột:** `vn_person_authority.entity_type` (provenance tracking)
- Values từ bản 11/10: 1.482 monk, 11 lay_person, 8 mythological, 6 indian_patriarch

**Smart field merging** (Admin decisions):
- **name_vi**: GIỮ hiện tại (2 chữ phiên âm đúng)
- **biographical_note_vi**: GIỮ hiện tại (tiểu sử mới)
- **name_zh**: DÙNG backup (khôi phục 10 Hán chữ)
- **generation_order**: GIỮ hiện tại (thế hệ mới)
- **dila_id, status, ttl_filename, dharma_lineage**: GIỮ hiện tại
- **passage (dịch)**: GIỮ vi_text + translation_draft hiện tại
- **4 alias_***: Backup + re-insert với entity_type='monk'

**Rollback:** `docs/ROLLBACK.md` + backup file: `data/backups/lineage_backup_T380_<ts>.db`

---

## Done When

- [ ] Dừng app.py, server.py, local_gateway.py (Admin)
- [ ] Checkpoint WAL files
- [ ] Create backup via sqlite3.backup() API
- [ ] sha256 checksumming (backup + source)
- [ ] Dry-run trên copy DB → PASS
- [ ] Execute restore (4 tables, TEMP merge logic)
- [ ] ALTER TABLE vn_person_authority ADD entity_type
- [ ] Backup + re-insert 4 alias_* rows
- [ ] PRAGMA quick_check: OK
- [ ] Row counts verified:
  - [ ] ai_person_name = 39.269
  - [ ] passage = 44.820
  - [ ] vn_person_authority = 1.511 (1.507 + 4 alias)
  - [ ] vn_person_relations = 2.013
- [ ] 137 passage rows vẫn mang vi_text + translation_draft hiện tại
- [ ] 1.007 name_vi vẫn là tên ngắn (phiên âm)
- [ ] entity_type populated + verified
- [ ] Execution log saved: `docs/sessions/2026-10-13/T380_EXECUTION_LOG.md`
- [ ] daoanh-qa sign-off (integrity + API test + entity_type check)
- [ ] Admin xác nhận DONE

---

## Implementation Details

### Workflow (5 bước)

1. **Preparation (daoanh-debugger)**
   - Verify 3 servers sẽ dừng (Admin xác nhận)
   - Checkpoint WAL files
   - Backup lineage.db → `data/backups/lineage_backup_T380_<ts>.db` via `sqlite3.backup()` API
   - Calculate sha256: backup file + source 11/10 backup

2. **Dry-run (daoanh-debugger)**
   - Copy lineage.db → lineage_dryrun.db
   - Run T380_RESTORE_SCRIPT.py --mode dry-run on copy
   - If PASS → proceed to step 3
   - If FAIL → report errors, NO changes to real DB

3. **Restore (daoanh-debugger — app.py dừng)**
   - Run T380_RESTORE_SCRIPT.py --mode execute
   - Script logic:
     ```
     1. Read PRAGMA table_info (current + backup)
     2. BEGIN TRANSACTION
     3. Chụp TEMP: vn_person_authority (name_vi, biographical_note_vi, generation_order, dila_id, status, ttl_filename, dharma_lineage)
     4. Chụp TEMP: passage (vi_text, translation_draft)
     5. Chụp TEMP: 4 alias_* rows (id NOT IN backup)
     6. ALTER TABLE vn_person_authority ADD COLUMN entity_type TEXT DEFAULT 'monk'
     7. DELETE FROM 4 tables
     8. INSERT ai_person_name FROM backup.ai_person_name
     9. INSERT passage FROM backup.passage (tất cả columns)
     10. INSERT vn_person_authority FROM backup (smart merge: keep CURRENT fields, restore name_zh, add entity_type)
     11. INSERT vn_person_relations FROM backup
     12. UPDATE vn_person_authority: set name_vi, biographical_note_vi, generation_order, dila_id, status, ttl_filename, dharma_lineage FROM TEMP
     13. UPDATE passage: set vi_text, translation_draft FROM TEMP (137 rows)
     14. Re-insert 4 alias_* FROM TEMP with entity_type='monk'
     15. Verify row counts
     16. PRAGMA quick_check
     17. COMMIT
     ```
   - Log: timestamps, sha256, row counts, errors

4. **Verification (daoanh-qa)**
   - PRAGMA quick_check: OK
   - Row count verification: 39.269 / 44.820 / 1.511 / 2.013
   - Test API: `/api/namevimap` should return Claude column (va.name_vi)
   - Test API: `/api/search_monk?q=Nhân Dũng` should return A000108 with name_vi
   - Verify entity_type column: 1.482 monk populated correctly
   - Verify 137 passage rows have vi_text + translation_draft (không trống)
   - Verify 1.007 name_vi khác from CURRENT retained (2 chữ)
   - Verify 4 alias_* rows present with entity_type='monk'

5. **Commit (luồng chính)**
   - Git add: task file, script, execution log, docs
   - Git commit with attribution (Admin duyệt files before commit)

---

## Critical Notes

- **TEMP snapshot trước DELETE**: Cần backup dữ liệu hiện tại vào bảng TEMP trước khi xóa, để UPDATE lại sau restore
- **Smart field merge**: Không phải "thay toàn bộ" — lựa chọn smart từng field (CURRENT vs BACKUP)
- **Atomic transaction**: Nếu lỗi → ROLLBACK tất cả (không bị half-baked)
- **Dry-run is safe**: Không touch real DB
- **Rollback ready**: sha256 checksumming + backup location documented

---

## Resources

- Backup source (verified): `data/backups/lineage.T265-lo-D-20261011-101118.db`
- Implementation plan: `docs/sessions/2026-10-13/T380_IMPLEMENTATION_PLAN.md`
- Restore script: `docs/sessions/2026-10-13/T380_RESTORE_SCRIPT.py`
- Execution log: `docs/sessions/2026-10-13/T380_EXECUTION_LOG.md`
- Rollback procedure: `docs/ROLLBACK.md`

---

## Related Tasks

- **T379**: Data loss audit (completed)
- **T381**: Rebuild dharma_lineage_base + dharma_lineage_ttl_vn (after T380)
- **Phase 2** (after T380): Gemini batch transliterate remaining persons
- **Phase 3** (after T380): Xác Minh Place tab implementation

---

## Attribution

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
