---
id: T63
title: "Person Bio VI Phase 1 — Lexicon TU SĨ Direct Match (437 persons)"
module: Person Authority
priority: high
status: done
depends_on: [T46, T62]
created: 2026-08-27
updated: 2026-08-27
done_when: ≥400 persons có bio_vi_draft từ lexicon TU SĨ; bảng person_bio_vi_draft tồn tại; avg bio length ≥200 chars
---

# T63 — Person Bio VI Lexicon Phase 1

## Vấn đề

Hiện tại 48,673 persons có `bio` tiếng Hán (avg ~75 chars) nhưng `bio_vi` = NULL.
Người dùng Việt tra thiền sư không nhận được thông tin gì tiếng Việt về tiểu sử.

Trong khi đó, kho từ điển PG VN trong DB (`lexicon` table) có **6,985 entries nguồn TU SĨ**
với `definition` tiếng Việt dài trung bình 200–2,000+ ký tự — mô tả chi tiết về cuộc đời,
thành tựu, truyền thừa các vị thiền sư.

## Cơ chế (Phase 1 — Direct Match)

437 persons khớp trực tiếp vì `name_vi` trong `people` giống `headword` hoặc xuất hiện
trong `definition` của lexicon entries với nguồn TU SĨ.

```sql
SELECT p.id, p.name_zh, p.name_vi, l.definition, l.source
FROM people p
JOIN lexicon l ON (
    l.headword = p.name_vi
    OR l.headword LIKE '%' || p.name_vi || '%'
)
WHERE l.source IN ('TU_SI', 'PHAT_QUANG', 'THIEN_UYEN')
  AND p.bio_vi IS NULL
  AND l.definition IS NOT NULL
  AND LENGTH(l.definition) > 50
```

## Lưu ý học thuật

**Không sao chép nguyên văn từ điển** vào production `bio_vi`. Workflow đúng:
- `person_bio_vi_draft` = bản nháp cho admin tổng hợp, viết lại bằng lời riêng
- `source_lexicon_id` lưu rõ để attribution
- Sau admin approve: copy summary → `people.bio_vi`

## Acceptance Criteria

- [ ] Script `t63_bio_vi_lexicon_p1.py` chạy, in danh sách matches ≥400 persons
- [ ] Bảng `person_bio_vi_draft` tồn tại với ≥400 rows
- [ ] Avg `char_count` của drafts ≥200 characters
- [ ] Dry-run: top 20 best matches (headword exact, dài nhất)
- [ ] Admin review 20 entries mẫu → xác nhận chất lượng đủ tốt

## Liên quan

- T64 (Phase 2): Mở rộng matching qua Chinese name → 2,000+ persons
- T62: Bulk name fix — tên đúng trước → bio match chính xác hơn
- `lexicon`: 166,278 rows, 22 từ điển PG VN

## Phê Chuẩn

Được phê chuẩn trong chiến lược PTDA 2026-08-27 (Phase A — Trụ 2: Hồ Sơ Tiếng Việt).
