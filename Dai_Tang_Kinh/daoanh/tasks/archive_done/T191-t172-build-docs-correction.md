---
id: T191-t172-build-docs-correction
title: "T191 — T172 build-docs correction (docs-only 0 code/0 DB): line refs drift + số liệu 一行 4-person + minor L3"
module: Editorial / Person Identity
priority: high
status: done
owner: claudecode
depends_on: [T172-hanviet-charwise-debug, T171-person-name-standard]
created: 2026-09-28
updated: 2026-09-28
done_at: "2026-09-28 (docs-only; guard/test/pipeline PASS trừ e2e:runtime EPERM pre-existing; commit 2-pass hash-fill)"
plan_approved_at: "2026-09-28 (Admin: phê chuẩn đề xuất — tạo T191 cho kế hoạch chi tiết đã thảo luận; update /docs + .md, dashboard, revert tiện lợi)"
done_when: |
  L1: SPEC + pointer — line refs sửa đúng app.py: `_han_viet()`=1849 · `HAN_VIET_CHAR`=1294 ·
      dual-write endpoints 13926/18308 (trước ghi 1822/1267/13114/17523 — drift).
  L2: `一行` search substring (LIKE) = 4 person distinct (A000008/A010168/A016240/A023828); exact name_zh='一行'=2.
      Sửa đồng bộ: T172 pointer addendum · T171 SPEC §14.3 + test §14.6 #2 · T171 pointer bullet.
  L3: SPEC §1 sidecar "12 cột dữ liệu + PK person_id" (13 field) · §2 path bulk_transliterate.py = root daoanh/ ·
      §3 định nghĩa is_transliteration · pointer banner/refs.
  Docs: banner [T191] ở SPEC + pointer; task + session + tasktodo + ROLLBACK + dashboard regen.
  Verify: DB read-only (一行 LIKE→4 ids · exact→2 · 大慧禅师 0) · npm run guard/test/pipeline.
  Revert: git revert --no-edit 7e2b27b3237364c8908654d716e8d96ec7ec4a76 (docs-only, 0 DB).
---

# T191-t172-build-docs-correction — T172 build-docs correction (line refs drift + số liệu 一行)

## Bối cảnh

Admin yêu cầu check 2 file `docs/Mimo-Flash/T172-hanviet-charwise-debug-SPEC.md` + `T172-hanviet-charwise-debug.md`
(pointer) "xác nhận vấn đề sau đúng logic chưa" (chuỗi vấn đề bị cắt — thực hiện audit chủ động như T189/T190).
Audit read-only đối chiếu DB `data/lineage.db` + `app.py` xác nhận **đa số claim đúng**, đồng thời phát hiện
**1 lệch số liệu + 1 nhóm line-refs drift + minor** → sửa docs tại chỗ:

- **L2 (lệch số liệu, ảnh hưởng T171+T172):** docs ghi search `一行` = **2 person** (A000008+A010168). DB thật
  (`name_zh LIKE %一行%`) = **4 ids**: A000008 · A010168 · **A016240 (`一行智嚴`)** · **A023828 (`釋一行`)**.
  Chỉ exact `name_zh='一行'` = 2. Search là substring (§4) → acceptance T171 §14.3/§14.6 + 2 pointer (T171+T172)
  sẽ FAIL nếu giữ "2". Đồng bộ sửa tất cả.
- **L1 (line refs drift +27 / -812):** `_han_viet()` = app.py **1849** (SPEC ghi 1822) · `HAN_VIET_CHAR` = app.py
  **1294** (SPEC §3 ghi export 1267) · dual-write endpoints = **13926** (`namevi_map_update`) / **18308**
  (`POST person/<id>/name_vi`) (pointer T172 ghi 13114/17523). Build theo refs cũ sẽ nhầm chỗ / hết đời.
- **L3 (minor):** SPEC §1 "sidecar 12 cột" nhưng liệt kê 13 (gồm PK `person_id`) → "12 cột dữ liệu + PK";
  §2 ghi `bulk_transliterate.py` không path — file ở **root `daoanh/`** (không trong `scripts/`);
  §3 cột `is_transliteration` chưa định nghĩa điều kiện set.

