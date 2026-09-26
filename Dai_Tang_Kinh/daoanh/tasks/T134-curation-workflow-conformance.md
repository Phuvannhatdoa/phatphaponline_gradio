---
id: T134
title: Curation-Workflow-Conformance: HITL demo + Curations Spec + Fix Resolutions-History Gap
priority: high
status: in_progress
owner: AI Engineer (build) · Lee Tổng (HITL quilt quan trọng)
module: Ops / Governance / Curation
created: 2026-09-14
updated: 2026-09-14
---
# T134 — Curation-Workflow-Conformance (Đường A): HITL demo + CURATION_WORKFLOW_SPEC + fix Resolutions-History

---

## 1. Context (AO — audit thật 2026-09-14, admin chọn Đường A 2026-09-14)

Spec "T116 Curation & Editor Workflow" (ZenQ naming — chú ý: số trùng với board T116 = System Registry) được admin gửi verify.
**Verdict: ~90% ĐÃ TỒN TẠI sẵn** = **T109 (conflict workflow) + T119 (editor dashboard + bulk review)**. Implement literal sẽ tạo
file/table/UI trùng. Admin phê chuẩn Đường A: T134 = **chỉ lấp GAP THẬT + minh hoạ HITL thật + doc conformance thin** (additive, 0 rebuild, 0 trùng lặp).

### Đã có sẵn (verified 2026-09-14 — KHÔNG làm lại)
- **Editor Dashboard = T119:** `admin/editor-dashboard.html` (7 tab: Claims / Feedback / Data Gaps / Resolutions / Audit Trail / Geo / Bio) + `GET /daoanh/api/admin/editor-stats` (app.py L16848+).
- **Dispute UI = T109:** `admin/conflicts.html` (so sánh 2 cột DILA ↔ MARCUS) + `GET /daoanh/api/admin/lineage-conflicts` (app.py L10572) + `POST .../resolve` (L10615).
- **Audit Log / Versioning:** bảng `en_audit_log` (9,000+ rows từ T83) — editor · created_at · evidence_sources · authority_rank · old/new_value · action; `entity_claims_audit` 447,885 audit_id SHA-256 (T109).
- **Bulk Action:** `POST /daoanh/api/admin/claims/bulk-review` (≤500, 1 audit row/claim).
- **Conflict Pool:** `lineage_conflicts_v2` **40,327 rows (40,321 mở)**; `conflict_pending` (T132 seeds, mới 0 rows).
- **Hàng chờ claims:** `GET /daoanh/api/admin/entity-claims/unverified` (447,885 unverified, pagination).
- **Trạng thái claim:** `verification_status ∈ verified|unverified|disputed|needs_review` — **KHÔNG có "Canonical"**, không auto-canonical (đúng spec HITL C).

### GAP THẬT (Đường A — làm 3 việc)
1. **G1 — Minh hoạ HITL thật** (data cho `resolutions_log`/`en_audit_log`): resolve **~5 conflict** + review **~5 claim** + **1 bulk-review** qua UI-endpoint thật → chứng minh Versioning + Bulk Action **chạy được**, không phải hàng chờ chết.
2. **G2 — Fix GAP THẬT phát hiện trong demo:** tab **Resolutions** trong editor-dashboard **LUÔN trống** vì `resolutions_log` **0/4 code path INSERT** (bảng mồ côi) — data versioning thật nằm trong `en_audit_log (action='resolve_lineage_conflict')`. → UNION 2 nguồn trong `GET /daoanh/api/admin/resolutions/history` (additive, 0 ALTER).
3. **G3 — Doc conformance THIN `docs/CURATION_WORKFLOW_SPEC.md`** + chốt T119 → done sau khi Lee regression review. KHÔNG tạo `PROJECT_STATUS.md`.

## 2. Pha (additive — thứ tự)

### P1 — Vòng HITL mẫu (G1)
- Resolve 5 conflict từ `lineage_conflicts_v2` qua `POST /daoanh/api/admin/lineage-conflicts/<id>/resolve` (editor='Lee Tổng'):
  #3 teacher_set → dila (6>1) · #5 teacher_set → dila (17>1) · #11 teacher_set → dila (13>0) · #10 student_set → dila (4>0) · #4 student_set → marcus (marcus 6>1) — **cả 2 hướng** chứng minh luật trọng tài DILA 100 > MARCUS 60.
