# TGS Build 2 — Phase A: Fix 2 evidence defects + indexes + backup

**Ngày:** 2026-08-30
**Build:** TGS Build 2 — Phase A (sau Phase 0 T73/T74 fix, commit `128a789`)
**Trạng thái:** ✅ DONE (py_compile + lint/test/e2e exit 0 + DB verified)

## Mục tiêu
Vá 2 defect thật phát hiện trong audit Build 2 (rẻ, giá trị cao, additive + reversible) và
bổ sung index đang thiếu trên evidence tables.

## A1 — `entity_unified` hardcode `source_id = 7` (CBETA sai)
- **Trước:** `app.py:11526` hardcode `source_id = 7` → CBETA thật là `source_id=3`
  (13,933 rows) → lookup CBETA evidence trong `/daoanh/api/entity/<id>/unified` **luôn rỗng**.
- **Sau:** resolve động từ `data_sources` theo `source_code='CBETA' AND active=1`,
  fallback `3` — chống tái phạm hardcode (chủ trương đã duyệt: join-by-source_code).
- Xác nhận: `py_compile app.py` OK; toàn app không còn `source_id = N` hardcode.

## A2 — T69 Wikidata wire fail im lặng (source_id=None)
- **Trước:** `scripts/wire_evidence_into_entity_claims.py` chèn EXTERNAL_ID với
  `source_id=None` ⇒ 0 EXTERNAL_ID claims dù có 148 Wikidata QID.
- **Sau:**
  1. Script mới `scripts/build2_add_wikidata_to_data_sources.py` (additive, idempotent,
     reversible) thêm Wikidata vào `data_sources` (`source_id=6`, `source_code='Wikidata'`, active=1).
  2. Wire script resolve `source_id` từ `data_sources` (fallback 6) thay `None`.
  - Kết quả: **148 EXTERNAL_ID claims** giờ mang `source_id=6` (verify: BY source_id → 6:148; sample Q:Q10398516...).
- Lưu ý: `source_authority` đã có Wikidata (score 25, implemented=0, "chỉ tham khảo ngoài",
  không phải nguồn chính) — chỉ thêm vào `data_sources` để EXTERNAL_ID có source_id hợp lệ.

## Index + Backup
- **Backup:** `data/lineage_backup_t69_a2.db` (1.28 GB) qua `sqlite3.Connection.backup()`
  — KHÔNG dùng `wal_checkpoint(TRUNCATE)` (bài học T58). DB file git-ignored.
- **Index mới (idempotent):**
  - `ix_entity_claims_entity_source` ON `entity_claims(entity_id, source_id, claim_type)`
    (trước 0 index → full-scan 447K rows)
  - `ix_entity_source_ids_entity` ON `entity_source_ids(entity_id)`

## Kiểm chứng
- `py_compile` OK (app.py, wire_evidence, build2_add_wikidata).
- `npm run lint` exit 0 (get_format:185 = false-positive môi trường, exit 0),
  `npm run test` ✅, `npm run e2e` ✅. `e2e:runtime` EPERM = môi trường (Playwright lock, không liên quan thay đổi Python).

## Reversible
- **A1:** revert app.py dòng CBETA block (git revert) — không ảnh hưởng DB.
- **A2:** `python scripts/build2_add_wikidata_to_data_sources.py --undo` xóa dòng Wikidata;
  wire claims xóa bằng `DELETE FROM entity_claims WHERE claim_type='EXTERNAL_ID'` hoặc restore `lineage_backup_t69_a2.db`.
- **Index:** `DROP INDEX` nếu cần, hoặc restore backup.
