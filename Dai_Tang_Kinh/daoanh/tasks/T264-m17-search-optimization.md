---
id: T264
title: "M17 — Tối ưu tìm kiếm (search)"
status: pending
created: 2026-10-07
updated: 2026-10-07
owner: ""
---

# T264 — Tối ưu tìm kiếm (search) — M17

**Task:** docs/integration/M17-search-optimization.md

## M?c tiêu
Nâng t?c d?. & đ? ch?nh tra c?u: fuzzy search, ranking, caching, query log (ph?ng án trung t?m = Search All).

## Cách ti?p c?n
- Phase 1 — `search_opt.py` (SSOT, pattern style_constitution): SearchCache LRU d?ng t?i 1000; levenshtein + fuzzy d?ng index (Zero-RAM); rank_results (match_type + authority + boost + feedback) + explain[].
- Phase 2 — additive DB: `search_query_log` (top 10k/ngày, rotate weekly), `search_feedback` (vote +-1); c?p nh?t docs/db_schema.md; API additive GET|POST /daoanh/api/search/cache/stats, /cache/purge, /ranking/config, /feedback.
- Phase 3 — 2 trang UI (pattern search_all.html): admin/search_caching.html (cache view + gauge + Purge), admin/search_ranking.html (test query + score + explain + boost slider + thumbs); route /daoanh/search/caching + /ranking.
- Test tests/test_m17_search_opt.py + wire test:m17 vao pipeline (unit + benchmark d?i 200ms).

## Acceptance criteria
- [ ] Fuzzy g?n cung 90% query l?i sai đánh máy (fixture >=20)
- [ ] Cache hit 70% tr?n truy v?n l?p
- [ ] Top-3 ch?c 80% tro?n (golden 30)
- [ ] API d?i 200ms
- [ ] Feedback đ?i ranking 24h n?i

## Notes
- Code do Claude Code vi?t; Cline docs-only. Module: DILA Integration Layer.
- Session log docs/sessions/2026-10-07_T264-m17-search-optimization.md; npm run pipeline XANG; build_progress_data.py; commit FEAT-m17-search-optimization.

## Ghi chú (dọn tài liệu 2026-10-08)
- File gốc thiếu frontmatter và tiêu đề ghi "T260" (trùng với task T260 có sẵn và không liên quan —
  `tasks/T260-evidence-claim-inspector-cross-source.md`). Đã thêm frontmatter YAML (`id: T264`,
  `status: pending`, `owner` để trống) và sửa "T260" → "T264" ở tiêu đề + đường dẫn session log, vì
  `docs/integration/M17-search-optimization.md` (đặc tả gốc) cũng ghi "tasks/T260-m17-search-optimization.md" —
  cho thấy đây là tham chiếu còn sót lại từ lúc đánh số cũ, không phải task T260 thật.
- Đã sửa phần mã hóa lỗi (ký tự "?") trong dòng tiêu đề dựa theo ngữ cảnh rõ ràng (tên file, đặc tả M17).
  **Chưa sửa** các ký tự "?" còn rải rác trong phần "Mục tiêu", "Cách tiếp cận", "Acceptance criteria" —
  ngoài phạm vi yêu cầu dọn dẹp lần này; nội dung nghiệp vụ giữ nguyên. Cần Admin xác nhận nếu muốn sửa
  toàn bộ mã hóa trong thân file và xác nhận `owner` của task này.
- `status: pending` được suy ra từ Acceptance criteria toàn bộ còn `[ ]` chưa tick — không có bằng chứng
  nào trong thân file cho thấy task đã hoàn thành.
