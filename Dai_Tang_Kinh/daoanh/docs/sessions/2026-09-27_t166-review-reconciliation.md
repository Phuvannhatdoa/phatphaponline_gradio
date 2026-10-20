# Session — 2026-09-27 T166 REVIEW reconciliation (docs-only)

## Verdict

REVIEW gốc `docs/Mimo-Flash/T166-phase45-continue-REVIEW.md` (rev.3, snapshot 07:30
09-26 = TRƯỚC build) → **đóng bằng delta đối chiếu, GIỮ NGUYÊN VĂN BẢN GỐC** theo quyết
định Admin ("giữ văn gốc"). Build T166 đã xong trước đó; file reconcile ghi RESOLVED/
CORRECTED/open cho từng claim, gỡ 3 lỗi nội tại của REVIEW, và chuyển raw INSERT @17401
sang task riêng (Admin: "ghi task riêng").

## Thay đổi

| # | File | Loại |
|---|---|---|
| 1 | `docs/Mimo-Flash/T166-review-reconciliation.md` | MỚI — SSOT delta P0-1→P1-6 + 3 lỗi nội tại + còn mở |
| 2 | `tasks/T166-bio-edit-write-path-guard.md` | MỚI — task pending: wire post_check @17401 HOẶC policy miễn trừ |
| 3 | `docs/sessions/2026-09-27_t166-review-reconciliation.md` | MỚI — session này |
| 4 | `docs/tasktodo.md` | +1 dòng pending `T166-bio-edit-write-path-guard` |

0 code / 0 DB.

## Key facts đối chiếu (đã verify repo thật)

- `4107cca`/`0150e66`/`b89c7bed` **tồn tại** (REVIEW gốc tưởng NOT FOUND) → P0-1 RESOLVED.
- `scripts/t166_identity_audit.py` + `npm run audit:t166` **tồn tại** (P0-3 RESOLVED, lệnh
  "BỎ audit:t166" = SAI, gỡ).
- `admin_namevi_map_delete` **trên HEAD vẫn 0 auth** (P0-4 MỞ THẬT; fix trong working tree
  nhưng chưa commit — row `<sha_t166_security>` thuộc agent khác).
- `admin/app.py` **KHÔNG tồn tại** (P1-6 "101 hit" = SAI, CORRECTED).
- Worker **đã wire** (p1-2 RESOLVED); T177 **là task thật** (P1-5 RESOLVED).
- Raw INSERT @17401 (bio-edit) **vẫn chưa post_check** → task riêng.

## 3 lỗi nội tại REVIEW gốc

1. SHA bịa `2710912`/`1810927` → Bước 0 thật = `4107cca`.
2. "admin/app.py mirror 101 hit" → file không tồn tại, bỏ ref.
3. Lệnh "BỎ npm run audit:t166" → script có thật, GIỮ.

## Còn mở (không code session này)

- `<sha_t166_security>` — commit auth delete endpoint, chờ agent sở hữu.
- `T166-bio-edit-write-path-guard` (pending) — chờ Admin chốt hướng wire/policy.

## Verify chưa chạy

Guard/pipeline sẽ chạy ngay trước commit (0 code nên không regress).

## Revert

`git revert --no-edit <sha_reconcile>` — docs-only, 0 DB/0 code.

---

# PHẦN 2 — BUILD T166-bio-edit-write-path-guard (cùng session, 2026-09-27)

## Admin phê duyệt

"Đồng ý build, hãy lưu logs, gitcommit, cập nhật các thông tin của các task mới vào
các .md files tương ứng. Bảo đảm mọi bugs khi fix đều có thể commit back về version
trước 1 cách thuận tiện. Gọi pipip khi done." + chốt hướng **Hướng 1 biến thể =
RECORD-not-block** (wire + GHI NHẬN, KHÔNG chặn admin).

## Giải pháp đã build

