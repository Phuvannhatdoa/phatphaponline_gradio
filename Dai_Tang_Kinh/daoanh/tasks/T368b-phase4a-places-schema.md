---
id: T368b
title: "Phase 4a: Places Schema Consolidation (places, places_dila, namevi_map_places)"
status: pending
created: 2026-10-13
updated: 2026-10-13
parent: T367
depends_on: []
blocked_by: []
done_when:
  - "Consolidated `places` table created with source tracking (DILA|VPS|TTL|admin)"
  - "places_dila merged into places (no data loss, audit trail kept)"
  - "namevi_map_places merged/mapped into places.name_vi (or linked via crosswalk)"
  - "All foreign keys and indexes created"
  - "Migration rollback script documented"
  - "Schema validated via PRAGMA commands"
  - "Code committed with test results"
---

## Context

**Lý do tách khỏi T368:** T368 ban đầu gộp cả person-entity tables
(person_activity, passage_entity_mention, entity_merge_log) và place-entity
tables (places, places_dila, namevi_map_places) trong cùng một task. Theo
yêu cầu sửa spec Phase 4 Bước 0 (Admin approved Option A), hai phạm vi này
được tách ra để dễ audit và dễ rollback độc lập.

**Current State:** Nhiều bảng places rời rạc — `places`, `places_dila`,
`namevi_map_places` (và có thể `places_pending`, `places_vps` tùy DB thực tế).
Cần audit số liệu thực tế trong `data/lineage.db` trước khi viết migration
script (không đoán số liệu).

---

## Scope

### 1. Audit bảng places hiện có

Trước khi migrate, chạy audit thực tế:
```bash
sqlite3 data/lineage.db ".tables" | grep -i place
sqlite3 data/lineage.db "SELECT COUNT(*) FROM places_dila"
sqlite3 data/lineage.db "SELECT COUNT(*) FROM namevi_map_places"
```
Ghi số liệu thực tế vào báo cáo trước khi viết script di chuyển dữ liệu.

### 2. Tạo bảng `places` hợp nhất

```sql
CREATE TABLE IF NOT EXISTS places (
    id TEXT PRIMARY KEY,  -- PK: "PL000000001"
    name_zh TEXT NOT NULL,
    name_vi TEXT,
    name_en TEXT,
    latitude REAL,
    longitude REAL,
    source TEXT NOT NULL,  -- 'DILA' | 'VPS' | 'TTL' | 'admin'
    status TEXT DEFAULT 'verified',  -- 'verified' | 'pending' | 'deprecated'
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (name_zh, source)
);

CREATE INDEX IF NOT EXISTS idx_places_source ON places(source);
CREATE INDEX IF NOT EXISTS idx_places_name_zh ON places(name_zh);
```

### 3. Merge `places_dila` + `namevi_map_places` vào `places`

- Import `places_dila` → `places` với `source='DILA'`.
- Map `namevi_map_places` (tên Việt do ZQ/TTL cung cấp) vào `places.name_vi`,
  giữ nguồn rõ ràng (không gán tên Việt cho nguồn DILA — theo quy tắc ZQ
  trong `daoanh/CLAUDE.md`).
- Idempotent: dùng `INSERT OR IGNORE` / `UNIQUE (name_zh, source)`, có dry-run
  và rollback script.

### 4. Rollback Script

```sql
-- Rollback T368b places migration
-- Chỉ drop bảng places MỚI nếu nó được tạo bởi migration này và chưa có
-- dữ liệu khác phụ thuộc (kiểm tra FK từ person_activity trước khi drop).
DROP TABLE IF EXISTS places;
```

---

## Testing & Verification

```bash
cd daoanh
sqlite3 data/lineage.db ".schema places" > docs/sessions/<date>/places_schema_before_t368b.sql
python -X utf8 scripts/t368b_create_places_table.py --dry-run
python -X utf8 scripts/t368b_verify_schema.py
```

- [ ] `places` table created with all columns
- [ ] places_dila data merged, 0 rows lost (conservation check: before == after)
- [ ] namevi_map_places mapped, source tagged correctly (not DILA)
- [ ] Rollback script tested (drops cleanly, no orphan FK from person_activity)

---

## Deliverables

1. `daoanh/scripts/t368b_create_places_table.py`
2. `daoanh/scripts/t368b_rollback.sql`
3. `daoanh/scripts/t368b_verify_schema.py`
4. `daoanh/docs/sessions/<date>/places_schema_before_t368b.sql` — backup
5. `daoanh/docs/sessions/<date>/T368b_test_results.md`

---

## Dependencies & Unblocks

**Depends on:** None (independent)
**Unblocks:** T368 (nếu `person_activity.place_id` cần FK tới `places` đã consolidate), T369 place-of-origin import

---

## Notes

- Không sửa raw DILA places data để vá lỗi UI — bảng `places` mới chỉ là
  lớp hợp nhất (DB PTDA), raw source giữ bất biến.
- Idempotent, có dry-run + backup tự động trước khi ghi DB thật, theo quy
  tắc migration bắt buộc trong `daoanh/CLAUDE.md`.

---

**Ready for daoanh-debugger implementation?** ✓
