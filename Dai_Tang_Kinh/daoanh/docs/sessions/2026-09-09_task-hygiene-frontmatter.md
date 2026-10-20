# Session — Task hygiene frontmatter (khớp SSOT)

**Ngày:** 2026-09-09 · **Commit:** `0d158d3`

## Vấn đề
Audit `tasks/*.md` frontmatter thấy lệch SSOT (tasktodo/roadmap):
- `tasks/T109-provenance-conflict-workflow.md`: `status: in_progress` — nhưng T109 đã DONE.
- `tasks/T111-persona-display-disclaimer.md` và `tasks/T114-roadmap-meta-update.md`: hai dòng
  `status:` (`pending` + `done`) trùng → YAML last-wins = done, nhưng dễ hiểu sai.

## Thay đổi (docs-only, 0 code, 0 DB)
- T109: `status: in_progress` → **done** (+ `updated` → 2026-09-09).
- T111 / T114: xoá dòng `status: pending` trùng, giữ `done`.
- `docs/ROLLBACK.md`: row `0d158d3`.
- Regen `data/progress_data.json` (dashboard phản ánh done mới).

## Ghi chú audit
- Slug lệch id: `tasks/T60-bio-vi-lexicon-phase2.md` (id T65) · `T61-place-desc-vi-lexicon-diadanh.md` (id T66)
  — có thể chủ ý (đánh số lại), **không đụng** trong phiên này; cần xác nhận.
- Port **:5000 đã trống** → T113 phần A (QA live) hết blocked điều kiện, cần start `app.py` + QA.
- Server :37700 (claude-mem) vẫn tắt → observation chưa POST (payloads lưu `%TEMP%\opencode\obs_*`).

## Rollback
- `git revert --no-edit 0d158d3` (0 DB).

## Việc kế tiếp
1. (Chờ Lee/fire) Start `app.py` :5000 → chạy QA phần A T113 (Batch 4 + Thiếu Lâm Tự + evidence drawer + doctrine tab).
2. Kiểm tra slug T60/T61/T65/T66 — sửa nếu thật sự lệch.
3. POST observation :37700 khi server mở.