- Quyết định kỹ thuật: gọi `_t166_post_check_translation(conn, source, vi_merged,
  policy=_t166_identity_lock_policy(conn))` TRƯỚC mọi raw INSERT/UPDATE `translation_cache`
  trong `api_admin_save_person_bio_vi` + `api_admin_save_person_dila_vi`; ghi 3 cột
  identity (`identity_status`/`identity_issues`/`identity_lock_hash`, guard
  `_t166_has_col` cho pre-migration) vào hàng vừa viết; response thêm `identity_status`+
  `identity_issues`. **Lý do không chặn:** verify_session ✓ (nguồn con người, HITL),
  chặn = deadlock khi admin sửa chính canonical name, regress T145, mâu thuẫn
  `is_trusted_translation (NULL=pass)`.
- Audit: `scripts/t166_identity_audit.py` thêm `_check_raw_writes()` +
  `ADMIN_MANUAL_RAW_WRITERS` — **đóng blind-spot** (`_check_app_guard` trước chỉ quét
  khối chứa `write_cache`, bỏ sót raw INSERT/UPDATE). `UPDATE translation_cache
  SET status=...` (invalidate/report) không tính — về lại đường write_cache có guard.
- Line refs đã dịch chuyển trong file làm việc (bio_vi route ~17623, helper chèn trước
  route; dila_vi ~17944). Ghi chú `wip_before.patch` snapshot 498 dòng lưu trước khi sửa.

## File thay đổi (session build)

| # | File | Nội dung |
|---|---|---|
| 1 | `app.py` | helper `_t166_has_col` + 2 route wired identity (chỉ hunk T166; WIP agent khác giữ nguyên) |
| 2 | `scripts/t166_identity_audit.py` | `_check_raw_writes` + `ADMIN_MANUAL_RAW_WRITERS` + wire main() |
| 3 | `tasks/T166-bio-edit-write-path-guard.md` | pending → done + quyết định + build log |
| 4 | `docs/tasktodo.md` | row T166-bio-edit-write-path-guard ⏳ PENDING → ✅ DONE |
| 5 | `docs/ROLLBACK.md` | +1 row `2f58ff67c7f17a0ed4949c6ee3290137ebc25f75` (giữ row `1be7ed7`/T180 của agent khác) |
| 6 | `docs/sessions/2026-09-27_t166-review-reconciliation.md` | session này (PHẦN 2) |

## Verify (PASS)

- `py_compile app.py scripts/t166_identity_audit.py` — PASS
- `npm run audit:t166` — **PASS (0 FAIL)** + 1 WARN inline Gemini key pre-existing
  (không chặn pipeline)
- `npm run test:t166` — **18/18 PASS** · `npm run test:t165` — **11/11 PASS**
- Smoke DB copy `smoke_t166_routes.py` — **3/3 PASS** (INSERT bio_vi + UPDATE dila_card
  ghi đủ 3 identity cols; post_check status = `review_required`, issue 1 → response có
  identity metadata; DB copy đã xoá)
- `npm run guard` — PASS · `npm run lint` — exit 0 (tự động TLS-template: chỉ HTML/JS)
- `npm run pipeline` — UAT 3/3 PASS + design compliance PASS; `e2e:runtime` **EPERM
  pre-existing** (dev server giữ `test-results\.last-run.json`), không chặn

## Commit

Hunk-granular (cacheinfo) do app.py + tasktodo.md + ROLLBACK.md shared-dirty với WIP
agent khác. Blob app.py = HEAD + CHỈ hunk T166 (loại WIP `t50-progress` + `admin_namevi_map_delete`).
Commit `2f58ff67c7f17a0ed4949c6ee3290137ebc25f75` sau khi build.

## Revert (bảo đảm "commit back thuận tiện")

`git revert --no-edit 2f58ff67c7f17a0ed4949c6ee3290137ebc25f75` — khôi phục 2 route về raw INSERT/UPDATE
không identity + audit trước. WIP agent khác không bị đụng (nằm ngoài blob).