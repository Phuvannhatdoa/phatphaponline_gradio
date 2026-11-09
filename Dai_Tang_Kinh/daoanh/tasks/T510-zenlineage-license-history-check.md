---
id: T510
title: "Đọc lịch sử ZENLINEAGE (chỉ đọc) — quyết có UPDATE sang LEGACY hay không"
module: Data
priority: p2
status: pending
created: 2026-10-31
updated: 2026-10-31
owner: unassigned
parent: tasks/T322-docs-cap-nhat-reality-check-plan.md
depends_on: [T231]
done_when: |
  Đã đọc (chỉ đọc) lịch sử ghi/giá trị legal_status_at_ingest cho nguồn ZENLINEAGE — lý do vì
  sao đang đo được NULL thay vì LEGACY như T231 ghi nhận. Có báo cáo rõ: giá trị hiện tại,
  lịch sử thay đổi nếu tìm được (log/audit), và đề xuất có nên UPDATE sang LEGACY hay không
  kèm lý do. Admin quyết định cuối cùng có UPDATE hay không — KHÔNG tự UPDATE khi chưa có
  quyết định này.
revert: |
  Giai đoạn đọc lịch sử: không ghi DB, không cần revert.
  Nếu sau này Admin duyệt UPDATE: phải có backup DB riêng (sqlite backup API,
  PRAGMA quick_check=ok) trước khi ghi, và lệnh revert cụ thể (UPDATE ngược lại NULL hoặc khôi
  phục backup) phải được bổ sung vào docs/ROLLBACK.md trước khi --apply.
outcome: >
  2026-10-31: tạo task theo quyết định Admin (họp T322) — chọn phương án B (đọc lịch sử
  ZENLINEAGE thành task riêng, tách khỏi T322). Chưa bắt đầu đọc.
---

# T510 — Đọc lịch sử ZENLINEAGE, quyết có UPDATE sang LEGACY hay không

## 1. Bối cảnh

T322 đo được: task T231 ghi nhận cột `legal_status_at_ingest` của nguồn `ZENLINEAGE` là
`LEGACY`, nhưng đo thực tế trong DB lại ra `NULL`. Chưa rõ nguyên nhân: có thể (a) T231 chưa
từng UPDATE cho nguồn này, (b) đã UPDATE nhưng bị ghi đè sau đó bởi import khác, hoặc (c) tài
liệu T231 ghi sai từ đầu.

**Quyết định Admin (họp T322, 2026-10-31):** chọn phương án **B** — tách việc đọc lịch sử
ZENLINEAGE thành task riêng (task này, T510), không xử lý trong T322.

## 2. Mục tiêu

Đọc (chỉ đọc) để trả lời:
- Giá trị hiện tại thật của `legal_status_at_ingest` cho mọi dòng thuộc nguồn ZENLINEAGE.
- Có bằng chứng (log, audit table, git history của script import) cho thấy từng có UPDATE
  thành LEGACY chưa, và nếu có thì bị ghi đè khi nào/bởi cái gì.
- Đề xuất: có nên UPDATE lại sang LEGACY hay không, dựa trên ý nghĩa thực tế của cờ này
  (license/trạng thái pháp lý dữ liệu).

## 3. Không làm trong task này

- Không UPDATE DB khi chưa có quyết định của Admin.
- Không đổi task T231.
- Mọi UPDATE DB (nếu sau này được duyệt) cần sao lưu và Admin duyệt riêng — không gộp vào
  lượt đọc này.

## 4. Các bước

- [ ] **Bước 1 —** query chỉ đọc giá trị `legal_status_at_ingest` hiện tại cho ZENLINEAGE.
- [ ] **Bước 2 —** tìm log/audit/script import liên quan, dựng lại lịch sử nếu có thể.
- [ ] **Bước 3 —** viết báo cáo + đề xuất, trình Admin.
- [ ] **Bước 4 —** (nếu Admin duyệt UPDATE) chuyển sang task/bước ghi riêng có backup.
- [ ] **Bước 5 —** Admin xác nhận DONE.
