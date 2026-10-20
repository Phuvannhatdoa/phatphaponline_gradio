# Session 2026-09-28 — T191-t172-build-docs-correction

**Agent:** claudecode · **Trạng thái:** DONE (docs-only, 0 code/0 DB) · **HEAD tại thời điểm build:** `ad5d250` (T190 đã commit; agent song song đã rename T171 → X-T171 trên worktree, chưa commit)

## Mục tiêu

Admin: "check và xác nhận vấn đề sau đúng logic chưa" trên 2 file
`docs/Mimo-Flash/T172-hanviet-charwise-debug-SPEC.md` + `T172-hanviet-charwise-debug.md` (chuỗi vấn đề bị cắt —
thực hiện audit chủ động như T189/T190). Sau audit → phê chuẩn: "phê chuẩn đề xuất này… tạo task mới Txx cho kế
hoạch chi tiết, update /docs + các .md tương ứng, cập nhật Dashboard".

## Audit (read-only, DB thật)

Claims T172 khớp 100%: A000006 = **17 âm** (`nhất sơn quốc sư nhất ninh nhất sơn nhất ninh diệu từ hoằng tế nhất sơn ninh`) ·
A000008 `一行`→`Nhất Hàng` · A000026 `了貞`→`Liễu Trinh` · A000044 `蘇嚩羅`→`Tô Phược La` (1) · A000047 `于頔`→`Vu 頔` ·
"A000006 dính '王' sai vai" cần bịt · `大慧禅师` = 0 · `hanviet_fallback` 8.650 · `custom_hanviet_override` 3.968 ·
map bẩn 4.869 NULL · 51 dup · people 48.673.

Phát hiện 3 vấn đề → **T191** (docs-only): **L2** search `一行` substring = **4 ids** (A000008/A010168/A016240 `一行智嚴`/
A023828 `釋一行`), docs + T171 acceptance ghi 2 → FAIL khi build · **L1** line refs drift `_han_viet`=1849 (ghi 1822),
`HAN_VIET_CHAR`=1294 (ghi 1267), dual-write 13926/18308 (pointer ghi 13114/17523) · **L3** minor (13 field sidecar,
path `bulk_transliterate.py`=root daoanh, thiếu định nghĩa `is_transliteration`).

## Thay đổi

1. **SPEC** `T172-hanviet-charwise-debug-SPEC.md`: banner `[2026-09-28 · T191]` → §1 sidecar "12 cột dữ liệu + PK"
   → §2 `_han_viet()`=app.py:1849 + `bulk_transliterate.py` path root → §3 export=app.py:1294 + `is_transliteration`
   định nghĩa (=1 khi unknown rỗng ∧ match {exact,normalized}).
2. **Pointer** `T172-hanviet-charwise-debug.md`: banner `[T191]` → addendum `一行`=4 (exact=2) + dual-write 13926/18308.
3. **X-T171 SPEC** (agent đã rename, worktree): §14.3 acceptance → 4 ids + exact 2 · §14.6 #2 → 4 ids.
4. **X-T171 pointer**: bullet search `一行` → 4 ids.
5. **Docs**: task `tasks/T191-...md` · session này · tasktodo top entry · ROLLBACK row.
6. **Dashboard**: regen `scripts/build_progress_data.py` → `data/progress_data.json`.

## Verify

- DB read-only: `一行` LIKE → 4 ids · exact → 2 · `大慧禅师` 0 · A000044 1 · fallback 8.650 · override 3.968.
- app.py: `def _han_viet`=1849 · `HAN_VIET_CHAR = {`=1294 · `def admin_namevi_map_update`=13926 ·
  route name_vi=18308.
- `npm run guard` PASS · `npm run test` PASS · `npm run pipeline` PASS trừ `e2e:runtime` EPERM pre-existing.
- Docs-only — code/DB không đổi; T172 vẫn `ready-for-dev`.

## Revert

- `git revert --no-edit 7e2b27b3237364c8908654d716e8d96ec7ec4a76` — docs-only, 0 DB.

## Còn lại

- T172 code build (sidecar + migration + API + UI) = task T172.
- Agent song song: rename T171→X-T171 chưa commit — để họ quyết (T191 không đụng rename; commit T191 đưa
  nguyên bản X-T171 worktree LF-normalized về path bare HEAD).