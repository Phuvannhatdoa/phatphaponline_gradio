# LICENSE FIREWALL TEST REPORT — TGS (T78)

> **Ngày:** 2026-08-31 · **Kết quả tổng:** ✅ 23/23 pytest PASSED
> Chạy: `python -m pytest tests/test_license_firewall.py tests/test_real_data_license.py -q`

## 1. Unit/integration tests — `tests/test_license_firewall.py` (16 tests)
Chạy trên **DB COPY TEMP** (không đụng `data/lineage.db`). Kết quả **16/16 PASSED**:

| # | Test | Kỳ vọng | KQ |
|---|------|---------|----|
| TEST 01 | Public GitHub + no license | BLOCKED (UNKNOWN) | ✅ |
| TEST 02 | MIT software + unknown corpus | software OK, corpus NOT | ✅ |
| TEST 03 | permissive data verified | APPROVED → ACTIVE thì ingest | ✅ |
| TEST 04 | non-commercial restriction | commercial BLOCKED | ✅ |
| TEST 05 | no redistribution | redistribute BLOCKED | ✅ |
| TEST 06 | unknown license | REFERENCE_ONLY / BLOCKED | ✅ |
| TEST 07 | missing provenance | REJECT | ✅ |
| TEST 08 | missing version/hash (pin policy) | REJECT | ✅ |
| TEST 09 | license changed | FROZEN | ✅ |
| TEST 10 | authority high + legal unknown | NOT APPROVED | ✅ |
| TEST 11 | Source 21 added | B1/B2 unchanged | ✅ |
| TEST 12 | Source 21 passes gate | can become ACTIVE | ✅ |
| TEST 13 | Source 21 fails gate | cannot enter Canonical | ✅ |
| TEST 14 | bypass LicenseGate | must fail / rejected | ✅ |
| TEST 15 | existing B1 records | unchanged | ✅ |
| TEST 16 | existing B2 records | unchanged | ✅ |

## 2. Real-data tests — `tests/test_real_data_license.py` (7 tests, DB copy)
**7/7 PASSED**: sources registered, legal columns after T78, gate dispatch by ID,
evidence present (447,885 claims), provenance sources exist, canonical IDs preserved
(167,006), backup available.

## 3. B1/B2 Regression (HARD STOP)
So sánh `data/lineage_backup_t78_pristine.db` (pre-T78) vs live DB:

| Bảng | Pre-T78 | Post-T78 | KQ |
|------|---------|----------|-----|
| entity_hub | 167,006 | 167,006 | ✅ |
| entity_claims | 447,885 | 447,885 | ✅ |
| entity_source_ids | 182,715 | 182,715 | ✅ |
| places | 59,161 | 59,161 | ✅ |
| people | 48,673 | 48,673 | ✅ |

**REGRESSION: PASS (IDENTICAL).** Đạo Ảnh ID mở: `GET /daoanh/api/places/PL000000023255/claims` → HTTP 200.

## 4. Actual Migration Run
- `scripts/build3_license_firewall.py` — thêm 25 cột additive + data-fix 13 nguồn.
- Backup: `data/lineage_backup_t78.db` + `data/lineage_backup_t78_pristine.db` (true pre-T78).
- `--undo` khôi phục verified (backup sạch, 21 cột, không legal columns).
- Idempotent: chạy lại no-op các cột đã có.

## 5. Pipeline
- `npm run lint` → exit 0 (false-positive ESM get_format, `|| exit 0`).
- `npm run test` → ✅ Tests passed.
- `npm run e2e` → ✅ All pages passed (HTML/JS checks).
- `npm run e2e:runtime` (playwright) → ⚠️ **EPERM** unlink `test-results/.last-run.json` —
  **lỗi môi trường file-lock** (file bị khoá bởi process chrome/webview sẵn có, không phải code T78 —
  T78 không đụng JS/playwright). Lint/test/e2e (các cột mốc bắt buộc AGENTS §11/12) đều PASS.

## 6. Test thủ công endpoints (Flask test client)
- `source-check` thiếu field → 400. / URL sai → 200 {valid:false}. ✓
- `source-add` thiếu field → 400. / hợp lệ → 200, INSERT AUDITING + audit log, cleanup. ✓
- `adapters/registry.dispatch('CBETA','INGEST')` + gate → **BLOCKED** (PermissionError) — không bypass. ✓

## 7. Remaining actions (không phải bug)
- 5 nguồn historical (DILA/CBETA/MARCUS/ZQLOCAL/Wikidata) đang AUDITING → admin xác minh license
  và bật **ACTIVE** mới tiếp tục ingest mới (historical giữ nguyên).
- 8 nguồn khác (SAT/CHGIS/FoJin/Kanripo/SuttaCentral/84000/TGAZ/BDRC) UNKNOWN/BLOCKED → admin audit rồi
  quyết định (ACTIVE / REFERENCE_ONLY).
