# Session 2026-10-11 — T213 follow-up: Admin duyệt B-C-D → entity_type + T278

> Task: `tasks/T213-vnpa-orphan-211-classification.md` (follow-up) + `tasks/T278-link-dila-indian-patriarchs.md` (mới).
> Môi trường: Windows box (`cwd=daoanh`), git shared index stale (mtime 2026-10-06) → commit qua temp-index.

## 1. Mục tiêu

Admin duyệt 2026-10-11 cho 3 bucket từ T213 classification:
- **Bucket C (11 Non-monk)** → tag `entity_type='lay_person'`
- **Bucket D (8 Mythological)** → tag `entity_type='mythological'`
- **Bucket B (6 Indian Patriarchs)** → tag `entity_type='indian_patriarch'` + tạo task **T278** link DILA IDs

## 2. Đã làm

### 2.1 Schema change
`ALTER TABLE vn_person_authority ADD COLUMN entity_type TEXT DEFAULT 'monk'`

### 2.2 Bucket C (11 rows) → lay_person
`banh_nhu_lam`, `cs_huong`, `do_huong_trinh`, `mac_tuong_thieu_hu`, `pham_xung`, `phan_luong_quy`, `quach_tuong_chanh`, `tang_khai`, `thu_ky_nam`, `trieu_lenh_cam`, `ty_bo_ton`
→ `UPDATE ... SET entity_type='lay_person'` (11 rows affected)

### 2.3 Bucket D (8 rows) → mythological
`thich_ca_mau_ni_phat`, `phat_bao_phap_hoa`, `phat_y_linh_nhac`, `thach_phat_hien_trong`, `thanh_vien_phat_nhan`, `tuyen_minh_phat_an`, `nguyet_chau_than_giam`, `thien_tue_bao_chuong`
→ `UPDATE ... SET entity_type='mythological'` (8 rows)

### 2.4 Bucket B (6 rows) → indian_patriarch
`da_da_xa_da`, `dao_tin`, `la_hau_la_da`, `ngu_phong_thuong_quan`, `su_tu_ty_kheo`, `uu_ba_cuc_da`
→ `UPDATE ... SET entity_type='indian_patriarch'` (6 rows)
→ Tạo task **T278** link DILA IDs cho 6 rows này.

### 2.5 Bucket A (186 rows) → monk (default)
Giữ nguyên `entity_type='monk'`.

### 2.6 Verify
```bash
python -X utf8 -c "
import sqlite3
c = sqlite3.connect('file:data/lineage.db?mode=ro', uri=True)
for et in ['monk','lay_person','mythological','indian_patriarch']:
    cnt = c.execute('SELECT COUNT(*) FROM vn_person_authority WHERE (dila_id=\"\" OR dila_id IS NULL) AND entity_type=?', (et,)).fetchone()[0]
    print(f'{et}: {cnt}')
"
# monk=186, lay_person=11, mythological=8, indian_patriarch=6 (total 211)
```

## 3. Backup
`data/lineage.db.bucket_BCD_20261011_000505.bak` (1.7GB)

## 4. Files tạo/sửa

| File | Loại |
|---|---|
| `tasks/T278-link-dila-indian-patriarchs.md` | task mới |
| `tasks/T213-vnpa-orphan-211-classification.md` | cập nhật follow-up |
| `docs/plans/2026-10-10-analysis-pack-t271-followups.md` | cập nhật §7 |
| `docs/tasktodo.md` | block T213 follow-up + T278 |
| `docs/ROLLBACK.md` | row T213 follow-up |
| `docs/sessions/2026-10-11_T213-followup-BCD.md` | session (này) |
| `docs/Handoff-2026-10-11_T213-followup-BCD.md` | Handoff (mới) |
| `data/progress_data.json` | regen dashboard |

## 5. Revert

| Phần | Lệnh | Mất dữ liệu? |
|---|---|---|
| Docs + code | `git revert --no-edit <sha-session>` | **0** |
| DB entity_type | Restore `data/lineage.db.bucket_BCD_20261011_000505.bak` | **0** (schema + data) |

## 6. Cảnh báo
- Shared `.git/index` stale (mtime 2026-10-06) — commit **BẮT BUỘC** qua temp-index.
- T278 pending — cần Admin duyệt khi tra xong DILA IDs.

## 7. Pipip

Done.