---
id: T508
title: "Đo số route chuẩn bằng app.url_map lúc chạy (tách app.py:5000 và server.py:5001)"
module: Docs
priority: p2
status: done
created: 2026-10-31
updated: 2026-11-01
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
  docs/sessions/2026-11-01/T508-coder/backup/REALITY_CHECK.md.bak-before-coder hoặc git revert nếu đã commit.
  Không có DB mutation, không có revert DB cần thiết.
outcome: >
  2026-10-31: tạo task theo quyết định Admin (họp T322) — chọn phương án C cho cách đo số
  route chuẩn. Chưa bắt đầu đo.
  2026-11-01 (coder): ĐÃ ĐO lúc runtime bằng len(app.url_map.iter_rules()).
  app.py (5000): 369 rule (368 nếu trừ rule Flask `static`), 344 view function, 366 path,
  method GET 245/ POST 124/ PUT 3/ DELETE 1/ PATCH 1.
  server.py (5001): 9 rule (8 nếu trừ `static`), 7 view function.
  Đếm tĩnh cùng ngày (regex `@\w*\.route(`): app.py 339 + server.py 8 = 347; toàn bộ *.py
  trong daoanh (bỏ docs/sessions) = 423 (20 file), (bỏ thêm docs/reports) = 419 (18 file).
  Script + log: docs/sessions/2026-11-01/T508-coder/ (measure_routes.py, route-count.log,
  route-count-utf8.txt, route-count-raw.json, live-server-check.log).
  Đã sao lưu (backup/REALITY_CHECK.md.bak-before-coder) và cập nhật
  docs/integration/REALITY_CHECK.md: thêm mục "Số route đo lúc runtime", ghi rõ số đo
  369/9, **số chuẩn Admin xác nhận = 376 (368 + 8, bỏ static)**, mốc tĩnh = 347.
  Không ghi DB: import app.py có gọi các ensure_*() chạy CREATE TABLE IF NOT EXISTS, nên
  script chuyển mọi sqlite3.connect sang thư mục sandbox tạm; đã xác nhận project KHÔNG
  sinh data/lineage.db (Test-Path data = False).
  **Admin đã xác nhận (2026-11-01)**: số chuẩn = 376; mốc 437/448 bỏ khỏi tài liệu (lịch sử,
  không tái lập được — nguồn gốc là file routes_*.py + core.py lúc T322, nay đã gộp vào app.py).
  Đã sửa theo TESTER-REPORT.md: (1) REALITY_CHECK.md cập nhật số chuẩn 376 + mốc 347; (2) sửa
  lời giải thích 448/437; (3) sửa số liệu 419/18 file → 423/20 (bỏ sessions) / 419/18 (bỏ thêm reports); (4) thêm route-count-utf8.txt; (5) sửa revert path; (6) status → testing.
  Bước 5: chờ Admin xác nhận DONE (coder không tự đánh DONE).

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

- [x] **Bước 1 —** viết script đo (chỉ đọc) chạy khi server đang live, hoặc thêm đoạn debug
      tạm thời không commit vào code production.
      → `docs/sessions/2026-11-01/T508-coder/measure_routes.py` (session artifact, không
      phải code production; patch `sqlite3.connect` sang sandbox để không ghi DB project).
- [x] **Bước 2 —** chạy đo thật trên local (app.py:5000, server.py:5001), ghi log kết quả.
      → `route-count.log` + `route-count-raw.json` + `live-server-check.log` (cùng thư mục).
      Kết quả: app.py **369 rule** (368 trừ `static`), server.py **9 rule** (8 trừ `static`).
- [x] **Bước 3 —** sao lưu REALITY_CHECK.md trước khi sửa, cập nhật số đo mới + nguồn đo.
      → backup: `docs/sessions/2026-11-01/T508-coder/backup/REALITY_CHECK.md.bak-before-coder`;
      đã thêm mục "Số route đo lúc runtime" vào `docs/integration/REALITY_CHECK.md`.
- [x] **Bước 4 —** báo Admin kết quả đo, xin xác nhận số chuẩn.
      → báo cáo trong `docs/sessions/2026-11-01/T508-coder/CODER-REPORT.md`; câu hỏi chờ
      Admin ghi ở mục 4 của báo cáo.
- [ ] **Bước 5 —** Admin xác nhận DONE. **(chờ Admin — coder không tự đánh DONE)**

## 5. Quyết định Admin (2026-11-01) và sửa theo tester

Admin đã chọn:
- **Số chuẩn runtime = 376** = `app.py` 368 + `server.py` 8 (phương án b: đo `len(app.url_map.iter_rules())`, BỎ rule `static` của Flask). Ghi rõ đây là số chuẩn; 369/9 và 344/7 chỉ là số tham khảo.
- **Mốc 437 (đếm tĩnh cũ): BỎ khỏi tài liệu.** Thay bằng **347** = đếm tĩnh lại trên code hiện tại (`app.py` 339 + `server.py` 8).

Nguồn: `docs/sessions/2026-11-01/T508-coder/TESTER-REPORT.md` (trong worktree này).

- [x] **Sửa 1 —** Cập nhật `docs/integration/REALITY_CHECK.md`: số chuẩn 376 (368 + 8, bỏ `static`), mốc tĩnh 347. Xoá mọi chỗ ghi 437/448 như số đúng; nếu cần nhắc thì ghi "437 là số cũ, không tái lập được".
- [x] **Sửa 2 —** Sửa giải thích nguồn gốc 448/437 trong REALITY_CHECK và CODER-REPORT §5.2: không phải do "bản backup app.py". Theo `docs/sessions/2026-10-31/REALITY_CHECK.md.bak-before-t322-clean`, lúc T322 route nằm ở `routes_*.py`, `core.py`, `t265_routes.py`, nay không còn. Ghi đúng như vậy.
- [x] **Sửa 3 —** Sửa số liệu "419 / 18 file": nếu chỉ bỏ `docs/sessions` thì 423 / 20; 419 là khi bỏ thêm `docs/reports`. Ghi đúng điều kiện.
- [x] **Sửa 4 —** Đổi `route-count.log` sang UTF-8 (hoặc thêm bản UTF-8 `.txt`) để đọc được. → đã thêm `route-count-utf8.txt`.
- [x] **Sửa 5 —** Sửa tên file backup trong trường `revert` cho khớp file thật.
- [x] **Sửa 6 —** Đổi lại `status: testing` khi xong. Ghi kết quả vào outcome.
- [ ] **Không làm:** không sửa `app.py`/`server.py`, không ghi DB, không commit.
