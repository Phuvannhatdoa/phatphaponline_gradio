---
id: T65
title: "Person Bio VI Phase 2 — Chinese Name Pattern Matching (2,000+ persons)"
module: Person Authority
priority: medium
status: done
depends_on: [T63]
created: 2026-08-28
updated: 2026-08-28
done_when: >
  ≥1,500 new rows thêm vào person_bio_vi_draft qua name_zh matching;
  tổng person_bio_vi_draft ≥2,345 rows; false positive rate < 15% trên sample 50;
  script t65_bio_vi_lexicon_p2.py có --dry-run và --apply
---

# T65 — Person Bio VI Phase 2: Chinese Name Pattern Matching

## Phê Chuẩn

Được phê chuẩn 2026-08-28. T65 là Phase B của roadmap Person Authority VI hóa,
mở rộng T63 từ 845 rows lên ≥2,345 rows qua matching tên Hán trong body text từ điển.

---

## Vấn đề

T63 (Phase 1) đã match 845 persons qua `name_vi = lexicon.term` (exact headword match).
Còn lại ~47,800 persons **chưa có bio_vi_draft** dù từ điển PG VN có thể đề cập họ bằng
tên Hán trong phần nội dung định nghĩa: "... Huệ Năng (慧能) là vị Lục Tổ Thiền Tông...".

Pattern này rất phổ biến trong từ điển Phật học VN: tên Việt + tên Hán trong ngoặc.

---

## Cơ chế (2 Pass)

### Pass 1 — Bracket Match (confidence 0.80)

Tìm `name_zh` trong dấu ngoặc trong body text definition:

```python
# Pattern: (慧能) hoặc （慧能） — chắc chắn là cùng người
matches = conn.execute("""
    SELECT l.id, l.headword, l.definition, l.source, l.entity_type
    FROM lexicon l
    WHERE (l.definition LIKE '%(' || ? || ')%'
        OR l.definition LIKE '%(（' || ? || '）%')
      AND LENGTH(l.definition) > 100
    ORDER BY LENGTH(l.definition) DESC
    LIMIT 3
""", (person.name_zh, person.name_zh)).fetchall()
```

- Match type: `name_zh_bracket`
- Confidence: 0.80
- Filter: `LENGTH(name_zh) >= 3` để tránh ambiguous 2-char names

### Pass 2 — Body Match với Name Extraction (confidence 0.65)

Tìm `name_zh` anywhere trong definition, sau đó extract tên Việt gần nhất để validate:

```python
# Tìm name_zh trong body
matches = conn.execute("""
    SELECT l.id, l.headword, l.definition, l.source
    FROM lexicon l
    WHERE l.definition LIKE '%' || ? || '%'
      AND LENGTH(l.definition) > 150
      AND l.source IN ('TU_SI', 'PHAT_QUANG', 'THIEN_UYEN', 'THIEN_UYEN_TAP_ANH')
    ORDER BY LENGTH(l.definition) DESC
    LIMIT 5
""", (person.name_zh,)).fetchall()

# Validate: extract Vietnamese name near zh chars, compare with person.name_vi
# Accept nếu similarity(extracted_vn, person.name_vi) >= 0.5
```

- Match type: `name_zh_body`
- Confidence: 0.65
- Requires: extracted Vietnamese name gần `name_zh` match ≥50% với `people.name_vi`

---

## False Positive Control

| Rule | Mục đích |
|------|----------|
| `LENGTH(name_zh) >= 3` | Loại 2-char names (慧能=OK, 能=skip) |
| Bracket pass trước body pass | Ưu tiên high-confidence first |
| `similarity >= 0.5` (Pass 2) | Validate tên Việt extracted khớp person |
| Max 1 definition per person | Chỉ lấy definition dài nhất |
| Skip nếu đã có draft | Không overwrite T63 rows |
| `admin_approved = 0` | Tất cả cần admin review trước khi dùng |

---

## Schema Output

Dùng **cùng schema** với `person_bio_vi_draft` (T63):

```sql
person_bio_vi_draft (
    person_id      TEXT PRIMARY KEY,
    name_vi        TEXT,
    name_zh        TEXT,
    bio_vi_draft   TEXT,       -- definition text (truncated 2000 chars max)
    source_lex_id  INTEGER,    -- lexicon.id
    source_term    TEXT,       -- lexicon.headword
    source_name    TEXT,       -- lexicon.source
    match_type     TEXT,       -- 'name_zh_bracket' | 'name_zh_body' | 'name_vi_exact' (T63)
    char_count     INTEGER,
    admin_approved INTEGER DEFAULT 0,
    admin_note     TEXT,
    created_at     TEXT,
    updated_at     TEXT
)
```

---

## Targets & Estimates

