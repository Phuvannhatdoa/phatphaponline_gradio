---
belongs_to: T166
directive: "[T166-REVIEW-RECONCILIATION]"
title: "T166 REVIEW reconciliation — delta đối chiếu 5 P0 + 6 P1 với trạng thái THẬT (docs-only)"
status: done
created: 2026-09-27
updated: 2026-09-27
designed_by: lead-ai-engineer
handoff_to: admin
supersedes: "docs/Mimo-Flash/T166-phase45-continue-REVIEW.md"
---

# T166 REVIEW reconciliation — đóng REVIEW 07:30 09-26 bằng delta đối chiếu trạng thái thật

> **Nguyên tắc:** File `T166-phase45-continue-REVIEW.md` (rev.3, snapshot **07:30 09-26 — TRƯỚC build**) được **GIỮ NGUYÊN VĂN BẢN** theo quyết định Admin. File này là SSOT delta: đối chiếu từng claim với repo/DB **thật**, ghi rõ RESOLVED/CORRECTED/open, và gỡ 3 lỗi nội tại của chính REVIEW.
> **0 code / 0 DB trong session này.** Commit: docs-only.

## 1. Verdict tổng

| Hạng mục | Kết luận |
|---|---|
| REVIEW gốc | Snapshot **07:30 09-26, trước build** — đa số P0/P1 đã bị phiên build sau đó giải quyết |
| T166-build trạng thái thật | **✅ DONE** — Phase 1→5, tasktodo line 17, pytest 117/117, matrix 23/23, audit PASS |
| Claim còn giá trị THẬT | **P0-4** (delete không auth — đang giữ placeholder `<sha_t166_security>`) + **P1-6 raw INSERT @17401** |
| Lỗi nội tại REVIEW | 3 — (1) SHA bịa `2710912`/`1810927`, (2) "admin/app.py 101 hit" (file không tồn tại), (3) lệnh "BỎ audit:t166" |

## 2. Bảng delta P0-1 → P1-6

| # | Claim REVIEW gốc | Trạng thái THẬT (2026-09-27) | Verdict |
|---|---|---|---|
| **P0-1** | `4107cca`/`0150e66`/`b89c7bed` NOT FOUND — work chưa commit | **ĐÃ tồn tại**: `4107cca` Phase 1 (canonical_lock core + 41 tests) · `0150e66` Phase 2.5+3.1 (fingerprint + identity migration) · `b89c7bed` Phase 2+3.2 (post_check + wire 4 paths + audit script). `canonical_lock.py`/`scripts/t166_identity_audit.py` ĐÃ tracked. | **RESOLVED** — SHAs directive hóa ra ĐÚNG; không commit thêm. |
| **P0-2** | `tasks/T166-…` không tồn tại; thật = `docs/Mimo-Flash/…` | Đúng — `docs/Mimo-Flash/X-T166-canonical-identity-guard.md` + SPEC tồn tại. | ✅ Giữ nguyên. |
| **P0-3** | `scripts/t166_identity_audit.py` = 0 · `npm run audit:t166` không có | **ĐÃ build**: script tồn tại (tracked), `"audit:t166"` trong `package.json:24` + wire vào `pipeline` (line 30). | **RESOLVED** — và lệnh "BỎ audit:t166" trong REVIEW §7 là SAI, gỡ bỏ (xem §4.3). |
| **P0-4** | `admin_namevi_map_delete` (app.py:13146) không `verify_session` — STOP-4 mở | **VẪN ĐÚNG trên HEAD**: `git show HEAD:…app.py` delete route = 0 auth. Fix đã có trong **working tree** (app.py:13152–13155) nhưng **CHƯA COMMIT** — đang giữ row `<sha_t166_security>` (docs/ROLLBACK.md:12, agent sở hữu khác). | ⚠️ **MỞ THẬT** — chờ agent sở hữu commit `<sha_t166_security>`; validate 403/403/200. |
| **P0-5** | Nhãn Phase 2.5/3.1/3.2 không có trong SPEC 0–5 | Đúng lúc đó; nhưng commit build thật dùng chính các nhãn này (0150e66 "Phase 2.5+3.1", b89c7bed "Phase 2+3.2"). | ✅ Giữ nguyên (ghi chú: build đã dùng nhãn). |
| **P1-1** | E2E không dấu `Quy+Son+Linh+Huu` sẽ FAIL oan (LIKE thô) | Đúng — `api_global_search` LIKE thô (app.py:2157), không `normalize_text`. | ✅ Giữ nguyên — pre-existing gap, không tính FAIL T166. |
| **P1-2** | Worker có thể CHƯA wire guard | **ĐÃ wire**: `scripts/cbeta_translate_worker.py:487-493` gọi `post_check_translation` → batch có identity guard. | **RESOLVED**. |
| **P1-3** | CASE 4/5 = BUG-026 residual | Đúng — `name_vi_map` còn row A001744, A010291 auto sai; thuộc BUG-026, không sửa trong T166. | ✅ Giữ nguyên. |
| **P1-4** | Seed LOCK theo `person_id`, không theo Han-string | Đúng (靈祐/慧辯 mỗi tên 5 người). | ✅ Giữ nguyên — áp dụng trong test matrix. |
| **P1-5** | "T177 = 0 hit, label bịa" · Dynamic Filter = T167/T165 Phase 8 | **T177 ĐÃ LÀ TASK THẬT** (62b593b absorb-directive-v2; tasktodo line 15 ✅ DONE). | **RESOLVED/CORRECTED** — T177 tồn tại; đừng quy T166 sang đó. |
| **P1-6** | §1 thiếu admin/app.py mirror (101 hit) + site list 4× write_cache + raw INSERT ~17350 | **CORRECTED (admin/app.py)**: `admin/app.py` **KHÔNG TỒN TẠI** (Test-Path=False; T177/T168 xác nhận — stack thật `app.py`). **ĐÚNG (sites)**: 4 cặp post_check→write_cache thật (6421→6428, 16782→16793, 17322→17329, 17899→17904). **ĐÚNG (raw INSERT)**: bio-edit route `/daoanh/api/admin/person/<id>/bio_vi` vẫn INSERT translation_cache (app.py:17401, `status='edited'`) KHÔNG post_check. | ⚠️ Raw INSERT @17401 → **task riêng** `T166-bio-edit-write-path-guard`. |

