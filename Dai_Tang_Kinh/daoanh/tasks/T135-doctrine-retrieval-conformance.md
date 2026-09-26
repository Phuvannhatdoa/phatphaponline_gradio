---
id: T135
title: Doctrine-Retrieval-Conformance: RETRIEVAL_ENGINE_SPEC + Public Audit Trail (T118)
priority: high
status: in_progress
owner: AI Engineer (build) · Lee Tổng (acceptance)
module: Ops / Governance / Retrieval
created: 2026-09-14
updated: 2026-09-14
---
# T135 — Doctrine-Retrieval-Conformance (Option A): RETRIEVAL_ENGINE_SPEC thin + Audit Trail bậc Tiến sĩ (T118)

---

## 1. Context (AO — audit thật 2026-09-14, Lee phê chuẩn Option A 2026-09-14)

Spec "Task T117: Doctrine Retrieval Engine" (body ghi "ĐẶC TẢ KHÁI NIỆM T115") được admin gửi verify lần 2.
**Verdict: logic ~90% ĐÃ TỒN TẠI sẵn** = **T111 (persona L1/L2/L3 + evidence drawer + disclaimer) + T126 QA (no_data trung thực) + T109/T118 (audit_id) + T113 (compliance/UAT)**.
Admin phê chuẩn **Option A**: không rebuild; đóng 2 GAP THẬT + ghi nhận 1 deviation có chủ ý.

### Đã có sẵn (verified 2026-09-14 — KHÔNG làm lại)
- **Policy Filter 3 tầng = T111:** `?level=L1|L2|L3` clip server-side **L1 chỉ `verified`** (app.py L14350/14557); UI persona-aware `_daEvidenceDrawer` (places.html L7595–7664: L1 ẩn source_code/thuật ngữ kỹ thuật · L2 thêm assertion_level+source_code+filters theo claim_type/assertion_level · L3 thêm claim_id/confidence/source_reference).
- **Evidence Drawer luôn đi kèm** (No Evidence = No Answer): `_daEvidenceDrawer` gắn mọi khối giáo lý/evidence (places.html L7504/8139) — đầy đủ source/passage, không hiển thị câu trả lời suông.
- **Data Disclaimer động:** `_daZenqDisclaimer()` (places.html L7569) + L1 không thấy thuật ngữ kỹ thuật.
- **NOT INDEXED / NO DATA trung thực:** `POST /daoanh/api/daitang/qa` → `mode:'no_data'` status 200 (app.py L18536) + `data_gap_requests` ghi nhận yêu cầu — **không bịa**.
- **L3 Full Assertion Object:** `verification_status` + `claim_id` + `audit_id` SHA-256 (`entity_claims_audit` 447,885, T109) + citation export audit_id (T122-D1).
- **Comparative (L2):** evidence drawer nhóm claim theo `claim_type` + badge `source_code` từng nguồn + 2 chọn lọc assertion_level/claim_type → người dùng đối chiếu cùng tag khác nguồn.

### Điểm cần chỉ ra (đã gửi, được phê chuẩn)
1. **Lệnh #5 sai quy chiếu:** KHÔNG có `docs/PROJECT_STATUS.md` (SSOT = tasktodo + dashboard). Số board T115 = Source Authority Matrix (DONE) — đặc tả này map vào **board T117 (Doctrine Retrieval) = T100+T111+T113**. Không tạo PROJECT_STATUS.md.
2. **Deviation có chủ ý — "Persona tự nhận diện":** hệ thống dùng **switcher tường minh** (localStorage `da_persona_level`, default L2) — đúng chủ đích (auto-detect không tin cậy + riêng tư). Ghi rõ trong spec.
3. **GAP thật #1 — Audit Trail bậc Tiến sĩ public:** chỉ có `GET /daoanh/api/admin/audit/trail` (admin-only). Thiếu public/research → **đóng trong T135** = implement T118.
4. **GAP thật #2 — `docs/RETRIEVAL_ENGINE_SPEC.md` chưa tồn tại:** admin chủ động yêu cầu → tạo **conformance-pointer THIN** (pattern T133/T134), không phải design mới/trùng.

## 2. Pha (additive — thứ tự)

