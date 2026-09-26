---
id: T118
title: "Research Audit Tier API (Bậc Tiến sĩ — Audit Trail)"
module: API / Research Tier
priority: low
depends_on: [T111, T100, T108]
created: 2026-09-09
updated: 2026-09-14
owner: AI Engineer (impl T135) · Lee Tổng (acceptance)
status: done
---
# T118 — Research Audit Tier API (Track 2 của "T117 Doctrine Retrieval" rà đặc tả)

## Bối cảnh
Rà đặc tả "T117 Doctrine Retrieval Engine" (2026-09-09): hầu hết đã phủ bởi T100+T111+T113.

**DONE (impl trong T135, 2026-09-14):** `GET /daoanh/api/research/entity/<entity_ref>/audit-trail` (public, read-only, 0 ALTER, LIMIT 200) — history `en_audit_log` + `audit_id` SHA-256 (`entity_claims_audit`) + `data_status: indexed|no_data`. Backup `app.py.bak-t135-audit-trail.py`.
**Delta thực sự duy nhất** = bậc Tiến sĩ cần **Audit Trail**: dữ liệu thô + lịch sử thay đổi record.
`en_audit_log` (editor · evidence · created_at) + `entity_claims_audit.audit_id` (SHA-256) đã tồn tại
nhưng **admin-only**; evidence response không kèm `audit_id`. Task này mở public/research tier.

## Phạm vi (additive, đúng ràng buộc)
- KHÔNG ALTER bảng base; 0 migration; 0 bảng mới.
- Chỉ đọc (JOIN `en_audit_log` + `entity_claims_audit` + `entity_claims`).
- Không thay đổi `?level` hiện tại; endpoint mới độc lập, giới hạn L3/admin.
- Không login mới (tận dụng session hiện có nếu có).

## Mở rộng 2026-09-09 (ráspec QA/UAT — "tái lập kết quả" Test 2)
Đặc tả "System QA & Compliance UAT" Test 2 (Tiến sĩ) yêu cầu xuất trọn **Provenance + Audit ID +
Citation chuẩn để tái lập kết quả**. Ngoài Audit Trail, thêm deliverable export citation:
- **CSL-JSON export**: KHÔNG tồn tại hiện nay (0 khắp repo) — endpoint trả CSL-JSON items cho entity
  (claim_id/authority/source_reference/access date… chuẩn citeproc).
- **BibTeX chuẩn**: nâng cấp từ tối giản hiện tại (`places.html` `dtCopyCite` → `@incollection` chỉ
  ref_code) lên full metadata (author/title/booktitle/publisher/DOI), đồng bộ CSL-JSON.

## Rà đặc tả nhầm "T118 Knowledge Base Management & User Training" (ráspec5 2026-09-09)
Lee gửi đặc tả **header "T118 (Dành cho ClaudeCode)"** nội dung "Knowledge Base Management & User
Training / KNOWLEDGE_MGMT_SPEC.md / Learning Path / Curation Registry / Feedback Loop". **Header
nhầm** — task này = Research Audit Tier. Phân mảnh đúng chủ sở hữu:

| Đặc tả | Chủ sở hữu | Trạng thái |
|---|---|---|
| Academic Scaffolding (Cử nhân→Tiến sĩ) | **T111** persona `?level=L1/L2/L3` | ✅ DONE |
| Tách Canonical / Draft | **T100/T108** `verification_status` + assertions L1/L2/L3 gating | ✅ kiến trúc |
| Learning Path (đi theo truyền thừa) | **T59** (Giáo Dục) — nền: `lineage_chronology` 49,560 · Nexus graph · events 3,530 | 🟡 dữ liệu có, UI chưa |
| Curation Registry / Knowledge Packages (đóng gói) | **T59** + **T119** (editor) | 🔴 UI chưa có |
| **Feedback Loop** (NOT INDEXED → yêu cầu bổ sung → báo admin → T112) | **T112** (D-feedback) | 🔴 chưa có logging |

**Cam kết:** KHÔNG tạo `KNOWLEDGE_MGMT_SPEC.md`/`LEARNING_PATH_SPEC.md` (A2: SSOT = SCHEMA_DESIGN +
tasktodo/roadmap; Learning Path thuộc T59) · KHÔNG update `PROJECT_STATUS.md` (không tồn tại) ·
KHÔNG gán "Knowledge Mgmt" cho task này. Delta thật duy nhất = **D-feedback → T112**.
- Gói `?raw=1` tái lập kết quả: raw passages + audit_id + citation file.

## Đề xuất
- `GET /daoanh/api/research/entity/<entity_id>/audit-trail` (chỉ persona L3 `/ chủ sở hữu giấy phép`):
  trả `Full Assertion Object` = claim fields + `audit_id` + lịch sử `en_audit_log` cho entity.
- Tùy chọn `?raw=1` → JSON export dữ liệu thô (research).
- Trả về trung thực `{"status":"NO_DATA"}` thay vì rỗng khi entity chưa có log.

## Acceptance (dự kiến)
- `npm run pipeline` PASS trước review.
- Verify additive: 0 chạm dữ liệu base; revert = chỉ xóa route (không có DB thay đổi).
- Nhật ký thẩm định bậc Tiến sĩ hiển thị đủ theo rubric đặc tả (minh bạch + trung thực negative case).

## Trạng thái
- **pending** — Track 2, chờ Lee duyệt sau khi chốt Track 1 (docs). ~0,5 ngày.

## X?y d?ng Batch B (2026-09-10) ? IMPLEMENTED (??t 1)
- `GET /daoanh/api/admin/audit/trail?entity_ref=&page=` ? en_audit_log append-only, tr? `audit_id` = `en-<log_id>`.
- `GET /daoanh/api/public/export/citation?entity_id=&format=csl-json|bibtex&audit_id=` ?
  xu?t tr?ch d?n chu?n h?c thu?t (CSL-JSON array / BibTeX), resolver: places_dila ? dila_reference ? people ? entity_hub.
- Ch?a l?m (??t sau): full audit id xuy?n m?i export public / ch? k? hash b?ng ch?ng.
- Tr?ng th?i: **in_progress** ? ch? Lee review h?i quy ? done.
## X?y d?ng Batch D (2026-09-10) ? ??T 2 IMPLEMENTED
- `_audit_ref_lookup(audit_id)` ? tra en_audit_log (d?ng en-<log_id>): action/editor/**
  authority_rank/verification_status/evidence_sources/created_at.
- `GET /api/public/export/citation` m? r?ng: audit_id xuy?n v?o export ? CSL-JSON entry
  th?m `audit` object + `signature`; BibTeX note th?m `SIG=<sha256(entity_id|audit_id|title)>`.
  Ch? k? b?ng ch?ng ?n ??nh theo m?i ??nh d?ng, backward compatible.
- Tr?ng th?i: **in_progress** ? c?n ch? Lee review; ??t ti?p c? th?: audit id xuy?n m?i
  export public (evidence drawer / index.html) + ch? k? t?ng m?c.
