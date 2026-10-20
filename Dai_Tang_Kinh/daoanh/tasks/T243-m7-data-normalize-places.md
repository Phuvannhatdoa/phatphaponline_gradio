---
id: T243
title: "M7 — Data: Ingest DILA place + chuẩn hóa tên địa danh"
module: GIS / Places
priority: high
status: done
depends_on: []
created: 2026-10-06
updated: 2026-10-07
done_when: "Module chuẩn hóa tên (NFKC, bỏ hậu tố 寺/院/庵/chùa/tự, key không dấu tiếng Việt, Hán-Việt+pinyin) xây xong + DILA place đọc được với chỉ số tìm kiếm theo khóa chuẩn."
done_evidence: "scripts/vn_places_name_utils.py + scripts/vn_places_t243_normalize.py; test 9/9 (npm run test:t243); apply lineage.db → place_norm_keys=250.784 (FTS rows=250.784), distinct_norm_keys=86.818, places=59.167 (58.480 có GPS), hanvi+pinyin=14.174, suffix_stripped=20.993; report data/t243_place_norm_report.json; pipeline XANH."
---

# T243 — M7 · Data: Ingest DILA place + Name Normalization

> Nguồn đặc tả (Single Source): `docs/integration/Uu-Tien-1-T07-gis-buddhist-maps-consolidated.md` (M7 toàn cầu).

## 📎 Liên kết các phần khác — MỞ TRƯỚC KHI DEV
| Phần | Đường dẫn | Dùng để |
|---|---|---|
| Đặc tả M7 | `docs/integration/Uu-Tien-1-T07-gis-buddhist-maps-consolidated.md` | Yêu cầu dữ liệu + chuẩn hóa tên (§Dữ liệu, §Logic) |
| Schema DB | `docs/db_schema.md` | Bảng `places_dila` (RAW), chỉ số tìm kiếm |
| Hàm chuẩn hóa có sẵn | `app.py` → `normalize_text()` | Tái dùng bỏ dấu tiếng Việt |
| Script dir | `scripts/` (làm trong `daoanh/`) | Đặt script ingest |

## Mục tiêu
Đưa nguồn chính **DILA place** (~59.375 nơi, 58.500 có tọa độ, CC BY-SA 3.0) vào pipeline,
kèm module **chuẩn hóa tên** để phục vụ khớp ở T244.

## Cách tiếp cận
1. Tạo module chuẩn hóa tên: **NFKC**; bỏ hậu tố `寺,院,庵,chùa,tự`; tạo **khóa phụ bỏ dấu tiếng Việt** (tái dùng `normalize_text()` của `app.py`); dùng cả **Hán Việt** và **pinyin**.
2. Đọc `places_dila` (RAW) theo danh sách, sinh khóa chuẩn + chỉ số tìm kiếm (Zero-RAM; không nạp toàn bộ).
3. Output metadata (số record, coverage tọa độ) — không sửa bảng RAW.

## Ràng buộc
- Zero-RAM, Code Preservation (`places_dila` READ-ONLY), 3-Layer.
- Không dùng `YEAR_START`/BGIS để suy năm (M7 §Logic).

## Acceptance criteria
- [x] Hàm chuẩn hóa: NFKC + bỏ 4 hậu tố + khóa không dấu tiếng Việt + Hán-Việt/pinyin.
- [x] Đọc `places_dila` không sửa bảng; report coverage tọa độ.
- [x] Chỉ số tìm kiếm theo khóa chuẩn hoạt động.

## Kết quả 2026-10-07 (acceptance filled)
- **Module**: `scripts/vn_places_name_utils.py` — `nfkc()`, `vn_key()` (tái dùng `normalize_text()` của app.py qua AST-extract, `NORMALIZE_FROM_APP=True`), `strip_facility()` (hậu tố Hán `寺/院/庵/廟/塔/閣/堂/殿/宮/觀/精舍/蘭若/伽藍/道場` + tiền tố VN `chùa/tổ đình/thiền viện/tịnh xá/…`), `hanvi_reading()` (bảng `hanviet_char_map` + `custom_hanviet_override` chồng lên), `pinyin_reading()` (pypinyin 0.55.0, lazy).
- **Ingest**: `scripts/vn_places_t243_normalize.py` — CLI `--apply/--dry-run/--revert/--db/--limit/--report`; tạo 2 bảng **additive** `place_norm_keys` + FTS5 `place_norm_fts` (external-content, rebuild idempotent). Đọc `places_dila` **READ-ONLY** bằng generator (Zero-RAM), tên Việt tốt nhất lấy `namevi_map_places GROUP BY dila_id MIN(name_vi)`.
- **Số đo** (apply lineage.db, ~34s): places_total **59.167**, places_with_geo **58.480** (98,8%), places_with_vi_name **59.150**, rows_keys=fts_rows **250.784**, distinct_norm_keys **86.818**, hanvi_rows=pinyin_rows **14.174**, suffix_stripped_rows **20.993**. Report: `data/t243_place_norm_report.json`.
- **Verify search**: `MATCH '"tran quoc"'` → 24 row, `'"kim cuong"'` → 112 row (0.0s).
- **Test**: `tests/test_t243_place_name_normalize.py` 9/9 (unit K1–K6 + integration G1–G5: dry-run không ghi, apply count khớp, FTS trả đúng dila_id, revert DROP 2 bảng, apply lại idempotent). Wired `test:t243` vào pipeline sau `test:t242`.
- **Revert**: `python -X utf8 scripts/vn_places_t243_normalize.py --revert` → DROP 2 bảng (additive, mất 0 dữ liệu cũ).