# Session Log — 2026-08-30 (T22 Strategy)

## Tóm tắt

Sau khi hoàn thành T64/T64b (Wikidata P571 Layer A), phân tích ceiling và đề xuất
chiến lược tối ưu tiếp theo cho dự án PTDA.

## Kết quả T64/T64b (Wikidata Layer A)

| Phase | Script | Rows | wikidata_p571 total | Coverage |
|-------|--------|------|---------------------|----------|
| Baseline | — | 0 | 116 | 5.32% |
| T64 Phase 1 | t64_wikidata_p571_import.py | +24 | 140 | 5.47% |
| T64b Phase 2 | t64b_wikidata_name_match.py (opencc s2t) | +6 | **146** | **5.50%** |

Ceiling: ~150 rows tổng (không thể tăng thêm — Wikidata/DILA index entities khác nhau về bản chất).

## T22.1 Audit Done

Audit xác nhận:
- **REUSE FIRST** = đúng — không cần train ML để extract founding dates
- Wikidata ceiling xác nhận thực nghiệm (~150 rows)
- Regex approach trên `places_dila.note` hợp lệ và đáng làm ngay

## Chiến lược T22 được phê chuẩn

### Track A — Content ETL

**T22d** (next): Regex ETL trên 14,010 DILA notes → 270+ founding dates

Patterns đã test:
- `公元X年`: 116 trường hợp (conf 0.88)
- `X年建/創`: 76 trường hợp (conf 0.85)
- `建於X年`: 45 trường hợp (conf 0.85)
- Renovation context (`重修`...): confidence × 0.7
- Target: coverage 5.50% → ≥10%

### Track B — Content Translation

**T74**: Gemini batch translate 14,000 rows `place_desc_vi_draft` (Hán → Việt)
- Rate limit: 1 req/4s (≤15 RPM)
- Priority: 寺廟 category (11,886 rows) trước
- Resume capable: detect Hanzi còn lại

### Track C — Admin UI

**T73**: Review UI cho 2,093 rows `person_bio_vi_draft`
- Routes: GET/POST `/daoanh/admin/bio-review` + bulk-approve + stats
- Cần: `ALTER TABLE people ADD COLUMN bio_vi TEXT`

## Files tạo/cập nhật trong session này

| File | Thay đổi |
|------|---------|
| `tasks/T22-nlp-fosi-zhi-founding-dates.md` | status → in_progress, Layer A done, Layer D READY |
| `tasks/T22.1-founding-date-data-reuse-audit.md` | status → done |
| `tasks/T22d-regex-dila-notes-founding.md` | Tạo mới — Layer D spec |
| `tasks/T73-admin-review-bio-vi-draft.md` | Tạo mới (đổi từ T67 → T73 để tránh conflict) |
| `tasks/T74-place-desc-vi-gemini-translate.md` | Tạo mới (đổi từ T68 → T74 để tránh conflict) |
| `docs/tasktodo.md` | Thêm Phase C section + T22/T22.1/T22d/T73/T74; cập nhật bảng tổng quan 71 tasks, done=51, 72% |
| `data/progress_data.json` | Rebuild: 72%, done=51, 82 tasks |
| `docs/sessions/2026-08-30/session_t22_strategy_log.md` | File này |

## Dashboard

- Tasks: 71 → 82 (build_progress_data tính cả sub-tasks)
- Done: 42 → 51
- Tiến độ: 71% → 72%
