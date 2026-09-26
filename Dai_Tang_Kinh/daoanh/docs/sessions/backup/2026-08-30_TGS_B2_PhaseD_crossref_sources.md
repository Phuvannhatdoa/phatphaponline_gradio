# Session: TGS Build 2 — Phase D (Cross-Ref Sources vào Authority Matrix)

**Date:** 2026-08-30
**Branch/Task:** TGS Build 2 Phase D (queue: SAT → Kanripo → SuttaCentral/VRI → 84000 Toh → CHGIS/TGAZ)
**Status:** DONE

## Objective
Đăng ký các nguồn cross-reference còn thiếu vào master authority matrix
(`source_authority` + `data_sources`) theo Build 2 plan, với `implemented=0`
(không coi nguồn là tích hợp cho tới khi có pipeline + data thật).

## Script mới
`scripts/build2_register_crossref_sources.py` — additive / idempotent / reversible:

1. **data_sources** (thêm +7 rows, id 7→13):
   - SAT (7), CHGIS (8), FoJin (9), Kanripo (10), SuttaCentral (11), 84000 (12), TGAZ (13)
   - Mỗi dòng có: source_type (crossref/gis), authority_scope, license_note, active=1.
2. **source_authority** (thêm +4 rows, `implemented=0`):
   - Kanripo=70 (order 9), TGAZ=55 (order 10), SuttaCentral=50 (order 11), 84000=45 (order 12)
3. **Đồng bộ source_id** từ `data_sources` (giống T68) cho mọi matrix-row đang NULL.

## Reversibility (đã verify round-trip)
- `--dry-run`: in chính xác những gì sẽ làm.
- `--undo`: xóa đúng các dòng build này thêm; reset `source_id=NULL` cho
  SAT/CHGIS/FoJin (vốn NULL trước Phase D). Matrix trả về nguyên trạng 9 dòng.
- `--apply` lại: khôi phục đầy đủ 13 nguồn. → **Thử nghiệm revert/re-apply PASS.**

## Final Matrix (13 nguồn)
| source_code | source_id | score | order | implemented |
|---|---|---|---|---|
| DILA | 1 | 100 | 1 | 1 |
| CBETA | 3 | 80 | 2 | 1 |
| SAT | 7 | 75 | 3 | 0 |
| Kanripo | 10 | 70 | 9 | 0 |
| MARCUS | 4 | 60 | 4 | 1 |
| CHGIS | 8 | 58 | 5 | 0 |
| ZQLOCAL | 5 | 50 | 0 | 1 |
| SuttaCentral | 11 | 50 | 11 | 0 |
| BDRC | 2 | 40 | 6 | 0 |
| FoJin | 9 | 40 | 7 | 0 |
| 84000 | 12 | 45 | 12 | 0 |
| TGAZ | 13 | 55 | 10 | 0 |
| Wikidata | 6 | 25 | 8 | 0 |

## Verification
- `python -m py_compile scripts/build2_register_crossref_sources.py` → OK (sau 3 bug fix:
  `undo` undefined trong `do_apply` — đã gỡ; `if not dry_run and not undo` → `if not dry_run`).
- Idempotent: chạy lại → toàn bộ "[ok] đã có ... — bỏ qua".
- `python -m py_compile app.py` → OK (Phase C endpoint không bị ảnh hưởng).
- Flask test client `GET /daoanh/api/places/PL000000008975/claims` → status 200,
  claims_count 206, first claim DILA / COORDINATE / auth_score 100.
- Pipeline: lint=0 (ESM env false-positive), test=0, e2e=0 (All pages passed).

## Files Changed
- `scripts/build2_register_crossref_sources.py` (mới)
- `docs/sessions/2026-08-30_TGS_B2_PhaseD_crossref_sources.md` (log này)
- `docs/tasktodo.md`, `docs/TGS-integration-masterplan.md` (ghi nhận Phase D)

## Next Steps
- Phase E: refresh `docs/build1_inventory.md` + `docs/trusted-sources.md` (15→20 sources),
  thêm session logs; cập nhật trạng thái T73/T74.
- Sau Phase D: các nguồn cross-ref vẫn `implemented=0` — khi có pipeline + data thật
  (T34 GĐ B/C/D, T35, T21/CHGIS) mới set `implemented=1`.