# Session 2026-08-27 — Chiến Lược PTDA Phase A/B Phê Chuẩn

## Tóm tắt

Phiên thảo luận chiến lược toàn diện về hướng phát triển tiếp theo của PTDA.
Audit DB thực tế → xác định gap → đề xuất → phê chuẩn → tạo task.

## Kết quả phiên

### Artifact chiến lược
Đã publish: [Chiến Lược PTDA](https://claude.ai/code/artifact/f589b9a0-a064-4fb5-affe-1e0d871e3305)

### Tasks được tạo mới

| Task | Tên | Priority | Phase |
|------|-----|----------|-------|
| T57 | Person name_vi Bulk Pattern Fix (~1,006 persons) | HIGH | A |
| T58 | Person Bio VI Phase 1 — Lexicon TU SĨ Direct Match | HIGH | A |
| T59 | Wikidata P571 Import Batch (~1,500 founding dates) | HIGH | A |
| T60 | Person Bio VI Phase 2 — Chinese Name Pattern Matching | MEDIUM | B |
| T61 | Place Description VI — Lexicon ĐỊA DANH 15,863 entries | MEDIUM | B |

### Điểm phát hiện cốt lõi

**Lexicon 166K entries là goldmine chưa khai thác:**
- 22 từ điển PG VN trong DB có Vietnamese definitions chất lượng cao
- 6,985 entries TU SĨ với bio tiếng Việt dài 200–2,000+ chars
- 15,863 entries ĐỊA DANH với mô tả địa danh tiếng Việt
- Trước T46/T47/T48: chưa ai dùng lexicon để improve chất lượng dữ liệu chính

**Gap lớn nhất:**
- Tên Việt: 100% phủ số lượng nhưng chỉ 0.8% persons / 7.6% places đã review
- Timeline: 5.32% coverage (94.7% places không có ngày)
- Bio tiếng Việt: NULL cho 48,673 persons

### Điểm hiện tại và mục tiêu

| Giai đoạn | Điểm |
|-----------|------|
| Hiện tại (2026-08-27) | 6.2/10 |
| Sau Phase A (T57+T58+T59) | ~7.0/10 |
| Sau Phase B (T60+T61+T46 review) | ~7.8/10 |
| Sau Phase C (NLP + scholar review) | ~8.5/10 |

### Nguyên tắc thiết kế được confirm

1. Lexicon-first, không phải ML-first
2. Pattern trước (bulk), case-by-case sau (lexicon cross-ref)
3. Không tăng coverage số lượng — tăng chất lượng reviewed rate
4. Tài nguyên trong tầm tay (SQLite local + lexicon đã load) luôn ưu tiên
5. Confidence trail: auto(0.5) → pattern-fixed(0.72) → lexicon-verified(0.75) → admin(0.85) → scholar(1.0)

### Lịch sử ID conflict T57-T59

T57/T58/T59 đã được gán tạm cho TGS portal ideas (Glossary/Search/Education) từ session trước
nhưng không có task file. Chiến lược mới có quyền ưu tiên cao hơn:
- Glossary Đa Ngôn → **T62**
- Tìm Kiếm Thông Minh → **T63**
- Giáo Dục → **T64**

## Trạng thái dashboard sau session

```
66 task trên board (done=36, blocked=3)
total_progress: 69%
```

## Files được tạo/sửa trong phiên này

- `tasks/T57-person-name-bulk-pattern-fix.md` (new)
- `tasks/T58-bio-vi-lexicon-phase1.md` (new)
- `tasks/T59-wikidata-timeline-import.md` (new)
- `tasks/T60-bio-vi-lexicon-phase2.md` (new)
- `tasks/T61-place-desc-vi-lexicon-diadanh.md` (new)
- `docs/tasktodo.md` (updated: T57-T61 sections + status table)
- `data/progress_data.json` (rebuilt: 66 tasks)
- `docs/sessions/2026-08-27_strategy_ptda_phase_ab.md` (this file)

## Bước tiếp theo (Phase A)

1. **Viết T57 script** `t57_bulk_name_pattern_fix.py` — dry-run trước
2. **Chạy T46 `--apply-clear`** — 21 CLEAR corrections đã sẵn sàng
3. **Viết T58 script** `t58_bio_vi_lexicon_p1.py`
4. **Viết T59 script** `t59_wikidata_p571_import.py` — SPARQL download
5. **T28 server restart** — Tab Nhân Vật live