### P1 — Audit Trail public bậc Tiến sĩ (đóng GAP #1 = T118)
- **Endpoint mới `GET /daoanh/api/research/entity/<entity_ref>/audit-trail`** (app.py, sau `api_admin_audit_trail`, trước `_citation_lookup`):
  - read-only, 0 ALTER, query tham số hoá, Zero-RAM (LIMIT 200).
  - resolve entity qua `_resolve_entity_id` (entity_hub) → match `en_audit_log.entity_ref LIKE %ref%` (person A…/canonical_label/địa danh) → `history` (log_id→`audit_id=en-<id>`, action, field_name, old/new, evidence_sources, authority_rank, editor, verification_status, created_at).
  - `claims_audit`: mỗi claim của entity kèm `audit_id` SHA-256 từ `entity_claims_audit` + `verification_status` + by_status.
  - `data_status: indexed|no_data` trung thực.
- L3 persona = nghiên cứu sinh → đúng đặc tả "truy xuất lịch sử thay đổi của record".
- Backup `docs/sessions/app.py.bak-t135-audit-trail.py`. Verify: py_compile + mô phỏng SQL 3 nhóm (A000005 indexed 2 history · PL000000023255 indexed 38 claims · chuỗi không tồn tại → no_data).

### P2 — `docs/RETRIEVAL_ENGINE_SPEC.md` (conformance thin, đóng GAP #2)
- Ánh xạ spec → module ĐÃ-CÓ (Policy Filter→T111 · Evidence Drawer→_daEvidenceDrawer · Disclaimer→_daZenqDisclaimer · NOT INDEXED→T126 no_data+data_gap_requests · L3 Full Assertion→audit_id+claims_audit · Comparative L2→evidence drawer grouped+source badges).
- Qui trình "No Evidence = No Answer" + Lệnh truy vấn cho ClaudeCode (đã có sẵn → trỏ, không lặp).
- Bảng thẩm định 4 tiêu chí (Tính phân cấp/Trung thực/Minh bạch/Negative case) kèm cách verify từng dòng.
- Ghi rõ: deviation persona-switcher · không PROJECT_STATUS.md · số board mapping.

### P3 — Task + trạng thái + dashboard
- Task file `tasks/T135-doctrine-retrieval-conformance.md` + session `docs/sessions/2026-09-14_t135-doctrine-retrieval-conformance.md`.
- tasktodo: **T135 ACTIVE** (đầu mục) · **T118 ✅ DONE (impl trong T135)** · ghi chú T117 conformance verified.
- Regen dashboard (`python -X utf8 scripts/build_progress_data.py`) → board 56 tasks.

## 3. Non-goals (KHÔNG làm)
- KHÔNG tạo `PROJECT_STATUS.md`; KHÔNG re-open T111/T115/T117 (conformance chỉ, không rebuild).
- KHÔNG implement auto-detect persona (giữ switcher tường minh).
- KHÔNG thay QA engine; KHÔNG đổi schema (0 ALTER); KHÔNG expose dữ liệu nhạy cảm (audit trail read-only, chỉ trường provenance học thuật).

## 4. Acceptance
- Endpoint `/daoanh/api/research/entity/<id>/audit-trail` tồn tại + py_compile OK + 3 nhóm (indexed/no_data) đúng.
- `docs/RETRIEVAL_ENGINE_SPEC.md` tạo được, thin, không trùng file hiện hữu; self-check table đầy đủ.
- tasktodo: T135 ACTIVE + T118 DONE; session doc; dashboard 56 tasks.
- Live :5000 sau restart (chờ admin — Update Admin schedule sau T134).

## 5. Risks
- Restart app:5000 Access denied từ shell (PID 5012) → admin restart `start_servers.py`; verify offline trước.
- `entity_ref` format đa dạng (A…/PL…/dila) → matching LIKE %ref% cộng canonical_label; rủi ro miss format lạ — giới hạn 200, ghi chú.
- Groq không liên quan (0 LLM call trong T135).

## 6. Rollback
- app.py chỉ thêm 1 route (backup `.bak-t135-audit-trail.py` sẵn); docs additive; tasktodo/dashboard regen lại được. Real git index không đụng (temp-index policy).