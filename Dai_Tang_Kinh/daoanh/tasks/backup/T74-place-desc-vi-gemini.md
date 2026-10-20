---
id: T74
title: "Place Desc VI — Tạm Dịch DILA note → Tiếng Việt (T73 pattern)"
module: Place Content
priority: medium
status: done
depends_on: [T73]
created: 2026-08-31
updated: 2026-08-31
completed: 2026-08-31
done_when: >
  User xem địa danh có mô tả DILA (chữ Hán) → thấy nút "Tạm Dịch (AI)".
  Click → Gemini dịch theo rules Phật học (T73 system) → auto-save vào translation_cache.
  Lần sau load ngay từ cache. Nút "Báo lỗi dịch" → admin tra cứu.
---

# T74 — Place Desc VI (Tạm Dịch DILA note → Tiếng Việt)

## Mục tiêu

Mở rộng hệ thống T73 (translation_rules + translation_cache) cho địa danh.
Dịch `places_dila.note` (17,085 rows chữ Hán học thuật DILA) sang tiếng Việt
bằng cùng Gemini + rules Phật học, cùng lazy-cache pattern.

## Kiến trúc

Tái dùng hoàn toàn T73:
- `translation_rules` — thêm 2 rules mới: PLACE_TERMS (thuật ngữ kiến trúc) + DILA_SOURCE_BADGE
- `translation_cache` — source_type='place_note', entity_id=dila_id
- `_t73_build_prompt()`, `_t73_call_gemini()`, `_t73_rules_version()` — tái dùng nguyên

## Subtasks

- [x] T74a: Seed 2 rules mới: PLACE_TERMS, DILA_SOURCE_BADGE vào translation_rules
- [x] T74b: API `GET/POST /daoanh/api/place/<dila_id>/translate` — lazy cache + Gemini
- [x] T74c: API `POST /daoanh/api/place/<dila_id>/translate/report` — báo lỗi
- [x] T74d: Frontend `places.html` — `#placeTranslatePanel` + JS functions (loadPlaceTranslation, translatePlace, reportPlaceTranslation)
- [x] T74e: py_compile OK

## UI pattern (places.html)

```
[Mô Tả DILA]        ← luôn hiện nếu có dila_note (chữ Hán)
  <nguyên bản chữ Hán>

[Bản Dịch Tiếng Việt] [badge: Tạm dịch AI]  ← từ cache nếu có
  <bản dịch tiếng Việt>
  [Dịch lại]  [Báo lỗi dịch]

hoặc nếu chưa dịch:
  [Tạm Dịch (AI)]   Dịch mô tả DILA sang tiếng Việt
```

## Scope

17,085 địa danh có `places_dila.note` không null.
Lazy: chỉ dịch khi user thực sự xem. Không batch tự động.
Batch (tùy chọn tương lai): admin có thể chạy script dịch top 1000 địa danh phổ biến nhất.
