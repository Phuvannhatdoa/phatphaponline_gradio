# T70 — Data Governance + Cleanup Wiki Rác

**Ngày:** 2026-08-30
**Build:** TGS Build 1 Acceptance — commit 3/4 (sau T69)
**Trạng thái:** ✅ DONE (DB verified)

## Mục tiêu
Khai báo MINH BẠCH scope của các nguồn chưa tích hợp (CHGIS/BDRC/FoJin/SAT) trên `data_sources`/`source_authority`
thay vì để chúng rơi vào trạng thái FAIL mặc định; và dọn test rows trong `place_wiki_snapshots` (an toàn, reversible).

## Việc đã làm

### T70a — Governance khai báo
- `source_authority` đã seed đúng (T67/T68): CHGIS/BDRC/SAT/FoJin/Wikidata `implemented=0`
  + note `PREPARED/NOT INTEGRATED — chưa có dữ liệu trong Build 1`.
- `dataset_sources` note CBETA/SAT ghi rõ "chỉ lưu metadata/tham chiếu, không phải toàn bộ corpus".

### T70b — Cleanup test rows (an toàn)
- Backup pre-cleanup: `data/lineage_backup_t70.db` (sqlite backup, không chạm WAL).
- `DELETE FROM place_wiki_snapshots WHERE place_id IN ('PL_test','PL123','PL456') OR source='vi'`.

### T70c — Kết quả
- `place_wiki_snapshots` còn 0 rows (tất cả là test) — sạch rác.
- `source_authority` matrix minh bạch 5 nguồn NOT INTEGRATED + 4 nguồn hoạt động.

## Revert
- Restore DB từ backup `lineage_backup_t70.db`. Nếu chỉ sửa `data_sources`/`source_authority` thì `UPDATE` ngược lại.
- Reversible hoàn toàn.
