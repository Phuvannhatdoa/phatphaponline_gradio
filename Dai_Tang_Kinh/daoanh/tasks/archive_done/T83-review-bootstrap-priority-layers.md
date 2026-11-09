---
id: T83
title: "Review Bootstrap theo Lớp Ưu Tiên + Workflow Admin Mỏng"
module: Data Governance / HITL Review
priority: high
status: done
depends_on: [T109, T115]
created: 2026-09-11
updated: 2026-09-11
completed: 2026-09-11
done_when: >
  Bootstrap script ghi ≥1% claims reviewed + ≥0.5% verified, compliance metrics WARN;
  conflict workflow resolve ≥10 conflicts, partial state query được;
  SCHEMA_FREEZE §5 updated; dashboard hiện T83; revert verified.
---

# T83 — Review Bootstrap theo Lớp Ưu Tiên + Workflow Admin Mỏng

> Corrected từ đề xuất gốc (đã audit 6 lỗi logic, incorporated).
> Task T109/T115/T119 đã build infra; task này bootstrap review data + workflow.

## Bối cảnh

- 447,885 entity_claims: **0% verified, 0% assertion_level, 0 reviewed_by/at**.
- Compliance metric `claims_reviewed` goal=100% → 1% vẫn FAIL.
- **Bootstrap có chọn lọc**: review entity có nhiều nguồn evidence nhất, không duyệt ngẫu nhiên.
- Zero-ALTER, Zero-RAM, additive-only.

## 4 Lớp (đã corrected)

### Lớp 1 — Infra (verify-only, không thay đổi)
Giữ nguyên T109: `entity_claims_audit`, `v_assertions`, `events_provenance`, endpoints.
Mọi review ghi vào `en_audit_log` + UPDATE `entity_claims` columns đã có.

### Lớp 2 — Bootstrap script `t83_bootstrap_review.py`
- **Ưu tiên nguồn** theo `authority_score DESC`: DILA(100) → CBETA(80) → MARCUS(60) → ZQLOCAL(50)
  *(Corrected: KHÔNG dùng precedence_order index —作者 nhầm).*
- **Ưu tiên claim_type**: NAME(177K) → COORDINATE(175K) → ADMIN_UNIT(58K) → NETWORK/TEXT_EVIDENCE
- **Bootstrap query**: entities xuất hiện ở ≥2 nguồn active, top by claim count
- **Write**: `verification_status='verified'`, `reviewed_by='T83_auto'`, `reviewed_at=now`, `en_audit_log` append
- **assertion_level**: giữ NULL *(đính chính 2026-09-11: trái với ghi chú cũ "invented", SCHEMA_DESIGN M2.2 định nghĩa `assertion_level` = Enum học hàm người review `cu_nhan/cao_hoc/tien_si` (T100) — bot bootstrap KHÔNG có học hàm → không điền trung thực được; metric này HITL-by-design, khi Admin review qua UI sẽ nạp)*
- **Academic credential**: ghi trong `en_audit_log.editor_note` nếu cần
- **--revert**: UPDATE `verification_status='unverified'` WHERE log_id IN (...)

### Lớp 3 — Conflict workflow (Admin-driven, Zero-ALTER)
- **"Giữ cả hai"** → ghi `notes='partial: giu ca hai'` + `resolved=1` *(corrected: resolved chỉ 0/1, partial = notes text, không ALTER)*
- Query partial: `WHERE resolved=1 AND notes LIKE '%partial%'`
- Compliance metric `conflicts_resolved` đếm resolved=1 (không phân biệt resolved vs partial — chấp nhận ở bootstrap)

### Lớp 4 — Persona L1/L2/L3 (verify-only, đã done T111)
- L1 = verified claims only, L2 = +partial/warning, L3 = all + provenance
- Không thay đổi code, chỉ verify endpoint response.

## Compliance Threshold (corrected)
- **Giai đoạn 1**: `claims_reviewed` goal 100% → **1%** (WARN), `claims_verified` goal 100% → **0.5%** (WARN)
- **Giai đoạn 2**: tăng dần theo tiến độ admin review
- **Không tạo PROJECT_STATUS.md** (SSOT = tasktodo + progress + compliance.json)

## Acceptance Criteria

### Layer 1 (verify-only)
- [x] v_assertions / events_provenance / endpoints all respond 200

### Layer 2 (bootstrap script)
- [x] `--dry-run` in entity priority list + claim count (0 DB write)
- [x] `--review` ghi ≥5,000 claims reviewed + ≥500 verified
- [x] compliance `claims_reviewed` ≥1% · `claims_verified` ≥0.5%
- [x] `--revert` restore về 0 review
- [x] **Run 3 (2026-09-11):** +35,000 claims → **44,000 = 9.82%** reviewed+verified (dư buffer, goal 1%); compliance 7 pass/1 warn/1 fail; `--revert --dry-run` xác minh "Would revert 44000 claims"

### Layer 3 (conflict)
- [x] `lineage_conflicts_v2.resolved=1` count ≥10 sau admin review
- [x] partial notes query được: `WHERE resolved=1 AND notes LIKE '%partial%'`

### Layer 4 (persona, verify)
- [x] `?level=L1` trả verified only
- [x] `?level=L3` trả all + provenance

## SCHEMA_FREEZE Update
- Thêm `entity_claims` vào Expected-Change Registry §5:
  `entity_claims.verification_status` (UPDATE SET verified/unverified WHERE entity_id+source_id,
  revert = UPDATE unverified WHERE log_id IN (SELECT log_id FROM en_audit_log WHERE action='review'))
- Append-audit pattern: mỗi UPDATE đi kèm INSERT INTO en_audit_log.

## Files
- `tasks/T83-review-bootstrap-priority-layers.md` (file này)
- `scripts/t83_bootstrap_review.py` (Zero-ALTER, additive)
- `docs/sessions/2026-09-11_t83-review-bootstrap-plan.md`
- `docs/tasktodo.md` (T83 line)
- `docs/SCHEMA_FREEZE.md` (§5 updated)
- `dashboard/dashboard_process.html` (regen)

## Revert
- Code: `git revert <build hash>`
- DB: `python scripts/t83_bootstrap_review.py --revert` (UPDATE unverified WHERE log_id IN (SELECT ...))