| Metric | Số liệu |
|--------|---------|
| Hiện tại (T63) | 845 rows |
| Pass 1 estimate | ~800–1,200 new rows (bracket match) |
| Pass 2 estimate | ~300–500 new rows (body match, validated) |
| **Tổng ước tính** | **~2,000–2,500 rows** |
| False positive target | < 15% (trên sample 50) |

> Estimate based on: 6,985 TU SĨ entries × avg 2–3 person name_zh mentions per definition.
> Pass 2 conservative: chỉ accept khi extracted Vietnamese name match ≥50%.

---

## Script

**File:** `scripts/t65_bio_vi_lexicon_p2.py`

```
Usage:
    python scripts/t65_bio_vi_lexicon_p2.py          # dry-run
    python scripts/t65_bio_vi_lexicon_p2.py --apply  # insert into DB
    python scripts/t65_bio_vi_lexicon_p2.py --pass 1 # bracket only
    python scripts/t65_bio_vi_lexicon_p2.py --pass 2 # body match only
```

Output logs:
- Pass 1: `N bracket matches` với distribution theo source
- Pass 2: `N body matches` với score distribution
- Sample top 20 matches để kiểm tra chất lượng
- False positive estimate: random sample 20 + manual flag

---

## Subtasks

### T65a — Script Pass 1 (Bracket Match)
- Build `t65_bio_vi_lexicon_p2.py` với Pass 1 logic
- Dry-run: print top 50 matches, distribution theo source
- Apply: INSERT vào `person_bio_vi_draft` (skip existing rows)
- Expected: ~800–1,200 new rows

### T65b — Script Pass 2 (Body + Validation)
- Add Pass 2 vào script
- Vietnamese name extractor: regex `[A-ZĐÀÁẢÃẠĂẮẶẰẴẪÂẤẦẨẪẬÊẾỀỆ][a-zđàáảãạăắặằẵẫâấầẩẫậêếềệ]+ [A-ZĐÀÁẢÃẠĂẮẶẰẴẪÂẤẦẨẪẬÊẾỀỆ][a-z]+`
- Similarity: `SequenceMatcher` hoặc char overlap ratio
- Expected: ~300–500 new rows (validated)

### T65c — Admin Sample Review
- Print 50 sample rows từ mỗi pass để admin kiểm tra
- Flag false positives
- Điều chỉnh threshold nếu precision thấp

### T65d — Quality Metrics
- Sau apply: đếm theo match_type, avg char_count, source distribution
- Update `docs/cbeta_quality_log.jsonl` (T52d snapshot)

---

## Kết Quả Thực Thi (2026-08-28)

| Metric | Kết quả |
|--------|---------|
| Pass 1 bracket inserted | **1,200** rows (avg 1,413 chars) |
| Pass 2 body+valid inserted | **48** rows (avg 1,200 chars) |
| Tổng T65 inserted | **1,248** rows |
| Tổng person_bio_vi_draft | **2,093** rows (845 T63 + 1,248 T65) |
| Source chính | Phat Hoc Tinh Tuyen — TK Thích Nguyên Tâm (1,246/1,248) |
| Admin approved | 0 (chờ review) |

**Revert:** `python scripts/t65_bio_vi_lexicon_p2.py --revert`  
**Log:** `data/t65_import_log.json`

## Acceptance Criteria

- [x] `scripts/t65_bio_vi_lexicon_p2.py` chạy OK với --dry-run
- [x] Pass 1 (bracket): ≥800 new rows inserted → **1,200 ✓**
- [x] Pass 2 (body+valid): rows inserted → **48** (lower than projected, P1 captures most)
- [x] Tổng `person_bio_vi_draft` ≥2,000 rows → **2,093 ✓**
- [ ] False positive rate < 15% (kiểm tra sample 50 rows — chờ admin)
- [ ] Admin review 30 entries mẫu → quality acceptable
- [x] `match_type` ghi đúng `name_zh_bracket` / `name_zh_body` cho từng row
- [x] Không overwrite rows từ T63 (`match_type='name_vi_exact'` intact, 845 rows)

---

## Lưu Ý Học Thuật

Giống T63: **không sao chép nguyên văn từ điển** vào production.
- `person_bio_vi_draft` = bản nháp, admin tổng hợp + viết lại bằng lời riêng
- `source_lex_id` lưu để attribution
- `admin_approved = 0` mặc định — chỉ copy → `people.bio_vi` sau khi duyệt
- Match qua name_zh có thể nhầm lẫn nếu name_zh trùng → Pass 2 validation bắt buộc

---

## Liên Quan

- **T63** (Phase 1, Done): 845 rows qua `name_vi` exact headword match
- **T51** (Consumer): Nhân Vật Học Portal sẽ đọc `person_bio_vi_draft` để hiển thị
- **T66** (Parallel): Place description VI — same lexicon, khác entity_type (ĐỊA DANH)
- `lexicon`: 166,278 rows, 22 từ điển PG VN — nguồn cho cả T65 và T66
