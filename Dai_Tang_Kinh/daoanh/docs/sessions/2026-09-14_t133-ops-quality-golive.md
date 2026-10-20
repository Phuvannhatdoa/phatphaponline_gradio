# Session — 2026-09-14 T133 Ops-Quality-GoLive (Spec T117–T121 vs hệ thống)

## Bối cảnh
Admin gửi spec ZenQ **T117–T121** (System QA & Compliance / Knowledge Mgmt & Training / Production Deployment & Live Support / Feedback-Driven Curation / Cross-Sect Interop) yêu cầu verify. Audit thật trên DB + code → **verdict: ~70–80% ĐÃ TỒN TẠI sẵn**; chỉ còn GAP THẬT nhỏ. Admin phê chuẩn → **T133**.

## Kết quả audit (verified 2026-09-14)

### Đã có sẵn (KHÔNG làm lại)
| Spec | Hiện trạng thật |
|---|---|
| T117 §2 Compliance Meter | ≡ **T113**: `scripts/verify_design_compliance.py` → `data/design_compliance.json` + route `/daoanh/api/compliance/dashboard?regenerate=1` app.py:11624 + khối dashboard L676. Chạy lại ngay: **9 metric · pass 7 / warn 1 / fail 1** — claims_with_source 100% · reviewed 9.82% · audit 100% · events_provenance 100% · conflicts_resolved 0.02% (warn) · assertion_level 0% (fail, HITL-by-design) · glossary_vi 75.54% |
| T117 Test 1 Cử nhân | ≡ persona **L1** (`?level=L1` app.py:14282/14494) clip claims 'verified' — Unverified không ra người thường |
| T117 Test 2 Tiến sĩ | ≡ **T118 citation** `/daoanh/api/public/export/citation?entity_id&format=csl-json\|bibtex&audit_id` (app.py:16895) — CSL/BibTeX + signature sha256 + audit_id xuyên + evidence_sources |
| T117 (tra cứu cơ bản) | ≡ T126 QA backend live |
| T118 Feedback / bổ sung DL (NOT INDEXED → yêu cầu) | ≡ **`data_gap_requests`** (OPS_GAP_TABLE app.py:16474) + **`user_feedback`** (Ráspec6/T119, app.py:16475) + ops counter gap_new/feedback_new |
| T119 Production / hardening / monitor | auth admin riêng (:5001) ✓; monitor=data_gap_requests ✓; maintenance=verify_design_compliance ✓; **Daily backup ≡ `scripts/daily_backup.py` (T116 O1)** — sqlite online backup + gz + sha + prune 14 ngày + OPS_LOG, cron `0 2 * * *` |
| T120 refinement pipeline | geo-enrich HITL, web_enrichment_cache, translation_error_report (T123), user_feedback loop ✓ |
| T121 cross-sect | `people.sect` có sẵn; chưa có mapping-bridge cross-tông (GAP dài hạn — ngoài phạm vi T133) |

### GAP THẬT (T133 sẽ làm)
1. Thiếu `docs/QA_COMPLIANCE_SPEC.md` · `docs/KNOWLEDGE_MGMT_SPEC.md` · `docs/DEPLOYMENT_SPEC.md` (conformance-pointer, trỏ các module ĐÃ-CÓ, KHÔNG lặp nội dung). KHÔNG tạo `docs/PROJECT_STATUS.md` (map tasktodo + dashboard).
2. Thiếu **UAT persona script** (`scripts/uat_persona_test.py` — 3 case: Cử nhân / Tiến sĩ / Negative → uat_report.json + exit code).
3. Daily backup = verify + ghi cron (KHÔNG tạo script mới).
4. Pipeline gate: `test:gov` pytest + `test:uat` + verify_design_compliance assert KPI.
5. **Người phụ trách (`owner`)** — additive frontmatter + build_progress_data.py + card dashboard (ĐÃ LÀM trong session).

## Files touch (2026-09-14)
- `tasks/T133-ops-quality-golive.md` — task file (owner/module/id, GAP chính xác sau audit, P3 = verify daily_backup có sẵn).
- `tasks/T131-*.md`, `tasks/T132-*.md` — thêm frontmatter owner/module.
- `scripts/build_progress_data.py` — `scan_tasks()` thêm `'owner': meta.get('owner','')`.
- `dashboard/dashboard_process.html` — card task hiện "Người phụ trách: …" khi có owner.
- `docs/sessions/2026-09-14_t133-ops-quality-golive.md` (file này).
- `docs/tasktodo.md` — entry T133 (mục này session).

## Next actions
1. ~Viết 3 spec docs conformance (`QA_COMPLIANCE_SPEC.md`, `KNOWLEDGE_MGMT_SPEC.md`, `DEPLOYMENT_SPEC.md`) — **DONE 2026-09-14**.
2. ~Viết `scripts/uat_persona_test.py` — **DONE 2026-09-14, 3/3 PASS + HTTP live (signature self-consistent với :5000)**; report `data/uat_report.json`.
3. ~Verify `daily_backup.py` — **DONE 2026-09-14** (T116 O1 đầy đủ: online backup + gz + sha + verify + prune 14d + OPS_LOG; cron `0 2 * * *` đã ghi trong DEPLOYMENT_SPEC; KHÔNG tạo script mới; không chạy thật snapshot ~600MB).
4. ~Gắn `test:uat`/`test:compliance` vào pipeline — **DONE 2026-09-14** (package.json; cả 2 exit 0).
5. ~`owner` Người phụ trách trên board — **DONE 2026-09-14** (frontmatter `owner:` ở T131/T132/T133 + `build_progress_data.py` scan + card dashboard).
6. REMAIN: full `npm run pipeline` (lint+test+uat+compliance+e2e+playwright) → admin confirm → chuyển task sang implement T131/T132 theo batch.

## Bổ sung lỗi gặp khi implement (ghi nhận)
- `glob` tool không tin cậy xác nhận tồn tại file trong repo này → dùng Test-Path/grep/read.
- PowerShell vòng lặp `Get-Content -Raw → Set-Content -Encoding UTF8` làm hỏng ký tự UTF-8 không phải ASCII (đọc ANSI trước) → **luôn dùng tool Write/Edit thay vì round-trip qua Set-Content** (đã viết lại uat_persona_test.py sạch).
- `places_dila` không có cột `name_vi` (chỉ `name`) ; `entity_claims.entity_id` là ID nội bộ numeric (159344 = PL000000000220), join qua `entity_hub.canonical_label`.
- Task YAML frontmatter phải có `---` đóng/mở — thiếu → dashboard fallback status 'pending' (đã sửa T131/T132/T133).

## State
- Dashboard: 54 task trên board (đã regen sau thêm T133; tỷ lệ done cập nhật theo task_meta).
- Đang chờ: chạy implement các pha 1–4 (theo batch phân tích tích hợp hoặc ngay khi admin yêu cầu).