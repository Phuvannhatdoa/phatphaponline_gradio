---
id: T445b
title: "Wizard UI T444 — phần logic thật (B1, B3, B4, B5/B8, B7, B9, CSV), chờ T444 backend"
module: Admin / Places translation
priority: high
status: pending
created: 2026-11-02
updated: 2026-11-02
owner: unassigned
parent: tasks/T445-placevn-wizard-ui-b0-b9.md
depends_on: [T444, T445a]
former_ids: []
done_when: |
  Các bước có dữ liệu thật, kiểm bằng trình duyệt (không chỉ kiểm cú pháp):
  - B1: preview 3.800 ID, checkbox, xuất sample_b1_fixed.csv.
  - B3: nạp từ điển 2.446 mục, idempotent, có dry-run.
  - B4: lưu 7 quy tắc từ form inline.
  - B5/B8: theo dõi batch Gemini bằng số liệu thật (polling).
  - B7: nạp 100 mẫu, duyệt mục chọn.
  - B9: thống kê, missing/duplicate, xuất 3 CSV.
  - Resume khi đóng/mở lại wizard; E2E trên trình duyệt có ảnh chụp và network log.
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Hoàn tác bằng sao lưu trong session của task này khi bắt đầu.
outcome: >
  2026-11-02: tách từ T445 theo quyết định Admin. Chưa bắt đầu; chờ T444 backend.
---

# T445b — Logic thật của wizard

Chưa bắt đầu. Chỉ làm sau khi T444 backend (dịch Gemini) xong và T445a được Admin xác nhận DONE.
