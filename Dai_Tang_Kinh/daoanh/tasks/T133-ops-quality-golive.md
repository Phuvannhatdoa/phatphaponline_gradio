---
id: T133
title: OPS-Quality-GoLive: QA/Compliance Spec + UAT Persona + Backup + Pipeline Gate
priority: high
status: in_progress
owner: AI Engineer (build) · Lee Tổng (value)
module: Ops / Governance
created: 2026-09-14
updated: 2026-09-14
---
# T133 — OPS-Quality-GoLive: QA/Compliance Spec + UAT Persona + Daily Backup + Pipeline Gate

---

## 1. Context (AO — audit thật 2026-09-14, phê chuẩn 2026-09-14)

Spec T117–T121 (ZenQ naming: System QA & Compliance / Knowledge Mgmt & Training / Production Deployment & Live Support / Feedback-Driven Curation / Cross-Sect Interop) được admin gửi verify.
**Verdict: ~70–80% ĐÃ TỒN TẠI sẵn** dưới tên module khác; implement literal sẽ tạo file/script/table trùng. Admin phê chuẩn quy đổi thành task **chỉ lấp GAP THẬT** (additive, 0 rebuild, 0 trùng lặp).

### Đã có sẵn (verified — KHÔNG làm lại)
- **Compliance Meter = T113 ĐÚNG Y HỆT spec T117 §2:** `scripts/verify_design_compliance.py` → `data/design_compliance.json` (đã tạo: claims_with_source 100% pass · claims_with_confidence 100% · claims_reviewed 9.82 · claims_verified 9.82 · claims_with_audit 100 · events_provenance 100 · conflicts_resolved 0.02 warn · glossary_vi 75.54) + route `/daoanh/api/compliance/dashboard?regenerate=1` (app.py L11624) + dashboard block.
- **Persona = T111:** `?level=L1|L2|L3` server-side clip claims 'verified' (app.py L14282/L14494) → Cử nhân chỉ thấy verified. Unverified không ra người thường ✓.
- **Citation/Audit = T118:** `/daoanh/api/public/export/citation?entity_id&format=csl-json|bibtex&audit_id` (app.py L16895) — CSL/BibTeX + signature sha256(entity_id|audit_id|title), audit_id xuyên evidence_sources; `entity_claims_audit` 100% phủ.
- **Feedback/NOT-INDEXED request ĐÃ CÓ:** `data_gap_requests` (OPS_GAP_TABLE, Ráspec5, app.py L16474, list+update) + `user_feedback` (Ráspec6/T119, L16475) + ops counter gap_new/feedback_new (L17088).
- Auth admin riêng (:5001 server.py). Geo-enrich HITL (T121), translation_error_report (T123).

### GAP THẬT (làm 4 việc + 1 verify — sau audit chính xác 2026-09-14)
1. **Thiếu 3 spec docs:** `docs/QA_COMPLIANCE_SPEC.md`, `docs/KNOWLEDGE_MGMT_SPEC.md`, `docs/DEPLOYMENT_SPEC.md`. KHÔNG tạo `docs/PROJECT_STATUS.md` trùng — trạng thái bắt buộc map vào `docs/tasktodo.md` + `dashboard/`.
2. **Thiếu UAT persona script** (test 3 case thật: Cử nhân/Tiến sĩ/Negative → exit code).
3. **Daily Backup ĐÃ CÓ** (`scripts/daily_backup.py` — T116 D-Ops O1: sqlite online `Connection.backup()` + .gz + sha + prune 14 ngày + ghi `docs/OPS_LOG.md`; cron `0 2 * * *`). → **CHỈ verify + ghi cron + trỏ trong DEPLOYMENT_SPEC, KHÔNG tạo script mới**.
4. **Thiếu pipeline gate** compliance (assert KPI quan trọng).
5. **Thiếu "Người phụ trách" (`owner`)** trên board task (additive: frontmatter `owner:` → `build_progress_data.py` + card dashboard).

## 2. Pha (additive — thứ tự)

### P1 — 3 Spec Docs (không trùng tài liệu hiện hữu)
- `docs/QA_COMPLIANCE_SPEC.md`: UAT spec + bảng tiêu chí thẩm định (trung thực/kế thừa/minh bạch/tuân thủ/tái lập) — trỏ ĐÃ-CÓ ≡: verify_design_compliance.py · T111 persona L1-L3 · /export/citation · data_gap_requests/user_feedback · entity_claims_audit. Ghi rõ "không dùng AI summary thay thế (retrieval AO)".
- `docs/KNOWLEDGE_MGMT_SPEC.md`: khái niệm Learning Path (nền: lineage Lâm Tế 41–42, phả hệ), Academic Scaffolding (L1→L3 persona), Curation Registry (nền: admin dashboard / T116 curation), Canonical≠Draft (nền: verification_status + conflict_pending). Ghi rõ: Knowledge Package sẽ BUILD SAU (T134 candidate) — không hứa trong task này.
- `docs/DEPLOYMENT_SPEC.md`: Ops protocols (monitor=data_gap_requests, feedback=user_feedback, hardening=auth :5001, maintenance=re-chạy verify_design_compliance định kỳ), Go-live (Beta=dashboard whitelist, Data Freeze=SCHEMA_FREEZE, DR=backup_daily).
- 5 file đều "conformance pointer" — không lặp nội dung code/DB.

