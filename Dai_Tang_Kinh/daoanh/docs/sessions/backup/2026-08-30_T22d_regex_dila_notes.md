# Session 2026-08-30 — T22d: Regex ETL Founding Dates từ DILA Notes

## Tóm tắt

Implement T22d (Layer D của T22 founding-dates pipeline): khai thác `places_dila.note` bằng regex
để tìm năm thành lập chùa/địa điểm. Không cần NLP/GPU — deterministic, nhanh, reversible.

## Kết quả

| Metric | Giá trị |
|--------|---------|
| Notes scanned | 17,085 (tất cả rows có note trong places_dila) |
| Rows inserted | **276** |
| Source | `dila_note_regex` |
| Event type | `founding` |
| Renovation flagged | 6 rows (confidence × 0.7) |
| Errors | 0 |

### Breakdown theo pattern

| Pattern | Count | Confidence |
|---------|-------|-----------|
| `gongyan` (公元X年) | 122 | 0.88 |
| `year_jian` (X年建/創...) | 74 | 0.85 |
| `jian_yu` (建於X年) | 46 | 0.85 |
| `chuangjian` (創建X年) | 14 | 0.85 |
| `xiyuan` (西元X年) | 13 | 0.85 |
| `shijian_gongyan` (始建...公元X年) | 7 | 0.90 |
| **Total** | **276** | — |

### Place timeline coverage sau T22d

| Source | Count |
|--------|-------|
| dila_era_name | 1,471 |
| dila_dynasty | 851 |
| dila_note | 719 |
| **dila_note_regex (T22d mới)** | **276** |
| wikidata | 155 |
| wikidata_p571 | 146 |
| dila_fosizhi | 15 |
| **Tổng** | **3,633** |

## Files

- Script: `scripts/t22d_regex_dila_notes.py`
- Log: `data/t22d_regex_log.json`
- Task: `tasks/T22d-regex-dila-notes-founding.md` (status → done)

## Revert

```sql
DELETE FROM place_timeline_events WHERE source = 'dila_note_regex';
```
Hoặc:
```bash
python scripts/t22d_regex_dila_notes.py --revert
```

## Ghi chú kỹ thuật

- `confidence` column trong `place_timeline_events` là TEXT — store '0.88' dạng string
- 17,085 notes (nhiều hơn 14,010 trong spec ban đầu — spec dùng ước tính, thực tế query không có WHERE)
- Existing source `dila_note` (719 rows) dùng confidence='regex_note' (non-numeric) — T22d tách biệt hoàn toàn
- Idempotent: DELETE source='dila_note_regex' rồi INSERT lại mỗi lần chạy --apply
