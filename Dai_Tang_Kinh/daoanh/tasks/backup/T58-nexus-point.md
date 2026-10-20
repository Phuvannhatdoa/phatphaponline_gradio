# T58 — Nexus Point: Event-Centric Knowledge Graph

**Trạng thái:** ✅ DONE (2026-08-29) — build phiên 1 (4 commits).
**ID liên quan:** T16 (CBETA XML — đã CANCELLED vì P5a không có persName/placeName tag);
T40 (place_person_bibl 13,933 citation thật); T39/T41/T42/T43 (person-place links).
**Khác biệt:** T58 dùng nguồn đã có (place_person_bibl + place_timeline_events) → không cần
quét XML; nexus = **EVENT↔TEXT** (passage citation), không phải place↔place.

## Mô tả

Xây đồ thị **Nexus Point** cho 1 thực thể (person/place): thực thể → **sự kiện** →
**văn bản passage** (trích dẫn CBETA thật) → **mốc thời gian** (year/era/JDN).
Mô hình event-centric được user xác nhận: TIME gắn vào EVENT, không gắn vào TEXT;
era = tầng hiển thị, JDN = tầng chuẩn hóa (proleptic Gregorian, năm âm TCN OK).

## Thiết kế dữ liệu (additive — KHÔNG đụng bảng nguồn)

1. **Commit 1 — `cbeta_person_mentions` / `cbeta_place_mentions`** (passage-level ETL)
   - Nguồn: `passage` (7,563) + `passage_entity` (378,483 links).
   - Kết quả: person 72,628 / place 16,311; `context_snippet` = raw_text ~200 ký tự.
   - Script: `scripts/build_cbeta_mentions.py` (idempotent).
2. **Commit 2 — `event_text_link`** (bridge EVENT↔TEXT)
   - Nguồn: `place_person_bibl` (person_place, cbeta_ref thật) + `place_timeline_events`
     (place_founding/dissolved, year).
   - Kết quả: 17,284 rows; 13,933 có cbeta_ref.
   - Script: `scripts/build_event_text_link.py` (idempotent).
3. **Commit 3 — `era_year_jdn`** (TIME normalized layer)
   - `to_jdn(year)` proleptic Gregorian (kiểm chứng 2000→2451545); năm âm TCN xử lý bằng
     phép chia sàn Python.
   - Kết quả: 986 rows (12 BCE, -1599 → 2002).
   - Script: `scripts/build_era_year_jdn.py` (idempotent).
4. **Commit 4 — Nexus API + UI**
   - API `GET /daoanh/api/nexus/<id>?type=person|place` (app.py) — cùng shape nodes/edges.
   - UI: tab `🔥 Nexus` trong places.html, tái dùng `_renderVisGraph`; màu nhóm mới
     (event `#8b5cf6`, time `#d97706`); tooltip = citation nguồn thật.

## Verify

- Live API: place `PL000000000002` → 23 nodes/24 edges (citation `T50n2059_p0338c09`...);
  person `A009306` (Thích Huyền Trang) → 679 nodes/723 edges (`T50n2060_p0447c17` + `唐高僧傳`).
- `npm run test` ✅ / `npm run e2e` ✅ / `py_compile` OK / inline JS parse OK.

## Done when

- [x] 4 commits build + verify API.
- [x] Sự cố DB đã khôi phục (backup 1.1GB) + glossary tái tạo 248K.
- [ ] (chờ admin) Xem tab `🔥 Nexus` trên browser để duyệt trực quan.
- [ ] (tùy chọn) Nối TIME theo era-name display; edge màu theo loại sự kiện.

## Session log

`docs/sessions/2026-08-29_T58_nexus_point.md`