### P2 — UAT Persona script `scripts/uat_persona_test.py`
Chạy trên DB thật + App :5000 (nếu chạy) hoặc hàm trực tiếp:
- **Test 1 Cử nhân:** truy vấn "Tứ Diệu Đế" qua retrieval QA (đường hiện hữu) → assert trả lời ngắn gọn có nguồn; assert **KHÔNG có log kỹ thuật** (không leak trace/stack); assert chỉ dữ liệu verified cho L1.
- **Test 2 Tiến sĩ:** truy vấn phức tạp (entity có evidence đa nguồn) → gọi `/daoanh/api/public/export/citation?format=bibtex&csl-json&audit_id` → assert có provenance + audit_id + signature khớp sha256(entity_id|audit_id|title) + BibTeX hợp lệ.
- **Test 3 Negative:** query ngoài phạm vi (chuỗi không tồn tại) → assert trả trung thực (empty/`NOT INDEXED` tương đương), **không 502/504**, và ghi nhận vào `data_gap_requests` nếu cấu hình.
- Output JSON `data/uat_report.json` + `exit 0/1` theo fail criteria (No Source / Conflict tự gộp / Unverified hiện cho L1 / Negative không trung thực).
- Node/pytest độc lập, không đụng DB (read-only hoặc copy).

### P3 — Daily Backup verify + wiring (ĐÃ CÓ `scripts/daily_backup.py`, KHÔNG tạo mới)
- Xác nhận `scripts/daily_backup.py` (T116 O1) đầy đủ: online backup khi DB đang chạy, .gz, sha, `KEEP_DAYS=14`, append `docs/OPS_LOG.md`.
- Ghi cron thật vào `docs/DEPLOYMENT_SPEC.md` (bản VPS): `0 2 * * * cd /opt/.../daoanh && python scripts/daily_backup.py >> data/backup.log 2>&1`.
- Giữ feedback loop: `data_gap_requests` (query monitor) + `user_feedback` (feedback inbox) — trỏ trong spec, KHÔNG đụng code.

### P4 — Pipeline gate
- package.json: `"test:gov"` (đã có trong T131 plan — nếu chưa, thêm giờ): chạy pytest governance + `verify_design_compliance`. Và `"test:uat"`: `python scripts/uat_persona_test.py`.
- Gắn vào `pipeline`: `npm run test:gov && npm run test:uat && verify_design_compliance` (assert: claims_with_source≥100, claims_with_audit≥100, claims_reviewed>0 → warn không fail).
- KHÔNG làm yếu test; e2e:runtime EPERM pre-existing ghi nhận.

### P5 — Backups + Người phụ trách trên Dashboard
- Snapshot trước đổi: `[System.IO.File]::Copy` app.py/places.html + `.bak-t133`.
- **`owner:` frontmatter** (additive, 0 phá vỡ): thêm field `owner` vào tasks ACTIVE (T133 + T131/T132…). Sửa `scripts/build_progress_data.py` `scan_tasks()` thêm `'owner': meta.get('owner','')` + card `dashboard/dashboard_process.html` `renderTaskBoard` hiện "Người phụ trách: …" khi có owner. KHÔNG sửa layout cột tasktodo (giữ format đã ổn định).
- Session doc `docs/sessions/2026-09-14_t133-ops-quality-golive.md`; `python -X utf8 scripts/build_progress_data.py` regen dashboard.
- Chỉ commit qua temp-index khi user yêu cầu.

## 3. Non-goals (KHÔNG làm)
- KHÔNG tạo `docs/PROJECT_STATUS.md` (map tasktodo+dashboard); KHÔNG rename data_gap_requests→query_log/content_request_log (đã tồn tại, spec cho phép "equivalent"); KHÔNG build Learning Path/Curation Registry UI trong task này (ghi "T134 candidate"); KHÔNG sửa AI core/QA engine; KHÔNG đổi DB schema canonical; KHÔNG fake data; KHÔNG 0 ALTER destructive.

## 4. Acceptance
- 3 spec docs tạo được, không trùng file hiện hữu.
- uat_persona_test chạy 3 case → uat_report.json + exit code đúng.
- backup_daily tạo snapshot + prune N ngày.
- pipeline gate: compliance KPI + UAT PASS (trừ pre-existing EPERM ghi nhận).
- tasktodo có entry T133 (ACTIVE) + board dashboard hiện "Người phụ trách" (owner) khi có; trạng thái T117–T121 map đúng board.

## 5. Risks
- App :5000 có thể đang chạy → Test 2/3 cần URL config, fallback gọi hàm nội bộ nếu không reachable.
- Pipeline pytest dependency (không có pytest thì test:gov fallback unittest runner).
- Cột "Người phụ trách" thay đổi layout tasktodo — giữ nguyên format cũ + thêm header mới.

## 6. Rollback
- Docs additive; script mới không đụng code cũ; tasktodo/dashboard có thể revert b4_commit. Real git index không đụng (temp-index).