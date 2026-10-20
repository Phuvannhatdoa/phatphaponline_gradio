---
id: T428
title: "BUG-046: Cột Claude trong namevimap.html bị chèn data y chang cột TTL name_vi"
status: done
created: 2026-10-19
updated: 2026-10-20
done_when: >
  Cột "Claude" trên http://127.0.0.1:8080/daoanh/admin/namevimap.html hiển thị
  giá trị đúng nguồn của nó (field claude/codex_name, không phải bản sao của
  ttl_name_vi). Root cause được xác định ở đúng lớp (data/backend/frontend) và
  sửa tại đó. Admin xác nhận DONE sau khi xem screenshot before/after.
---

## Triệu chứng

Route: `http://127.0.0.1:8080/daoanh/admin/namevimap.html`
Bảng cột: DILA ID | Hán tự | DILA name_vi | Claude | Gemini (39,269/48,673) | TTL name_vi | Từ Điển

Cột "Claude" hiển thị data giống y hệt cột "TTL name_vi" — không phải data
riêng của Claude/codex (từ import XML commit 0d2ea40, bảng `codex_person_name`
theo BUG-045/liên quan).

## Nguyên nhân nghi ngờ (chưa xác minh)

- Backend: SQL SELECT alias sai, hoặc thiếu JOIN bảng codex_person_name, lấy
  nhầm field ttl_name_vi gán vào key "claude".
- Frontend: `namevimap.html` bind nhầm field cho cột Claude (dùng
  `row.ttl_name_vi` thay vì field codex/claude riêng).
- Data: script import ghi nhầm giá trị vào cột claude_name trong DB.

## Phạm vi dự kiến

- Đọc API phục vụ `namevimap.html` (tìm route "namevimap" trong `app.py`).
- Đọc SQL SELECT, kiểm tra field mapping.
- Đọc DB trực tiếp (`daoanh/data/lineage.db`) so sánh field ttl_name_vi vs
  claude/codex field.
- Đọc frontend `daoanh/admin/namevimap.html` xem bind field nào vào cột nào.
- Sửa đúng lớp root cause (không hard-code UI).
- Backup file trước khi sửa vào `docs/sessions/2026-10-19/BUG-046/`.

## Tham chiếu

- `daoanh/docs/bugs.md` — mục "BUG-046"
- Liên quan BUG-045 (codex_person_name import, cột Claude hiện 0)
