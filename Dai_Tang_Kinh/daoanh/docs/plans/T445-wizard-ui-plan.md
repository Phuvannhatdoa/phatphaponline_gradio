# T445 — Wizard UI cho T444 Gemini Places Translation (B0-B9)

## Mục tiêu
Nâng cấp `placevn.html` thành Wizard Flow UI (B0→B9) để phục vụ T444.

## Đã triển khai (Coder)
- Thêm state `wizardOpen`, `wizardStep` (0-8), `wizardBusy`, `wizardLogs`, `wizardProgress`.
- Thêm nút "Wizard T444" trên header placevn.html.
- Thêm modal Wizard 9 bước (B0-B9) với navigation Back/Next.
- Backend: 9 endpoint stub/robust trong app.py:
  - POST /daoanh/api/admin/backup
  - POST /daoanh/api/admin/fix-ids
  - POST /daoanh/api/admin/add-columns
  - POST /daoanh/api/admin/load-dictionary
  - POST /daoanh/api/admin/update-rules
  - POST /daoanh/api/admin/approve-sample
  - POST /daoanh/api/admin/report
  - GET /daoanh/api/admin/export-csv
  - GET /daoanh/api/admin/batch-status
- Real-time: hiện dùng polling `/batch-status` (WebSocket chưa có lib; có thể nâng cấp SSE sau).

## Chưa làm / chờ T444
- Logic backend chi tiết cho fix-ids, load-dictionary, report, batch monitoring.
- WebSocket thật (cần flask-sock/simple-websocket) — chưa cài.
- Resume state persistence (localStorage) — chưa làm.

## Files changed
- admin/placevn.html
- app.py
- docs/plans/T445-wizard-ui-plan.md
