---
id: T22d
title: "T22 Layer D — Regex ETL: Founding Dates từ places_dila.note"
module: GIS Places / Timeline
priority: high
status: done
depends_on: [T22, T22.1]
created: 2026-08-30
updated: 2026-08-30
completed: 2026-08-30
done_when: Script chạy qua 14,010 DILA notes; ≥200 founding dates inserted vào place_timeline_events; log đầy đủ; admin review queue có thể filter theo source='dila_note_regex'
---

# T22d — Regex ETL: Founding Dates từ DILA Notes

## Bối cảnh

T22 Layer D: khai thác `places_dila.note` (14,010 rows có note) bằng regex để tìm
năm thành lập chùa/địa điểm. Đã test sơ bộ: **270 places** có year patterns rõ ràng.

Layer D ≠ Layer E (Ollama NLP). Layer D chỉ dùng regex — nhanh, xác định, không cần
GPU/AI, không sai về cú pháp.

## Phân tích dữ liệu (2026-08-30)

Đã test 14,010 DILA notes với regex patterns:

| Pattern | Count | Ví dụ |
|---------|-------|-------|
| `公元X年` | 116 | `公元1227年` |
| `X年建/創` | 76 | `916年建`, `1918年創` |
| `建於X年` | 45 | `建於1725年` |
| `西元X年` | 13 | `西元795年` |
| `創建於X年` | 13 | `創建於1960年` |
| `建於公元X年` | 4 | `建於公元684年` |
| Khác | 3 | `始建年代：公元1959年`, `741 AD` |
| **Tổng** | **270** | — |

## Cảnh báo cần xử lý

Pattern cần giảm confidence hoặc flag:
- Gần `重修/重建/重興/重創` → có thể là năm trùng tu, không phải thành lập
- Year > 1949 → có thể là modern, không phải historical founding
- Note tiếng Anh/tiếng Anh lẫn → cần check `X century BC` (249 BC → year=-249)

## Script cần viết

`scripts/t22d_regex_dila_notes.py`

```
python t22d_regex_dila_notes.py            # dry-run: count + top 30 mẫu
python t22d_regex_dila_notes.py --apply    # insert vào place_timeline_events
python t22d_regex_dila_notes.py --verbose  # in từng match
```

### Logic

```python
PATTERNS = [
    (r'公元\s*(\d{3,4})\s*年',          0.88, 'gongyan'),
    (r'(\d{3,4})\s*年[建創興]',          0.85, 'year_jian'),
    (r'建[於于]\s*(\d{3,4})\s*年',       0.85, 'jian_yu'),
    (r'西元\s*(\d{3,4})\s*年',           0.85, 'xiyuan'),
    (r'創建[於于]?\s*(\d{3,4})\s*年',    0.85, 'chuangjian'),
    (r'始建.{0,10}公元\s*(\d{3,4})\s*年', 0.90, 'shijian_gongyan'),
    (r'(\d{3,4})\s*(?:AD|CE)\b',          0.80, 'ad_ce'),
]
RENOVATION = re.compile(r'重修|重建|重興|重創|重立')

# Insert vào place_timeline_events:
source     = 'dila_note_regex'
event_type = 'founding'
confidence = pattern_conf * (0.7 if renovation_context else 1.0)
# Nếu renovation → thêm 'RENOVATION_CONTEXT' vào evidence
```

### Schema insert

```sql
INSERT OR IGNORE INTO place_timeline_events
    (dila_id, event_type, year, label_zh, source, source_ref, confidence, created_at)
VALUES (?, 'founding', ?, ?, 'dila_note_regex', ?, ?, ?)
-- source_ref = pattern name (e.g. 'gongyan', 'jian_yu')
```

## Acceptance Criteria

- [x] Script `t22d_regex_dila_notes.py` với --dry-run / --apply / --verbose / --revert / --stats
- [x] Chạy qua toàn bộ 17,085 DILA notes (có note)
- [x] 276 rows inserted vào `place_timeline_events` với `source='dila_note_regex'` (≥200 ✓)
- [x] Renovation context bị flag (6 rows, confidence × 0.7)
- [x] Log file `data/t22d_regex_log.json`
- [x] 0 rows với year < 1 hoặc year > 2000 (validate bounds)
- [x] Không duplicate: idempotent DELETE+INSERT per run

## Rollback

```sql
DELETE FROM place_timeline_events WHERE source = 'dila_note_regex';
```

## Liên quan

- T22 (in_progress): parent pipeline task — Layer D
- T22.1 (done): audit xác nhận regex approach hợp lệ
- T64/T64b (done): Layer A Wikidata — ceiling ~150 rows
- T22e (future): Layer E Ollama NLP — cho raw_xml narrative text
