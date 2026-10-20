# CBETA Migration Rollout Plan — Alignment Schema

**Ngày:** 2026-09-04  
**Mục tiêu:** Migrate từ ordinal mapping sang passage-ID-based alignment  
**Phạm vi:** Toàn bộ bảng `passage` + thêm schema mới  
**Gate:** Cần owner approval trước khi chạy Phase 2+

---

## Overview

```
Phase 0: Audit (read-only)      → 1 tuần
Phase 1: Schema creation        → 2 ngày (no data change)
Phase 2: T50n2060 pilot repair  → 1 tuần (1 work)
Phase 3: Validation & QA        → 3 ngày
Phase 4: Other priority works   → theo priority
Phase 5: Full corpus migration  → 2–4 tuần
```

---

## Phase 0 — Audit (Read-only, không cần approval)

**Chạy:** `python scripts/audit_cbeta_corpus.py`

Kết quả cần có:
- [ ] Tổng số passages, % đã dịch
- [ ] Distribution theo source/work
- [ ] Passages quá dài (> 2000 chars)
- [ ] Duplicate raw_text
- [ ] vi_text suspicious (ratio, Han text leakage)
- [ ] Orphan entity mentions

**Deliverable:** `docs/cbeta-corpus-audit-results-{date}.md`

**Gate:** Không cần approval, chỉ read.

---

## Phase 1 — Schema Creation (Không đụng data cũ)

### Migrations (additive only):

```sql
-- Migration 001: Add text_passages table
CREATE TABLE IF NOT EXISTS text_passages (
    passage_id          TEXT PRIMARY KEY,
    work_id             TEXT NOT NULL,
    source_system       TEXT NOT NULL DEFAULT 'CBETA',
    canonical_ref       TEXT,
    juan                TEXT,
    sequence_no         INTEGER,
    original_zh         TEXT NOT NULL,
    raw_zh_hash         TEXT NOT NULL,
    segmentation_method TEXT,
    tei_anchor_start    TEXT,
    tei_anchor_end      TEXT,
    source_url          TEXT,
    source_version      TEXT,
    import_run_id       TEXT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Migration 002: Add translation_segments table
CREATE TABLE IF NOT EXISTS translation_segments (
    translation_id      TEXT PRIMARY KEY,
    work_id             TEXT NOT NULL,
    language            TEXT DEFAULT 'vi',
    translation_text    TEXT NOT NULL,
    translator_type     TEXT,
    model_name          TEXT,
    prompt_version      TEXT,
    source_passage_ids  TEXT,
    translation_status  TEXT DEFAULT 'draft',
    review_status       TEXT DEFAULT 'pending',
    reviewer            TEXT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Migration 003: Add alignment table
CREATE TABLE IF NOT EXISTS passage_translation_alignment (
    alignment_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    passage_id          TEXT NOT NULL,
    translation_id      TEXT NOT NULL,
    alignment_type      TEXT NOT NULL,
    source_start_offset INTEGER,
    source_end_offset   INTEGER,
    confidence          REAL DEFAULT 0.5,
    alignment_method    TEXT,
    review_status       TEXT DEFAULT 'pending',
    reviewer            TEXT,
    note                TEXT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (passage_id) REFERENCES text_passages(passage_id),
    FOREIGN KEY (translation_id) REFERENCES translation_segments(translation_id)
);

-- Migration 004: Add hash column to existing passage table
ALTER TABLE passage ADD COLUMN raw_zh_hash TEXT;
ALTER TABLE passage ADD COLUMN passage_id_ref TEXT; -- link to text_passages
ALTER TABLE passage ADD COLUMN segmentation_method TEXT DEFAULT 'punctuation';
```

**Rollback:** DROP các tables mới, DROP columns mới (nếu SQLite hỗ trợ).

**Gate:** Cần review migration SQL trước khi chạy.

---

## Phase 2 — T50n2060 Pilot Repair

**Điều kiện bắt đầu:**
- [ ] Phase 0 audit hoàn thành
- [ ] Phase 1 schema đã tạo
- [ ] Backup DB xác nhận
- [ ] Owner approval

**Các bước:**
1. Extract raw passages T50n2060 → segment → tạo `text_passages` records
2. Re-translate với segment-aware prompt (batch 3–5 segments)
3. Validate responses (xem `alignment-test-cases.md`)
4. Tạo `translation_segments` và `passage_translation_alignment`
5. Test TC-001 đến TC-011
6. Update UI để đọc từ alignment table khi có

**Báo cáo sau pilot:**
- Số passages processed
- Số alignment records created
- % test cases passed
- Issues found

---

## Phase 3 — Validation & QA

Sau pilot T50n2060:
- So sánh bản dịch mới vs cũ (semantic similarity check)
- Human review ít nhất 10 đoạn ngẫu nhiên
- Verify TC-001 (Hán 41 phải đúng nội dung)
- Performance test: rendering 54+ aligned segments
- A/B test UI: alignment-based hover vs ordinal hover

---

## Phase 4 — Priority Works

Sau khi T50n2060 pilot thành công:

| Priority | Work | Lý do |
|---------|------|-------|
| P1 | T51n2076 | Nhiều entity mentions nhất |
| P2 | T50n2059 | Cao Tăng Truyện bản khác |
| P3 | Other T50 | Cùng loại corpus |
| P4 | X series | Xu zangjing |
| P5 | Còn lại | Full sweep |

---

## Phase 5 — Full Corpus Migration

**Điều kiện:**
- Phase 4 stable với ít nhất 3 works
- Automated pipeline hoạt động không cần manual intervention
- Test suite pass > 95%
- Human reviewer workflow setup

**Không run Phase 5 trước:**
- Backup strategy hoàn chỉnh
- Rollback tested
- Monitoring in place (track alignment errors)
- Có at least 1 human reviewer available

---

## Rollback Plan

| Phase | Rollback |
|-------|---------|
| Phase 1 | DROP new tables (no data loss) |
| Phase 2 | DELETE từ new tables, giữ old passage table nguyên |
| Phase 3+ | Restore from backup, hoặc set alignment_status='reverted' |

Không DROP `passage` table ở bất kỳ phase nào. Chỉ add, không overwrite.

---

## Không chạy destructive operations nếu chưa:

- [ ] `cp data/lineage.db data/lineage.db.backup_$(date +%Y%m%d_%H%M%S)`
- [ ] Test migration SQL trên bản copy trước
- [ ] Document số records sẽ bị ảnh hưởng
- [ ] Owner approval (đặc biệt trước Phase 2+)
- [ ] Có rollback script ready

---

*Xem thêm: `cbeta-global-passage-standard.md` · `cbeta-corpus-audit.md` · `t50n2060-repair-plan.md`*
