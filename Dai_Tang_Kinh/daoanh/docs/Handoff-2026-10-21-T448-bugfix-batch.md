# Handoff 2026-10-21 — T448 fix tuần tự bug UI/GIS (T412/T416/T406)

## 1. Thông tin đọc nhanh

| Mục | Giá trị |
|---|---|
| Ngày | 2026-10-21 |
| HEAD | `80723409` (branch `truyen-dang-the-pho-clean`) |
| Task | T448 (✅ DONE) + T412 ✅ + T416 ✅ + T406 ✅ |
| Commit session | `776296a0`, `b40abd67`, `22d90d7a`, `80723409` |
| DB | Có thay đổi: 2 index (T416). Backup `data/backups/T416_20261021_172504/lineage.db` |
| Test | py_compile OK; đo endpoint bằng Flask test client |
| Dashboard | đã regen `data/progress_data.json` (done=10, 181 task, 63%) |

## 2. Đọc trong 2 phút

- **T412 (BUG-037)**: code ĐÃ CÓ sẵn trong app.py/places.html (session khác viết ~13:44, chưa commit).
  Coordinator **kiểm chứng**: A004980 → "Hưng Hóa Tồn Tưởng" (TTL), fallback DILA đúng → đánh DONE.
- **T416**: coordinator **tự sửa** (Task tool giao `daoanh-debugger` abort 2 lần): thêm
  `INDEXED BY idx_places_pending_name_zh` (code) + 2 index DB covering → `'Thiếu L'` 1.7–9.3 s còn
  **186–304 ms**; `'Nghĩa Huyền'` 1.5–1.9 s còn **199–227 ms**.
- **T406**: code có sẵn (guard `Number.isFinite`) → kiểm + đánh DONE.

**3 việc Admin nên biết:** (1) T412/T406 code vẫn CHƯA commit (file trộn WIP session khác);
(2) T416 đã commit code+index; (3) mốc <200 ms tuyệt đối cho mọi chuỗi cần FTS5 (chưa làm).

## 3. Chi tiết từng bug

| Bug | File | Bằng chứng |
|---|---|---|
| T412 | app.py (L6367+ `_t412_*`), places.html (`_t412NameSourceNote`) | test client A004980/A004981 → TTL; A003627/A000490 → DILA fallback |
| T416 | app.py route `public_autocomplete` + `_t416_pending_index_hint`; `scripts/t416_add_autocomplete_indexes.py` | đo 5 chuỗi trước/sau; EXPLAIN QUERY PLAN |
| T406 | places.html (~L1515) | diff guard isFinite |

## 4. Cảnh báo bắt buộc

- **app.py + places.html đang trộn WIP session khác** (T412/T440/T445/T446). Commit của session này
  dùng **blob dựng từ HEAD + phần T416** (§17) → KHÔNG sweep WIP. Khi session khác commit,
  phần T412/T406 sẽ vào lịch sử theo cách của họ.
- `Task tool` giao subagent `daoanh-debugger` bị **abort 2 lần** → không dùng được trong phiên này.
- DB write duy nhất: 2 index (additive). Revert = DROP INDEX, không mất dữ liệu.

## 5. Lệnh revert

| Việc | Lệnh | Mất dữ liệu? |
|---|---|---|
| T416 index DB | `python -X utf8 scripts/t416_add_autocomplete_indexes.py --revert` | Không |
| T416 code | `git revert 80723409 b40abd67` | Không |
| Toàn session | `git revert 80723409 22d90d7a b40abd67 776296a0` | Không |

## 6. File tạo/sửa

- `scripts/t416_add_autocomplete_indexes.py` (mới)
- `docs/sessions/2026-10-21/T416/T416_REPORT.md`, `T412/T412_VERIFY_REPORT.md`, `T406/T406_QA_NOTE.md` (mới)
- `tasks/T448-fix-bug-batch-ui-gis.md` (mới), `tasks/T412-*.md`, `tasks/T416-*.md`, `tasks/T406-*.md` (status)
- `docs/tasktodo.md`, `docs/ROLLBACK.md`, `AGENTS.md` (quy tắc pipip)
- `data/backups/T416_20261021_171603/` và `T416_20261021_172504/` (DB)

## 7. Sai lầm đã vấp

- Tạo `idx_namevi_places_name_vi` (1 cột) **vô dụng** cho LIKE `%q%` (wildcard đầu) → phải đổi sang
  covering index `(name_vi, dila_id, name_zh)`. Bài học: index B-tree không giúp LIKE `%x%`;
  dùng covering index hoặc FTS5.
- `python -c "...\"..."` trong PowerShell vỡ → luôn viết temp `.py`.
- `git add` một số file im lặng không vào index → verify `git diff --cached --name-only` rồi
  bổ sung bằng `git hash-object -w` + `update-index --cacheinfo`.

## 8. Việc CHƯA xong

1. Commit T412 + T406 (code đã có, chưa commit) — chờ session sở hữu hoặc Admin quyết.
2. T416 <200 ms tuyệt đối → FTS5 (task riêng).
3. T412 phần (6) mapping DB (Lâm Tế Nghĩa Huyền, Bách Trượng Hoài Hải chưa nối TTL) — cần Admin duyệt từng dòng.
4. QA độc lập (`daoanh-qa`) cho cả 3 bug — chưa chạy (Task tool abort).

## 9. Lệnh kiểm tra nhanh

```powershell
git log --oneline -5
python -X utf8 scripts/t416_add_autocomplete_indexes.py --dry-run
python -X utf8 -u "$env:TEMP\opencode\t416final.py"   # đo endpoint (nếu còn file)
```

## 10. Ghi chú cho agent kế tiếp

1. Kiểm `git rev-parse HEAD` + `git log --oneline -3` trước khi commit (HEAD dịch liên tục).
2. Commit file trộn WIP: dùng blob từ HEAD + phần của mình (§17), đừng `git add` cả file.
3. `Task tool` subagent có thể abort — nếu vậy tự làm việc nhỏ + ghi lý do vào report.
4. Mọi DB write: backup trước (script có sẵn), ghi ROLLBACK, revert bằng script `--revert`.
