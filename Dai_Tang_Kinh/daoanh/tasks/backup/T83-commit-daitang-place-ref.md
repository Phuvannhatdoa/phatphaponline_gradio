---
id: T83
title: "T83 — Complete TAB_DAI_TANG commit: safe ref-write on lock-protected volume (E:\\Backup 2025)"
module: Hạ tầng / Docs (Git ops)
priority: high
status: done
depends_on: [TAB_DAI_TANG_PLACE]
created: 2026-09-01
updated: 2026-09-01
completed: 2026-09-01
done_when: Commit chứa toàn bộ tài liệu TAB_DAI_TANG + task T83 được gắn vào refs/heads/master (HEAD = commit mới), verify git rev-parse/log/status OK; script rollback 1-lệnh về commit cũ; dashboard + docs cập nhật.
---

# T83 — Complete TAB_DAI_TANG commit (safe ref-write)

## Mục tiêu

Hoàn tất việc **commit tài liệu TAB_DAI_TANG_PLACE** vào `master` — bị chặn vì volume
`E:\Backup 2025` (folder Data/backup → có backup/sync agent) **từ chối mọi rename/unlink
trên file git** (`.git/index`, `refs/heads/master`) nên `git add`/`git commit` không thể
cập nhật ref theo vòng đời chuẩn (atomic-rename).

Đã **giải mã nguyên nhân gốc bằng đo thật**: rename/move/atomic-replace trên file git
bị chặn (`Access denied` / "Cannot create a file when that file already exists"),
NHƯNG **ghi-đè byte trực tiếp vào chính file đó hoạt động** (`File.Copy(src, ref, true)`).
→ Giải pháp tối ưu: **tạo commit object bằng git (KHÔNG đụng ref), rồi ghi SHA trực tiếp
vào `refs/heads/master` bằng byte-copy (có backup + xác minh + script rollback).**

## Bối cảnh kỹ thuật

- Commit object đã tạo & xác minh: `2ac3d0a8` (tree `9b16fc37`, parent `031e7a3`,
  3 file A + 2 file M, 272 insertions, KHÔNG lẫn thay đổi T74).
- Trạng thái trước khi wiring: `refs/heads/master` = `031e7a3` (backup
  `.git\daitang_master_backup` lưu SHA này).
- Volume: NTFS, label "Data", Healthy. Vấn đề nằm ở lớp backup/sync chặn rename/unlink.
- Rollback: ghi lại SHA cũ `031e7a3` vào ref → trả nguyên trạng (tương đương revert/reset).

## Các bước (kế hoạch chi tiết — Admin "vô não")

### Bước 1 — Hoàn tất tài liệu
- Task file `tasks/T83-...md`; cập nhật `docs/tasktodo.md`, `docs/progress.md`;
  session log `docs/sessions/2026-09-01_T83_commit_daitang_ref.md`.
- Chạy `python scripts/build_progress_data.py` → Dashboard `data/progress_data.json`.

### Bước 2 — Dựng commit duy nhất
- Build 1 commit mới `C_T83` chứa: 5 file docs TAB_DAI_TANG + task T83 + session T83 +
  tasktodo + progress + dashboard JSON. (Thay cho `2ac3d0a8` ban đầu, vì chưa wire nên không ảnh hưởng.)
- Verify bằng `git cat-file` + `git diff <old> <C_T83> --name-status` = chỉ đúng các file tài liệu.

### Bước 3 — Ghi ref an toàn (byte-copy, không xóa/rename)
- Guard: HEAD còn = `031e7a3` (nếu session khác nhảy → DỪNG, báo, không ghi đè).
- Backup: `.git\refs\heads\master.bak_t83` (gộp cả backup cũ).
- Ghi SHA `C_T83` (40 ký tự, KHÔNG `\n` thừa, KHÔNG probe ghi khác) bằng byte-copy.
- Xác minh: `git rev-parse HEAD` == `C_T83`, `git log --oneline -3`, `git status` đọc tốt.

### Bước 4 — Script rollback / tái lập (Admin no-coding)
- `scripts/t83_ref_write.py`: `--dry-run` / `--apply` / `--verify` / `--restore` /
  `--status`. Restore ghi lại SHA backup (`031e7a3`).
- Ghi log + tasktodo (Session Continuation Protocol, AGENTS.md §0).

## Acceptance Criteria

- [x] Commit object hợp lệ, tree chứa đúng tài liệu (verify name-status)
- [x] `refs/heads/master` = commit mới; `git rev-parse HEAD` khớp; `git log` sạch; `git status` OK
- [x] Backup SHA cũ lưu sẵn; `--restore` trả về `031e7a3` (rollback 1-lệnh)
- [x] Script `scripts/t83_ref_write.py --verify` PASS
- [x] Dashboard `progress_data.json` hiển thị task T83 (+ TAB_DAI_TANG)

## Rollback

```bash
# Trả master về trước commit (restore SHA cũ đã backup)
python Dai_Tang_Kinh/daoanh/scripts/t83_ref_write.py --restore
# (== git reset --hard 031e7a3 về mặt ref; KHÔNG xóa commit C_T83 — object vẫn còn để wire lại)
```

Không thay đổi code/DB. Commit object sau khi wire vẫn nằm trong reflog/object store.

## Ghi chú an toàn
- KHÔNG bao giờ rename/delete/probe-ghi lên `refs/heads/master` ngoài cơ chế byte-copy có backup.
- Mọi thao tác ghi ref phải: guard HEAD → backup → ghi → verify → (restore nếu fail).
