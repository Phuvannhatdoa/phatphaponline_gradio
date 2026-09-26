# TASKS — Dashboard Process Tracker

> **Nguồn sự thật.** Tick `[x]` khi xong. Trạng thái: `[ ]` pending, `[~]` in progress, `[x]` done. Sau mỗi task cập nhật `handoff.md`.

## Bước 1 — Tài liệu plan (done khi: 4 file dashboard/ tồn tại)

- [x] T1. Tạo `dashboard/README.md` — tổng quan + entry point
- [x] T2. Tạo `dashboard/plan.md` — plan chi tiết đã chốt
- [x] T3. Tạo `dashboard/tasks.md` — checklist này
- [x] T4. Tạo `dashboard/handoff.md` — session continuation (trạng thái ban đầu)

## Bước 2 — Script generator (done khi: `python scripts/build_progress_data.py` ra JSON hợp lệ)

- [x] T5. Viết `scripts/build_progress_data.py`: parse docs MD (headers/✅⏳❌/claims)
- [x] T6. Scan code: `@app.route` (app.py, server.py, api_ttl_rebuild.py, conflict_server.py) + def/docstring scripts
- [x] T7. Đối chiếu → `{modules[], endpoints_compare[]}`, tính progress% theo code
- [x] T8. Ghi `data/progress_data.json` + summary stdout (tiếng Việt, try/except)
- [x] T9. Chạy CLI verify JSON đúng

## Bước 3 — Route API (done khi: GET 200 trả JSON)

- [x] T10. Thêm route `GET /daoanh/api/progress/dashboard` vào app.py (serve JSON, auto-gen nếu thiếu, `?regenerate=1`)
- [x] T11. Test local (app.py:5010) — route + regenerate đều 200

## Bước 4 — UI dashboard (done khi: render qua :8080, Refresh hoạt động)

- [x] T12. Tạo `dashboard/dashboard_process.html`: header + nút Refresh + timestamp
- [x] T13. Module cards: progress bar, badge routes found/claimed, warnings
- [x] T14. Bảng endpoints đối chiếu ✓/✗
- [x] T15. Auto-refresh 60 phút + fetch an toàn (timeout)

## Bước 5 — Verify thực

- [x] T16. API 5010: 200, 12 module, 45% tổng, 39 endpoints; regenerate=1 hoạt động
- [x] T17. Static HTML qua gateway :8080 = 200; E2E check dashboard_process.html PASS
- [x] T17b. Restart app.py (kill PID 13576 elevated) → API 5000 OK, qua gateway 8080 OK, Refresh `?regenerate=1` OK (49%)

## Bước 6 — Docs + commit (done khi: pipeline PASS)

- [x] T18. Tạo `docs/sessions/2026-08-13_progress_dashboard.md`
- [x] T19. Cập nhật `docs/progress.md` (thêm section Dashboard)
- [x] T20. Cập nhật `tasks.md` + `handoff.md` (trạng thái cuối)
- [ ] T21. Chạy `npm run pipeline` → PASS (WSL/bash chưa có sẵn trên Windows — đã chạy e2e + JS syntax thay thế)
- [x] T22. Commit từ git root `visjs-app/` (`feat: dashboard process tracker docs ↔ code + docs`) — commit `5cfb47e`

## Bước 7 — VPS Sync: rsync local → production (done khi: production khớp 100% với local)

- [x] T23. Fix `places/index.html` VPS: thêm section VĂN BẢN LIÊN QUAN + JS render `text_info` — verify production Thiếu Lâm Tự hiển thị đúng ✅ (2026-08-30)
- [ ] T24. Chạy rsync từ Git Bash (--exclude db/cache/log) — xem lệnh chi tiết trong `docs/sessions/2026-08-30_places_text_info_vps_sync.md`
- [ ] T25. Verify diff sau sync: compare file count/size, kiểm tra không mất db/log
- [ ] T26. Restart Flask trên VPS (`screen -dmS flask python app.py` hoặc `pkill -f app.py`)
- [ ] T27. Test production `https://phatphaponline.org/daoanh/places/` — mọi tính năng hoạt động đúng như local

## Bước 8 — HOME GUI Redesign (done khi: home.html mới live, search demo hoạt động)

> Đã phê chuẩn 2026-08-30. Mockup: https://claude.ai/code/artifact/7c6fd489-47f7-4319-b41d-88b23bcff41e  
> Spec đầy đủ: `docs/HOME-redesign-approved-2026-08-30.md`

- [x] T75. Implement search-first hero vào `daoanh/home.html` — commit `e5dd4fc` (2026-08-30)
- [x] T76. Thêm inline place result panel `#placeResult` (demo Thiếu Lâm Tự) — included in e5dd4fc
- [x] T77. Implement 6 module cards grid — included in e5dd4fc
- [x] T78. Wiring JS: handleSearch/showPlaceDemo/closePlaceDemo — included in e5dd4fc
- [ ] T79. Verify + sync: rsync home.html lên VPS (sau khi T24–T27 done), test production — đang chờ rsync admin
