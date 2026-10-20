---
id: T154
title: "agents/README refresh (kiến trúc hiện tại)"
module: docs
priority: low
status: done
depends_on: []
created: 2026-09-17
updated: 2026-09-17
done_when:
  - "[x] Thay version-history lỗi thời (v2.x→v8.1, nội dung cũ 2026-04) bằng README hiện tại (kiến trúc 2 server + tính năng + công nghệ + nguyên tắc)"
  - "[x] 0 code, docs-only, additive"
---

# T154 — agents/README refresh (kiến trúc hiện tại)

> **Module:** `docs` (`Dai_Tang_Kinh/agents/README.md`)
> **Priority:** low · **Status:** done
> **Type:** docs (additive, 0 code, 0 ALTER, 0 DB, 0 API)
> **Created:** 2026-09-17 · **Updated:** 2026-09-17

---

## 1. Bối cảnh

`agents/README.md` còn tồn đọng chuỗi version-history lỗi thời (v2.2/v2.0/v5.4/v7.2/v8.0/v8.1, giai đoạn 2026-04) — mô tả tính năng không còn phản ánh hệ thống hiện tại (2 server 5000/5001, Đạo Ảnh Mapping, TTL Ontology, Cổng Nhân Vật Học T51…).

## 2. Thay đổi (docs-only)

- Rút gọn còn ~57 dòng, mô tả **kiến trúc hiện tại**:
  - Bảng máy chủ: Auth Gateway `server.py:5001` · Main Server `app.py:5000` · Local Gateway `local_gateway.py:8080`.
  - Tính năng chính: Đạo Ảnh Mapping · TTL Ontology · Nhân Vật Học Portal (T51) · CBETA Content (T53) · CBETA Analytics (T54).
  - Công nghệ (Flask/SQLite/GraphDB/Tailwind) + Nguyên tắc (Zero-RAM, bất biến dữ liệu) + Liên kết nhanh.
- Xoá chuỗi version-history cũ (không còn giá trị tham chiếu).
- 0 code, 0 DB.

## 3. Verify

- Markdown-only; không ảnh hưởng runtime/API/DB.

## 4. Revert

`git revert --no-edit <sha_T154>` (chỉ `agents/README.md`).
