# Session: Process Dashboard — Note UNdone TTL file

**Date:** 2026-08-31
**Branch/Task:** Process dashboard note
**Status:** DONE

## Objective
Thêm đoạn chú thích rõ ràng lên Process Tracker dashboard (`dashboard/dashboard_process.html`) thông báo cho admin rằng **TTL file** chưa hoàn thành (UNdone) — để làm sau.

## Context
- Module "TTL Thiền Sư VN" (progress 71%, in_progress) có task **T05** — "TTL mở rộng ETL ~2000 file + dila_id" đang **blocked**.
- `data/ttl/old/*.ttl` (16 file) chưa được nạp/xử lý đầy đủ.

## Thay đổi — `dashboard/dashboard_process.html`
Chèn banner chú thích ngay sau tiêu đề section "Task Board — chức năng cần dev" (trước KPI row):
- Nội dung: "⚠️ UNdone — TTL file: Việc nạp/xử lý `data/ttl/old/*.ttl` (mở rộng ETL ~2000 file + gán `dila_id`) chưa hoàn thành — task T05 đang blocked. Để làm SAU (kế hoạch song song với gateway TTL hiện tại). Xem thẻ T05 ở cột Blocked bên dưới."
- Style: nền amber (rgba(245,158,11,0.12)), viền amber, chữ #fde68a → nổi bật, admin dễ thấy.

## Verification
- `http://localhost:5000/daoanh/dashboard/` (app.py) trả HTTP 200 + chứa banner UNdone.
- `http://localhost:8080/daoanh/dashboard/` (gateway 8080) trả HTTP 200 + chứa banner.
- `npm run e2e`: dashboard_process.html → Script block 1 Syntax OK, ALL PASSED.

## Files Changed
- `dashboard/dashboard_process.html` — banner note UNdone TTL.
- `docs/sessions/2026-08-31_process_dashboard_ttl_undone_note.md` (log này).

## Next Steps
- Khi nào dev pipeline TTL ETL mở rộng (T05), cập nhật lại banner (hoặc gỡ khi task done).
