---
id: T97
title: "Timeline / Event Evidence Layer"
module: Timeline / Event Evidence
priority: high
status: done
depends_on: [T14, T23, T69, T96]
created: 2026-09-05
updated: 2026-09-05
phase_done: "Phase 0+4 (Build 1) + Phase 1+2+3 (Build 2) done"
done_when: >
  Tab Niên Đại hiển thị time mention có evidence (nguồn + span) theo entity;
  Tab Sự Kiện hiển thị event record độc lập tái dùng được;
  mọi mốc thời gian đều có precision (exact_year / reign_era / relative / unknown);
  không có năm tự sinh, không ghi đè raw source;
  API trả về empty-state thay vì null/undefined khi entity chưa có data.
---

# T97 — Timeline / Event Evidence Layer

## Mục tiêu

Xây dựng lõi dữ liệu evidence-first cho hai tab Niên Đại và Sự Kiện.
Tái sử dụng tối đa dữ liệu DILA + CBETA + Marcus đã có trong hệ thống;
không tự tạo historical fact, không copy dữ liệu giữa hai tab.

## Bối cảnh & Phê chuẩn

**Phê chuẩn ngày 2026-09-05** sau thảo luận về prompt Plan Agent.
Kế hoạch chi tiết: `docs/sessions/2026-09-05_T97_timeline-event-evidence-plan.md`

**Nguyên tắc cứng:**
- Raw DILA/CBETA không được bị ghi đè
- Mốc relative / dynasty_period / unknown không được ép thành CE year
- Một time mention ≠ event; một co-mention ≠ relation
- AI output chỉ là candidate, không phải fact
- Niên Đại và Sự Kiện dùng chung core data, không copy record

## Phases

### Phase 0 — Data audit (Plan Agent)
- Đọc kiến trúc thật (CLAUDE.md, app.py, lineage.db)
- Kiểm kê Tab Niên Đại / Tab Sự Kiện đọc từ đâu hiện tại
- Xác minh DILA Time Authority, CBETA passage, Marcus relation
- POC Thiếu Lâm Tự: tìm ID, raw desc, CBETA ref, entity mapping
- **Output:** `docs/sessions/2026-09-05_T97_timeline-event-evidence-plan.md`
- **Gate:** Admin review Verified findings → APPROVED trước khi Build

### Phase 1 — Source/passage/entity evidence foundation
- Bổ sung/chuẩn hoá bảng `sources`, `event_evidence`
- Link `time_mention_id` trong `event_evidence`
- Không import bulk, không xóa data cũ

### Phase 2 — Deterministic time mention parser + DILA mapping
- Parser regex cho exact year, reign era, relative, dynasty period
- Map `北魏太和19年` → CE 495 chỉ khi có DILA Time Authority local
- Output: `extraction_method=regex_rule` hoặc `authority_mapping`

### Phase 3 — Event candidate workflow
- UI admin tạo/duyệt event candidate
- Status: candidate → reviewed / disputed / rejected
- Mỗi event có ≥1 evidence trỏ về source span cụ thể

### Phase 4 — UI Timeline / Event tabs
- Tab Niên Đại: query view theo entity, sort chronological
- Tab Sự Kiện: hồ sơ event độc lập, filter by status/type
- Empty-state khi chưa có data (không lỗi)

## Taxonomy bắt buộc

**Time precision:** `exact_day | month | year | year_range | reign_era | dynasty_period | relative | unknown`

**Event status:** `candidate | reviewed | disputed | rejected`

**Extraction method:** `imported | regex_rule | authority_mapping | ai_assisted | editorial`

## Schema tối thiểu đề xuất

```
sources          : source_id, provider, title, url, version, license, attribution
time_mentions    : mention_id, source_record_id, raw_time_zh, normalized_start,
                   normalized_end, precision, time_authority_id, extraction_method, confidence
events           : event_id, event_type, title_zh, title_vi, start, end, precision,
                   extraction_method, review_status, confidence
event_entities   : event_id, entity_id, role (subject/participant/place/text/institution)
event_evidence   : event_id, time_mention_id, passage_or_source_record,
                   exact_span, source_ref, evidence_type, reviewer_note
translations     : translation_id, source_segment_id, lang, content,
                   translation_status, model_or_editor, created_at
```

Ưu tiên adapter/mapping với bảng hiện có trước khi tạo bảng mới.

## Acceptance criteria

- [x] Mọi timeline record mở được nguồn/evidence (không null)
- [x] Không duplicate event từ cùng source nói lại một việc
- [x] Không có năm tự sinh (CE year không có authority mapping)
- [x] Không ghi đè raw Hán văn gốc
- [x] Niên Đại và Sự Kiện không copy record
- [x] Trang không lỗi khi entity chưa có time/event data
- [x] API không lộ undefined/null (trả empty array)
- [x] Test cases: exact year, dynasty, relative date, missing source,
      conflicting records, duplicate evidence

## Non-goals (Task này KHÔNG làm)

- Full-corpus event extraction
- Dịch hàng loạt bằng AI
- Redesign toàn bộ UI
- Crawl/import Phật Quang Sơn
- Thay database engine/framework
- Graph visualization mới

## Blockers hiện tại

- ~~**[GATE]** Phase 0 plan chưa được Admin review~~ — Admin APPROVED 2026-09-05, Build bắt đầu
- ~~**[DATA]** DILA Time Authority = 0 rows~~ — `time_periods` có 117,429 rows (CLAUDE.md sai); 115,921 có start_year
- ~~**[ARCH]** Tab Niên Đại / Tab Sự Kiện đọc từ đâu chưa xác minh~~ — Phase 0 audit xong:
  - Tab Niên Đại: `/api/places/<id>/timeline` + `place_timeline_events` + Wikidata — WORKING
  - Tab Sự Kiện: stub `_renderPendingTab` — Build 1 DONE (API + UI)

## Build log

- **Build 1 (2026-09-05):** Phase 0 audit + Tab Sự Kiện (Phase 4):
  - Backend: `GET /daoanh/api/places/<id>/events` (nexus_events + event_text_link)
  - Frontend: `loadSukienTab` + `renderSukienTab` thật (2 section: monks + CBETA refs)
  - Rollback: `git revert 45e6c1d`
  - Session: `docs/sessions/2026-09-05_T97_build1_sukien_tab.md`

- **Build 2 (2026-09-05):** Phase 1+2+3 — Schema + Parser + Event Candidate Admin:
  - `scripts/t97_schema_migrate.py` — 4 tables (time_mentions, events, event_entities, event_evidence)
  - `scripts/t97_parse_time_mentions.py` — regex parser + DILA map + seed 3530 events
  - API: `GET /daoanh/api/events`, `PATCH /daoanh/api/events/<id>`, `GET /api/places/<id>/time-mentions`
  - `admin/events.html` — review UI (candidate/reviewed/disputed/rejected)
  - Rollback code: `git revert HEAD`; rollback DB: `python scripts/t97_schema_migrate.py --revert`
  - Session: `docs/sessions/2026-09-05_T97_build2_phase2_3.md`
