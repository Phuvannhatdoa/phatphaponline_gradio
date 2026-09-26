# Session: Search DB first + name_vi_norm

**Date:** 2026-05-23

## Mô tả task

Search on placevn.html: DB first (places_pending), diacritics-free via name_vi_norm, lexicon fallback.

1. Add `name_vi_norm TEXT` column to `places_pending` — diacritics-free, lowercase name_vi
2. Populate on save (manual + auto_save endpoints)
3. Search endpoint 3-phase: DB search -> word fallback -> Hán fallback
4. Fix `normalize_text()` — đ->d handling

## Vấn đề

1. `normalize_text()` không xử lý đ (U+0111) — Unicode NFD không decompose nó. Fix: thay thế bằng tay
2. Migration OFFSET skip rows vì result set thay đổi — fix cursor-based (last_rowid)
3. Han_fallback false positive khi match Hán tự đơn — fix yêu cầu >=3 từ

## Files changed

| File | Status | Description |
|------|--------|-------------|
| `app.py` (line 27) | MODIFIED | normalize_text() đ->d |
| `app.py` (lines 1554-1588) | MODIFIED | Save endpoints update name_vi_norm |
| `app.py` (lines 1625-1710) | REWRITTEN | Search endpoint 3-phase |
| `scripts/migrate_name_vi_norm.py` | NEW | Migration for 118,295 rows |
| `docs/progress.md` | UPDATED | Phase 2c status |

## Test results

- "Khoat Tat Da Quoc" => 1 result (mode=db) — diacritics-free works
- "Hung Do Kho Thap Son" (cate=mountain) => 2 results (mode=db)
- "Te Chau" => multiple results (mode=db)
- "Thieu Lam Tu" => 0 results (no place has this name_vi in DB)
- Not found => 0 results (mode=none)
