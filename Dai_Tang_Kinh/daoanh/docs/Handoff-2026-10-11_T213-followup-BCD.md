# Handoff 2026-10-11 — T213 follow-up: Admin duyệt B-C-D → entity_type + T278

## 1. Bảng thông tin đọc nhanh

| Mục | Giá trị |
|---|---|
| Ngày bàn giao | 2026-10-11 |
| HEAD (trước commit) | `b5ebaa4824de8471a7711df30501a8968bff8e4a` |
| Session đã làm | `docs/sessions/2026-10-11_T213-followup-BCD.md` |
| Task | `tasks/T213-vnpa-orphan-211-classification.md` (follow-up) + `tasks/T278-link-dila-indian-patriarchs.md` (mới) |
| Trạng thái test | `audit:honesty:strict` PASS 7/7. |
| Preflight | SSOT toplevel = `visjs-app`; **shared `.git/index` stale** (mtime 2026-10-06) → commit qua temp-index |
| DB | **Có mutation** — ALTER TABLE + 25 UPDATE rows. Backup `data/lineage.db.bucket_BCD_20261011_000505.bak` |
| TTL | Không đụng TTL |

## 2. Đọc trong 2 phút

- **Đã làm:** Admin duyệt 3 bucket T213: (1) Bucket C 11 Non-monk → `entity_type='lay_person'`. (2) Bucket D 8 Mythological → `entity_type='mythological'`. (3) Bucket B 6 Indian Patriarchs → `entity_type='indian_patriarch'` + tạo task **T278** link DILA IDs.
- **Schema:** Thêm cột `entity_type` vào `vn_person_authority` (default 'monk').
- **Phát hiện quan trọng:** Shared `.git/index` stale 5 ngày — commit **BẮT BUỘC** qua temp-index.

## 3. Đề xuất chữa dựng

| Bucket | Action | Rows | Evidence |
|---|---|---|---|
| C | `entity_type='lay_person'` | 11 | Cs-/Cư Sĩ prefix |
| D | `entity_type='mythological'` | 8 | Buddha/Bodhisattva names |
| B | `entity_type='indian_patriarch'` + T278 | 6 | Ton-Gia prefix |
| A | `entity_type='monk'` (default) | 186 | TS- files |

## 4. Cảnh báo bắt buộc

- **Shared `.git/index` STALE** — mtime 2026-10-06. Commit qua temp-index (`GIT_INDEX_FILE=%TEMP%\wt_...` + `read-tree HEAD` + plumbing + CAS).
- T278 **pending** — cần tra DILA IDs cho 6 Indian Patriarchs trước khi close.

## 5. Lệnh revert

| Phần | Lệnh | Mất dữ liệu? |
|---|---|---|
| Docs + code | `git revert --no-edit <sha-session>` | **0** |
| DB entity_type | Restore `data/lineage.db.bucket_BCD_20261011_000505.bak` | **0** |

## 6. Bảng file tạo/sửa

| File | Loại |
|---|---|
| `tasks/T278-link-dila-indian-patriarchs.md` | task mới |
| `tasks/T213-vnpa-orphan-211-classification.md` | follow-up |
| `docs/plans/2026-10-10-analysis-pack-t271-followups.md` | §7 update |
| `docs/tasktodo.md` | T213 follow-up + T278 block |
| `docs/ROLLBACK.md` | row T213 follow-up |
| `docs/sessions/2026-10-11_T213-followup-BCD.md` | session |
| `docs/Handoff-2026-10-11_T213-followup-BCD.md` | Handoff |
| `data/progress_data.json` | regen |

## 7. Sai lầm / bài học

- Shared index stale — đã thành thói quen dùng temp-index, không gặp sự cố.

## 8. Việc CHƯA xong

1. **T278** — link DILA IDs cho 6 Indian Patriarchs (pending Admin tra DILA/CBETA).
2. Shared index stale — vẫn workaround bằng temp-index.

## 9. Lệnh kiểm tra nhanh (1 phút)

```bash
cd .../daoanh
# entity_type distribution
python -X utf8 -c "import sqlite3;c=sqlite3.connect('file:data/lineage.db?mode=ro',uri=True);[print(f'{et}: {c.execute(\"SELECT COUNT(*) FROM vn_person_authority WHERE (dila_id=\\\"\\\" OR dila_id IS NULL) AND entity_type=?\",(et,)).fetchone()[0]}') for et in ['monk','lay_person','mythological','indian_patriarch']]"
# audit
python -X utf8 scripts/audit_data_honesty.py --strict
# HEAD
git rev-parse HEAD
```

## 10. Ghi chú cho agent kế tiếp

1. Đọc session + Handoff này.
2. **BẮT BUỘC** temp-index cho commit tiếp theo.
3. T278: tra DILA IDs cho 6 rows `entity_type='indian_patriarch'`.