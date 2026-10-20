---
id: T76
title: "B2 Real Data Acceptance Test (REAL DATA, không mock)"
module: DILA Integration Layer
priority: high
status: done
depends_on: [T67, T68, T69, T70]
created: 2026-08-31
updated: 2026-08-31
completed: 2026-08-31
done_when: >
  Chứng minh Build 2 hoạt động trên DATA THẬT (không mock, không database test thay thế, không
  hard-code PASS): DILA vẫn là canonical, evidence có provenance, cross-reference khớp canonical
  entity, authority ranking phân biệt source authority với match confidence, conflict được phát
  hiện (nếu có case thật), evidence graph truy ngược được, Đạo Ảnh human-review được, negative
  tests không crash, data integrity trước/sau (checksum) không thay đổi, Build 1 không regression.
---

# T76 — B2 Real Data Acceptance Test

## Mục tiêu
Xác nhận **Build 2 thực sự hoạt động trên DATA THẬT** của hệ thống (`data/lineage.db`),
không dùng mock data, fake entity, synthetic evidence hoặc hard-coded expected result.
Build 1 đã tồn tại và **KHÔNG được rebuild**.

## Nguyên tắc (tuân thủ Build 2 hard-rules)
- **Read-only test**: không tạo database test thay thế, không seed mock records.
- **KHÔNG hard-code** kết quả để làm PASS.
- **DILA = canonical identity**; external ID chỉ là cross-reference.
- **Phân biệt SOURCE AUTHORITY vs MATCH CONFIDENCE.**
- **DO NOT modify architecture merely to make tests pass.**
- Tết thiếu nguồn tích hợp thật → báo đúng trạng thái (không đánh PASS vội).

## Kết quả (2026-08-31) — REAL DATA

**Verdict: `PARTIAL`** (5 PASS siêu thật + 3 PARTIAL vì dữ liệu/máy móc chưa đủ; 0 CRITICAL FAIL).

| Test | Result | Evidence |
|---|---|---|
| Canonical Identity | ✅ PASS | 0 canonical PLACE ngoài prefix `PL0`; DILA giữ canonical |
| Source Evidence | ✅ PASS | DILA 293,177 / ZQLOCAL 118,295 / MARCUS 22,332 / CBETA 13,933 / Wikidata 148 |
| Provenance | ⚠️ PARTIAL | CBETA/MARCUS/Wikidata 100% ref+retrieved; DILA retrieved=0; ZQLOCAL ref=0 |
| Cross-reference | ✅ PASS | 15 entity ≥3 sources; gắn cùng canonical, không merge mù |
| Entity Matching | ⚠️ PARTIAL | geo_cross_ref=181, name_vi_map_places=0 (dữ liệu mỏng) |
| Authority Ranking | ✅ PASS | 13-source matrix; API xếp theo authority desc (DILA đầu) |
| Conflict Detection | ⚠️ PARTIAL | conflict_pending=0 — không seed, không case thật để phát hiện |
| Evidence Graph | ✅ PASS | entity→evidence→source→record→ref→retrieved đủ |
| Human Review | ✅ PASS | canonical_decision=2, en_audit_log=2, 1 verified |
| Negative Tests | ✅ PASS | DILA không tồn tại → 0 claims, không crash, API HTTP 200 |
| Data Integrity | ✅ PASS | checksum before/after IDENTICAL (chỉ khác timestamp) |
| Performance | ✅ PASS | claims 1.18ms, source_ids 0.39ms, authority 0.19ms, hub 87ms |
| End-to-End | ✅ PASS | API thật `/claims` HTTP 200, resolved=181597, DILA đầu |

**Thống kê:** REAL ENTITIES TESTED = 15 · SOURCES TESTED = 5 · EVIDENCE = 447,885 ·
CONFLICTS = 0 · HUMAN REVIEW = 2 · CRITICAL FAILURES = 0 · REGRESSION = PASS.

## Subtasks
- [x] T76a: Environment audit (matrix nguồn + status thật) — `docs/T76_B2_REAL_DATA_ENVIRONMENT_REPORT.md`
- [x] T76b: Chọn ≥10 canonical entities thật (15 found) — baseline Thiếu Lâm Tự entity 181597
- [x] T76c: Canonical Identity + Source Evidence + Provenance test (read-only queries)
- [x] T76d: Cross-reference + Entity Matching survey
- [x] T76e: Authority Ranking + Conflict survey (real, không seed)
- [x] T76f: Evidence Graph + Human Review
- [x] T76g: Negative + End-to-End + Performance
- [x] T76h: Data Integrity — checksum before/after (`data/t76_checksum_before.json` / `after.json`)
- [x] T76i: Regression `npm run pipeline` (lint/test/e2e exit 0)
- [x] T76j: 3 report — env / acceptance / failures-remediation

## Reports
- `docs/T76_B2_REAL_DATA_ENVIRONMENT_REPORT.md`
- `docs/T76_B2_REAL_DATA_ACCEPTANCE_REPORT.md`
- `docs/T76_B2_FAILURES_AND_REMEDIATION.md`
- Checksum: `data/t76_checksum_before.json`, `data/t76_checksum_after.json`

## Revert / Rollback
- T76 hoàn toàn read-only → **không thay đổi DB** (checksum identical).
- Nếu fixed sau này: mọi script mới có `--undo` + backup để quay về version trước.