## Thay đổi (docs-only)

| # | File | Sửa |
|---|------|-----|
| L1 | T172 SPEC §2/§3 · T172 pointer | `_han_viet()`→app.py:1849 · `HAN_VIET_CHAR`→app.py:1294 · dual-write→13926/18308 |
| L2 | T172 pointer addendum · X-T171 SPEC §14.3 + §14.6#2 · X-T171 pointer | `一行` substring → **4 ids** (A000008/A010168/A016240/A023828) · exact = 2 · KHÔNG gộp giữ nguyên |
| L3 | T172 SPEC §1/§2/§3 | sidecar 13 field (12 cột dữ liệu + PK) · path `bulk_transliterate.py`=root · định nghĩa `is_transliteration` (=1 khi unknown rỗng ∧ match {exact,normalized}) |
| Docs | SPEC banner `[2026-09-28 · T191]` + pointer banner · T171 pointer/SPEC `[T191]` note · `tasks/T191-...md` · session | log + commit 2-pass hash-fill |

## Việc đã làm

1. **T172 SPEC**: banner `[T191]` mới (L1/L2/L3 + số liệu DB) → §1 sidecar 13 field → §2 `bulk_transliterate.py`
   = root daoanh + `_han_viet()`=1849 → §3 export=1294 + `is_transliteration` định nghĩa.
2. **T172 pointer**: banner `[T191]` → addendum search `一行` = 4 + dual-write 13926/18308.
3. **X-T171 SPEC**: §14.3 acceptance → 4 ids + exact=2 · test §14.6 #2 → 4 ids (+exact 2).
4. **X-T171 pointer**: bullet search → 4 ids.
5. **Docs**: task `tasks/T191-...md` · session `docs/sessions/2026-09-28_t191-t172-build-docs-correction.md` ·
   tasktodo top entry · ROLLBACK row.
6. **Dashboard**: regen `scripts/build_progress_data.py` → `data/progress_data.json`.

> ⚠️ Tình huống hunk-granular (giống T189/T190): agent song song đã **rename T171 → X-T171** (SPEC + pointer) trên
> worktree, chưa commit; T172 files vẫn bare. Commit T191 đưa **nguyên bản worktree LF-normalized** tại path HEAD:
> X-T171-content → `docs/Mimo-Flash/T171-person-name-standard-SPEC.md`/`.md` (bare, đã track) — KHÔNG đổi tên file.
> Agent song song giữ nguyên rename X- của họ; không xung đột hunk (phần họ edit không trùng phần T191).

## Verify

- DB read-only: `name_zh LIKE '%一行%'` = 4 ids (A000008/A010168/A016240/A023828) · `name_zh='一行'` = 2 ·
  `大慧禅师` = 0 · A000044 `Tô Phược La` = 1 · `hanviet_fallback` 8.650 · `custom_hanviet_override` 3.968 ·
  people 48.673 · `name_vi_map` 4.869 dila_id NULL · 51 dup.
- app.py grep: `def _han_viet`=1849 · `HAN_VIET_CHAR = {`=1294 · `def admin_namevi_map_update`=13926 ·
  route `POST person/<id>/name_vi`=18308.
- `npm run guard` PASS · `npm run test` PASS · `npm run pipeline` toàn PASS trừ `e2e:runtime` EPERM pre-existing.
- Docs-only — không chạm code/DB; tất cả task vẫn giữ trạng thái cũ (T172 code chưa build).

## Revert

- `git revert --no-edit 7e2b27b3237364c8908654d716e8d96ec7ec4a76` — docs-only, 0 DB. Quay về HEAD pre-T191.

## Còn lại (không thuộc T191)

- T172 code build (sidecar + migration + API + UI) = task T172: SPEC vẫn `ready-for-dev`.
- Agent song song: rename T171→X-T171 của họ chưa commit; để họ quyết (T191 không đụng rename).