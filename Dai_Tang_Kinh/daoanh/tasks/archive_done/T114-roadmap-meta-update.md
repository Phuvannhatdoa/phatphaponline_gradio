---
id: T114
title: "Master Roadmap Meta-Update — đồng bộ lộ trình Evidence-first"
module: Project Management / Docs
priority: medium
depends_on: [T108]
created: 2026-09-08
updated: 2026-09-09
status: done
done_when: >
  tasktodo.md/progress.md/roadmap.md/ROLLBACK.md đồng bộ theo tiến độ thực của
  T108-T113 sau mỗi commit; session docs đầy đủ; không để stale số liệu
  (mọi con số kiểm chứng DB thật).
---

# T114 — Master Roadmap Meta-Update

## Mục tiêu
Lộ trình Evidence-first (T108–T114) là văn bản **sống**: mỗi khi một task trong
chuỗi đổi trạng thái, cập nhật tasktodo/progress/roadmap/ROLLBACK trong cùng commit.

## Quy tắc
- Số liệu chỉ dùng DB thật (13/5/8 · 130 bảng · 447,885 · 40,327 · 248k) — không sao chép số cũ.
- Mỗi commit: code + docs hash-fill, kèm session doc.
- Dashboard cập nhật bằng `python scripts/build_progress_data.py`.

## Acceptance
- Không tồn tại số liệu lệch ở docs chính (tasktodo/progress/roadmap).
- Lộ trình T108–T114 hiển thị đúng trạng thái trên Dashboard.

## Tiến độ (2026-09-09) — DONE (commit `e822336` + session-note)
- Đồng bộ toàn chuỗi: tasktodo/progress/roadmap/SCHEMA_DESIGN phản ánh **T111 ✅ · T112 draft chờ duyệt ·
  T113 phần B ✅ · phần A blocked :5000**; ROLLBACK.md thêm 6 row (X·C113·C111·D113·D111 + hash-fill) đã
  hash-fill đúng commit; task files T111/T113/T114 ghi tiến độ; 2 session mới.
- Dashboard: `python scripts/build_progress_data.py` chạy lại (Progress + Data Quality đọc
  `design_compliance.json`). Không còn placeholder hash; 0 số liệu stale.