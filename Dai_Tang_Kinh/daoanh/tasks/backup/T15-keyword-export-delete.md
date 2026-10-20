---
id: T15
title: Keyword map export/delete + category filter
module: Keywords
priority: low
status: done
depends_on: []
created: 2026-08-13
updated: 2026-08-13
done_when: keyword_import.html có export/delete keyword_map + filter theo category
---

# T15 — Keyword map export/delete + category filter

## Mục tiêu
Progress Keyword Import: thêm feature export/delete `keyword_map` và filter theo category cho admin.

## Cách tiếp cận
- API export keyword_map (CSV/JSON) có filter category.
- API delete keyword_map (theo id hoặc bulk).
- UI keyword_import.html thêm nút Export/Delete + dropdown category filter.
- Giữ nguyên parse_txt/bulk_import hiện có.

## Acceptance criteria (checklist)
- [ ] API export CSV/JSON
- [ ] API delete (đơn + bulk)
- [ ] Filter category trong UI
- [ ] Không break parse_txt/bulk_import
