---
id: T82
title: "Schema Freeze + Data Lock Status (release gate)"
module: Data Governance / Release
priority: high
status: done
depends_on: []
created: 2026-09-11
updated: 2026-09-11
completed: 2026-09-11
done_when: >
  docs/SCHEMA_FREEZE.md mô tả toàn bộ 137 tables + 4 views với phân lớp freeze;
  checksum baseline regenerate data/checksums.json (--verify PASS);
  expected-change registry (row thay đổi hợp lệ qua HITL) được liệt kê;
  task info + session doc cập nhật, commit scoped revert được.
---

# T82 — Schema Freeze + Data Lock Status

> Lưu ý: task này là **T82 mới** (release gate). Tiền thân `T82-consolidation-data-lock.md`
> (2026-09-01) đã done ở `tasks/backup/`. tasktodo trỏ đúng task mới này.

## Mục tiêu

"Đóng băng schema + audit toàn bộ data trước release" — theo đúng trọng tâm trong `docs/tasktodo.md`.
Phiên read-only: 0 ALTER, 0 INSERT/UPDATE/DELETE, 0 sửa app.py/HTML. Chỉ query + ghi docs.

## Delivery

### 1. Schema snapshot (read-only)
- Quét `sqlite_master` → **137 tables + 4 views**.
- Phân lớp freeze: **RAW 5 · CORE 15 · MAPPING 70 · DERIVED 44 · AUDIT 2 · VIEW 4**.
- Snapshot lưu `data/schema_snapshot.json` (gitignored) — layer + rows từng bảng.

### 2. Checksum baseline (Data-Lock)
- Chạy `scripts/t82_checksum.py` (streaming zero-RAM) → `data/checksums.json`.
- 7 bảng: people 48,673 · places 59,161 · places_dila 59,167 · place_timeline_events 3,688 ·
  vn_person_events 5,351 · place_person_bibl 13,933 · entity_claims 447,885.
- Verify: `python scripts/t82_checksum.py --verify`.

### 3. `docs/SCHEMA_FREEZE.md`
- 137 tables + 4 views phân lớp freeze + quy tắc (0 ALTER/DROP, DERIVED-only cho bảng mới).
- Expected-change registry: person_bio_vi_draft · place_desc_vi_draft · geo_cross_ref ·
  text_reading_log · en_audit_log · lineage_conflicts_v2.
- Release gate: verify_design_compliance (T113) + checksum verify.

## Files tạo
- `docs/SCHEMA_FREEZE.md` (commit)
- `docs/sessions/2026-09-11_t82-schema-freeze.md` (commit)
- `docs/tasktodo.md` — dòng T82 cập nhật (commit)
- `data/checksums.json` + `data/schema_snapshot.json` (gitignored, chỉ trên disk)
- `tasks/T82-schema-freeze-data-lock.md` (file này)

## Build Log

### 2026-09-11 — Build hoàn tất
- Checksum regenerate → 7 bảng OK.
- Schema snapshot → 137 tables + 4 views, phân lớp đúng (RAW 5 / CORE 15 / MAPPING 70 / DERIVED 44 / AUDIT 2).
- SCHEMA_FREEZE.md tạo với placeholder hash.
- Commit build: `a8336fb4` → hash-fill trong docs. Revert: `git revert a8336fb4` (docs-only, không có ALTER/INSERT để revert).

## Acceptance Criteria
- [x] `docs/SCHEMA_FREEZE.md` liệt kê 137 tables + 4 views + phân lớp
- [x] `data/checksums.json` regenerate (7 bảng) — `--verify` PASS
- [x] Expected-change registry trong SCHEMA_FREEZE §5
- [x] tasktodo + session doc cập nhật
- [x] Commit scoped (temp-index), revert thuận tiện `git revert <hash>`