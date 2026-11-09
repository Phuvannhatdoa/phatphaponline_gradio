---
id: T109
title: "Provenance Compliance & Conflict Resolution Workflow"
module: Data Governance / Assertion Architecture
priority: high
status: done
depends_on: [T108, T100]
created: 2026-09-08
updated: 2026-09-09
done_when: >
  (A) events (3,530) có provenance trong bảng dẫn xuất events_provenance
  (nguồn places_dila, 100% match verified) — Zero-ALTER;
  (B) entity_claims_audit (audit_id SHA-256 content-hash, M5 SCHEMA_DESIGN)
  backfill toàn bộ 447,885, idempotent (re-ETL trùng giá trị), 0 NULL;
  (C) admin workflow xử lý lineage_conflicts_v2 (40,327): API list + resolve
  ghi en_audit_log (editor/reviewed_at) + resolved=1; endpoint review claim
  gán assertion_level/verification_status/reviewed_by/reviewed_at;
  (D) v_assertions + v_events_full (Adapter = SQL View) khả dụng cho API mới;
  (E) compliance metric claims_with_audit/events_provenance = 100%.
---

# T109 — Provenance Compliance & Conflict Resolution Workflow (Zero-ALTER · Zero-RAM · Lean)

## Mục tiêu (gap thật #1/#2 của SCHEMA_DESIGN M7.2)
1. **Bịt lỗ hổng Provenance của `events`** — 3,530 events hiện source-less, vi phạm M1.
2. **Gán Audit ID content-hash** (M5) cho toàn bộ entity_claims — điều kiện "10 năm sau truy vấn lại".
3. **Mở workflow thẩm định** cho 40,327 conflicts + 447,885 claims đang 100% unverified — đóng alert #4.

## Phạm vi (tuân điều lệnh check07 — KHÔNG DROP/ALTER bảng base, Adapter = SQL View + bảng dẫn xuất)
- **DB (ETL `scripts/etl_t109_provenance.py`, `--dry-run/--apply/--revert` + backup):**
  - Bảng dẫn xuất **`entity_claims_audit`**: `(claim_id, entity_id, claim_type, predicate, object_text, source_id, audit_id, built_at)` —
    `audit_id = SHA-256(entity_id|claim_type|predicate|object_text|source_id)`, backfill 447,885 bằng generator (Zero-RAM), idempotent (INSERT OR REPLACE).
  - Bảng dẫn xuất **`events_provenance`**: `(event_id, source_id, source_reference, source_citation, attribution_note)` —
    backfill 100% (3,530/3,530 verified) từ `places_dila` (`SUBSTR(event_id,13) = places_dila.id`; source_id='DILA'; source_citation = note/listbibl).
  - SQL View **`v_assertions`** (3 khối + audit_id + authority_score/precedence_order) & **`v_events_full`** (events LEFT JOIN events_provenance).
  - KHÔNG tạo bảng conflicts_review — dùng **`en_audit_log`** (bảng ĐÃ CÓ, Lean).
- **Code (app.py, endpoint additive):**
  - `GET /daoanh/api/admin/lineage-conflicts` — list pending (LIMIT/OFFSET).
  - `POST /daoanh/api/admin/lineage-conflicts/<id>/resolve` — ghi `en_audit_log` (editor, reviewed_at=created_at, winner_source) + `UPDATE resolved=1`.
  - `POST /daoanh/api/admin/claims/<claim_id>/review` — gán review state cho claim (cột CÓ SẴN từ T100).
- **UI:** `admin/conflicts.html` (mới, nhẹ, fetch API, addEventListener — không inline handler).
- **KHÔNG:** xóa data; không tự quyết conflict (chỉ trình Admin); không ALTER bảng base; không bịa provenance (event nào ko có nguồn → không row + đánh dấu 'cần thẩm định').

## Phụ thuộc
T108 (docs/SCHEMA_DESIGN.md) · T100 (assertion_level cu_nhan/cao_hoc/tien_si, en_audit_log có sẵn).

## Acceptance
- 1 ETL script Zero-ALTER + backup, revert khả dụng (DROP 2 bảng + 2 view; 0 chạm dữ liệu base).
- `events_provenance` compliance = **100%** (xác minh bằng JOIN places_dila).
- UI admin xử lý conflict có nhật ký `editor`/`reviewed_at` trong `en_audit_log`.
- `npm run pipeline` PASS trước review; DB thay đổi verify bởi compliance metric.

## Rà đặc tả "Lineage Consensus Engine" (2026-09-09) — XÁC NHẬN ĐÃ PHỦ

