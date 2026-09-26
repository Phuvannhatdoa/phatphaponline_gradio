# Session — Build Batch D (T122 Immediate-fix bundle) 2026-09-10

**Commit:** code=`3b87ea32` · docs=`5a8d9e3b` · **Mode:** build (Lee: "phê chuẩn đề xuất… Đồng ý build")

## Bối cảnh
Sau Batch A+B (f73e3ce5/74b29e3/85525c9/b3faa76), Lee yêu cầu danh sách undone + đề xuất fix ngay.
Review toàn bộ tasktodo + board (41 task · done=8) → Batch D (4 hạng mục không cần key/quyết định/agent ngoài).
Task driver mới **T122** (max T-number=121 cũ → T122 tránh trùng agent song song).

## D1 — T118 đợt 2: audit_id xuyên export + chữ ký bằng chứng
- `_audit_ref_lookup(audit_id)` — nhận `en-<log_id>`, trả dict en_audit_log (action/editor/
  authority_rank/evidence/created_at) hoặc None.
- `GET /api/public/export/citation` mở rộng: audit block trong CSL-JSON + `signature` =
  sha256(entity_id|audit_id|title) ở cả CSL (.signature) và BibTeX (`SIG=`). Backward compatible.
- Verify: csl nhận audit real en-5 → `audit` object đầy đủ; bibtex có `SIG=`; audit giả → vẫn 200, không audit block.

## D2 — T121 lần chạy đầu (candidate-only)
- `python scripts/enrich_places.py --limit=50 --run` → timeout mạng (Wikidata ~10s/call), ghi được
  **9 candidate** (PL000000000048…PL000000008349; 2/9 kèm elevation 94m/242m); wikidata_qid chính thức
  giữ NULL (HITL, không auto-approve). Tiếp tục qua cron; candidate sẵn trong tab Geo Enrichment.

## D3 — T73: Bio Review UI + 3 route admin
- `GET /api/admin/bio-review/pending?status=pending|approved|rejected|all&page=` (2,093 row, LEFT
  JOIN people, cột `has_bio_vi`, Zero-RAM).
- `POST /api/admin/bio-review/<person_id>` {action approve|reject} → admin_approved=±1 + en_audit_log.
- `POST /api/admin/bio-review/apply` {person_ids≤200} → copy draft approved vào `people.bio_vi`
  (idempotent skip nếu giống) + en_audit_log `bio_apply`. HITL 2 bước (copy tách — admin chỉ định).
- editor-dashboard.html: tab **Bio Review** + badge; editor-stats thêm `bio_pending`.

## D4 — Docs hygiene
- **BUG-009** (bugs.md + tasktodo "open") ≡ **MAP_SEMANTIC_MARKER_ICONS_001** (places.html
  `getPlaceIconSvg`/`cateMap` đã có, UI verify 2026-09-08) → CLOSED-as-duplicate, 1 lần admin confirm DONE chung.
- Stub ređirect **T51→T53** + **T52-analytics→T54** (nội dung đã chuyển số) → move `tasks/backup/`;
  board không còn đếm ghost (41 = 39 + T73 + T122).
- task files mới: `tasks/T73-admin-review-bio-vi.md` (in_progress), `tasks/T122-batch-d-immediate-fix-bundle.md` (in_progress).
- Append mục Batch D vào `tasks/T118` + `tasks/T121`.

## Smoke test (Flask test_client, DB dọn sạch sau)
- GET bio-review pending/all=2093 · approved=0→1 (sau approve smoke) · approve A000019=200 · apply=applied 1
  · editor-stats bio_pending=2092 · citation csl sig/bibtex SIG · citation audit real en-5 có `audit`. **9/9 PASS**.
- Restore: xoá en_audit_log bio_*, reset admin_approved=0, people.bio_vi A000019 trả về NULL.

## Verification
- Pipeline: lint **PASS** · test **PASS** · e2e **PASS** (editor-dashboard.html trong danh sách quét).
- Regen: 41 task · done=8 · blocked=2 · 273 commits.
- b4_commit.py patched: hỗ trợ `R:<path>` (force-remove trong temp index) để commit move stub.

## Rollback
- `git revert --no-edit 3b87ea32` (gỡ code D1+D3) · `git revert --no-edit 5a8d9e3b` (gỡ docs).
- Candidate D2: `UPDATE geo_cross_ref SET enrich_status='none' WHERE enrich_source_qid IS NOT NULL AND enrich_status='candidate'`.
- Apply-đã-ghi people.bio_vi: khôi phục theo en_audit_log bio_apply.old_value.

## Việc kế tiếp
- Lee test hồi quy :5000: tab Bio Review (duyệt 1 draft → apply), citation audit_id có signature,
  Geo Enrichment duyệt candidate; đóng T73/T118/T121 → done.
- Cron: `daily_backup.py` + `enrich_places.py --limit=100 --run` (giờ mạng tốt).
- Batch C (BUG-012/014, T101) khi agent ngoài bàn giao; T113 đóng khi claims_reviewed>0.