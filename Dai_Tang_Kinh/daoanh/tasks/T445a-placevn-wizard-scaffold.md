---
id: T445a
title: "Wizard UI T444 — phần khung (scaffold): route đúng spec, B2 dry-run, stub 501, giao diện"
module: Admin / Places translation
priority: high
status: done
created: 2026-11-01
updated: 2026-11-02
owner: unassigned
parent: tasks/T445-placevn-wizard-ui-b0-b9.md
depends_on: []
former_ids: []
done_when: |
  Khung wizard đúng spec, không giả thành công:
  - 9 route có tên đúng spec (load-schema, batch-monitor, và alias cũ) trong app.py.
  - load-schema mặc định dry-run, chỉ ALTER khi apply=true.
  - Route chưa làm trả HTTP 501 "chưa triển khai", không trả success: true.
  - WebSocket đổi thành polling: ghi lệch spec trong outcome (Admin duyệt).
  - placevn.html chỉ thêm, giữ mã cũ; cú pháp app.py và khối JS đạt.
  Phần logic thật (B1, B3, B4, B5/B8 dữ liệu, B7, B9, CSV) KHÔNG thuộc T445a, chuyển sang T445b.
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Hoàn tác bằng sao lưu docs/sessions/2026-11-01/T445-coder/backup/*.bak-before-coder.
outcome: >
  2026-11-02: tách từ T445 theo quyết định Admin.
  (1) LỆCH SPEC — WebSocket đổi thành polling, Admin đã duyệt lệch ngày 2026-11-02: spec T444 yêu cầu
  WebSocket real-time cho batch monitor; chưa triển khai vì project không có
  flask-sock và không thêm thư viện. Thay bằng polling GET
  /daoanh/api/admin/batch-monitor (alias /batch-status); ghi chú trong code tại
  app.py dòng 25960-25962. Không giả lập WebSocket.
  (2) Tester OpenRouter 2026-11-01 đã báo PASS 5/5 mục khung: (a) route đúng tên spec
  (load-schema, batch-monitor) + alias cũ; (b) B2 load-schema mặc định dry-run, chỉ
  ALTER khi apply=true; (c) 6 route chưa làm trả HTTP 501, không success giả;
  (d) lệch spec WebSocket→polling được ghi trong code; (e) cú pháp app.py (AST) và
  khối JS placevn.html đạt. Xem docs/sessions/2026-11-01/T445a-coder/TESTER-REPORT.md.
  Chưa làm: logic thật (B1, B3, B4, B5/B8 dữ liệu, B7, B9, CSV) thuộc T445b; kiểm
  trình duyệt. Trạng thái giữ nguyên testing, không tự đánh DONE.
---

# T445a — Khung wizard (scaffold)

Phạm vi là phần đã code và đã kiểm ở T445. Các file đã đổi nằm trong
`docs/sessions/2026-11-01/T445-coder/CODER-REPORT.md`: `app.py` (10 endpoint) và `admin/placevn.html`.
