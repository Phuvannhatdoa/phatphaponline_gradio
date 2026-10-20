---
id: T43
title: Pre-compute Bio Person-Place — Chuyển bio text search thành bảng pre-computed
module: Person Authority
priority: medium
status: done
depends_on: [T40, T41]
created: 2026-08-25
updated: 2026-08-25
done_when: Bảng place_person_bio_cache tồn tại; API persons không cần LIKE query real-time; response time giảm ≥50%
---

# T43 — Pre-compute Bio Person-Place

## Mục tiêu

Hiện tại bio text search chạy real-time mỗi API call:
```sql
SELECT * FROM people WHERE bio LIKE '%少林寺%' OR bio LIKE '%少室寺%' LIMIT 200
```
Với 48,180 rows có bio, mỗi LIKE query mất ~200-500ms. Với nhiều địa điểm đồng thời → chậm.

T43 = chạy 1 lần cho tất cả 59,167 places → lưu kết quả vào `place_person_bio_cache`.

## Background — Phát hiện từ T40 Coverage Analysis

- 47,229 places trong DB **không có bibl** → bio search là nguồn DUY NHẤT cho chúng
- Nhưng bio search real-time không scale: Thiên Thai Sơn request timed out trong test
- Pre-compute giúp: response nhanh + biết trước places nào có kết quả (skip empty)
- Không tăng số links mới, nhưng **tăng reliability + tăng coverage thực tế** (places không timeout)

## Cách tiếp cận

### Script `scripts/precompute_bio_person_place.py`

```python
for place in places_dila (59,167 rows):
    1. Lấy name_variants từ raw_xml (như trong api_places_persons)
    2. LIKE query against people.bio
    3. Classify: is_direct (僧人/住持...) hay indirect (mention only)
    4. Insert vào place_person_bio_cache
    5. Log: places với >0 results vs empty
```

### Schema `place_person_bio_cache`
```sql
CREATE TABLE IF NOT EXISTS place_person_bio_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    place_id TEXT NOT NULL,
    person_id TEXT NOT NULL,
    matched_variant TEXT,
    is_direct INTEGER DEFAULT 0,
    relation_hint TEXT,
    bio_snippet TEXT,
    confidence REAL DEFAULT 0.6,
    indexed_at TEXT DEFAULT (datetime('now')),
    UNIQUE(place_id, person_id)
);
CREATE INDEX IF NOT EXISTS idx_ppbc_place ON place_person_bio_cache(place_id);
```

### Thay đổi API
```python
# TRƯỚC (real-time LIKE):
bio_rows = conn.execute(f"SELECT ... FROM people WHERE bio LIKE ? ...", params)

# SAU (lookup):
bio_rows = conn.execute(
    "SELECT ... FROM place_person_bio_cache ppbc JOIN people p ON p.id=ppbc.person_id WHERE ppbc.place_id=?",
    (place_id,)
)
```

### Refresh strategy
- Chạy script 1 lần full (tất cả 59K places) — có thể mất 30-60 phút
- Re-run khi có `people.bio` update mới (T41 bổ sung birthplace etc.)
- Flag `--since DATE` để re-index incremental

## Yield ước tính

| Metric | Trước T43 | Sau T43 |
|---|---|---|
| Places có bio persons (đã pre-computed) | 0 | ~3,000-8,000 |
| API response time cho Thiên Thai Sơn | Timeout | <100ms |
| Places với 0 bio persons (confirmed) | Unknown | Biết rõ → skip |
| Coverage bio (% places có ≥1 person) | Unknown | ~5-15% ước tính |

## Trade-off
**Pros:** Speed, reliability, predictability  
**Cons:** Cache có thể stale nếu bio data thay đổi (cần invalidation strategy)

## Acceptance criteria
- [x] Script `scripts/precompute_bio_person_place.py` chạy full 59K places
- [x] Bảng `place_person_bio_cache` có dữ liệu (≥10,000 unique person-place pairs)
- [x] API không còn LIKE query real-time trong bio path (cache-first + fallback)
- [x] Response time Thiên Thai Sơn: timeout → <200ms
- [x] Log: bao nhiêu places có ≥1 kết quả vs 0 kết quả
- [x] `--refresh` flag để re-index sau bio update

## Kết quả thực tế (2026-08-25)

| Metric | Kết quả |
|--------|---------|
| place_person_bio_cache total rows | **470,745** |
| Unique places cached | **20,120** |
| Unique persons cached | **40,250** |
| Coverage (places với ≥1 bio person) | ~34% (20,120/59,167) |
| Thời gian chạy | ~30 phút |
| In-memory approach | Tải 48,180 bio persons 1 lần → per-place string matching |

API: cache-first lookup → fallback to real-time LIKE nếu cache rỗng cho place đó.
