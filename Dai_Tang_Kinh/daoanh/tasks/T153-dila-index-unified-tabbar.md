---
id: T153
title: "DILA Index unified tab bar (Place Index + Person Index)"
module: admin
priority: medium
status: done
depends_on: [T147]
created: 2026-09-17
updated: 2026-09-17
done_when:
  - "[x] Thêm tab bar chung cho admin/dila_index.html + admin/dila_person_index.html (📍 DILA Place Index / 👤 DILA Person Index)"
  - "[x] Đổi tiêu đề trang thành 'DILA Index' (Place/Person phân biệt qua tab active)"
  - "[x] Thuần UI (HTML/CSS), 0 ALTER, 0 DB, 0 API, additive"
---

# T153 — DILA Index unified tab bar (Place Index + Person Index)

> **Module:** `admin` (DILA Place Index · DILA Person Index)
> **Priority:** medium · **Status:** done
> **Type:** UI fix (additive, HTML/CSS only, 0 ALTER, 0 Schema, 0 DB, 0 API)
> **Created:** 2026-09-17 · **Updated:** 2026-09-17
> **Depends on:** T147 (DILA Person Index DONE)

---

## 1. Bối cảnh

Sau T147, `admin/dila_index.html` (Place) và `admin/dila_person_index.html` (Person) là 2 trang song song nhưng điều hướng rời rạc: Place Index chỉ có link "Admin", Person Index có link "DILA Place Index". Dễ lạc khi chuyển qua lại.

## 2. Thay đổi (additive, UI-only)

| File | Nội dung |
|------|----------|
| `admin/dila_index.html` | Thêm CSS `.da-tabbar`/`.da-tab`/`.da-tab.active`; đổi `<h1>` → "DILA Index"; thêm tab bar: 📍 DILA Place Index (**active**) · 👤 DILA Person Index |
| `admin/dila_person_index.html` | Áp dụng cùng CSS + tab bar; bỏ link rời "DILA Place Index" trong breadcrumb; đổi `<h1>` → "DILA Index"; tab 👤 DILA Person Index (**active**) |

- Tab bar dùng chung CSS pattern, active tab đổi màu `--da-cyan` + border dưới.
- 0 thay đổi JS logic search/filter/pagination/export.

## 3. Verify

- HTML/CSS thuần, không đổi JS → chạy pipeline (lint/test/e2e) PASS.
- Không ảnh hưởng API/DB.

## 4. Revert

`git revert --no-edit <sha_T153>` (chỉ 2 file HTML, 0 DB).
