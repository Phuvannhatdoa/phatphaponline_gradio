---
id: T01
title: Seed monk từ persons.json (48K records)
module: DILA Authority
priority: high
status: done
depends_on: []
created: 2026-07-29
updated: 2026-08-17
done_when: namevi-queue API trả phần lớn records có name_vi (>= 90% / 48.412) ✅ ĐÃ THÍCH HỎA
---

# T01 — Seed monk từ persons.json (48K records)

## Mục tiêu
namevi-queue API có 48.412 records nhưng chỉ 335/48.412 có `name_vi`. Cần ETL bulk auto-generate từ persons.json (DILA / Khoá 1) để toàn bộ tên tăng trưởng có phiên âm Hán-Việt.

## Cách tiếp cận
- Đọc persons.json → extract tên Hán + metadata.
- Chạy Hán-Việt transliteration cho từng tên.
- Bulk upsert vào `namevi_map_places` (ưu tiên giữ `approved` hiện có, không ghi đè manual).

## Acceptance criteria (checklist)
- [x] Script ETL đọc persons.json (generator, zero-RAM)
- [ ] Bulk upsert vào namevi_map_places với nguồn ghi rõ `auto`
- [ ] `GET /daoanh/api/admin/namevi-queue` trả phần lớn records có name_vi
- [ ] Không ghi đè 335 records `approved` hiện có
