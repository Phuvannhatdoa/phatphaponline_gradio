---
id: T376
title: "Thu gọn docs/tasktodo.md: chuyển mục DONE sang docs/archive/tasktodo-done-2026.md"
status: done
created: 2026-10-13
updated: 2026-11-01
owner: claude-code (phiên housekeeping 2026-10-13)
plan_approved_at: "2026-10-13 (Admin duyệt qua chat)"
dispatch: approved
done_when: >
  (1) Mục của task đã `status: done` (theo frontmatter tasks/) chuyển nguyên văn sang
  docs/archive/tasktodo-done-2026.md; tasktodo.md có dòng trỏ tới file lưu trữ.
  (2) Không mục nào bị mất: số ký tự nội dung (trừ khoảng trắng) trước = sau (tasktodo + archive).
  (3) `python scripts/build_progress_data.py` trước/sau cho cùng số task.
  (4) Mốc `a4397c2a` (commit gom nhiều task, không revert riêng được); phần sửa L1
  ở `45b2b5ec`. Hoàn tác bằng `docs/sessions/2026-10-13/housekeeping/tasktodo.md.bak-before-T376`.
  (5) Admin xác nhận DONE.
revert: >
  Mốc a4397c2a (commit gom nhiều task) KHÔNG revert riêng được. Phần sửa L1
  revert bằng: git revert --no-edit 45b2b5ec (docs-only). Hoàn tác thủ công:
  chép docs/sessions/2026-10-13/housekeeping/tasktodo.md.bak-before-T376 →
  docs/tasktodo.md, rồi bỏ các block T376 trong docs/archive/tasktodo-done-2026.md.
outcome: >
  2026-10-13: Chỉ `scripts/build_progress_data.py` (quét mọi docs/**/*.md tìm claim endpoint) và vài script
  audit cũ đọc tasktodo.md; dashboard chỉ nhắc tên file. Chuyển 74 mục (114 dòng) có task file `status: done`
  + dòng trạng thái DONE sang docs/archive/tasktodo-done-2026.md; thêm dòng trỏ ở đầu tasktodo.md.
  246.439 → 137.091 byte (615 → 434 dòng). Bảo toàn: 196.791 = 109.126 + 87.665 ký tự (trừ khoảng trắng).
  build_progress_data trước = sau (295 task, done 157, 72%, 331 endpoint). Phần văn xuôi ACTIVE/PENDING và
  mục không có task file giữ nguyên. Lưu ý: dự án đã có docs/taskdone.md (protocol cũ) — file mới trỏ tới nó.
  Commit: a4397c2a (mốc gom, không revert riêng được) + 45b2b5ec (phần sửa L1).
  Chờ daoanh-qa + Admin.
  2026-11-01: Admin xác nhận DONE; commit phần L3 ở <SHA mới — xem BLOCKER: commit L3
  tạm hoãn, chi tiết trong báo cáo cùng ngày — SHA sẽ điền khi commit thực hiện được>.
---

# T376 — Thu gọn tasktodo.md

## Các bước

- [x] Kiểm tra code nào đọc `docs/tasktodo.md` (scripts/, dashboard/, admin/, app.py)
- [x] Chạy `build_progress_data.py` lấy số liệu trước
- [x] Sao lưu tasktodo.md
- [x] Chạy `scripts/t376_archive_tasktodo_done.py --dry-run`, rà danh sách
- [x] Áp dụng, kiểm bảo toàn nội dung
- [x] Chạy lại `build_progress_data.py`, so số task
- [ ] Commit riêng, tiền tố `T376` (BLOCKED 2026-11-01 — xem outcome: patch L3 không áp dụng sạch lên HEAD trên 4/7 file, chưa commit)
- [x] Admin xác nhận DONE
