---
id: T82
title: "T82 — Consolidation + Data-Lock: Hợp nhất vn_person_events, Checksum, Data Dictionary, Wire UI"
module: Timeline / Data Governance
priority: high
status: done
depends_on: [T79, T80, T81]
created: 2026-09-01
updated: 2026-09-01
completed: 2026-09-01
done_when: vn_person_events source=None legacy được hợp nhất chuẩn; checksum lock (streaming, zero-RAM) cho các bảng lớn; docs/DATA_DICTIONARY.md tạo; wire UI Thời kỳ hoạt động + timeline place; dashboard cập nhật
---

# T82 — Consolidation + Data-Lock

## Mục tiêu

"Hardening" sau chuỗi T79–T81: bảo vệ và chuẩn hoá dữ liệu timeline vừa build thay vì mở thêm tính năng mới.
Phù hợp toàn bộ constraint dự án: **Zero-RAM**, **Code Preservation**, **Rollback thuận tiện**, **Handover admin "vô não"**, **SSOT bền vững 2026–2045**.

## Bước 1 — Hợp nhất `vn_person_events` (ExploreTemporal Track)

- Hiện tại có **45 rows `source=None`** (legacy pre-existing) + 203 `dila_person_regex` + 5,103 `dila_active_regex`.
- Hợp nhất các row `source=NULL` về source chuẩn (vd `legacy_migration`), gắn `confidence`/`source_ref` khi suy luận được từ context.
- Chuẩn hoá `event_type` taxonomy chung: `birth`, `death`, `active`, `floruit`.
- **Additive/reversible**: `scripts/t82_merge_events.py` (`--dry-run`/`--apply`/`--revert`), backup snapshot trước khi apply.
- **Rollback:** khôi phục source=NULL về trạng thái trước.

## Bước 2 — Data-Lock Checksum (Zero-RAM)

- `scripts/t82_checksum.py` (hoặc `checksums.py`): scan tuần tự từng bảng lớn — **byte-offset/streaming**, KHÔNG nạp hết bảng vào RAM (Zero-RAM Principle).
- Ghi `data/checksums.json`: `{table: {row_count, sha256, updated_at}}`.
- `--verify`: đọc lại + so sánh → phát hiện regression ngay sau mỗi phiên build.
- Dùng cho các bảng: `people`, `places`, `places_dila`, `place_timeline_events`, `vn_person_events`, `place_person_bibl`, `entity_claims`.
- Neutral với data bất biến (raw) + cho phép "expected-change registry" cho bảng tăng dần.

## Bước 3 — Data Dictionary (Handover "vô não")

- `docs/DATA_DICTIONARY.md`: mô tả các bảng timeline vừa tạo (vn_person_events, place_timeline_events, source, confidence).
- Ghi rõ: ý nghĩa event_type, format `（YYYY）`, confidence từng nguồn, **rollback SQL 1-lệnh cho từng task** (T79/80/81/82).
- Đúng triết lý AGENTS.md: "giải thích logic vô não trước".

## Bước 4 — Wire UI (additive, không đụng logic cũ)

- Thêm tab "Thời kỳ hoạt động" trong bio panel đọc `vn_person_events` (active/floruit từ T81) + tab timeline place từ `place_timeline_events` (founding từ T80).
- Chỉ thêm render layer, KHÔNG sửa endpoint/lưu trữ cũ.

## Acceptance Criteria

- [x] Script `t82_merge_events.py` chạy --dry-run / --apply / --revert (Step1 — 45 legacy merged)
- [x] 0 rows `source=NULL` còn lại trong `vn_person_events` (45 → `legacy_ttl`)
- [x] `t82_checksum.py` sinh `data/checksums.json` cho 7 bảng lớn, `--verify` PASS (Step2)
- [x] `docs/DATA_DICTIONARY.md` tạo — đủ event_type, confidence, rollback SQL 1-lệnh (Step3)
- [x] UI tab "Thời kỳ hoạt động" + timeline place render dữ liệu thật (Step4 — additive render trong bio panel)
- [x] Dashboard cập nhật: build_progress_data.py chạy lại, task T82 hiển thị

## Rollback

```sql
-- Bước 1 (merge events):
DELETE FROM vn_person_events WHERE source = 'legacy_migration';  -- nếu muốn xoá bản hợp nhất riêng
-- Khôi phục source=NULL các row legacy từ snapshot backup t82
```

## Liên quan

- **T79** (done): death events (203)
- **T80** (done): founding coverage (55, temple 27.4%)
- **T81** (done): active/floruit (5,103)
- **T78/T72**: legal firewall + frozen contract — checksum lock bổ trợ

## Ghi chú cho admin

- Đây là task "củng cố" → giá trị dài hạn: dữ liệu được khoá, phát hiện regression, dễ rollback, admin hiểu "vô não".
- Mỗi bước đều có revert riêng → commit back thuận tiện.

## Tiến độ build (2026-09-01)

- **Step1 DONE:** `t82_merge_events.py` — 45 legacy rows `source=NULL` → `legacy_ttl`, confidence→1.0,
  `Birth`/`Death`→`birth`/`death` (khớp T79/T81), giữ KeyLifeEvent/Contribution/PhilosophicalStance.
  Backup `data/t82_legacy_backup.json` + round-trip revert verified. 0 source=NULL còn lại.
- **Step2 DONE:** `t82_checksum.py` — streaming sha256 zero-RAM → `data/checksums.json` cho 7 bảng
  (people, places, places_dila, place_timeline_events, vn_person_events, place_person_bibl, entity_claims); `--verify` PASS.
- **Step3 DONE:** `docs/DATA_DICTIONARY.md` — data dictionary + rollback SQL 1-lệnh cho T79/80/81/82.
- **Step4 DONE:** Wire UI additive trong `places.html`:
  - Thêm block "Thời Kỳ Hoạt Động · Sự Kiện" (`#personEventsBlock` + `#personEventsList`).
  - `selectPerson()` gọi `loadPersonTimeline(dilaId)` → fetch `GET /daoanh/api/persons/<id>`.
  - app.py `api_person_by_id` (line ~12949) thêm trường `timeline`/`timeline_count` đọc `vn_person_events`
    (active/floruit T81, birth/death T79, legacy T82) — additive, KHÔNG đổi field cũ.
  - Reset block khi chọn place (`selectItem`) và khi chọn person khác.
- **Place timeline (T80) đã tự wire sẵn** qua `GET /daoanh/api/places/<id>/timeline` → `static_events` (chứa `dila_founding_phase2`).
