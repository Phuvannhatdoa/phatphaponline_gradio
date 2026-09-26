---
id: T65
title: "Person Bio VI Phase 2 — Chinese Name Pattern Matching (2,000+ persons)"
module: Person Authority
priority: medium
status: pending
depends_on: [T58]
created: 2026-08-27
updated: 2026-08-27
done_when: ≥1,500 additional persons có bio_vi_draft qua Chinese name matching; tổng person_bio_vi_draft ≥2,000 rows
---

# T60 — Person Bio VI Lexicon Phase 2

## Mục tiêu

T58 xử lý 437 persons khớp trực tiếp qua `name_vi`. T60 mở rộng sang matching
qua **tên Hán trong phần nội dung definition** — nhiều từ điển PG VN ghi "Huệ Năng (慧能)..."
trong body text, không nhất thiết là headword.

Với 6,985 entries TU SĨ và 48,673 persons, tiềm năng tổng cộng ~2,000–3,000 matches.

## Cơ chế

```python
# Phase 2: Tìm name_zh của person trong body text của definitions
for person in all_persons_without_bio_vi:
    zh = person.name_zh  # e.g. "慧能"
    matches = conn.execute("""
        SELECT id, definition, source, headword
        FROM lexicon
        WHERE definition LIKE '%' || ? || '%'
          AND source IN ('TU_SI', 'PHAT_QUANG', 'THIEN_UYEN', 'THIEN_UYEN_TAP_ANH')
          AND LENGTH(definition) > 100
        LIMIT 3
    """, (zh,)).fetchall()
    
    for m in matches:
        # Extract Vietnamese name mentioned alongside zh character
        vn_name = extract_vn_name_near(m.definition, zh)
        score = similarity(vn_name, person.name_vi) if vn_name else 0
        if score > 0.5:
            # good match
```

## Xử lý false positives

- Tên Hán ngắn (2 ký tự như 慧能) có thể match vào nhiều contexts khác nhau
- Filter: chỉ accept khi name_zh xuất hiện trong dấu ngoặc `(慧能)` hoặc gần boundary sentence
- Score threshold: ≥0.6 để đảm bảo quality

## Acceptance Criteria

- [ ] Script `t60_bio_vi_lexicon_p2.py` chạy, extend bảng `person_bio_vi_draft`
- [ ] ≥1,500 new rows so với Phase 1 (≥1,937 total)
- [ ] False positive rate < 15% trên sample 50 rows
- [ ] Admin review 30 rows mẫu → quality acceptable
- [ ] Log: distribution của match scores (histogram)

## Liên quan

- T58 (Phase 1): Direct name_vi match — prerequisite
- T61: Place description VI (cùng phase B, parallel)
- `lexicon.definition`: 166K rows, nhiều chứa tên Hán trong parens
