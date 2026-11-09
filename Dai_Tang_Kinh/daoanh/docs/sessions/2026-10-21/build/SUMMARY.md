# BUILD SUMMARY — 2026-10-21

- HEAD (baseline): `2570f6fbd3cf3d9941f1ba837ea7bea4233b4374`
- Log chính: `docs/sessions/2026-10-21/build/pipeline-132935.log` (có cả chuỗi `npm run pipeline` và các bước chạy tiếp; mỗi bước có header `######## STEP` + `EXIT_CODE=`)
- Chuỗi `npm run pipeline` gốc **dừng tại `audit:honesty:strict` (exit 1)** nên các bước sau không chạy trong chuỗi. Tôi chạy tiếp từng bước còn lại, mỗi bước độc lập, không dừng khi lỗi.
- npm không lỗi shim trên máy này (chạy được qua `cmd /c npm run ...`).

## Bảng bước

| # | Bước (npm run) | Lệnh thực tế | Exit | PASS/FAIL | Lỗi mới/cũ | Log |
|---|---|---|---|---|---|---|
| 1 | guard | `python -X utf8 scripts/repo_guard.py` | 0 | PASS | — | pipeline-132935.log |
| 2 | dup:ids | `python -X utf8 scripts/build_progress_data.py --check-dup-ids` | 0 | PASS | — | pipeline-132935.log |
| 3 | audit:honesty:strict | `python -X utf8 scripts/audit_data_honesty.py --strict` | 1 | **FAIL** (H1,H2,H3,H4,H5) | CŨ (dữ liệu DB) | pipeline-132935.log L24-51 |
| 4 | audit:h3 | `python -X utf8 scripts/audit_h3_conflicts.py` | 0 | PASS (exit) — **⚠ GHI ĐÈ FILE TRACKED** | Side-effect MỚI của build | pipeline-132935.log L54 |
| 5 | lint | `node scripts/lint-check.js` | 0 | PASS | — | L82 |
| 6 | test | `node tests/run-tests.js` | 0 | PASS | — | L104 |
| 7 | test:t226 | `python -X utf8 tests/test_t226_ttl_profile.py` | 0 | PASS | — | L112 |
| 8 | test:t227 | `python -X utf8 tests/test_t227_db_ttl_export.py` | 0 | PASS | — | L150 |
| 9 | test:t232 | `python -B -X utf8 tests/test_t232_generation_engine.py` | 1 | **FAIL** 1/20 (`test_09_missing_parent_is_incomplete`: `'candidate' != 'incomplete'`) | CŨ (code logic đã commit) | L180-222 |
| 10 | test:t233 | `python -B -X utf8 tests/test_t233_codex_namevi.py` | 0 | PASS | — | L224 |
| 11 | test:t253 | `python -X utf8 tests/test_t253_person_import.py` | 0 | PASS | — | L262 |
| 12 | test:t242 | `python -X utf8 tests/test_t242_vn_places_etl.py` | 0 | PASS | — | L274 |
| 13 | test:t243 | `python -X utf8 tests/test_t243_place_name_normalize.py` | 0 | PASS | — | L291 |
| 14 | test:t244 | `python -X utf8 tests/test_t244_matching.py` | 0 | PASS | — | L299 |
| 15 | test:translation | chuỗi t165→t211 (`&&`) | 1 | **FAIL** — Gap 17 case `17c name_vi = Đơn Hà Thiên Nhiên` nhận `Thiên Nhiên` (68/69) | CŨ (dữ liệu vn_person_authority) | L316-742 |
| 16 | test:uat | `python -X utf8 scripts/uat_persona_test.py` | 0 | PASS (3/3) | — | L744 |
| 17 | test:compliance | `python -X utf8 scripts/verify_design_compliance.py` | 0 | PASS exit nhưng **metric fail=2** (claims_assertion_level 0%, conflicts_resolved 0%) | CŨ (cảnh báo, không làm exit≠0) | L757 |
| 18 | test:gov | `python -X utf8 -m pytest tests/test_b25_authority_contract.py -v` | 0 | PASS | — | L775 |
| 19 | audit:t166 | `python -X utf8 scripts/t166_identity_audit.py` | 1 | **FAIL** `sqlite3.OperationalError: no such column: identity_status` (translation_cache) | CŨ (schema DB thiếu cột, script trong HEAD) | L809-831 |
| 20 | e2e | `node scripts/e2e-test.js` | 0 | PASS | — | L833 |
| 21 | e2e:runtime | `node scripts/run-runtime-tests.cjs` | 0 | PASS | — | L884 |

Tổng: 21 bước · PASS 17 (trong đó 1 có side-effect phá dữ liệu) · FAIL 4 (honesty:strict, t232, translation, t166).