Lee gửi đặc tả (header đề "T115" — washing đề "T109 Conflict Engine Workflow"; nội dung mô tả lại T109).
Đối chiếu read-only với DB + UI — **phủ 100% hạ tầng**:

| Y/c đặc tả | Thực trạng (verified) |
|---|---|
| Pool `lineage_conflicts_v2` (40,327) + `dila_data`/`marcus_data` | ✅ có (T109) |
| `resolutions_log` (thời gian/người/lý do) | ✅ `resolved_at`·`resolved_by`·`notes` → `chosen_source`/`previous_source` |
| UI Quản trị tranh chấp side-by-side | ✅ `admin/conflicts.html` + route `/daoanh/api/admin/lineage-conflicts[/<id>/resolve]` |
| Audit không xóa lịch sử | ✅ `en_audit_log` (editor·evidence·created_at) |
| Data Lock (không lọt ra query chính) | ✅ hệ quả additive — `v_assertions` tách biệt pool |
| HITL / không tự gộp | ✅ khớp nguyên tắc task này |

**2 Gap ghi nhận (không thay đổi code trong mục này):** (1) UI chưa render Authority Score
(JOIN `source_authority` DILA=100/MARCUS=60 — additive; tùy chọn → task T117 sau); (2) không có cờ
`lock` riêng — "Data Lock" là hệ quả kiến trúc tách pool (không cần cờ mới). Chi tiết:
`docs/lineage-conflict-implementation.md` mục "Rà đặc tả ... — Gap & xác nhận".
**Cam kết:** KHÔNG tạo `CONFLICT_ENGINE_SPEC.md` (trùng 2 file docs) · KHÔNG re-open (task này đã done).

## Rà đặc tả "Curation & Editor Workflow" (2026-09-09) — HITL ĐÃ CÓ + 4 UI gaps

Lee gửi đặc tả (header đề **"Task T118"**, mô tả "Curation & Editor Workflow"; body ghi **"ĐẶC TẢ
KHÁI NIỆM T116"** và lệnh gọi **"Task T116"** — T116 repo = System Registry docs-only, khác hoàn toàn).
Đối chiếu read-only DB + app.py + admin pages — **cơ chế HITL đã xây dựng xong**:

| Đặc tả yêu cầu | Hiện trạng (verified) |
|---|---|
| HITL 3 bước (Review → Acceptance → Commit) | ✅ `entity_claims.verification_status` (default `unverified`) + `reviewed_by/reviewed_at` + `POST /daoanh/api/admin/claims/<id>/review` (verdict: verified/disputed/needs_review/unverified + assertion_level + en_audit_log) |
| Audit Log (ai duyệt / lúc nào / lý do) | ✅ `en_audit_log` (editor·evidence_sources·created_at·old/new_value) + `resolutions_log` (resolved_by·resolved_at·notes) + `entity_claims.reviewed_by/at` |
| Dispute Resolution UI (side-by-side) | ✅ `admin/conflicts.html` (197 dòng) — so sánh DILA vs Marcus, resolve per-conflict |
| "Không tự Canonical" | ✅ 447,885 claim = 100% `unverified` (0 auto-promote); L1 clips verified (=0 → honest empty) |
| Bio-review HITL pattern | ✅ `admin/bio-review.html` + approve/reject/bulk-approve + list?status=0/1/-1 + stats |
| T221 staged approval | ✅ `t221/approve/<gate>` + `reject/<gate>` |
| Name-vi approve | ✅ `namevi-map/approve` |

**4 UI gaps ghi nhận (không phải lỗi hồi quy — là thiếu tiện ích, chờ T119):**
1. Unverified claims list endpoint — `GET /api/admin/verification/list` load JSON file, KHÔNG query `entity_claims` (447,885 row).
2. Bulk claim review — chỉ per-claim POST, KHÔNG có bulk endpoint (bio-review đã có mẫu).
3. Unified Editor Dashboard — 24 trang admin riêng lẻ, KHÔNG trang tổng hợp hàng chờ.
4. Resolution History viewer — `resolutions_log` = 0 rows, KHÔNG UI browse lịch sử.

**Cam kết:** KHÔNG tạo `CURATION_WORKFLOW_SPEC.md` (trùng T109 + SCHEMA_DESIGN + PROVENANCE_POLICY
+ lineage-conflict-implementation.md + SOURCE_AUTHORITY_MATRIX) · KHÔNG update `PROJECT_STATUS.md`
(SSOT = tasktodo/roadmap) · KHÔNG re-open T109. Task mới **T119** (Track 2, pending) xử lý 4 gaps.