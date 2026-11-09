---
id: T509
title: "T231 Bước 4 — nối LicenseGate vào route app (code route, cần Admin duyệt phạm vi trước)"
module: Backend
priority: p2
status: pending
created: 2026-10-31
updated: 2026-10-31
owner: unassigned
parent: tasks/T322-docs-cap-nhat-reality-check-plan.md
depends_on: [T231]
done_when: |
  Bước 4 của T231 (nối LicenseGate vào route app — xem thân bài T231 hiện vẫn ghi ⬜ TODO dù
  frontmatter status: done) được thực hiện đúng phạm vi đã được Admin duyệt trước khi code.
  Route nào bị gate, hành vi gate (chặn/log/cảnh báo) phải khớp đúng mô tả đã duyệt. Admin xác
  nhận DONE sau khi test thật qua browser/route thật — không tự đánh DONE.
revert: |
  Code route thay đổi — backup file route liên quan trước khi sửa (docs/sessions/<ngày>/).
  Revert bằng git revert (nếu đã commit) hoặc khôi phục file backup. Nếu có ghi DB (ví dụ cờ
  gate trong bảng cấu hình), phải có backup DB riêng + lệnh revert DB tương ứng — bổ sung khi
  biết chi tiết implementation.
outcome: >
  2026-10-31: tạo task theo quyết định Admin (họp T322) — chọn phương án B, giữ T231 ở trạng
  thái done nhưng tách Bước 4 (route app gate) thành task riêng này. Chưa bắt đầu code.
---

# T509 — T231 Bước 4: nối LicenseGate vào route app

## 1. Bối cảnh

T322 phát hiện mâu thuẫn: task `T231` có frontmatter `status: done` nhưng thân bài Bước 4
("nối LicenseGate vào route app") vẫn đánh dấu `⬜ TODO`. Nghĩa là phần quan trọng nhất của
T231 (áp gate thật vào route, không chỉ pass-through dữ liệu `legal_status_at_ingest=LEGACY`)
**chưa được triển khai**.

**Quyết định Admin (họp T322, 2026-10-31):** chọn phương án **B** — giữ T231 ở trạng thái
`done` (không đổi lại thành `in_progress`/`pending`), tách riêng Bước 4 thành task mới (task
này, T509) để làm độc lập và theo dõi riêng.

## 2. Mục tiêu

Hoàn thiện việc nối `LicenseGate` (hoặc cơ chế tương đương đã thiết kế ở T231) vào route thật
của app, để license/giấy phép dữ liệu được kiểm tra tại thời điểm request thay vì chỉ lưu cờ
tĩnh trong DB.

## 3. BẮT BUỘC trước khi code

**Code route thay đổi cần Admin duyệt phạm vi trước khi làm.** Agent phải trình bày:
- Route nào sẽ bị gate (danh sách cụ thể).
- Hành vi khi gate kích hoạt (chặn 403? chỉ log? cảnh báo UI?).
- Có ảnh hưởng route public (`/daoanh/api/public/*`) hay chỉ route admin?

Chỉ sau khi Admin duyệt phạm vi này mới bắt đầu sửa code.

## 4. Không làm trong task này

- Không tự quyết phạm vi gate khi chưa có Admin duyệt.
- Không đổi `status` của T231.
- Không ghi DB tay ngoài những gì đã được duyệt trong implementation.

## 5. Các bước

- [ ] **Bước 1 —** đọc lại chi tiết T231 Bước 4 + code `LicenseGate` hiện có (nếu đã có class/
      module nào dạng khung).
- [ ] **Bước 2 —** soạn đề xuất phạm vi route bị gate, trình Admin duyệt.
- [ ] **Bước 3 —** sau khi Admin duyệt, backup file route liên quan, code nối gate.
- [ ] **Bước 4 —** test thật qua route/browser, xác nhận gate hoạt động đúng phạm vi đã duyệt.
- [ ] **Bước 5 —** Admin xác nhận DONE.
