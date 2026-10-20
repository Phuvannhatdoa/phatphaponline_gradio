# 2026-08-29 — T58: Nexus Point — Event-Centric Knowledge Graph (4 Commits) ✅

## Mô tả ngắn task

User yêu cầu logic-check đề xuất "KNOWLEDGE GRAPH = NEXUS POINT" (PERSON → teacher_of →
PERSON → lived_at → PLACE → mentioned_in → CBETA → during → TIME). Sau khi logic-check,
user xác nhận lại mô hình **event-centric** (TIME gắn vào EVENT, không phải TEXT; tách
`lived_at` thành birth_at/resided_at/active_at; era = tầng hiển thị, JDN = tầng chuẩn hóa;
event↔passage là nexus thật). Kế hoạch triển khai 4 commit — user duyệt bản build + cách
commit-back thuận tiện.

## Sự cố DB (đã xử lý — bài học quan trọng)

- **Sự cố:** Lệnh backup bằng `PRAGMA wal_checkpoint(TRUNCATE)` trong lúc server còn mở
  WAL đã vô tình **truncate file `lineage.db-wal`** — nơi chứa toàn bộ schema+data
  (main file `lineage.db` chỉ là header 4,096 bytes trong chế độ WAL). Server trả
  `no such table: lexicon`.
- **Xử lý:** Dừng `app.py` → **restore** `data/lineage.db` từ backup an toàn
  `%TEMP%\opencode\lineage_backup_20260829_193510.db` (1.1 GB, chụp 19:35, 105 bảng).
  **Tái tạo glossary** qua `import_glossary_yokoyama.py` (248,095 rows, MB_GLOSSARY id=6).
  Restart `app.py` → verify live glossary + đồng môn OK.
- **Bài học:** KHÔNG bao giờ chạy `wal_checkpoint(TRUNCATE)` / backup bằng connect trong
  lúc server mở WAL. Backup DB phải làm khi server DỪNG, hoặc dùng transaction backup an toàn.

## Build — 4 Commit

### Commit 1 — Passage-level CBETA mentions ✅
- Script `scripts/build_cbeta_mentions.py` — ETL từ bảng trung gian `passage` (7,563) +
  `passage_entity` (378,483 links) → populate `cbeta_person_mentions` / `cbeta_place_mentions`
  (vốn trống). Place ID chuẩn hóa về dạng dài PLxxxxxxxxxxxx; `context_snippet` = raw_text
  cắt ~200 ký tự; tên lấy từ `people.name_zh` / `places_dila.name_zh`. Idempotent (DELETE rồi INSERT).
- Kết quả: **cbeta_person_mentions 72,628** / **cbeta_place_mentions 16,311**.
- Verify: `A025190` → 5 CBETA texts (X77n1524, T51n2076, T50n2062...) qua
  `/daoanh/api/person/A025190/profile`.

### Commit 2 — EVENT↔TEXT bridge `event_text_link` ✅
- Script `scripts/build_event_text_link.py` — bảng bridge (additive, UNIQUE(source_table, source_id)):
  - `place_person_bibl` (13,933) → event_type `person_place`, entity_type `person`, cbeta_ref thật.
  - `place_timeline_events` (3,351) → `place_founding`/`place_dissolved`, year, source_ref.
- Kết quả: **17,284 rows** (person_place 13,933 / place_founding 3,310 / place_dissolved 41; 13,933 có cbeta_ref).

### Commit 3 — TIME normalized layer `era_year_jdn` ✅
- Script `scripts/build_era_year_jdn.py` — `to_jdn(year)` proleptic Gregorian (kiểm chứng
  2000→2451545). Populate từ `place_timeline_events.year`: **986 rows** (12 năm BCE,
  -1599 Nhà Thương → 2002).
- Bảng `era_year_jdn(year UNIQUE, era_name, jdn, year_bce, source, created_at)`.

### Commit 4 — Nexus API + UI ✅
- **API:** Route `GET /daoanh/api/nexus/<entity_id>?type=person|place` (app.py) — entity →
  EVENT → TEXT (passage với citation `cbeta_ref`) → TIME (year). Mỗi edge mang nguồn thật
  (cbeta_ref / source_ref). Cùng shape nodes/edges → tái dùng `_renderVisGraph`.
  - Helper `_nexus_title_for_sigla` (tựa sách từ cbeta.db).
  - Place label từ `places_dila.name` + `namevi_map_places`.
- **UI:** Tab mới **`🔥 Nexus`** trong places.html (data-t="nexus") + panel `tp-nexus` +
  `renderNexusTab(d)` + dispatch trong `loadTabData` (hoạt động cả person lẫn place) + màu
  nhóm mới (event `#8b5cf6`, time `#d97706`) trong `_renderVisGraph`.
- **Verify live:** place `PL000000000002` (Thiếc Nhã Kha Sơn) → 23 nodes / 24 edges với
  citation `T50n2059_p0338c09` ... ; person `A009306` (Thích Huyền Trang) → 679 nodes / 723 edges,
  `T50n2060_p0447c17` + `唐高僧傳`.

## Tester / Verify

- `npm run test` ✅ / `npm run e2e` (static) ✅.
- `new Function` parse inline JS places.html ✅ (toàn bộ inline script).
- `py_compile` app.py ✅; live API test 2 entity types qua HTTP.
- Lint script cố hữu: `node --check` temp file không đuôi → ESM `get_format` lỗi môi trường
  (không phải lỗi code; JS đã parse riêng OK).

## Trạng thái subtasks

| Phần | Trạng thái |
|------|-----------|
| Sự cố DB restore + tái tạo glossary | ✅ DONE (bài học ghi trên) |
| Commit 1 — CBETA mentions (72,628 / 16,311) | ✅ DONE |
| Commit 2 — `event_text_link` (17,284) | ✅ DONE |
| Commit 3 — `era_year_jdn` (986, 12 BCE) | ✅ DONE |
| Commit 4 — Nexus API + UI tab | ✅ DONE |
| Demo UI trực quan (vis-network trên browser) | ⏸ XÁC NHẬN — API verified; chờ admin xem tab live |

## Việc tiếp theo

1. Admin mở places.html tab `🔥 Nexus` trên 1 địa danh (vd Thiếc Nhã Kha Sơn/Trường An) và 1 tăng
   nhân (Thích Huyền Trang) để xem đồ thị trực quan + tooltip citation.
2. Tùy chọn: nối TIME (era_year_jdn) hiển thị theo era (không chỉ năm) cho đẹp hơn; thêm edge màu
   theo loại sự kiện.
3. Plant bản Việt hóa glossary Yokoyama (chờ admin — tách từ T57).

## Revert

Atomic commit phiên này: `feat(T58): Nexus Point - event-centric knowledge graph (CBETA
mentions ETL + event_text_link bridge + era_year_jdn + nexus API + UI tab) + docs`.
Mỗi script build riêng revert được bằng `--revert` nếu có (hiện idempotent re-run).
DB backup an toàn: `%TEMP%\opencode\lineage_backup_20260829_193510.db` (lineage.db không git-track).
