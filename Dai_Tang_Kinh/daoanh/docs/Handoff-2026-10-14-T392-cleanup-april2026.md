# Handoff — T392 Dọn 8 file tài liệu tháng 4/2026 — 2026-10-14

## 1. Bảng thông tin đọc nhanh

| Mục | Giá trị |
|---|---|
| Task | T392, ✅ DONE — move 8 file .md tháng 4/2026 → Backup-Old/ |
| HEAD trước | `1b19192` |
| Commit | `049804a` (chore(T392)) |
| File | 8 file .md, 61.470 byte |
| Tests | guard PASS · route 363 · dup:ids FAIL 1 (T274, y như cũ) · progress_data.json không đổi |
| DB/TTL/ETL | 0 mutation |

## 2. Đọc trong 2 phút

8 file .md gốc tại `Dai_Tang_Kinh/daoanh/` có ngày nội dung 2026-04-10 → 04-14 (tháng đầu tiên của dự án Đạo Ảnh) đã được di chuyển vào `visjs-app/Backup-Old/2026-10-14/`. Nội dung 8 file này đã được hợp nhất vào `docs/DEV_HISTORY.md:262` (liệt kê tên từng file). 0 tham chiếu code sống, 0 route Flask, 0 link markdown bị đứt. Move không xoá vĩnh viễn — khôi phục bằng `git revert` hoặc script restore.

## 3. Phần đã xây dựng và chứng cứ

- Script: `scripts/t391_backup_old.py` (--dry-run/--apply/--restore, hash guard)
- Manifest: `Backup-Old/2026-10-14/MANIFEST-2026-10-14.md` + `manifest-2026-10-14.json`
- 8 file đã move (tương đối repo root):
  1. `Dai_Tang_Kinh/daoanh/DILA_Structure_Report.md` (04-10, 31.737 B)
  2. `Dai_Tang_Kinh/daoanh/FEATURE_PLAN.md` (04-10/12, 7.777 B)
  3. `Dai_Tang_Kinh/daoanh/QA2.md` (04-12, 3.274 B)
  4. `Dai_Tang_Kinh/daoanh/QA_REPORT_V2.md` (04-12, 2.008 B)
  5. `Dai_Tang_Kinh/daoanh/TASK_LOG_QA1.md` (04-12, 1.241 B)
  6. `Dai_Tang_Kinh/daoanh/TASK_LOG.md` (04-13, 1.423 B)
  7. `Dai_Tang_Kinh/daoanh/SYSTEM_MAP.md` (04-14, 1.237 B)
  8. `Dai_Tang_Kinh/daoanh/Timeline Tich Hop.md` (04-14, 12.773 B)
- Commit: `049804a` (9 files changed: 8 deletions + .gitignore)
- Verify: guard PASS · route 363 · dup:ids FAIL 1 (T274, pre-existing) · progress_data.json không đổi
- Restore test: QA2.md restored → sha256 match → move back OK

## 4. Cảnh báo bắt buộc

- **Move 60 KB, giải phóng 0 byte.** Chỉ gọn thư mục gốc. Dung lượng ổ không đổi.
- **Backup-Old/ gitignored** — nội dung backup chỉ trên đĩa. 8 file tracked an toàn vì còn trong git history (tầng 1 restore: `git revert`).
- **SYSTEM_MAP.md** là output sinh bởi `datafusion.py:284` — nếu sau này chạy `datafusion.py` nó sẽ được tạo lại ở gốc (không phải lỗi).
- `.git` vẫn 3.9 GB do `data/backups/lineage_t165_20260925_135855.db` (1.376 GB) commit trước khi `data/` vào `.gitignore`. Cần viết lại history — **không** làm trong T392.
- Không đụng: 4 file DB 5.80 GiB (tháng 10), 39 file rác T377 (tháng 8), 23 script, mọi log.

## 5. Revert từng phần

| Phần | Hoàn tác | Mất dữ liệu? |
|---|---|---|
| 8 file tracked | `git revert --no-edit 049804a` | Không |
| 1 file tracked | `scripts/t391_backup_old.py --restore <path>` | Không |
| Hash guard | Restore dừng nếu drift (hash khác) | Không |

