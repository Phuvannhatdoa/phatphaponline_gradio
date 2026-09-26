---
id: T73
title: "Admin Review UI — Batch Duyệt bio_vi_draft (2,093 rows)"
module: Person Authority / Admin
priority: high
status: done
depends_on: [T63, T65]
created: 2026-08-30
updated: 2026-08-30
completed: 2026-08-30
done_when: Trang admin /daoanh/admin/bio-review hoạt động; admin có thể approve/reject/edit từng draft; bulk approve theo source; --copy-approved script copy approved drafts → people.bio_vi
---

# T73 — Admin Review UI: bio_vi_draft

## Vấn đề

2,093 bản thảo tiểu sử tiếng Việt (avg 1,050 chars) đang nằm trong `person_bio_vi_draft`
với `admin_approved = 0`. Không có giao diện duyệt → toàn bộ staging tắc vô thời hạn.

Người dùng tra thiền sư vẫn không nhận được thông tin tiếng Việt dù data đã có sẵn.

## Phân bố hiện tại (2026-08-30)

| match_type | Nguồn | Rows |
|-----------|-------|------|
| exact_term | Từ điển Thiền Tông Hán Việt | 602 |
| exact_term | Phật Học Tinh Tuyển | 102 |
| exact_term | Từ điển PH Tổng Hợp | 67 |
| exact_term | Trích Lục Từ Ngữ PH | 40 |
| exact_term | Phật Quang Từ Điển | 34 |
| name_zh_bracket | Phật Học Tinh Tuyển | 1,198 |
| name_zh_body | Phật Học Tinh Tuyển | 48 |
| **Tổng** | | **2,093** |

## Thiết kế UI

### Route cần thêm vào app.py

```
GET  /daoanh/admin/bio-review              → trang review với pagination
POST /daoanh/admin/bio-review/approve      → approve 1 draft
POST /daoanh/admin/bio-review/reject       → reject + note
POST /daoanh/admin/bio-review/bulk-approve → approve theo filter
GET  /daoanh/api/admin/bio-review/stats    → counts by source/status
```

### Layout trang admin

```
┌─────────────────────────────────────────────────────────────────┐
│  BIO VI DRAFT REVIEW                    2,093 pending  [Stats]  │
│  Filter: [Tất cả ▼] [Nguồn: Thiền Tông ▼] [Conf ≥ 0.8]        │
│  [Bulk Approve: Thiền Tông Hán Việt — 602 rows]                 │
├──────────────────────────────────────────────────────────────────│
│  Huệ Năng (慧能) — PL0001234                                     │
│  Nguồn: Từ điển Thiền Tông | Exact match | 1,045 chars          │
│  ─────────────────────────────────────────────────────────────── │
│  [Lục tổ Huệ Năng (638–713)... bản thảo 200 chars đầu...]      │
│  [Xem đầy đủ ▼]                                                  │
│  [✅ Approve] [✏ Sửa rồi approve] [❌ Reject] → với ghi chú     │
├──────────────────────────────────────────────────────────────────│
│  Trí Nghiễm (智儼) — PL0001235  ...                              │
└──────────────────────────────────────────────────────────────────┘
```

### Workflow

1. Admin xem draft trong trang
2. **Approve** → `admin_approved = 1`, `admin_note = ''`
3. **Edit + Approve** → cập nhật `bio_vi_draft`, sau đó approve
4. **Reject** → `admin_approved = -1`, ghi lý do
5. Sau batch approve → chạy `t63_bio_vi_lexicon_p1.py --copy-approved`
   → copy `bio_vi_draft` → `people.bio` cho các rows đã approve

### Bulk approve logic

```
- "Approve tất cả từ Từ điển Thiền Tông (exact_term)" → 602 rows
- "Approve tất cả exact_term chưa review" → ~845 rows
- Luôn có confirm dialog trước khi bulk
```

## Acceptance Criteria

- [x] Route `/daoanh/admin/bio-review` load được, có pagination (20/page)
- [x] Approve 1 row: `admin_approved = 1` trong DB
- [x] Reject 1 row: `admin_approved = -1`, lưu admin_note
- [x] Bulk approve theo source hoạt động (có confirm dialog)
- [x] Stats API trả về counts đúng
- [x] `t73_copy_approved_bio_vi.py --apply` copy drafts → `people.bio_vi` (ALTER TABLE + copy)
- [x] `people.bio_vi` column thêm thành công (ALTER TABLE idempotent)

## Note kỹ thuật

- `people` table: cột bio_vi KHÔNG tồn tại — cột đúng là `bio` (tiếng Hán).
  Cần quyết định: có tạo `bio_vi` riêng hay ghi vào `bio`?
  **Đề xuất:** Tạo ALTER TABLE people ADD COLUMN bio_vi TEXT — giữ `bio` gốc tiếng Hán nguyên vẹn.

## Rollback

Xóa route khỏi app.py. Data trong person_bio_vi_draft không bị ảnh hưởng.
ALTER TABLE dễ revert nếu cần (drop column hoặc ignore).

## Liên quan

- T63 (done): tạo 845 exact_term drafts
- T65 (done): tạo 1,248 name_zh bracket/body drafts
- T73 (`--copy-approved` step): copy approved → production bio_vi
