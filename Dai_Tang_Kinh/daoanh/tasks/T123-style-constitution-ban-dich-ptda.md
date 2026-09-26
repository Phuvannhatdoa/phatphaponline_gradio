---
id: T123
title: "Style Constitution 'Ban Dịch PTDA' — Style-Lock 4 lớp + Báo lỗi dịch + Đề xuất fix rule (văn phong đồng nhất mọi luồng Groq)"
module: Editorial / LLM Translation
priority: high
status: done
depends_on: [T50, T73, T74, T85, T96]
created: 2026-09-12
updated: 2026-09-12
plan_approved_at: "2026-09-12 (Lee phê chuẩn — Style Constitution, bám sát từ điển danh tác, báo lỗi tự động + đề xuất fix rule)"
done_when: "Mọi luồng dịch Groq (passage legacy, T85 segments, translate_context, place, bio) dùng chung builder nhúng active rules + glossary lock + exemplar + persona Ban Dịch PTDA; nút Báo lỗi dịch ghi translation_error_report kèm snapshot/link; admin/translation_cache.html hiện chi tiết lỗi + hệ thống đề xuất rule fix; API /daoanh/api/translate-rules public; smoke đoạn Thích Diên Huy hết 'chàng'."
---

# T123 — Style Constitution "Ban Dịch PTDA" (2026-09-12)

Kế hoạch chi tiết đã thảo luận + Lee phê chuẩn (2026-09-12). Mục tiêu: **mọi rules active
trong `translation_rules` dashboard áp dụng xuyên suốt mọi luồng dịch Groq** — văn phong,
kính ngữ, thuật ngữ đồng nhất bất kể dịch qua đường nào. Bám sát **các bộ từ điển danh tác**
trong DB (`lexicon`, `glossary_vi`) làm exemplar + glossary lock.

## Nguyên nhân gốc (case "chàng")
- `t50_passage_vi_backfill.py` query rules DB nhưng `build_prompt` KHÔNG nhúng nội dung rules.
- `api_passage_translate` legacy (app.py:15652) dùng system tĩnh `_BUDDHIST_SYSTEM_PROMPT`.
- `_t85_translate_unit` (app.py:15481) + `translate_context` (app.py:2333) prompt hardcode.
- Chỉ `api_place_translate` (15296) + bio T73 (15120) dùng rules DB.

## Quyết định thiết kế (Lee chốt)
1. **Invalidate:** rules đổi → chỉ áp dụng lần dịch SAU. Bản dịch cũ để nguyên (tạm ok).
   User/tester random-check thấy cần dịch lại → bấm nút "Dịch lại" → đoạn đó dịch lại rule mới.
   KHÔNG auto-heal. Giữ panel Invalidate thủ công trong admin (bulk nếu muốn).
2. **Báo lỗi:** user báo bất kỳ lỗi nào (văn phong/kỹ thuật/sai nghĩa...) → ghi
   `translation_error_report` (snapshot + link + note). Admin xem chi tiết lỗi từ đâu ra +
   hệ thống đề xuất rule fix. Admin chạy bảng mới → `rules_version` đổi.
3. **Exemplar/glossary:** bám sát 22 từ điển lexicon danh tác (Từ Điển Thiền Tông Hán-Việt
   ~2,575 cặp Hán-Việt passage-level, Từ Điển Hán-Việt Nguyễn Quốc Hùng, Tam Tạng Pháp Số,
   Phật Học Tinh Tuyền, Phật Quang, Đoàn Trung Còn...).

## Mục tiêu
Tập trung hóa prompt dịch Groq về 1 unified Style-Lock builder; toàn bộ rule/style/glossary/
exemplar nằm trong DB `translation_rules` + 3 bảng additive mới; cache ghi `rules_version`;
admin có đủ dữ liệu chi tiết để duy tu văn phong qua dashboard.

## Checklist
- [x] T1. Task file T123 + session doc + tasktodo + `build_progress_data.py` (dashboard)
- [x] T2. Seed 8 rules Style Constitution vào `translation_rules` (upsert, is_active=1)
       (PERSONA_BAN_DICH, EXPRESSION_PRINCIPLE, NO_ADDITION, GLOSSARY_LOCK_STABLE,
        CANONICAL_NAMES, TONE_OVERALL, LITERARY_PURITY, HONORIFIC_PRONOUN)
- [x] T3. Bảng `translation_exemplar` (seed ~2,724 cặp Hán-Việt từ lexicon, active 2-3 mẫu danh tác)
- [x] T4. Bảng `translation_glossary` (lock ~80 thuật ngữ từ lexicon/glossary_vi, nguồn danh tác)
- [x] T5. Bảng `translation_error_report` (cache_id, source_type, entity_id, snapshot, error_type,
       note, page_url, status pending/resolved, created_at)
- [x] T6. Unified Style-Lock builder `_t73_build_style_prompt` trong app.py — nhúng persona +
       active rules + glossary + exemplar + nguyên bản; trả (prompt, rules_version)
- [x] T7. Áp builder cho 5 luồng: passage legacy (15652), T85 `_t85_translate_unit` (15481),
       `translate_context` (2333), place (15296), bio T73 (15120). Lock temperature ≤0.15
       + model `llm_config` + cache ghi `prompt_version=rules_version`.
- [x] T8. Nút "Báo lỗi dịch" phía user (văn phong/kỹ thuật/sai nghĩa/khác) → ghi
       `translation_error_report` + tăng `report_count` (≥3 → status reported)
- [x] T9. Nâng cấp `admin/translation_cache.html`: tab Báo lỗi chi tiết (Hán gốc ↔ bản dịch lỗi
       ↔ link/đoạn ↔ note) + hệ thống đề xuất fix rule (mapping loại lỗi → rule_code gợi ý)
- [x] T10. Endpoint public `GET /daoanh/api/translate-rules` (rules_version, active rules, counts)
- [x] T11. Fix `t50_passage_vi_backfill.py` `build_prompt` → nhúng active rules + glossary +
       exemplar + persona Ban Dịch PTDA
- [x] T12. Smoke: dịch lại đoạn "Thích Diên Huy" hết "chàng"; report → admin thấy đề xuất;
         3 luồng dịch trả `prompt_version`; `/daoanh/api/translate-rules` 200 public
- [x] T13. test + e2e (npm run pipeline) → PASS
- [x] T14. Commit temp-index (parent 2922725) — revert thuận tiện từng tầng

## Files
- `scripts/seed_style_constitution.py` — seed rules + 3 bảng
- `scripts/t50_passage_vi_backfill.py` — fix build_prompt
- `app.py` — unified builder + 5 luồng + report route + translate-rules endpoint
- `admin/translation_cache.html` — tab báo lỗi + đề xuất fix
- `admin/places.html` — badge "Ban Dịch PTDA" (nếu không xung đột agent ngoài)
- `docs/sessions/2026-09-12_t123-style-constitution.md`

## Done khi
Mọi luồng Groq nhúng Style Constitution; báo lỗi có snapshot/link + admin thấy đề xuất rule;
dịch lại "Thích Diên Huy" không còn "chàng"; `npm run pipeline` PASS; commit revert tiện lợi.