---
id: T158
title: "GlossaryResolver — Pre-translation DB lookup + reject duplicate AI proposals"
module: translation
priority: high
status: done
depends_on: [T123, T73]
created: 2026-09-21
updated: 2026-09-21
done_when: |
  1. _glossary_resolver(conn, source_text) trả kết quả đúng từ ≥8 authority tables
  2. db_verified terms được inject vào GLOSSARY LOCK của prompt (không gọi LLM cho những gì DB đã có)
  3. _save_suggested_rules từ chối AI proposals có zh_term đã db_verified trong resolver
  4. Endpoint api_person_dila_translate truyền resolver vào lock và _save_suggested_rules
  5. Backfill: pending rules có zh_term đã db_verified được dismiss tự động (script)
---

## Bug description (trước khi fix)

**Vấn đề**: AI tạo pending rules cho những thuật ngữ đã có trong DB (vd: 南嶽→Nam Nhạc trong
namevi_map_places, 祖堂集→Tổ Đường Tập trong term_glossaries). 3-layer dedup hiện tại chỉ
check 3 bảng (namevi_map_places, term_glossaries, places) và chỉ chạy SAU khi AI đã đề xuất.

Không có bước PRE-TRANSLATION lookup để:
- Inject db_verified terms vào GLOSSARY LOCK trước khi gọi LLM
- Ngăn LLM "sáng tác" bản dịch cho thuật ngữ đã có sẵn trong DB

**Hậu quả**: 40 pending rules tích tụ, nhiều là duplicate của dữ liệu trong DB.

## Implementation

### 1. `_glossary_resolver(conn, source_text)` — NEW function (app.py ~line 15893)

Extract Hanzi terms từ source_text, lookup qua 12 authority tables theo priority:
1. `translation_glossary` (is_locked=1) → db_verified
2. `person_display_names` → db_verified
3. `vn_person_authority` (status='verified') → db_verified
4. `canonical_decision` → db_verified
5. `name_vi_map` (name_vi_final) → db_verified
6. `person_name_correction` (status='approved') → db_verified
7. `term_glossaries` (confidence≥0.7) → db_verified
8. `namevi_map_places` (reviewed OR confidence≥0.8) → db_verified
9. `cbeta_catalog_vn` (title_zh→title_vi) → db_verified
10. `doctrine_concept` → db_verified
11. `monk_dict` → db_verified
12. `namevi_map_places` (all) → db_ambiguous

Returns: `{resolved: {zh: {term_vi, source, status}}, unresolved: [zh,...]}`

### 2. Endpoint `api_person_dila_translate` — inject resolver into GLOSSARY LOCK

After `lock = _t73_style_lock(conn)`:
- Call `_glossary_resolver(conn, source_text)`
- Merge db_verified results vào `lock['glossary']` (deduplicated)
- Store as `lock['resolver']`

### 3. `_save_suggested_rules` — use resolver for dedup

Add optional `resolver` param. If resolver available: check db_verified first (covers 12 tables).
Falls back to existing 3-table check when resolver not passed.

### 4. Backfill script

`scripts/cleanup_pending_rules.py` — run resolver against pending rule texts,
dismiss those whose zh_terms are db_verified.

## Acceptance criteria

- [x] `_glossary_resolver` returns correct results for 天然→Thiên Nhiên, 祖堂集→Tổ Đường Tập, 禪師→Thiền Sư
- [x] API dịch DILA card: lock['glossary'] augmented với db_verified terms từ source text
- [x] Khi AI đề xuất term đã db_verified → `_save_suggested_rules` từ chối (không insert)
- [x] `lock['resolver']` populated và truyền vào `_save_suggested_rules`
- [x] Syntax check app.py OK (no SyntaxError)
- [x] Backfill script `scripts/cleanup_pending_rules.py` — dry-run: 21 dismiss / 18 keep (admin review needed)

## Done — Admin xác nhận 2026-09-21

14 priority tables: translation_glossary → person_display_names → vn_person_authority →
canonical_decision → name_vi_map → person_name_correction → term_glossaries → marcus_reference →
namevi_map_places_hq → cbeta_catalog_vn → doctrine_concept → monk_dict →
translation_rules_active → namevi_map_places (ambiguous).
