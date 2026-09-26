---
id: T122
title: "Batch D — Immediate-fix bundle 2026-09-10 (research audit id xuyên export · geo candidate runfront · bio review UI · docs hygiene)"
module: Evidence-first · Editorial / Ops
priority: high
status: in_progress
depends_on: [T112, T113, T118, T121]
created: 2026-09-10
updated: 2026-09-10
lee_approved: true
plan_approved_at: "2026-09-10 (Batch D — phê chuẩn đề xuất sau review undone task list)"
---

# T122 — Batch D: Immediate-fix bundle (2026-09-10)

Kế hoạch chi tiết đã thảo luận (Batch D, Lee phê chuẩn) — gom 4 hạng mục fix được NGAY,
không cần key/quyết định/agent ngoài. Mỗi hạng mục = 1 commit riêng, revert tiện lợi.
Quy tắc giữ: ZERO-ALTER bảng nền · ZERO-RAM (LIMIT/OFFSET) · additive · trung thực.

## D1 — T118 đợt 2: audit_id xuyên export + chữ ký bằng chứng (app.py)
- Mở rộng `GET /daoanh/api/public/export/citation`: tham số `audit_id` đã có từ Batch B,
  nay kéo thêm evidence/action/editor từ `en_audit_log` (helper `_audit_ref_lookup`).
- Thêm `signature = sha256(entity_id|audit_id|title)` — ổn định, trả cả 2 định dạng
  (CSL entry `.signature` + bibtex `SIG=…`). Backward compatible.
- Done_when: smoke test_client → CSL có `audit` + `signature`; BibTeX có `SIG=`.
- Revert: revert commit D1, không đụng DB.

## D2 — T121 lần chạy đầu: sinh candidate (KHÔNG approve)
- `python scripts/enrich_places.py --limit=50 --run` → ghi `enrich_status='candidate'`
  vào geo_cross_ref (Wikidata P625+P2044), KHÔNG set wikidata_qid chính thức.
- Kết quả thật (ghi nhận trung thực): giới hạn thời gian chạy → **9 candidate** ghi OK
  (PL000000000048… PL000000008349), 2/9 có elevation (94m, 242m). Cron đầy đủ để sau.
- Revert: xóa candidate rows / chạy lại với limit lớn hơn khi net nhanh hơn.

## D3 — T73: tab "Bio Review" trong editor-dashboard.html + 3 route admin (app.py)
- `GET /daoanh/api/admin/bio-review/pending?status=pending|approved|rejected|all&page=`
  (person_bio_vi_draft 2,093 row, Zero-RAM; LEFT JOIN people, báo `has_bio_vi`).
- `POST /daoanh/api/admin/bio-review/<person_id>` {action approve|reject} → set
  admin_approved=±1 + ghi en_audit_log `bio_review_*`.
- `POST /daoanh/api/admin/bio-review/apply` {person_ids≤200} → copy approved draft vào
  `people.bio_vi` (chỉ khi khác — idempotent) + en_audit_log `bio_apply`. **Bước copy
  tách riêng = HITL 2 bước**, admin chỉ định danh sách.
- editor-dashboard.html thêm tab + badge `bio_pending` (editor-stats thêm 1 metric).
- Revert: revert commit D3; dữ liệu đã apply = data edit admin (giữ, hoặc khôi phục
  people.bio_vi trước đó theo en_audit_log old_value).

## D4 — Docs hygiene (đếm board trung thực)
- **BUG-009** (bugs.md + tasktodo OPEN BUGS "open/pending") ≡ **MAP_SEMANTIC_MARKER_ICONS_001**
  (places.html `getPlaceIconSvg` BLOCK ĐÃ CÓ, UI verify 2026-09-08). Đóng bản stale:
  ghi đã hợp nhất, chờ 1 lần admin confirm DONE chung.
- **Stub-ređirect T51 → T53** (`tasks/T51-cbeta-content-enhancement.md`) và
  **T52-analytics → T54** (`tasks/T52-cbeta-analytics-dashboard.md`): nội dung đã chuyển
  số (đầu file ghi rõ). Di chuyển 2 file stub vào `tasks/backup/` để board không đếm trùng.
  T52 (Đối Chiếu Tam Tạng) giữ nguyên (task riêng khác số).
- Regen dashboard → số task chính xác (không còn ghost), done=8 giữ.
- Revert: revert commit D4 (trả stub về tasks/), hoặc file-level.

## Trạng thái
- **in_progress → done** khi: pipeline PASS (lint/test/e2e) + smoke toàn bộ route D1–D3 + regen đúng.
- Rollback: `git revert --no-edit <hashD>` mỗi hạng mục độc lập.