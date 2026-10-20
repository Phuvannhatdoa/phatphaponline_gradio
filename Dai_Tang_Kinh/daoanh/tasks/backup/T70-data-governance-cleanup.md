---
id: T70
title: "Data Governance — khai báo scope CHGIS/BDRC/FoJin/SAT + cleanup wiki rác"
module: Hạ tầng / Docs
priority: medium
status: done
depends_on: [T68]
created: 2026-08-30
updated: 2026-08-30
completed: 2026-08-30
done_when: >
  data_sources / source_authority khai báo rõ trạng thái CHGIS/BDRC/FoJin/SAT là
  PREPARED/NOT INTEGRATED (implemented=0) thay vì để mơ hồ; test rows trong
  place_wiki_snapshots bị xóa an toàn (backup trước) — Build 1 quản trị nguồn minh bạch.
---

# T70 — Data Governance + Cleanup Wiki Rác

## Mục tiêu
Khai báo MINH BẠCH scope của các nguồn chưa tích hợp (CHGIS/BDRC/FoJin/SAT) trên `data_sources`/`source_authority`
thay vì để chúng rơi vào trạng thái FAIL mơ hồ; và dọn test rows trong `place_wiki_snapshots` (an toàn, reversible).
Đây là quyết định quản trị dữ liệu: Build 1 tập trung NỐI đa-nguồn có sẵn, không bắt buộc import toàn bộ nguồn mới.

## Hiện Trạng (Codebase)
- `geo_cross_ref`: chgis_svid 0, tgaz 0, bdrc 0, marcus_ref 0 (chỉ wikidata 148 + bgis 33 có giá trị).
- `data_sources`: BDRC active=0; CHGIS / FoJin / SAT không có dòng riêng.
- `sat_crossref` (2,913) — chỉ URL cbeta→SAT, KHÔNG phải chứng cứ văn bản.
- `entity_source_ids`: BDRC chỉ 1 row.
- `place_wiki_snapshots` (4): `PL_test`, `PL123`, `PL456` ("Chùa Thiếu Lâm"), `source='vi'` → test pollution.

## Thiết Kế (additive, reversible)

### Bảng/source update
- Cập nhật `data_sources`: thêm dòng CHGIS / FoJin / SAT (nếu chưa có) với `active=0` + `authority_scope` đúng.
- Cập nhật `source_authority` (từ T68): đánh `implemented=0` cho CHGIS/BDRC/SAT + ghi `note='PREPARED/NOT INTEGRATED — chưa có dữ liệu trong Build 1'`.
- Cập nhật `dataset_sources` note cho CBETA/SAT rõ "chỉ lưu metadata/tham chiếu, không phải toàn bộ corpus".

### Cleanup test rows (an toàn)
- **Backup DB trước khi xóa** (server DỪNG, không wal_checkpoint TRUNCATE — bài học T58).
- Xóa trong transaction: `DELETE FROM place_wiki_snapshots WHERE place_id IN ('PL_test','PL123','PL456') OR source='vi'`.

### Docs
- Cập nhật `GAP_REPORT.md` / `docs/` ghi rõ scope khai báo để acceptance matrix không còn "FAIL mơ hồ".

## Subtasks
- [x] T70a: source_authority đã seed đúng (T67/T68): CHGIS/BDRC/SAT/FoJin/Wikidata implemented=0; CBETA dataset_sources note updated
- [x] T70b: Backup lineage_backup_t70.db; xóa 4 test rows place_wiki_snapshots (PL123/PL456/PL_test + PL000000023255 source=vi)
- [x] T70c: place_wiki_snapshots còn 0 rows (tất cả là test). source_authority matrix minh bạch.
- [x] T70d: git commit (Build 1 - T68+T69+T70)

## Revert
- Restore DB từ backup (an toàn). Nếu chỉ sửa `data_sources`/`source_authority` → `UPDATE` ngược lại.
- Reversible hoàn toàn.
