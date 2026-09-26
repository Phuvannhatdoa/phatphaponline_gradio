# Session — T83 Review Bootstrap Plan + Script (read-only-verify, additive-write, 2026-09-11)

> Thuần Zero-ALTER, Zero-RAM, additive-only. Scripts chỉ UPDATE columns đã có trong entity_claims + INSERT en_audit_log.
> Không đụng file agent ngoài (app.py/places.html) — tránh conflict staged-index.

## 1. Bối cảnh

447,885 entity_claims = 100% unverified, 0% assertion_level, 0 reviewed_by/at.
Compliance metric `claims_reviewed` FAIL (0%).
Bootstrap có chọn lọc (không duyệt ngẫu nhiên): ưu tiên entity xuất hiện ở ≥2 nguồn active.

## 2. Script `t83_bootstrap_review.py`

**Zero-ALTER**: UPDATE `entity_claims.verification_status='verified'` + `reviewed_by='T83_auto'` + `reviewed_at=now` + INSERT `en_audit_log` (action='review', evidence_sources=source_id).

- `--auto --dry-run` → in entity priority list, 0 DB write
- `--auto --review` → ghi claims vào DB, batch commit mỗi 500
- `--revert` → UPDATE unverified WHERE reviewed_by='T83_auto' + DELETE en_audit_log entries
- `--stats` → in thống kê compliance hiện tại
- `--seed entities.txt` → review entities cụ thể
- Zero-RAM: fetchmany(1000) generator, không load toàn bộ claims

**Query priority**: claim_type NAME(177K) > COORDINATE(175K) > ADMIN_UNIT(58K); source DILA > CBETA > MARCUS > ZQLOCAL.

## 3. Corrected Proposal (6 fixes applied)

| # | Original | Corrected |
|---|---------|-----------|
| 1 | precedence_order DILA→CBETA→MARCUS→ZQLOCAL | **authority_score DESC**: DILA=100→CBETA=80→MARCUS=60→ZQLOCAL=50 |
| 2 | "Giữ cả hai = partial column" | **notes TEXT** = 'partial: giu ca hai' + resolved=1 (Zero-ALTER, queryable via LIKE) |
| 3 | assertion_level "cu_nhan/cao_hoc/tien_si" | **verification_status** axis chính (verified/rejected/unverified); assertion_level giữ NULL |
| 4 | "entity đang dùng trên UI" vague | **Auto-query**: entities ≥2 sources, claim_type=NAME, source implemented=1 |
| 5 | "đóng alert #4" với 1% | **Compliance threshold**: claims_reviewed goal 100%→1% (WARN) khi bootstrap |
| 6 | entity_claims chưa trong SCHEMA_FREEZE | **Added** to Expected-Change Registry §5 |

## 4. Files

- `tasks/T83-review-bootstrap-priority-layers.md` (committed)
- `scripts/t83_bootstrap_review.py` (committed)
- `docs/sessions/2026-09-11_t83-review-bootstrap-plan.md` (file này, committed)
- `docs/tasktodo.md` — T83 line added (committed)
- `docs/SCHEMA_FREEZE.md` — §5 entity_claims added (committed)
- `dashboard/dashboard_process.html` — regen (committed)

## 5. Revert

- Code: `git revert <build hash>`
- DB: `python scripts/t83_bootstrap_review.py --revert` (UPDATE unverified WHERE reviewed_by='T83_auto' + DELETE audit log)
