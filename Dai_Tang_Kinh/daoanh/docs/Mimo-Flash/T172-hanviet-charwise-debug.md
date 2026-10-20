---
id: T172
title: "Debug Pipeline Phiên Âm Hán-Việt Theo Từng Hán Tự (Charwise)"
status: ready-for-dev
priority: high
tags: [dila, transliteration, han-viet, debug, sidecar]
created: 2026-09-25
depends_on: [T166, T171]
---

# T172 — Debug Pipeline Phiên Âm Hán-Việt Theo Từng Hán Tự

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
- **Addendum (T171)** search `一行` = **2 person** (A000008+A010168) — không gộp; dual-write 2 endpoint (app.py:13114/17523); guard không INSERT `people` ngoài ETL.

## Acceptance (rút gọn)
A000006/A000008/A000026/A000047 gắn cờ duyệt · `𧧌震` không crash · `蘇嚩羅` exception flag · legacy nguyên vẹn · test + backup + idempotent + rollback · `T172-…-REPORT.md`.

## Revert
`git revert --no-edit <sha_T172>` từng phase + `scripts/t172_hanviet_charwise_migrate.py --revert`.
