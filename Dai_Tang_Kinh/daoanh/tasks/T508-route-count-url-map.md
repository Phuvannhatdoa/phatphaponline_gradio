---
id: T508
title: "Đo số route chuẩn bằng app.url_map lúc chạy (tách app.py:5000 và server.py:5001)"
module: Docs
priority: p2
status: coding
created: 2026-10-31
updated: 2026-10-31
owner: unassigned
parent: tasks/T322-docs-cap-nhat-reality-check-plan.md
depends_on: []
done_when: |
  Đo được số route thực tế lúc runtime bằng len(app.url_map) (hoặc tương đương) cho cả
  app.py (port 5000) và server.py (port 5001), tách riêng 2 số, so sánh với số đếm tĩnh
  437 bằng regex decorator hiện có trong REALITY_CHECK.md. Chỉ đọc, không ghi DB, không sửa
  route code. Cập nhật docs/integration/REALITY_CHECK.md với số đo mới + nguồn đo (lệnh/script
  dùng). Admin xác nhận số chuẩn sau khi có kết quả đo — KHÔNG tự chọn số chuẩn khi chưa có
  xác nhận.
revert: |
  Chỉ sửa docs/integration/REALITY_CHECK.md (đọc). Hoàn tác bằng backup
  docs/sessions/<ngày làm>/REALITY_CHECK.md.bak-before-t508 hoặc git revert nếu đã commit.
  Không có DB mutation, không có revert DB cần thiết.
outcome: >
  2026-10-31: tạo task theo quyết định Admin (họp T322) — chọn phương án C cho cách đo số
  route chuẩn. Chưa bắt đầu đo.
---

# T508 — Đo số route chuẩn bằng app.url_map lúc chạy

## 1. Bối cảnh

T322 đo số route bằng regex decorator `@\w*\.route(` tĩnh trên source, ra 448 tổng − 11 route
tooling/dev/test = 437. Đây là **cận dưới**, không phải số tuyệt đối vì chưa đo `app.url_map`
lúc runtime (Flask tự thêm route framework như `/static/<path:filename>`, và không bắt được
route đăng ký động qua blueprint phức tạp hoặc alias).

**Quyết định Admin (họp T322, 2026-10-31):** chọn phương án **C** — đo số route chuẩn bằng
`len(app.url_map)` lúc app đang chạy thật, tách riêng con số của `app.py` (cổng 5000) và
`server.py` (cổng 5001). Giữ nguyên số tham chiếu cũ 437 (đếm tĩnh) làm mốc so sánh, không xóa.

## 2. Mục tiêu

- Viết script hoặc endpoint chẩn đoán (chỉ đọc) để in `len(app.url_map._rules)` (hoặc
  `list(app.url_map.iter_rules())`) khi `app.py`/`server.py` đang chạy.
- Ghi lại 2 số: route của app.py (5000) và route của server.py (5001), có loại trừ rule nội
  bộ của Flask (`static`) nếu cần làm rõ, ghi chú rõ có loại trừ hay không.
- So sánh với số đếm tĩnh 437/448 hiện có trong `docs/integration/REALITY_CHECK.md`, giải
  thích chênh lệch (nếu có).

## 3. Không làm trong task này

- Không tự chọn "số chuẩn" để công bố — chỉ đo và báo cáo, Admin xác nhận số chuẩn sau khi có
  kết quả đo thật.
- Không sửa route, không đổi logic app.py/server.py.
- Không ghi DB.

## 4. Các bước

- [ ] **Bước 1 —** viết script đo (chỉ đọc) chạy khi server đang live, hoặc thêm đoạn debug
      tạm thời không commit vào code production.
- [ ] **Bước 2 —** chạy đo thật trên local (app.py:5000, server.py:5001), ghi log kết quả.
- [ ] **Bước 3 —** sao lưu REALITY_CHECK.md trước khi sửa, cập nhật số đo mới + nguồn đo.
- [ ] **Bước 4 —** báo Admin kết quả đo, xin xác nhận số chuẩn.
- [ ] **Bước 5 —** Admin xác nhận DONE.
