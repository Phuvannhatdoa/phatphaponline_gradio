---
id: T172
title: "Debug Pipeline Phiên Âm Hán-Việt Theo Từng Hán Tự (Charwise)"
status: built
priority: high
tags: [dila, transliteration, han-viet, debug, sidecar]
created: 2026-09-25
depends_on: [T166, T171]
---

# T172 — Debug Pipeline Phiên Âm Hán-Việt Theo Từng Hán Tự

> **[2026-09-29 · T172-BUILD] ✅ BUILD DONE (code+data+docs; guard/lint/test/e2e PASS trừ e2e:runtime EPERM
> pre-existing) — migrate DB THẬT: `person_hanviet_debug` **47.036 rows** (valid 40.575 · mismatch 920 ·
> unknown_char 534 · exception 1 · needs_review 5.006; legacy exact 38.912/normalized 1.661/differs 5.930/
> not_comparable 533; translit 40.573) · people 48.673 nguyên vẹn · `hanviet_char_map` 11.300 char (poly 552) ·
> APP: list `?hv_status` + detail `hv` + `GET /daoanh/api/dila/hv/stats` · UI ⚠/filter/#card-hv · tests **64/64** ·
> lint-check.ps1 fixed (Batch 4). REPORT: `T172-hanviet-charwise-debug-REPORT.md`. **Phase 1 re-verify UI live (7 ví dụ)
> = NỢ acceptance sau restart server.** Revert: `git revert --no-edit <sha_T172_pass1>` + migrate `--revert`.

> **[2026-09-28 · T191] AMEND (docs-only, 0 code/0 DB; Admin phê chuẩn đề xuất audit):** `一行` search substring
> = **4 person** (A000008/A010168/**A016240 `一行智嚴`**/**A023828 `釋一行`**; exact `name_zh='一行'`=2) — sửa acceptance
> đồng bộ T171 SPEC §14.3/§14.6 · dual-write refs **13926/18308** (drift cũ 13114/17523) ·
> SPEC line refs `_han_viet`=app.py:**1849** · `HAN_VIET_CHAR`=app.py:**1294** · `is_transliteration` đã định nghĩa.
> Chi tiết: `tasks/T191-t172-build-docs-correction.md`.

## Mục tiêu
Cột "Tên Việt" DILA Person Index nhiều lỗi (chuỗi metadata/hiệu thay vì âm Hán-Việt). Tạo lớp kiểm tra kỹ thuật `han_viet_charwise` (1 Hán tự → 1 âm tiết, không LLM), validate, đối chiếu legacy, UI ⚠/filter — **không thay thế cột legacy, không tạo person trùng**.

## SSOT
- **SPEC:** `docs/Mimo-Flash/T172-hanviet-charwise-debug-SPEC.md`
- **Plan đã inspect:** `HANVIET_DEBUG_PLAN.md` (nguyên nhân pipeline, 6 ví dụ lệch DB, 3 dict xung đột, design đầy đủ)

## Admin chốt (2026-09-25)
1. Đa âm → reading chính dict version + `needs_review` + candidates (không placeholder cho chữ có âm).
2. Addendum gộp tên → **T171** (`person_name_alias`), không tạo `person_names`.
3. Lưu debug → sidecar `person_hanviet_debug` (không ALTER `people`).
4. Legacy giữ display; charwise = khối debug.

## Điểm mấu chốt (review → 4 P0 + 6 P1/P2)
- **P0** ID 4 ký tự = 0 row → pad 7 ký tự.
- **P0** 6/7 ví dụ lệch DB (A000008=`Nhất Hàng` ≠ "Đại Huệ Thiền Sư" — tên đó không tồn tại local) → **Phase 1 re-verify UI live**.
- **P0** Rule placeholder `[?行]` mâu thuẫn test `Nhất Hành` → chốt reading chính.
- **P0** Root cause đã verify: seed từ `name_vi_map` trộn 5 nguồn, lexicon tra cả chuỗi (`bulk_transliterate.py` P1), `_han_viet()` chỉ cho place.
- **P1** Merge 3 dict (`HAN_VIET_CHAR`/`hanviet_fallback`/`custom_hanviet_override`) → `hanviet_char_map` version.
- **P1** Exception list bảng seed, không auto-detect.
- **P1** `not_comparable` khi legacy chứa Hán lạ (`Vu 頔`).
- **P1** Sidecar + backup + idempotent + `--revert`.
- **Addendum (T171)** search `一行` (LIKE) = **4 person** (A000008/A010168/**A016240**/ **A023828**; exact `name_zh='一行'` = 2) [T191 sửa số liệu]; dual-write 2 endpoint (app.py:**13926**/**18308** [T191 sửa ref drift 13114/17523]); guard không INSERT `people` ngoài ETL.

## Acceptance (rút gọn)
A000006/A000008/A000026/A000047 gắn cờ duyệt · `𧧌震` không crash · `蘇嚩羅` exception flag · legacy nguyên vẹn · test + backup + idempotent + rollback · `T172-…-REPORT.md`.

## Revert
`git revert --no-edit <sha_T172>` từng phase + `scripts/t172_hanviet_charwise_migrate.py --revert`.
