# Session — T166 Phase 2 + Phase 3 (Build & Integration) 2026-09-26

## Build directive (Admin)
"Đồng ý build, hãy lưu logs, gitcommit và update các thông tin của các task mới vào các .md files tương ứng. Bảo đảm mọi bugs khi fix đều có thể commit back về version trước đó 1 cách thuận tiện. Gọi pipip khi done"

## Tóm tắt đã làm

### Phase 2.5 — style_constitution.py T166 wiring (commit `0150e66` cùng migration)
1. Inject `_t166_identity_block(lock)` (render CanonicalLock §5 → 4 block LOCKED/CANDIDATE/CONFLICT/UNKNOWN) TRƯỚC block Style Constitution trong `build_style_prompt` — identity > glossary > style (constraint cao nhất).
2. `style_lock` giờ set `t166_lock_fingerprint` (qua `_t166_fingerprint`) + `t166_identity_lock` entries.
3. **Gating fingerprint**: chỉ nhận giá trị khi có LOCKED entry trong source → rỗng khi không có LOCKED ⇒ **KHÔNG mass-miss cache** (SPEC §9). Verify 3 trường hợp: 丹霞天然 (LOCKED) → fp `0f8d286c...` ; source VI-thuần/Hán-CANDIDATE-only → fp `''`.
4. `write_cache` mở rộng 3 cột identity với guard `_has_col` (pre-migration vẫn legacy chạy như T165).
5. Helpers: `is_trusted_translation(NULL='pass')`, `is_draft_translation`, `identity_lock_policy(conn, default='P-PARTIAL')`.

### Phase 3.1 — Migration `scripts/t166_identity_migrate.py` (commit `0150e66`)
- CLI `--stats/--dry-run/--apply/--revert`, backup sqlite API an toàn khi DB mở.
- ADD: `translation_cache.identity_status/identity_issues/identity_lock_hash TEXT` + `translation_rules.identity_lock_policy TEXT DEFAULT 'P-PARTIAL'` + index `idx_tc_identity(identity_status)`.
- **--apply trên DB thật**: backup `data/backups/lineage_t166_20260926_075955.db` (+ lần 2 `080107`). `identity_lock_policy` seed P-PARTIAL × 112.
- **Revert verified 2 chiều**: `--revert` → DROP 4 cột + index, 1762 cache rows + 112 rules NGUYÊN VẸN → re-`--apply` thành công.
- Baseline: 1762 cache rows, **0 có constitution_hash** (cache vẫn chạy legacy `rules_version`).

### Phase 3.2a — SECURITY fix SPEC §7.1 (commit `b89c7bed`)
- `admin_namevi_map_update` (nguồn tạo LOCKED authority `name_vi_map.final+approved` = 1.0) thiếu auth → **thêm `verify_session` → 403**. Bất kỳ ai tải app lên có thể "đúc" nguồn LOCK ⇒ SPEC §20.2 #15.
- `api_name_vi_lookup` trả `name_vi_source` (`final`/`auto`/`base`) cho UI badge "Auto chưa duyệt".
- Helpers `_dict_or`/`_json_or_parse` chịu row pre-migration (không crash).

### Phase 2 — Wire `_t166_post_check_translation` vào app.py (commit `b89c7bed`)
- `canonical_lock.py` thêm `post_check_translation(conn, source_text, output, policy)` — post-assert cho luồng đã dùng Style Constitution prompt (pre-assert nhẹ bắt P-STOP còn sót; không dựng prompt lại).
- 4 translate paths wire: `api_person_translate` (person_bio) · `api_person_dila_translate` (dila_card, sau override relations bằng DB truth) · place_note · relation_evidence — mọi write_cache đều ghi identity_status/issues/hash + expose khi cache-hit.
- Verify smoke: 丹霞天然→Đơn Hà Thiên Nhiên `pass`; Thích+sai → `failed` HARD CANONICAL_IDENTITY_MISMATCH (khớp matrix test B); no-Hán → pass fp `''`.

### Phase 3.2b — Write-deny audit `scripts/t166_identity_audit.py`
- CI: schema 4 cột + index · mọi khối write_cache phải có `_t166_post_check_translation` (verify: 4/4 write_blocks đều có post_check) · route admin-write phải `verify_session` · policy hợp lệ · data không có `identity_lock_hash` cô đơn.
- Wire vào `npm run pipeline` khâu `audit:t166` (FAIL exit 1 = dừng; WARN không chặn).
- 1 WARN pre-existing: inline Gemini API key trong app.py (SPEC §20.2 advice — để Admin xử lý riêng).

### Phase 2 — cbeta_translate_worker.py (commit `b89c7bed`)
- Worker KHÔNG đụng translation_cache (SPEC thực tế: viết translation_segments) ⇒ identity ghi vào `validation_report` + hạ `translation_status='needs_review'` khi có issue.

## Tests
- `test_t166_canonical_lock.py` **18/18** PASS
- `test_t166_matrix.py` **23/23** PASS (real DB read-only)
- `test_t165_style_constitution.py` **11/11** PASS
- `scripts/t166_identity_audit.py` PASS (0 FAIL + 1 WARN)
- UAT 3/3 · e2e PASS · guard PASS · py_compile app/canonical_lock/style_constitution/cbeta_worker OK

## Commits
- `4107cca` — Phase 1 core + tests (session trước)
- `0150e66` — Phase 2.5 style_constitution + Phase 3.1 migration
- `b89c7bed` — Phase 2 wire app.py + audit + worker + package.json + Phase 3.2

## Todo còn lại (Phase 4/5)
- Matrix A–J đầy đủ chạy real DB ro (đã có 23/23 trong test suite)
- `npm run pipeline` toàn bộ
- Dashboard regen + taskdone closure + docs

## Revert nhanh
```
git revert --no-edit b89c7bed && git revert --no-edit 0150e66 && git revert --no-edit 4107cca
python -X utf8 scripts/t166_identity_migrate.py --revert
# hoặc restore data/backups/lineage_t166_20260926_080107.db
```