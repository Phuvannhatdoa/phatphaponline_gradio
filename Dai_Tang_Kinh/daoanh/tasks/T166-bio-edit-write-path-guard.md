---
id: T166-bio-edit-write-path-guard
title: "T166 bio-edit write-path guard — wire post_check vào raw INSERT translation_cache @17401"
status: done
priority: medium
module: translation_cache / T166 identity guard
created: 2026-09-27
updated: 2026-09-27
depends_on: T166-build
---

# T166-bio-edit-write-path-guard

## Bối cảnh (phát hiện trong T166 REVIEW reconciliation, 2026-09-27)

REVIEW gốc `docs/Mimo-Flash/T166-phase45-continue-REVIEW.md` P1-6 flag: raw
`INSERT INTO translation_cache` trong route bio-edit **KHÔNG qua**
`_t166_post_check_translation`. Đối chiếu code thật:

- Route: `@app.route('/daoanh/api/admin/person/<person_id>/bio_vi', methods=['POST'])`
  — app.py:17359
- Raw write: app.py:**17401** — `INSERT INTO translation_cache (…, status='edited', …)`
  (`model_id='manual'`) khi chưa có `translation_id`; có nhánh `UPDATE … status='edited'`
  khi có `translation_id` (app.py:17392).
- 4 write path khác ĐÃ wire post_check→write_cache: 6421→6428, 16782→16793,
  17322→17329, 17899→17904. **Riêng route bio_vi này KHÔNG.**

Invariant T166 (§4 cache safety): `LLM → cache write → identity validation` là CẤM;
đúng phải `post_check → write`. Bio-edit là **admin manual** (không phải LLM output)
nên cần quyết định policy trước khi code.

## Quyết định Admin (chốt 2026-09-27)

**Hướng 1 biến thể — "Wire + GHI NHẬN, KHÔNG chặn admin" (RECORD-not-block).**
Admin chốt: build, wire post_check vào 2 route admin manual, ghi identity cols
(`identity_status`/`identity_issues`/`identity_lock_hash`) vào hàng vừa viết (guard
`_has_col` cho pre-migration). KHÔNG chặn save dù post_check `blocked`/`review_required`
— vì verify_session ✓ (nguồn là con người, HITL), chặn = deadlock khi admin sửa chính
canonical name, regress T145, và mâu thuẫn `is_trusted_translation (NULL=pass)`. Identity
metadata trả trong JSON response để UI cảnh báo nhẹ (amber). Audit script THÊM
`_check_raw_writes` đóng blind-spot: quét cả raw INSERT/UPDATE translation_cache
(nội dung), whitelist 2 route admin-manual, yêu cầu post_check cho block còn lại.

## Build đã thực hiện (2026-09-27, commit `2f58ff67c7f17a0ed4949c6ee3290137ebc25f75`)

- **app.py `api_admin_save_person_bio_vi`** + **`api_admin_save_person_dila_vi`**:
  - Gọi `_t166_post_check_translation(conn, p['bio'], bio_vi|vi_merged,
    policy=_t166_identity_lock_policy(conn))` trước mọi INSERT/UPDATE translation_cache.
  - INSERT nhánh (chưa có translation_id): thêm cột identity vào câu SQL khi `_has_col`;
    UPDATE nhánh: cập nhật identity cols.
  - Response thêm `identity_status` + `identity_issues`.
  - Thêm helper `_t166_has_col(conn, table, col)` (mirror style_constitution._has_col).
- **scripts/t166_identity_audit.py**: thêm `ADMIN_MANUAL_RAW_WRITERS` (2 route) +
  `_check_raw_writes()` (quét raw write nội dung — bỏ qua `UPDATE SET status=…`
  invalidate/report), wire vào `main()`. Đóng blind-spot audit khi `_check_app_guard`
  chỉ quét khối có `write_cache`.
- **Verify:** py_compile PASS · `audit:t166` PASS (0 FAIL, 1 WARN key inline pre-existing) ·
  `test:t166` 18/18 · `test:t165` 11/11 · smoke test DB copy 3/3 (INSERT bio_vi + UPDATE
  dila_card ghi đủ 3 identity cols, post_check status=review_required) · guard PASS ·
  `npm run pipeline` chạy tới UAT/compliance PASS, `e2e:runtime` EPERM pre-existing.

## Acceptance

- [x] Quyết định hướng 1 biến thể được Admin chốt
- [x] `npm run audit:t166` PASS (0 FAIL)
- [x] `npm run pipeline` PASS (e2e:runtime EPERM pre-existing được ghi chú) — guard/lint exit 0, smoke DB copy PASS
- [x] Bio-edit không regress: smoke test INSERT bio_vi + UPDATE dila_card ghi identity cols 200-equivalent
- [x] py_compile PASS

## Revert

- `git revert --no-edit 2f58ff67c7f17a0ed4949c6ee3290137ebc25f75` — app.py hunks + audit script + docs
  (commit hunk-granular cacheinfo, chỉ chứa file/hunk của T166-bio-edit-write-path-guard;
  WIP agent khác không nằm trong commit)

## Mục liên quan

- `docs/ROLLBACK.md` — row `<sha_t166_security>` (đang chờ agent sở hữu commit)
- `docs/Mimo-Flash/T166-review-reconciliation.md` — §4.3 / §5 mục 2