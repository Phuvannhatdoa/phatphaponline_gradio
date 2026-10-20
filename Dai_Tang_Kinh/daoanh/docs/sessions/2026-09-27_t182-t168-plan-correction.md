# Session 2026-09-27 — T182: T168 PLAN correction (docs-only)

## Tổng quan
- **Task:** `tasks/T182-t168-plan-correction.md`
- **Admin:** phê chuẩn đề xuất sửa T168 PLAN (8 sai lệch S1–S8 audit read-only 2026-09-27).
- **Phạm vi:** docs-only, 0 code, 0 DB, 0 API — sửa additive tại chỗ file plan, không tạo bản copy.
- **Repo root:** SSOT `visjs-app` (guard PASS — không repo lồng trong `daoanh/`).

## Việc đã làm

### 1. File plan `docs/Mimo-Flash/X-T168-rule-resolver-context-compiler-PLAN.md`
Ghi chú: file đã được đổi tên `T168-…→X-T168-…` trong lúc audit/build (prefix `X-` — convention role/review). 8 lệch đã sửa:
| # | Nội dung cũ (snapshot 2026-09-25) | Sửa thành (thật 2026-09-27) | Loại |
|---|-----------------------------------|-----------------------------|------|
| S1 | audit scope dùng `admin/app.py (18.865 dòng)`, A1 line 61 `admin/app.py:18193` | bỏ nguồn ảo → chỉ `app.py`; chú thích `admin/app.py` KHÔNG tồn tại (xác nhận tasks/T168-t165-spec-v2-review-accepted) | P0 |
| S2 | `rule_type` chỉ 4 giá trị (86/8/2/1) | 7 giá trị: terminology 90 · style 10 · forbidden 6 · gate 3 · provenance 1 · structure 1 · grammar 1 = **112** (T167 seed) | số liệu |
| S3 | P0-2 `RULE-%` = 0 row | **15 row** (T167 seeded RULE-001..015) — cập nhật tiền đề P0-2 | số liệu |
| S4 | 96 active + 1 dismissed, 0 pending | active **110** (+1 active/is_active=0) · dismissed 1 · pending 0 | số liệu |
| S5 | cache 1.761 (auto 1.752) | **1.799** (auto 1.790 · draft 2 · edited 6 · invalidated 1) + cột additive constitution_hash/glossary_hash | số liệu |
| S6 | `_t73_call_gemini` 0 retry/backoff | đã có `_T73_429_MAX_RETRY` + backoff 2s→4s + `_t165_persist_prompt_metrics` (T178 gap 13 build xong) | code ref |
| S7 | tests/ chỉ 4 file | **11 file** (test_t165/166/167/178/179 addition) | số liệu |
| S8 | line refs cũ (16272/16266/16330/16482/worker:188) | `_t73_rules_version`=16916 · `_t73_source_hash`=16923 · `_glossary_resolver`=16958 · `_t73_call_gemini`=17083 · worker `validate_unit`=212 | line drift |

Thêm: banner snapshot đầu file + frontmatter `status: pending → superseded` + `depends_on: +T167` + `updated: 2026-09-27` + tick Phase B (Phase 5/7 xong qua T166/T178/T179; Phase 8 report vẫn pending).

### 2. Docs
- `tasks/T182-t168-plan-correction.md` (mới, frontmatter đầy đủ).
- `docs/tasktodo.md`: row T182 (DONE) chèn đầu list ACTIVE sau T181.
- `docs/ROLLBACK.md`: row T182 với revert path.

### 3. Dashboard
- `python scripts/build_progress_data.py` → `data/progress_data.json` regen chứa T182.

## Verify
- `npm run guard` PASS (SSOT repo-root).
- `py_compile` không áp dụng (docs-only); frontmatter task T182 parse được (id/status/done_when đủ).
- `npm run pipeline` (2026-09-27 lát): **guard PASS · lint PASS · test PASS · t165/t166/t178/t179/t167 PASS · uat PASS · compliance PASS · gov PASS · audit:t166 PASS (0 FAIL + 1 WARN inline Gemini key không chặn) · e2e PASS (4/4 pages)**. Chỉ `e2e:runtime` fail `EPERM unlink test-results/.last-run.json` — pre-existing (file bị process khác giữ handle, không phải lỗi T182/docs).

## Revert
- **1 lệnh:** `git revert --no-edit 13b0ca59df55e719735698e49428462906e4f7d2` (docs-only).
- Cấm `cp *.bak` · cấm `reset --hard`.

## Ghi chú concurrency
- `docs/tasktodo.md` bị 1 process khác giữ handle ngắn hạn (edit tool fail `FileSystem.writeFile` vài lần) — sau đó nhả, edit thành công. Không cần xử lý.
- T181: script `scripts/t181_cbeta_download.py` + docs sẵn sàng commit riêng (chờ `index.lock` hết từ agent khác). Không đụng `app.py` (WIP agent khác vùng `t181_cbeta_catalog`).