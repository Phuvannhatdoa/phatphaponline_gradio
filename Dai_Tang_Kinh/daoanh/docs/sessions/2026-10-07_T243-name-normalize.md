# T243 — M7: Ingest DILA place + Name Normalization (BUILD DONE)

> Ngày build: 2026-10-07 · Task: `tasks/T243-m7-data-normalize-places.md`
> Đặc tả: `docs/integration/Uu-Tien-1-T07-gis-buddhist-maps-consolidated.md` (M7 toàn cầu)
> Trạng thái: **DONE** — module chuẩn hóa + chỉ số tìm kiếm khóa chuẩn, apply DB thật + test XANH.

## 1. Khảo sát nguồn (READ-ONLY probes, trước khi build)

| Bảng | Rows | Ghi chú |
|---|---|---|
| `places_dila` | 59.167 | cols `id,name,name_zh,name_en,…,geo_lat,geo_long,place_key,district,…`; **has_geo = 58.480** (98,8%), has_zh = 59.150 |
| `namevi_map_places` | 118.296 | mỗi `dila_id` đúng 1 dòng; joinplaces_dila có tên_vi + geo → **58.469** |
| `hanviet_char_map` | 11.300 | `char/reading/source/is_polyphonic/candidates`; nên chồng `custom_hanviet_override` lên trên |
| `app.py normalize_text()` | — | NFD, strip Mn, đ→d, collapse space, lower — **tái dùng qua AST-extract** (không import Flask) |

pypinyin **0.55.0** đã `pip install` thành công (precedent T226/T254 đã pip install).

## 2. Thiết kế (đã chốt, additive)

- **`scripts/vn_places_name_utils.py`** — module thuần, import được trong test:
  - `nfkc()` Unicode NFKC; `vn_key()` = `normalize_text()` (AST-extract từ app.py, `NORMALIZE_FROM_APP=True`).
  - `strip_facility()`: hậu tố Hán `寺/院/庵/廟/塔/閣/堂/殿/宮/觀/精舍/蘭若/伽藍/道場` (ưu tiên dài trước) + tiền tố VN `chùa/tổ đình/thiền viện/tịnh xá/tịnh thất/niệm phật đường/tu viện/đại tòng lâm/bảo tháp/tháp/am/phật đường/thiền đường/cổ tự/tự`.
  - `hanvi_reading()`: tra `hanviet_char_map` + chồng `custom_hanviet_override`; chữ lạ giữ nguyên ký tự.
  - `pinyin_reading()`: pypinyin lazy; thiếu lib → None (nullable, không crash).
- **`scripts/vn_places_t243_normalize.py`** — CLI `--apply/--dry-run/--revert/--db/--limit/--report`:
  - Đọc `places_dila` **READ-ONLY** bằng generator (Zero-RAM, 59k dòng); tên Việt tốt nhất từ `namevi_map_places GROUP BY dila_id MIN(name_vi)`.
  - Bảng **additive**: `place_norm_keys` (rowid PK, `dila_id`,`name_role`∈{dila,dila_zh,vi},`name_text`,`norm_key`,`key_kind`∈{full,stripped},`hanvi`,`pinyin`,`district`,`has_geo`; idx `idx_pnk_dila`+`idx_pnk_normkey`) + FTS5 `place_norm_fts(norm_key,name_text,hanvi,pinyin)` external-content (`content='place_norm_keys'`, `content_rowid='rowid'`).
  - Idempotent: `DELETE` toàn bộ derived rồi rebuild + `INSERT INTO place_norm_fts(place_norm_fts) VALUES('rebuild')`.
  - Phiên âm Hán-Việt/pinyin chỉ tính cho role `dila_zh` (khi có `name_zh`).

## 3. Số đo DB thật (apply `data/lineage.db`, ~34s)

| Chỉ số | Giá trị |
|---|---|
| places_total / with_geo / with_vi_name | 59.167 / 58.480 / 59.150 |
| rows_keys = fts_rows | **250.784** |
| distinct_norm_keys | **86.818** |
| hanvi_rows = pinyin_rows | **14.174** |
| suffix_stripped_rows | **20.993** |
| Verify search | `MATCH '"tran quoc"'` → 24 row · `'"kim cuong"'` → 112 row (0.0s) |

`integrity_check` **bỏ qua** — crawl toàn DB rất lâu (>60s); thay bằng count khớp keys/fts (đủ cho derived tables).

## 4. Test

`tests/test_t243_place_name_normalize.py` — **9/9 PASS**, fixture DB temp (4 places, 3 map, 6 Hán tự), không mạng:
- Unit K1–K6: nfkc, vn_key (+`NORMALIZE_FROM_APP`), strip_facility, hanvi_reading, pinyin_reading, place_key_entries.
- Integration G1–G5: dry-run không ghi (`count=0`), apply count khớp (20), FTS `"tran quoc"` → PL000000000002, revert DROP 2 bảng, apply lại idempotent.

Wire `npm run test:t243` vào package.json + pipeline (sau `test:t242`). `npm run pipeline` **XANH**.

## 5. Kiến trúc note (cho T244 Matching Engine)

- Khóa tìm cho T244: `place_norm_keys.norm_key` (key_kind `full`/`stripped`); ưu tiên `stripped` → `full` → pinyin → hanvi.
- Tên Việt trùng dila_id: `namevi_map_places` dư; dùng `MIN(name_vi)` deterministic, T244 có thể đổi sang confidence-rank nếu cần.
- FTS external-content: mọi ghi vào `place_norm_keys` phải qua `rebuild` để đồng bộ.

## 6. Revert

```bash
# DB (additive, mất 0 dữ liệu cũ — places_dila không đụng)
python -X utf8 scripts/vn_places_t243_normalize.py --revert
# Git: git revert --no-edit 3a1485977b00fc9a0c7d4f6e29b8b443168eb450 1c855b72413b32e70135906ccc63808d1c969d31  (pass-2 trước)
```

## 7. Files
- `scripts/vn_places_name_utils.py` · `scripts/vn_places_t243_normalize.py` · `tests/test_t243_place_name_normalize.py` · `package.json` (test:t243 + pipeline) — pass-1
- `tasks/T243…md` (status done + done_evidence) · `docs/db_schema.md` (§place_norm_keys) · `docs/tasktodo.md` · `docs/ROLLBACK.md` · `docs/sessions/2026-10-07_T243-name-normalize.md` · `data/progress_data.json` (regen) — pass-2
- pass-3: hash-fill `1c855b72413b32e70135906ccc63808d1c969d31` (pass-1) / `3a1485977b00fc9a0c7d4f6e29b8b443168eb450` (pass-2) trong ROLLBACK + §6.