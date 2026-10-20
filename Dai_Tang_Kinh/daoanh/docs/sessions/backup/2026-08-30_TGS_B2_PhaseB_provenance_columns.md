# TGS Build 2 — Phase B: Provenance columns trên entity_claims (additive)

**Ngày:** 2026-08-30
**Build:** TGS Build 2 — Phase B (sau Phase A `7f3e791`)
**Trạng thái:** ✅ DONE (DB verified + app.py compile OK)

## Mục tiêu
Bổ sung 2 cột provenance cho evidence-layer: `source_url` (URL nguồn) và `retrieved_at`
(thời điểm lấy dữ liệu) — yêu cầu của TGS Build 2 để truy vết nguồn evidence đa-nguồn.

## Việc đã làm — `scripts/build2_add_evidence_provenance_columns.py`
- **ADDITIVE:** `ALTER TABLE entity_claims ADD COLUMN source_url TEXT` + `retrieved_at TEXT`
  (chỉ ALTER nếu cột chưa tồn tại — idempotent; không drop/rename cột cũ, không đụng bảng nguồn).
- **Backfill `source_url`:** Wikidata EXTERNAL_ID (`source_reference LIKE 'T69:wikidata:%'`
  → `https://www.wikidata.org/wiki/Q…`) = **148 rows**.
- **Gán `retrieved_at`:** cho claims created trong 24h trước (lượt T69 wire) = **36,413 rows** (non-destructive, chỉ khi NULL).

## Kết quả (DB verified)
- `entity_claims` cols: … `source_url`, `retrieved_at` (2 cột mới ở cuối).
- `COUNT(source_url)=148`; `COUNT(retrieved_at)=36,413`.
- Total claims **447,885** = 447,737 + 148 (chỉ 148 Wikidata là claim mới từ A2; CBETA/Marcus idempotent
  thay thế, không tăng). ✓ nhất quán.

## Tác động app.py
- **KHÔNG** cần đổi app.py: cột mới là additive, code hiện tại đọc theo tên cột đã có.
  `py_compile app.py` OK. (Phase C sẽ dùng `source_url`/`retrieved_at` trong evidence query.)

## Reversible
- Cột additive — app vẫn chạy nếu bỏ qua; `--undo` xóa backfill source_url.
- Hoàn revert: restore backup `lineage_backup_t69_a2.db`.
