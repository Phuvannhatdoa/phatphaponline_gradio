# Session: Seed Task Board 17 task + Docs chuẩn GitBook

**Ngày:** 2026-08-13
**Module:** Hạ tầng / Docs
**Task liên quan:** T01–T17 (feature dev board), docs/SUMMARY.md, docs/README.md

---

## Mục tiêu

1. Cập nhật task mới vào các file `.md` để **claudecode và opencode hiểu chức năng cần có** để lên plan.
2. Từ các `docs/*.md`, trình bày tài liệu theo **chuẩn định dạng GitBook** của GitHub/opensource.

## Đã làm

### A. Seed Task Board (chuẩn Claude Code) — 17 task

Tạo file mới trong `tasks/` (1 task = 1 file, frontmatter YAML + acceptance criteria):

| ID | File | Nguồn gốc |
|----|------|-----------|
| T01 | seed-monk-persons | tasktodo Task 1 |
| T02 | passage-vi-entity-summary | tasktodo Task 2 + Khoá 5 phase 2 |
| T03 | fuzzy-match-cbeta-catalog | tasktodo Task 3 |
| T04 | marcus-glossaries-link | tasktodo Task 4 |
| T05 | ttl-expand-etl | tasktodo Task 5 (còn lại ~2000 file) |
| T06 | gis-cluster-click | tasktodo Task 6 + progress GIS density |
| T07 | wikipedia-fallback | tasktodo Task 7 |
| T08 | missing-hanzi-admin | tasktodo Task 8 |
| T09 | dashboard-stats-api | (đã có từ trước) |
| T10 | dila-place-index | Roadmap Khoá 4 |
| T11 | rag-vi-chat | Roadmap Khoá 6 |
| T12 | dich-muot-cache-translation | Roadmap Khoá 7 |
| T13 | cbdb-chatling-ai | progress CBDB |
| T14 | time-authority-import | DEV_HISTORY audit 2026-08-11 |
| T15 | keyword-export-delete | progress Keywords |
| T16 | nexus-points | DEV_HISTORY audit 2026-08-11 |
| T17 | knowledge-graph-viz | DEV_HISTORY audit 2026-08-11 |

Lưu ý: gộp "GIS cluster density icons" (dự kiến T14) vào T06 để tránh trùng; đánh lại số thứ tự không trùng ID.

### B. Docs chuẩn GitBook

- `docs/SUMMARY.md` — mục lục GitBook (liên kết toàn bộ tài liệu, nhóm theo mục).
- `docs/README.md` — trang entry: giới thiệu, "Bắt đầu từ đâu", cấu trúc tài liệu.
- `docs/bug-reports/README.md`, `docs/fix-logs/README.md`, `docs/sessions/README.md` — index từng thư mục con.
- Cập nhật `tasks/README.md` — thêm mục 7 "Registry task (2026-08-13)" (bảng 17 task + nguồn gốc).

## Verify

```powershell
python scripts\build_progress_data.py
# → 12 module, 80 endpoint, 65%, 17 task, Git 474 commits
GET http://localhost:5000/daoanh/api/progress/dashboard?regenerate=1 → 200 (tasks: 17)
GET http://localhost:8080/dashboard/dashboard_process.html → 200
node scripts\e2e-test.js → PASS
```

## Bước kế tiếp

- Dev theo thứ tự: T09 → T01 → T02 → T14 (xem DEV_HISTORY.md §Thứ tự ưu tiên).
- Sau mỗi task → tick acceptance criteria + đổi status → `python scripts/build_progress_data.py` → Refresh dashboard.
