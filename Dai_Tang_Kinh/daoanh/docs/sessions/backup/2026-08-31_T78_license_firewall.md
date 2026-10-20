# Session 2026-08-31 — T78: Legal/License Firewall + Legal Check

**Status:** DONE (đã test, B1/B2 regression PASS, docs hoàn tất)
**Scope:** TGS/PTDA — thêm layer Source Governance trước ingestion + menu admin "Legal Check".
**Build:** additive + reversible; migration có backup + `--undo`; KHÔNG phá B1/B2.

## 1. Việc đã làm
1. **Migration** `scripts/build3_license_firewall.py`:
   - ALTER additive `data_sources` +25 cột legal (`license_*`, `legal_status*`, `terms_status`,
     `version_policy`, `integration_mode`, `data_*`, `repository_url`, `updated_at`, ...)
     → final 46 cột.
   - Backup: `data/lineage_backup_t78.db` + `data/lineage_backup_t78_pristine.db` (true pre-T78=21 cột).
   - `--undo` đã verify: restore pristine, KHÔNG còn legal columns.
   - Idempotent: chạy lại no-op.
   - Data-fix additive 13 nguồn: 5 historical giữ + snapshot `legal_status_at_ingest`; 8 UNKNOWN/BLOCKED.
2. **Gate package** `gate/`:
   - `status.py` — máy trạng thái LegalStatus, **KHÔNG DEFAULT=ACTIVE**.
   - `license.py` — LicenseGate.checkSourcePermission (8 operations, phân biệt software vs corpus,
     rule SPDX, thêm RBRL redistribute).
   - `provenance.py` — ProvenanceGate (field bắt buộc, từ chối "latest" làm provenance duy nhất).
   - `analyzer.py` — curl public repo LICENSE/README + GitHub API, content_hash, report/notes/provenance.
3. **Backend** `app.py` (gia tăng, sau `admin_place_update`):
   - `POST /daoanh/api/admin/source-check` — kiểm tra tên+repo URL (public, no token).
   - `POST /daoanh/api/admin/source-add` — INSERT legal_status=AUDITING (KHÔNG tự ACTIVE) + audit log,
     auto `source_code`, update-if-exists; sửa lỗi `action` unbound trong nhánh INSERT.
4. **Frontend**:
   - `admin/source_check.html` — form 2 bước (tên+repo → CHECK & REPORT → report 3 phần A/B/C + notes
     + provenance → XÁC NHẬN THÊM).
   - `admin/index.html` — menu sidebar "Legal Check Nguồn" (Hệ thống, icon fa-scale-balanced).
5. **Adapter hook** `adapters/registry.py`: `dispatch` gọi LicenseGate trước, PermissionError khi blocked
   (no bypass). Kiểm chứng: `dispatch('CBETA','INGEST')` → BLOCKED.
6. **Tests**:
   - `tests/test_license_firewall.py` — 16/16 PASS (TEST 01–16).
   - `tests/test_real_data_license.py` — 7/7 PASS (DB copy, không đụng lineage.db).
   - B1/B2 regression: counts IDENTICAL (167,006 / 447,885 / 182,715 / 59,161 / 48,673).
   - Đạo Ảnh ID mở: `/daoanh/api/places/PL000000023255/claims` → HTTP 200.
7. **Docs** (hoàn tất):
   - `tasks/T78-license-firewall.md` · `docs/LICENSE_FIREWALL_AUDIT.md` · `docs/LICENSE_FIREWALL.md`
   - `docs/SOURCE_REGISTRY.md` · `docs/PROVENANCE_POLICY.md` · `docs/SOURCE_INTEGRATION_POLICY.md`
   - `docs/LICENSE_FIREWALL_TEST_REPORT.md`
   - Update: `docs/tasktodo.md`, `docs/progress.md`, `docs/roadmap.md`, `docs/trusted-sources.md`
   - `dashboard/dashboard_process.html` — banner ⚖️ LEGAL CHECK (T78).
   - Session này: `docs/sessions/2026-08-31_T78_license_firewall.md`.

## 2. Kết quả
- **23/23 pytest PASSED.**
- **Pipeline:** lint/test/e2e PASS. `e2e:runtime` (playwright) fail do **môi trường file-lock**
  (`EPERM unlink test-results/.last-run.json` — file bị process chrome/webview cũ khóa; KHÔNG phải code
  T78; không kill process người dùng).
- **Migration thật** đã chạy trên DB live (46 cột); undo verified.

## 3. Việc đang dở
- Server **PID 196 port 5000 stale** (không có route mới `/daoanh/api/admin/source-check` → 404).
  Cần **restart app.py** để menu/routes Legal Check hoạt động (đã báo admin vì chạm port live 5000/5001).

## 4. Todo tiếp theo
- [ ] Restart `app.py` (kill PID 196, chạy lại) → verify menu "Legal Check Nguồn" + routes.
- [ ] (Khi bật dữ liệu dashboard) chạy `scripts/build_progress_data.py` để thẻ T78 xuất hiện trên
      Task Board (progress_data.json là file phiên song song — tránh ghi đè trước khi merge).
- [ ] Admin xác minh license 5 nguồn historical → set ACTIVE để mở ingest mới (không tự động).
- [ ] Admin audit 8 nguồn UNKNOWN/BLOCKED → quyết định ACTIVE/REFERENCE_ONLY.

## 5. Lệnh xem nhanh
```bash
# Test
python -m pytest tests/test_license_firewall.py tests/test_real_data_license.py -q
# Chop undo migration (nếu cần)
python scripts/build3_license_firewall.py --undo
# Restart server
pkill -f app.py; python app.py
```
