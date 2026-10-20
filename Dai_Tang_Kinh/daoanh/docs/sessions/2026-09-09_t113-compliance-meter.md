# Session — T113m Compliance Meter (Phần B DONE)

**Ngày:** 2026-09-09 · **Trạng thái:** Phần B DONE · Phần A QA live chờ :5000 (BLOCKED)

## Mục tiêu
Triển khai "đồng hồ đo luật" cho 9 metric `SCHEMA_DESIGN M7.2` — read-only, Zero-RAM,
không đụng DB (chỉ SELECT/COUNT aggregate), output `data/design_compliance.json` hiển thị Dashboard.

## Việc đã làm
1. **Script mới** `scripts/verify_design_compliance.py`:
   - Mở DB read-only (`file:...?mode=ro` + `PRAGMA query_only=ON`).
   - 9 metric M7.2, mỗi metric = cặp `SELECT COUNT(*)` (total + passed) — không duyệt hàng.
   - Kèm `goal` (chuẩn đạt docs — bootstrap ≥1% cho review/verified/assertion/conflicts)
     + `baseline_2026-09-08` (đối chiếu tiến triển T109/T110).
   - CLI: mặc định ghi JSON + in summary; `--json` in raw to stdout.
2. **Output** `data/design_compliance.json` (generated_at · 132 bảng · metrics · summary).
3. **Dashboard** `dashboard_process.html`: section **"Data Quality — Compliance Meter"** +
   `loadCompliance()`/`renderCompliance()` (fetch `/daoanh/api/compliance/dashboard`, bảng
   metric + goal + baseline + màu pass/warn/fail).
4. **Route app.py** `/daoanh/api/compliance/dashboard` (mirror progress/dashboard, `?regenerate=1`).
   → Được gộp vào commit T111 (app.py dùng chung 2 task — tránh split file; ghi rõ trong ROLLBACK).

## Kết quả đo (2026-09-09, từ DB thật)
- **5 pass ✅:** claims_with_source 100% · claims_with_confidence 100% · claims_with_audit 100% (T109) ·
  events_provenance 100% (T109) · glossary_vi_coverage 75.54% (T110).
- **1 warn ⚠️:** conflicts_resolved 0.01% (4/40,327 — bootstrap ≥1% chỉ mất 1 conflict resolve).
- **3 fail ❌:** claims_reviewed 0% · claims_verified 0% · claims_assertion_level 0%
  (hiện trạng review 0% — phản ánh đúng; chờ luồng admin review T109 qua `admin/conflicts.html`).

## Kiểm chứng
- `npm run pipeline` PASSED (lint ✅ test ✅ e2e ✅; e2e:runtime EPERM pre-existing).
- Assertion: các cột metric tồn tại trong DB (PRAGMA) — đã verify. Alerts #4/#5 (`tab_readiness`)
  chưa đủ điều kiện đóng (review rate 0%) — tình huống trung thực.

## Ghi chú chuyển giao
- Phần A T113 (QA live :5000) blocked — port chiếm; cần admin dọn port trước khi đóng task.
- Sau mỗi luồng review: dashboard `?regenerate=1` (hoặc `python scripts/verify_design_compliance.py`).
- Revert: `git revert --no-edit 1a51a356 0ebffc29` (DB không đổi → không cần --revert DB).