## Tổng số lỗi MỚI (không phải cũ)

**0 lỗi mới xác nhận** về logic code. Lý do: code/test liên quan các lỗi FAIL là file đã commit trong HEAD và không nằm trong danh sách file chưa commit (ví dụ `src_python/generation_engine_v2.py` không có trong `git status`); FAIL còn lại đến từ dữ liệu DB (`data/` là ignored). Lưu ý: tôi **chưa** chạy lại trên bản HEAD tạm trong %TEMP% (DB dùng chung nên kết quả sẽ không đổi; chưa làm riêng).

**Nhưng có 1 thay đổi MỚI do build gây ra** (xem dưới) — đây là vấn đề nghiêm trọng hơn các FAIL.

## ⚠ BÁO NGAY — build ghi đè file tracked

`npm run audit:h3` (`scripts/audit_h3_conflicts.py` dòng 214–222) ghi đè bằng `io.open(..., "w")`:
- `docs/evidence/2026-10-08_T263_h3_conflicts.tsv`: HEAD **407 dòng** → worktree **1 dòng** (chỉ header). Mtime 13:30:34 = đúng lúc build chạy.
- `docs/evidence/2026-10-08_T263_h3_conflicts_summary.tsv`: HEAD nhóm A=47 / B=79 / C=280 → worktree **0 / 0 / 0**.

Nguyên nhân gốc (suy ra từ code + kết quả): script hard-code tên file theo ngày `DATE = 2026-10-08` và luôn ghi đè, không có guard "không ghi khi kết quả rỗng/thiếu DB". Tức là chạy lại `audit:h3` sẽ phá bằng chứng H3 gốc.
- **Chưa khôi phục** (theo chỉ thị: không checkout/reset). Khôi phục khi Admin duyệt: `git show HEAD:Dai_Tang_Kinh/daoanh/docs/evidence/2026-10-08_T263_h3_conflicts.tsv > ...` (hoặc `git checkout HEAD -- <file>`) — cần Admin quyết định.
- Khuyến nghị: không chạy `npm run audit:h3` / `npm run pipeline` cho đến khi script có guard không ghi đè (fix riêng, ngoài scope build này).

## Danh sách file build đã tự sinh/sửa (theo mtime trong cửa sổ 13:29–14:15)

| File | Thời điểm | Loại | Ghi chú |
|---|---|---|---|
| `docs/evidence/2026-10-08_T263_h3_conflicts.tsv` | 13:30:34 | **TRACKED — đã phá** | xem trên |
| `docs/evidence/2026-10-08_T263_h3_conflicts_summary.tsv` | 13:30:34 | **TRACKED — đã phá** | xem trên |
| `data/vn_places_merge_report.json` | 13:31:32 | generated (ignored) | |
| `data/uat_report.json` | 13:32:21 | generated (ignored) | |
| `data/design_compliance.json` | 13:32:39 | generated (ignored) | |
| `.pytest_cache/*` | 13:33:39 | cache | |
| `docs/reports/runtime-tests/run-MDNTy8/*` | 13:34:32–43 | artifact e2e:runtime (untracked) | |
| `logs/auth-5001-err.log` | 13:30:35 | log server | |
| `admin/placevn.html` | 13:35:51 | **TRACKED, đang M từ trước** | KHÔNG phải build (không bước nào ghi file này). Khả năng cao là session khác đang sửa — chưa xác minh |
| `app.py` | 13:44:51 | **TRACKED, đang M từ trước** | như trên — KHÔNG do build |
| `places.html` | 13:45:13 | **TRACKED, đang M từ trước** | như trên — KHÔNG do build |
| `logs/app-5000-err.log`, `logs/gateway-8080-err.log` | 14:14:17 | log server | ngoài pipeline (có thể do server khác đang chạy) |

Ghi chú baseline: `git-status-before.txt` **không đáng tin** — file lưu ra 0 dòng, trong khi sau build `git status --short` có ~200 mục. AGENTS §17 đã cảnh báo `git status` có thể hỏng im lặng trên máy này; nên không thể đối chiếu before/after bằng file đó. Đối chiếu theo mtime (ở trên) là bằng chứng chính. `git-status-after.txt` vẫn được lưu để tham khảo.

## Việc Admin cần quyết
1. Khôi phục 2 file `docs/evidence/2026-10-08_T263_*.tsv` từ HEAD? (Admin duyệt trước)
2. Có fix `audit_h3_conflicts.py` để không ghi đè khi rỗng không? (task riêng)
3. Có chấp nhận 4 FAIL (honesty:strict, t232, translation, t166) là known-debt để pipeline xanh không, hay phải sửa trước khi review?
