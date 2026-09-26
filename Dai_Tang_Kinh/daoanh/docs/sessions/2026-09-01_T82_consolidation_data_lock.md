---
id: 2026-09-01_T82_consolidation_data_lock
title: "T82 Session Log — Consolidation + Data-Lock (Kế hoạch được phê chuẩn)"
created: 2026-09-01
updated: 2026-09-01
---

# T82 — Session Log: Consolidation + Data-Lock

## Trạng thái
**PENDING — kế hoạch được Admin phê chuẩn 2026-09-01**

## Bối cảnh
Sau khi hoàn thành chuỗi timeline:
- T79: 203 death events (`vn_person_events`, source=`dila_person_regex`)
- T80: 55 founding events (`place_timeline_events`, source=`dila_founding_phase2`, temple coverage 27.4%)
- T81: 5,103 active/floruit events (`vn_person_events`, source=`dila_active_regex`)

Đề xuất tối ưu: **consolidation + data-lock** thay vì mở tính năng mới — để bảo vệ, chuẩn hoá dữ liệu vừa build,
phù hợp toàn bộ constraint (Zero-RAM, Code Preservation, Rollback thuận tiện, Handover admin vô não, SSOT 2026–2045).
Được Admin phê chuẩn tại phiên này.

## Phạm vi 4 bước

### Bước 1 — Hợp nhất `vn_person_events`
- Hợp nhất 45 rows `source=NULL` (legacy) → source chuẩn `legacy_migration` + gắn confidence/source_ref.
- Chuẩn hoá `event_type` taxonomy (birth/death/active/floruit).
- Script `scripts/t82_merge_events.py` (--dry-run/--apply/--revert) + snapshot backup.

### Bước 2 — Data-Lock Checksum (Zero-RAM)
- `scripts/t82_checksum.py`: scan streaming (byte-offset) các bảng lớn → `data/checksums.json`.
- `--verify` so sánh → phát hiện regression sau mỗi phiên build.
- Bảng: people, places, places_dila, place_timeline_events, vn_person_events, place_person_bibl, entity_claims.

### Bước 3 — Data Dictionary
- `docs/DATA_DICTIONARY.md`: event_type, format `（YYYY）`, confidence, rollback SQL 1-lệnh T79/80/81/82.

### Bước 4 — Wire UI (additive)
- Tab "Thời kỳ hoạt động" (T81) + timeline place (T80) trong bio/place panel — chỉ thêm render, không sửa endpoint cũ.

## Next
- Build Bước 1 (merge) → Bước 2 (checksum) → Bước 3 (dictionary) → Bước 4 (UI)
- Dry-run → verify → apply → log → commit từng bước
- Chạy `python scripts/build_progress_data.py` để cập nhật dashboard

## Build status (đã thực hiện 2026-09-01)

### Bước 1 — Hợp nhất `vn_person_events` ✅ DONE
- 45 rows legacy `source=NULL` → `source='legacy_ttl'`, `confidence=1.0` (curated TTL).
- Chuẩn hoá event_type: `Birth`→`birth`, `Death`→`death` (khớp T79/T81 lowercase). Giữ nguyên
  `KeyLifeEvent`/`Contribution`/`PhilosophicalStance` (type ngữ nghĩa riêng — không flatten để khỏi mất thông tin).
- `source_ref` = ttl_filename. **0 source=NULL còn lại** (5351 rows: legacy_ttl 45 + dila_person_regex 203 + dila_active_regex 5103).
- Script `scripts/t82_merge_events.py` (--dry-run/--apply/--revert/--stats) + **round-trip revert verified**.
- Rollback backup: `data/t82_legacy_backup.json`.

### Bước 2 — Data-Lock Checksum ✅ DONE
- `scripts/t82_checksum.py`: streaming sha256 từng dòng (fetchmany 1000, zero-RAM).
- 7 bảng khoá → `data/checksums.json`: people(48,673), places(59,161), places_dila(59,167),
  place_timeline_events(3,688), vn_person_events(5,351), place_person_bibl(13,933), entity_claims(447,885).
- `--verify` → ALL CHECKS PASSED.

### Bước 3 — Data Dictionary ✅ DONE
- `docs/DATA_DICTIONARY.md`: event_type taxonomy, confidence theo nguồn, format `（YYYY）`,
  rollback SQL 1-lệnh cho T79/80/81/82 + hướng dẫn checksum.

### Bước 4 — Wire UI ⏳ PENDING
- Tab "Thời kỳ hoạt động" (T81) + timeline place (T80) — chưa làm trong phiên này.

### Bước 4 — Wire UI ✅ DONE
- **Place timeline**: đã tự wire sẵn qua `GET /daoanh/api/places/<id>/timeline` → `static_events`
  (T80 `dila_founding_phase2` hiện trong list, source priority wikidata/dila_*).
- **Person "Thời kỳ hoạt động"** (bio panel block, additive):
  - `app.py` `api_person_by_id` (line ~12949) thêm `timeline` + `timeline_count`: đọc `vn_person_events`
    (active/floruit T81, birth/death T79, legacy T82) ORDER BY year. KHÔNG đổi field cũ.
  - `places.html`: block `#personEventsBlock` (Thời Kỳ Hoạt Động · Sự Kiện) + `#personEventsList`.
  - `selectPerson()` gọi `loadPersonTimeline(dilaId)` → fetch profile → render icon theo loại (🌱birth/🪔death/📅active/📍floruit), năm CE, confidence %, nguồn.
  - Reset block trong `selectItem` (place) và đầu `selectPerson`.
- **Verify**: `node --check` tất cả script blocks places.html PASS; app.py py_compile OK;
  query sim: A023586 → active 1986–1997 (conf 0.7); A038380 → rỗng (không lỗi).
