# Session Changes — 2026-08-25

## Tóm Tắt
Phiên làm việc tiếp tục từ context cũ (2026-08-24). Hoàn thành T32 Phase 2 — timeline coverage expansion bằng cách fix bug script và thêm 2 class targeted insertions.

## Git Commits

| Hash | Nội dung | Revertable? |
|------|---------|------------|
| `8fc72ee` | feat(T32): Phase 2 expansion — +12 founding dates, 4.55%→4.57% | `git revert 8fc72ee` |

---

## T32 Phase 2 — Timeline Coverage Expansion

### Bug phát hiện

`dila_note_founding_extract.py` line 242 — `re.search(r'[。；\n]', before + after)` là false-negative:
nếu sentence boundary `。` xuất hiện TRƯỚC founding keyword trong cùng câu, script block nhầm.

Ví dụ: "寺內。建於遼大安九年（1093）" → `。` trong before-window → skip sai → 石經處 không được extract dù có founding year rõ ràng.

### Fixes

| File | Thay đổi |
|------|---------|
| `scripts/dila_note_founding_extract.py` | Remove `敕建` khỏi RENOVATION_KW — 敕建 = imperially built/founded, không phải renovation |
| `scripts/t32_expansion.py` | **NEW** — targeted 2-class insert script với UNKNOWN_PAT (exclude 創建年代不詳/無考) |

### DB Changes (place_timeline_events)

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Total rows | 2,731 | 2,743 | +12 |
| Unique places | 2,691 | 2,703 | +12 |
| Coverage | 4.55% | 4.57% | +0.02pp |

| Class | Count | Dila Source |
|-------|-------|-------------|
| Note-founding (CE year + founding KW, blocked by sentence-boundary bug) | 5 | dila_note |
| Dynasty-renovation (founded in named dynasty, renovation CE year caused dynasty script skip) | 7 | dila_dynasty |

### Backfill ceiling
Rule-based extraction đã exhausted ≈4.57-4.6%.
Đạt 5% cần T22 NLP pipeline (blocked by T22.1 Gate 1).

### Backup
`docs/sessions/2026-08-25/lineage_pre_T32_expansion.db.bak` (810MB)

---

---

## T39 — Wikidata P571 Spatial Expansion (2026-08-25, phiên 2)

### Kết quả
- Download: 2,114 Buddhist temples China với P571 từ SPARQL (2,151 raw, 37 dedup)
- Spatial join: 33 matches (Haversine ≤0.5km + name_sim ≥0.4)
- Match rate: 1.5% (thấp hơn dự kiến 65% do scope DILA là Hán truyền classical)
- Insert: 33 rows mới, confidence 0.7-0.85

### DB changes
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Wikidata rows | 122 | 155 | +33 |
| Total unique places | 2,703 | 2,715 | +12 |
| Coverage | 4.57% | 4.59% | +0.02pp |

### Scripts tạo mới
- `scripts/t39_wikidata_p571_download.py`
- `scripts/t39_spatial_join.py`
- `scripts/t39_insert_timeline.py`

### Backup
`docs/sessions/2026-08-25/lineage_pre_T39.db.bak` (862MB)

---

## Revert Guide

| Thay đổi | Cách revert |
|---|---|
| Code changes | `git revert 8fc72ee` |
| DB changes | Restore từ `docs/sessions/2026-08-25/lineage_pre_T32_expansion.db.bak` |

---

## T47/T48/T49 — Place VI_NAME Quality Pipeline (2026-08-25, phiên 3)

### Phân tích thực hiện

Test thực tế trên DB:
- 118,293 VI_NAME entries, tất cả conf=0.5
- Lexicon 107,172 unique normalized terms
- T47 exact match (case-insensitive): 5,992 entries = 5.1%
- T48 regex test: 10,139 pairs extracted, 709 match DILA exact (chất lượng thấp do regex)
- Dự báo sau T49+T47+T48: conf≥0.65 cho 100% places, conf≥0.75 cho ~10%

### Tasks tạo mới

| Task | Tên | Priority | Status |
|------|-----|----------|--------|
| T47 | Place VI_NAME Verification — Lexicon Cross-Reference | high | pending |
| T48 | Place VI_NAME Reverse Index — Hán→Việt từ definitions | medium | pending |
| T49 | Place VI_NAME Pipeline Fix — Title Case + Buddhist suffixes | high | pending |

### Thứ tự implement

```
T49 (fix format: 0.5→0.65, 118K entries)
  ↓
T47 (verify vs lexicon: 0.65→0.75/0.85, ~6K entries)
  ↓
T48 (reverse index từ definitions: ~200-400 pairs mới)
```

### Ceiling phân tích

| Sau task | conf≥0.65 | conf≥0.75 | conf≥0.85 |
|----------|-----------|-----------|-----------|
| Hiện tại | 0% | 0% | 0% |
| Sau T49 | ~100% | 0% | 0% |
| Sau T49+T47 | ~100% | ~10% | ~3.3% |
| Sau T49+T47+T48 | ~100% | ~10.5% | ~3.3% |
| Sau T22 NLP (future) | ~100% | ~50%+ | TBD |

**Kết luận:** Ceiling không NLP là ~10% verified (conf≥0.75). Cần T22 NLP gate để vượt 50%.

### Files thay đổi

| File | Thay đổi |
|------|---------|
| `tasks/T47-place-vi-name-lexicon-verify.md` | NEW |
| `tasks/T48-place-vi-reverse-index-lexicon.md` | NEW |
| `tasks/T49-place-vi-character-pipeline-fix.md` | NEW |
| `docs/tasktodo.md` | +3 tasks, 45→48 tasks total |
| `data/progress_data.json` | Rebuilt (49 tasks on board, done=32) |