## 6. Bảng file tạo/sửa

| File | Thay đổi |
|---|---|
| `Dai_Tang_Kinh/daoanh/DILA_Structure_Report.md` | DELETE (move) |
| `Dai_Tang_Kinh/daoanh/FEATURE_PLAN.md` | DELETE (move) |
| `Dai_Tang_Kinh/daoanh/QA2.md` | DELETE (move) |
| `Dai_Tang_Kinh/daoanh/QA_REPORT_V2.md` | DELETE (move) |
| `Dai_Tang_Kinh/daoanh/TASK_LOG_QA1.md` | DELETE (move) |
| `Dai_Tang_Kinh/daoanh/TASK_LOG.md` | DELETE (move) |
| `Dai_Tang_Kinh/daoanh/SYSTEM_MAP.md` | DELETE (move) |
| `Dai_Tang_Kinh/daoanh/Timeline Tich Hop.md` | DELETE (move) |
| `visjs-app/.gitignore` | ADD `Backup-Old/` |
| `scripts/t391_backup_old.py` | NEW (move/restore tool) |
| `Backup-Old/2026-10-14/MANIFEST-2026-10-14.md` | NEW (human manifest) |
| `Backup-Old/2026-10-14/manifest-2026-10-14.json` | NEW (machine manifest) |
| `docs/tasktodo.md` | ADD T392 block |
| `docs/ROLLBACK.md` | ADD T392 row |
| `docs/Handoff-2026-10-14-T392-cleanup-april2026.md` | NEW (this file) |

## 7. Sai lầm / điều đã bị bác bỏ

- Ban đầu plan bao gồm 12 file (bao gồm 3 file tháng 5, 1 file tháng 10) — **đã sửa** theo quyết định bám sát "tháng cũ nhất = 2026-04-10 → 04-14". Loại bỏ: `session.md` (tháng 10), `QA_REPORT_V3.md` (05-13), `GAP_REPORT.md` (05-25), `NOTES_NGINX_FIX.md` (05-06).
- DB 5.80 GiB (tháng 10) **không đụng** theo quyết định Admin.

## 8. Việc chưa xong

- `.git` 3.9 GB (history có DB) → task riêng `T392` nếu cần.
- 39 file rác T377 (tháng 8) + 23 script (tháng 8/10) + 4 DB tháng 10 — chờ quyết định riêng.
- T274 duplicate ID (pre-existing) → cần đổi số theo AGENTS §16.

## 9. Lệnh kiểm tra nhanh

```bash
# visjs-app/
git rev-parse --abbrev-ref HEAD              # master
git diff --cached --name-status              # rỗng
python -X utf8 Dai_Tang_Kinh/daoanh/scripts/repo_guard.py
python -X utf8 -c "import sys,os;sys.path.insert(0,os.getcwd());import Dai_Tang_Kinh.daoanh.app;print(len(list(Dai_Tang_Kinh.daoanh.app.app.url_map.iter_rules())))"  # 363
python -X utf8 Dai_Tang_Kinh/daoanh/scripts/build_progress_data.py --check-dup-ids  # FAIL 1 (T274)
# Restore test:
python -X utf8 Dai_Tang_Kinh/daoanh/scripts/t391_backup_old.py --restore "Dai_Tang_Kinh/daoanh/QA2.md"
```

## 10. Ghi chú cho agent kế tiếp

- 8 file đã move có trong `Backup-Old/2026-10-14/` + manifest. Restore bằng script hoặc `git revert 049804a`.
- SYSTEMP_MAP.md sẽ tái sinh nếu chạy `datafusion.py` — không phải lỗi.
- `session.md` (tháng 10) **không** đụng — nằm ở gốc.
- T274 duplicate ID vẫn FAIL `dup:ids` (pre-existing, out of scope).

---

Commit SHA: `049804a`
MANIFEST: `visjs-app/Backup-Old/2026-10-14/MANIFEST-2026-10-14.md`