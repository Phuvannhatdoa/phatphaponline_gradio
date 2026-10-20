---
id: T53
title: "CBETA Content Enhancement"
module: CBETA Content / Translation Pipeline
priority: high
status: pending
depends_on: [T50]
created: 2026-08-26
updated: 2026-08-26
done_when: >
  Top 100 most-clicked refs translated to Vietnamese,
  vi_text populated for 5 imported texts,
  Toh crossref expanded to 50+ texts,
  Aggregate mention stats computed,
  name_normalization expanded to 100+ rules
---

# T53 — CBETA Content Enhancement

> **Lưu ý:** Task này trước đây mang số **T51**, được đổi sang T53 vào 2026-08-26
> để nhường số T51 cho chức năng mới "Nhân Vật Học Portal".

## Mục tiêu
Mở rộng nội dung CBETA: batch translate, expand crossrefs, build aggregate analytics.

## Audit Findings (2026-08-26)
- `cbeta_ref_passages`: 46 translated → need **batch translate top 100 refs**
- `passage.vi_text`: 0/7,563 populated → need **fill for 5 imported texts**
- `toh_cbeta_crossref`: 10/3,122 texts → need **expand to 50+**
- `name_normalization`: 17 rules → need **expand to 100+**
- No aggregate mention stats → need **build "Most Mentioned Places"**

## Subtasks

### T53a — Batch Translate Top 100 Refs
- Script: `scripts/t53_batch_translate.py`
- Uses existing Gemini pipeline from app.py
- Priority: most-clicked CBETA refs first
- Rate limit: 4 seconds between calls
- Result: 100 → Vietnamese text

### T53b — Fill Passage vi_text
- Script: `scripts/t53_fill_passage_vi.py`
- Action: Batch translate `passage.raw_text` → `passage.vi_text` for 5 imported texts
- Result: Full Vietnamese display available

### T53c — Expand Toh Crossref
- Script: `scripts/t53_expand_toh_crossref.py`
- Action: Add 40+ Tibetan-Hán canon mappings (Heart Sutra, Diamond Sutra, etc.)
- Source: 84000.co API + academic references
- Result: 10 → 50+ cross-canon links

### T53d — Build Aggregate Mention Stats
- Script: `scripts/t53_build_aggregates.py`
- Action: Compute `cbeta_place_mention_stats` and `cbeta_person_mention_stats`
- Source: `passage_entity` (378K links) + `passage` (7,563 texts)
- Result: Pre-computed analytics tables

### T53e — Expand Name Normalization
- Script: `scripts/t53_expand_name_norm.py`
- Action: Add 80+ rules to `name_normalization` table
- Source: Common Buddhist name variants from DILA + CBETA
- Result: Better name matching accuracy

## DB Schema Changes
```sql
CREATE TABLE IF NOT EXISTS cbeta_place_mention_stats (
    place_id TEXT PRIMARY KEY,
    mention_count INTEGER,
    top_texts TEXT,
    last_updated TEXT
);
CREATE TABLE IF NOT EXISTS cbeta_person_mention_stats (
    person_id TEXT PRIMARY KEY,
    mention_count INTEGER,
    top_texts TEXT,
    last_updated TEXT
);
```

## API Changes
- New: `GET /admin/cbeta/aggregates` — mention statistics
- New: `GET /admin/cbeta/batch-translate-status` — translation progress

## Estimated Effort: ~15 hours
