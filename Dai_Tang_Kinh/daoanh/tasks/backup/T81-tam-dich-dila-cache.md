---
id: T81
title: "Tạm Dịch DILA — Lazy Translation Cache với Rules Phật Học"
module: Person / Place Content
priority: high
status: done
depends_on: [T67, T68]
created: 2026-08-31
updated: 2026-08-31
completed: 2026-08-31
done_when: >
  Hệ thống "Tạm Dịch" cho people.bio (48K rows DILA, chữ Hán) hoạt động:
  User click nút → check cache → Gemini dịch theo rules Phật học → auto-save → Báo lỗi.
  Admin có thể update rules → invalidate bản dịch cũ theo rules_version → người sau dịch lại.
  Theo năm tích lũy corpus dịch DILA đầy đủ trong translation_cache.
---

# T73 — Tạm Dịch DILA + Translation Cache

## Mục tiêu

Dịch `people.bio` (tiểu sử DILA, chữ Hán học thuật, 48,180 rows) sang tiếng Việt
bằng Gemini với **rules Phật học cứng** (cấm pinyin, Hán-Việt, tước hiệu đúng, văn phong
học thuật). Cache kết quả vào `translation_cache` — tự tích lũy corpus dịch theo thời gian.

Kiến trúc lazy: chỉ dịch khi user xem, không batch toàn bộ. Cost-free cho 95% nhân vật
không ai tra.

## Kiến trúc

```
User click "Tạm Dịch"
  → GET /daoanh/api/person/<id>/translate
      → check translation_cache (source_hash + rules_version)
      → HIT: trả về ngay (0 token cost)
      → MISS: build prompt từ translation_rules đang active
           → call Gemini → auto-save → trả về
  → Hiển thị bản dịch + badge "Tạm dịch AI"
  → Nút "Báo lỗi" → POST /translate/report → report_count++

Admin update rules → rules_version thay đổi
  → /admin/translate/invalidate → mass-set status='invalidated'
  → User dịch lại với rules mới → bản dịch cũ hủy hoàn toàn
```

## Bảng mới

### `translation_rules`
Admin-updatable rules nhúng vào system prompt của Gemini.
8 rules mặc định: NO_PINYIN, HANVIET_NAMES, HANVIET_PLACES, BUDDHIST_TITLES,
REIGN_ERA, ACADEMIC_STYLE, CLASSICAL_SYNTAX, OUTPUT_FORMAT.

### `translation_cache`
Content-addressable cache: key = SHA256(source_text).
Trường quan trọng: `rules_version` (để batch-invalidate), `status` (auto/approved/reported/invalidated),
`report_count` (>= 3 → status='reported').

## Subtasks

- [x] T73a: Migration script `scripts/t73_translation_system.py` — tạo 2 bảng + seed 8 rules
- [x] T73b: API `GET /daoanh/api/persons/<id>` — person profile + bio từ cache
- [x] T73c: API `POST /daoanh/api/person/<id>/translate` — check cache → Gemini → auto-save
- [x] T73d: API `POST /daoanh/api/person/<id>/translate/report` — user báo lỗi
- [x] T73e: API `GET/POST /daoanh/api/admin/translation-rules` — CRUD rules
- [x] T73f: API `GET /daoanh/api/admin/translation-cache` — list với filter/pagination
- [x] T73g: API `POST /daoanh/api/admin/translate/invalidate` — mass-invalidate theo rules_version
- [x] T73h: Frontend `search.js` — nút Tạm Dịch + Báo lỗi + hiển thị bản dịch từ cache
- [x] T73i: Admin pages `admin/translation_rules.html` + `admin/translation_cache.html`
- [x] T73j: Admin menu index.html — thêm 2 link vào block "Place VN"
- [x] T73k: py_compile OK

## Rules version system

`rules_version` = SHA256[:16] của toàn bộ rule_text theo thứ tự priority.
Khi admin thay đổi/thêm/tắt bất kỳ rule → hash thay đổi → có thể invalidate chọn lọc
theo version cũ thay vì xóa tất cả.

## Revert

- Drop `translation_rules` + `translation_cache` — reversible.
- Remove API routes T73b-T73g từ app.py.
- Remove frontend code từ search.js.

## Thiết kế tương lai (T73+)

- Mở rộng cho place_note (T74): cùng cơ chế, source_type='place_note'
- Batch translate top 500 patriarchs offline bằng script
- User "approve" bản dịch → confidence tăng lên → có thể export corpus
- So sánh bản dịch nhiều versions khi admin query báo cáo chất lượng

## Ghi chú nguồn dịch

- `person_bio_vi_draft` (2,093 rows từ Từ Điển Thiền Tông Hán-Việt) → chỉ dùng làm
  reference cho admin tra tên/thuật ngữ, KHÔNG hiển thị trực tiếp thay cho DILA bio.
- `people.bio` (DILA, 48,180 rows) là nguồn chính thức → T73 dịch cái này.
