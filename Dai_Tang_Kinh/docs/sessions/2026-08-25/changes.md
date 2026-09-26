# Session 2026-08-25 — T37 + T38 Build

## Tasks hoàn thành

### T37 — Pali Place Reference
- **Script:** `daoanh/scripts/t37_seed_pali_place_ref.py`
- **Kết quả:** 15/15 địa danh Ấn Độ cổ đại seeded vào `pali_place_ref`, 0 not_found
- **Route mới:** `GET /daoanh/api/places/<place_id>/pali` (app.py line ~10673)
- **Response:** `{ok, place_id, refs[], total}` — refs có `sc_url_vi` (SuttaCentral bản Thích Minh Châu)

### T38 — Toh-CBETA Crossref
- **Script:** `daoanh/scripts/t38_seed_toh_crossref.py`
- **Kết quả:** 10 rows seeded (5 confirmed needs_review=0, 5 cần verify needs_review=1)
- **Route mới:** `GET /daoanh/api/cbeta/<sigla>/toh` (app.py line ~10720)
- **Response:** `{ok, sigla, toh_refs[], total}` — chỉ trả rows needs_review=0

## Files thay đổi

| File | Thay đổi |
|---|---|
| `daoanh/app.py` | +90 lines: 2 routes mới (pali, toh) |
| `daoanh/tasks/T37-pali-place-ref.md` | status: done, acceptance criteria ticked, completion log |
| `daoanh/tasks/T38-toh-cbeta-crossref.md` | status: done, acceptance criteria ticked, completion log |
| `daoanh/docs/tasktodo.md` | T37/T38 done, Done count 19→21, Pending 12→10 |
| `daoanh/data/progress_data.json` | rebuilt (scripts/build_progress_data.py) |
| `data/lineage.db` | +2 tables: pali_place_ref (15 rows), toh_cbeta_crossref (10 rows) |

## Ghi chú

- DB `data/lineage.db` là binary — không commit vào git (theo convention hiện tại)
- Cần server restart để 2 routes mới hoạt động (app.py đang chạy từ version cũ)
- T38 badge UI (tab Đại Tạng) chưa wire — cần server live để test
- Rows needs_review=1 (Toh127, 556, 62, 380, 479) KHÔNG xuất hiện trong API, chờ admin verify

## Revert

```bash
git revert HEAD  # nếu muốn rollback commit này
```
