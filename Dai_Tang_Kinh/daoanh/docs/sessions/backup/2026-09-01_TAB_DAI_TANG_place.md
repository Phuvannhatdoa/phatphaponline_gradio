---
id: 2026-09-01_TAB_DAI_TANG_place
title: "TAB_DAI_TANG_PLACE Session Log — Tab Đại Tạng 3 lớp (endpoint canon + tách tab places.html)"
created: 2026-09-01
updated: 2026-09-01
---

# TAB_DAI_TANG_PLACE — Session Log

## Trạng thái
**DONE (B1–B3) + B4 (docs) hoàn tất 2026-09-01**

## Bối cảnh
Tab "Đại Tạng" trong `places.html` là alias của `cbeta` (`data-t="daitang"`), không hiển thị
`raw_text` passage thật. Task này xây endpoint canon 3 lớp + tách tab riêng + modal đọc
`raw_text`, empty-state trung thực cho bản dịch Việt (kéo dài theo kế hoạch Đại Tạng đã phê chuẩn).

## Bước 1 — Backend (B1) ✅
- `GET /daoanh/api/entity/<entity_id>/canon` (`entity_canon`, app.py ~line 11530).
- `_resolve_dila_id` (line 4015): `PL022435`→`PL000000023255`, raw `PL023255`→湯陰. 404 handled.
- 3 lớp + summary + data_status + mapping; phân trang (page_size=10; page2 5 items, has_more thật).

## Bước 2 — Frontend (B2) ✅
- Panel riêng `#tp-daitang` (places.html line 224); bỏ alias cbeta trong tab handler (~988).
- `loadTabData` daitang (~1219) → fetch canon → `renderDaiTangTab` (catch `da-warn`).
- `renderDaiTangTab` (~1513): header/summary/Lớp A/Lớp B (card, chip `evidence:`, "Đọc trong ngữ
  cảnh", copy, báo sai)/Lớp C/phân trang/sidebar `HỒ SƠ LIÊN KẾT`.
- `openDaiTangReader` (~1474) modal đọc `raw_text`; `daiTangGoPage` (~1660); `daiTangReport` (~1700);
  helper `_daitangEscape`/`_daitangChip`. Bỏ `_renderDaiTangAgain` dead.
- Guard person-mode: `daitang` place-only.

## Bước 3 — Tests (B3) ✅
- `py_compile app.py` OK; `node --check` blocks OK; `npm run e2e` + `npm run test` PASS.
- Regression `/daoanh/api/places/PL000000023255/cbeta` OK (39 passages, 3 text).
- Endpoint canon test client: page 2, 404, id ngắn/dài OK.

## Data Reality (probe read-only DB thật) — PL000000023255
- `entity.alias_zh`=`少林寺` (header); `places_dila.name_zh`=`少室寺` (stored canon, Lớp A).
- `passage_entity`=15, `vi_text`=0 (empty-state Việt), `catalog_mapping`=6, `translation_cache`=0.
- `dila_reference` = person-refs table (KO phải place canon refs); Lớp A dùng `listbibl`/`raw_xml`.
- Không có JOIN lưu trữ DILA↔passage — Lớp A & B độc lập (đã xác minh).

## Phát hiện concurrency (quan trọng)
- Khi build, branch `master` di chuyển `4dc729f`→`8e7c77f` (chứa toàn bộ code canon này) →
  `5e3dad7` (T74). Code feature **đã được commit bởi session song song** trong `8e7c77f`.
- `git diff` app.py/places.html hiện tại chỉ còn thay đổi **T74 in-progress** (không thuộc task).
- B4 chỉ commit **docs** (không đưa thay đổi T74 vào).

## Next / Việc còn lại
- (Không) — feature done. Nếu muốn bản dịch Việt thật: chạy Translation Pipeline cho 15 passage
  (ngoài phạm vi, cần admin phê chuẩn; hiện empty-state trung thực).
- Lưu tasktodo (Session Continuation Protocol, AGENTS.md §0) sau khi commit.

## Files
- `tasks/TAB_DAI_TANG_PLACE.md`, `docs/TAB_DAI_TANG_IMPLEMENTATION_REPORT.md`, session này.
- Code: `app.py` (`entity_canon`), `places.html` (tab Đại Tạng). Commit gốc code: `8e7c77f`.