## 3. DONE checklist (ái dụng từ REVIEW §done)

| Mục | Trạng thái |
|---|---|
| Matrix A–J | ✅ PASS — `tests/test_t166_matrix.py` 23/23, real DB read-only |
| Real regression (seed person_id) | ✅ PASS — pytest 117/117 |
| canonical hard guard | ✅ PASS — canonical_lock 18/18 |
| post-check | ✅ PASS — wire 4 translate paths |
| cache safety (gồm site 17350 + worker) | ⚠️ **PHẦN DỞ** — worker ✓, 4 site ✓, **raw INSERT @17401 chưa** → task riêng |
| security (update + delete) | ⚠️ update ✓ (b89c7bed) · **delete chưa commit** (working tree, `<sha_t166_security>`) |
| t166_identity_audit | ✅ PASS (script tồn tại, pipeline chạy, 0 FAIL) |
| npm run guard / pipeline | ✅ PASS (e2e:runtime EPERM pre-existing) |
| live/e2e | ✅ biến thể dấu; không dấu = ghi nhận riêng (VPS-only) |
| dashboard regenerated | ✅ eef629f |
| commit SHA thật | ✅ 4107cca / 0150e66 / b89c7bed + b9a8141 + eef629f |
| rollback path thật | ✅ docs/ROLLBACK.md row 19/20/21 |

## 4. Gỡ 3 lỗi nội tại của REVIEW gốc (không sửa file gốc — ghi đây làm SSOT)

### 4.1 SHA Bước-0 bịa `2710912` + `1810927`
REVIEW §3 PROMPT CHỐT ghi "Bước 0 đã DONE — 2710912 (feat) + 1810927 (docs)". **Cả 2 KHÔNG tồn tại** (`git cat-file -t` = fatal). Bước 0 thật = **`4107cca`** (Phase 1) — dùng SHA thật, không dùng `2710912`/`1810927`.

### 4.2 "admin/app.py mirror đã wire (101 hit)" — SAI
`admin/app.py` **không tồn tại**. T177 (docs/Mimo-Flash/T177-dynamic-filter-absorb-directive-v2.md) đã ghi "KHÔNG tồn tại — T168 xác nhận; stack thật app.py 21.232 dòng". **Bỏ mọi ref mirror admin.**

### 4.3 Lệnh "BỎ npm run audit:t166" — SAI
`scripts/t166_identity_audit.py` ĐÃ tồn tại, `npm run audit:t166` ĐÃ trong pipeline. **GIỮ**, không bỏ. Bỏ đi = mất 1 check CI thật.

## 5. Còn mở (2 mục — KHÔNG code trong session này)

1. **`admin_namevi_map_delete` auth** — fix trong working tree nhưng chưa commit. Việc thuộc agent sở hữu row `<sha_t166_security>` (docs/ROLLBACK.md:12). Khi commit xong: verify 403 (no token) / 403 (invalid) / 200 (valid session) cả 2 endpoint update + delete.
2. **Raw INSERT translation_cache @17401** (bio-edit route) — chưa có `_t166_post_check_translation` trước write. Quyết định: wire guard HOẶC policy miễn trừ admin-manual-edit. → **Task riêng: `tasks/T166-bio-edit-write-path-guard.md`** (pending).

## 6. Revert

Docs-only session — `git revert --no-edit <sha_reconcile>` (chỉ file này + task + session + tasktodo, 0 DB/0 code).