- Review 5 claim cao chất lượng: `POST /daoanh/api/admin/claims/<id>/review` (claim 6985–6989, source DILA=1 → verified/high).
- 1 bulk: `POST /daoanh/api/admin/claims/bulk-review` với 10 claim (DILA/CBETA, verified/medium) → mỗi claim ghi en_audit_log.
- Verify DB read-only: `en_audit_log` action=resolve_lineage_conflict = 5 mới · claim verified 44,000 → 44,015 · resolutions/history trả 5.

### P2 — Fix Resolutions-History (G2, additive 0 ALTER)
- `app.py` `api_admin_resolutions_history` (L16742): thay query chỉ đọc `resolutions_log` bằng **UNION**: (a) `en_audit_log WHERE action='resolve_lineage_conflict'` JOIN `lineage_conflicts_v2 ON person_id=entity_ref` + (b) `resolutions_log` (legacy). total = 2 COUNT. 0 bảng mới, 0 ALTER.
- Backup pre-edit: `docs/sessions/app.py.bak-t134-resolutions-history.py`. Verify: py_compile + mô phỏng SQL trên DB read-only trả đủ 5 (ai/lúc nào/lý do/nguồn).
- **Restart :5000 chờ admin** (PID 5012 Access denied đối với shell build — admin chạy `start_servers.py`).

### P3 — Doc + chốt trạng thái (G3)
- `docs/CURATION_WORKFLOW_SPEC.md`: conformance-pointer thin — bảng ánh xạ spec→module ĐÃ-CÓ (Editor Dashboard · Dispute UI · Audit Log · Bulk · Conflict Pool), quy trình HITL 3 bước Review→Acceptance→Commit (verification_status + en_audit_log), đổi thuật ngữ "Canonical"→"verified", bảng self-check 4 trục (Minh bạch/Kiểm soát/An toàn/Thuận tiện) kèm cách verify từng dòng. KHÔNG lặp code/DB.
- Task file + session doc `docs/sessions/2026-09-14_t134-curation-workflow-conformance.md` + entry tasktodo ACTIVE + regen dashboard (`python -X utf8 scripts/build_progress_data.py`) → board 55 tasks.
- T119: giữ pending đến khi Lee regression review xong (fix resolutions nằm trong T134; session ghi rõ).

## 3. Non-goals (KHÔNG làm)
- KHÔNG tạo `docs/PROJECT_STATUS.md` (SSOT = tasktodo + roadmap + dashboard).
- KHÔNG tạo editor/conflict/bulk mới — chỉ dùng endpoint có sẵn; KHÔNG đụng DB schema (chỉ INSERT/UPDATE qua endpoint chính thức).
- KHÔNG auto-canonical batch lớn; KHÔNG review claims ngoài mẫu DILA/CBETA đã chọn; KHÔNG xoá logs.
- KHÔNG restart các server khác (5001/8080); KHÔNG đụng SQL Injection/hardcode (parametrized).

## 4. Acceptance
- en_audit_log: 5 resolve_lineage_conflict mới (editor Lee Tổng) + 15 claim_review mới (5 single-high + 10 bulk-medium); claim verified +15.
- resolutions/history trả đủ 5 phán quyết (conflict_id · name_vi · chosen_source · resolved_by · resolved_at) — chứng minh Versioning hiển thị.
- CURATION_WORKFLOW_SPEC.md tồn tại, thin, không trùng file; self-check 4 trục có cách verify.
- tasktodo entry T134 ACTIVE + session doc + dashboard 55 tasks; T119 pending (chờ Lee hồi quy).
- Live :5000 hiển thị Resolutions sau khi admin restart.

## 5. Risks
- Restart app:5000 Access denied từ shell (PID 5012) → admin phải chạy `start_servers.py` hoặc `python app.py`; code đã verify offline.
- Groq rate_limit không ảnh hưởng (không dùng LLM trong T134).
- Board count có thể lệch nếu active khác; regen sau khi session viết.

## 6. Rollback
- Docs additive · app.py chỉ sửa 1 hàm (backup `.bak-t134-resolutions-history.py` sẵn) · DB redaction = `POST .../resolve` không có undo — ghi chú trong session; hồi phục claim: `UPDATE entity_claims SET ... unverified` + xoá audit row tương ứng (chỉ admin). Real git index không đụng (temp-index policy).