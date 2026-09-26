---
id: T73
title: "Admin Review UI for bio_vi_draft (2,093 rows) + apply to people.bio_vi"
module: Editorial / Person Authority (Bio Vietnamese)
priority: medium
status: in_progress
depends_on: [T58, T59]
created: 2026-08-27
updated: 2026-09-10
done_when: >
  Admin duyệt/eject bio_vi_draft qua UI (tab Bio Review trong editor-dashboard.html),
  danh sách áp dụng (admin_approved=1) ghi vào people.bio_vi kèm en_audit_log bio_apply.
---

# T73 — Admin Review Bio VI (person_bio_vi_draft → people.bio_vi)

**Xây dựng Batch D (2026-09-10) — IMPLEMENTED (đợt 1):**
- `GET /daoanh/api/admin/bio-review/pending?status=&page=&per_page=` — hàng chờ
  `person_bio_vi_draft` (2,093 row), LEFT JOIN people, cột báo `has_bio_vi`, Zero-RAM.
- `POST /daoanh/api/admin/bio-review/<person_id>` `{action: approve|reject, note?}` —
  set `admin_approved = 1 | -1` + en_audit_log `bio_review_*`.
- `POST /daoanh/api/admin/bio-review/apply` `{person_ids ≤ 200}` — copy draft approved
  vào `people.bio_vi` (idempotent: bỏ qua dòng giống) + en_audit_log `bio_apply`.
- UI: tab **Bio Review** trong `admin/editor-dashboard.html` (badge số chờ), nút
  Duyệt/Từ chối mỗi dòng + "Áp dụng đã duyệt → people.bio_vi".
- `editor-stats` thêm metric `bio_pending`.
- Không ALTER bảng nền (person_bio_vi_draft T65 đã có sẵn); bước copy tách riêng = HITL 2 bước.
- Trạng thái: **in_progress** → chờ Lee test hồi quy :5000 (duyệt 1 draft + apply) → done.

Lịch sử (trước Batch D): script `t73_copy_approved_bio_vi.py` từng nêu chưa tồn tại —
UI này thay thế toàn bộ luồng (không cần script riêng).