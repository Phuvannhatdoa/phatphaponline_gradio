---
id: TAB_DAI_TANG_PLACE
title: "TAB_DAI_TANG_PLACE — Tab Đại Tạng (3 lớp DILA/CBETA) trong trang địa danh places.html"
module: DILA Integration Layer / CBETA
priority: high
status: done
depends_on: []
created: 2026-09-01
updated: 2026-09-01
completed: 2026-09-01
done_when: Endpoint GET /daoanh/api/entity/<entity_id>/canon trả 3 lớp (DILA raw refs / indexed passages / text metadata) dữ liệu thật; tab 📜 Đại Tạng tách riêng khỏi alias cbeta; modal đọc raw_text thật; empty-state trung thực cho bản dịch Việt không có.
---

# TAB_DAI_TANG_PLACE — Tab Đại Tạng (3 lớp)

## Mục tiêu

Tái thiết lại tab "Đại Tạng" trong trang `places.html`. Trước đây tab này là alias của
tab `cbeta` (`data-t="daitang"` alias `cbeta`) nên **không bao giờ hiển thị `raw_text` passage thật**.
Mục tiêu: tạo tab **riêng** hiển thị canon Tam Tạng theo mô hình **3 lớp** (đúng triết lý
Zero-RAM + SSOT + Code Preservation), dữ liệu thật từ DB, empty-state trung thực khi không có
bản dịch Việt (không bịa, không realtime LLM).

## Bước 1 — Backend: endpoint canon (app.py)

- Thêm `GET /daoanh/api/entity/<entity_id>/canon` (`entity_canon`, app.py ~line 11530).
- Resolve id ngắn → id đầy đủ qua `_resolve_dila_id` (line 4015): `PL022435`→`PL000000023255`, raw `PL023255`→湯陰.
- Trả 3 lớp:
  - **Lớp A** `dila_references[]`: dẫn CBETA + FOSIZHI lấy từ `places_dila.listbibl`/`raw_xml` (copy + link).
  - **Lớp B** `passages{}`: các passage indexed (bảng `passage_entity`→`passage`), phân trang.
  - **Lớp C** `texts[]`: metadata text qua `catalog_mapping`→`canon_catalog`/`cbeta_catalog_vn`
    (join `CAST(cb_cbeta AS TEXT)=catalog_id`).
- Kèm: `entity` (alias Hán hiển thị, authority_sources), `summary` (dila_reference_count,
  indexed_passage_count, text_count, translation_count), `data_status`, `mapping[]`.
- 404 khi id không tồn tại.

## Bước 2 — Frontend: tab Đại Tạng tách riêng (places.html)

- Panel riêng `#tp-daitang` (line 224) — **bỏ alias** `cbeta` trong tab-click handler (~988).
- `loadTabData` (~1219): daitang → fetch `/entity/<id>/canon` → `renderDaiTangTab` (catch → `da-warn`).
- `renderDaiTangTab` (~1513): header / thanh summary / Lớp A / Lớp B (card + chip `evidence:` +
  nút "Đọc trong ngữ cảnh" + copy + báo sai) / Lớp C / phân trang / sidebar `HỒ SƠ LIÊN KẾT`.
- `openDaiTangReader` (~1474): modal đọc `raw_text` thật.
- `daiTangGoPage` (~1660): đổi trang, re-fetch + rebuild Lớp B.
- Guard person-mode: `daitang` là place-only.

## Bước 3 — Kiểm thử

- `py_compile app.py` OK; `node --check` các script block places.html OK.
- `npm run e2e` + `npm run test` PASS.
- Regression: `/daoanh/api/places/PL000000023255/cbeta` vẫn OK.

## Data Reality (PL000000023255 — Thiếu Lâm Tự / 少林寺)

Đã probe DB thật (read-only, không sửa):
- `entity.alias_zh` = `少林寺` (header dùng cái này).
- `places_dila.name_zh` = **`少室寺`** (tên canon lưu trữ — KHÁC 少林寺; header dùng alias_zh).
- `passage_entity` = **15 passage**, **0 có `vi_text`** → Lớp B empty-state bản dịch Việt trung thực.
- `catalog_mapping` = **6 rows** → Lớp C text metadata (1524, 2059, 2060, 2061, 2062, 2210).
- `dila_reference` = bảng **person-refs** (KHÔNG phải place canon refs; Lớp A dùng `places_dila.listbibl`).
- `translation_cache` = **0 rows** → translation_count=0.

## Acceptance Criteria

- [x] Endpoint canon trả đủ 3 lớp + summary + phân trang (page_size=10: page1 has_more=True, page2 5 items)
- [x] Tab Đại Tạng tách riêng `#tp-daitang`, không còn là alias cbeta
- [x] Modal `openDaiTangReader` hiển thị `raw_text` thật
- [x] Bản dịch Việt = empty-state trung thực (không bịa, không LLM)
- [x] Regression cbeta cũ OK; test PASS; py_compile/node --check PASS

## Rollback (bản code đã nằm trong commit 8e7c77f)

Rollback toàn feature bằng cách revert commit chứa code:

```bash
git revert 8e7c77f   # bỏ endpoint canon + tab Đại Tạng (additive, không đụng DB/schema)
```

Không có thay đổi DB/schema nào — feature thuần additive (endpoint mới + render mới).

## Ghi chú đồng thời (concurrency)

- Code feature đã được commit vào `8e7c77f` bởi một session song song ("fix(places)... full-width
  tab bar"). Worktree hiện tại == HEAD về nội dung canon (git diff app.py/places.html chỉ còn
  thay đổi in-progress của session T74 — KHÔNG thuộc task này).
- Tài liệu: report `docs/TAB_DAI_TANG_IMPLEMENTATION_REPORT.md`, session
  `docs/sessions/2026-09-01_TAB_DAI_TANG_place.md`.
