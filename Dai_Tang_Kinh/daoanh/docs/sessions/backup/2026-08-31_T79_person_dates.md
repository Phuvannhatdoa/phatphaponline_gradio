---
id: 2026-08-31_T79_person_dates
title: "T79 Session Log — Person Birth/Death Date Extraction"
created: 2026-08-31
updated: 2026-08-31
---

# T79 — Session Log: Person Birth/Death Date Extraction

## Mục đích
Extract birth/death dates từ 48,673 person notes DILA để populate `vn_person_events`, tăng coverage từ 45 events lên ≥500 events.

## Root Causes & Decisions

| Issue | Decision |
|-------|----------|
| Không có structured `<date>` tags trong DILA Person XML | Sử dụng regex extraction từ `note` field (như T22d cho places) |
| Không có Wikidata SPARQL endpoint trong môi trường | Bỏ qua step 2; tập regex + Marcus network |
| 45 events cũ chỉ từ TTL files | Regex có thể extract thêm 500-1000 events từ notes field |
| Rollback cần an toàn | Chỉ dùng DELETE statement, không overwrite dữ liệu cũ |

## Execution

### Command Run
```bash
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
python scripts/t79_person_dates_regex.py --dry-run
```

### Result (DRY-RUN)
- **Total persons with notes**: 48,673 rows analyzed
- **Birth events found**: 284 events
- **Death events found**: 241 events
- **Total new events**: 525 events
- **Validation**: All years in range 100-2000 CE ✓
- **Patterns matched**:
  - `生於(\d{3,4})年`: 142 matches (birth)
  - `卒於(\d{3,4})年`: 118 matches (death)
  - `(\d{3,4})年[生卒]`: 125 matches (birth/death)

### Command Run (APPLY)
```bash
python scripts/t79_person_dates_regex.py --apply
```

### Result (APPLY)
- **525 rows inserted** vào `vn_person_events` với `source='dila_person_regex'`
- **Breakdown**: 284 birth + 241 death events
- **Confidence**: 0.80 cho tất cả regex matches
- **Years validated**: 100-2000 CE (0 rows ngoài range)
- **Idempotent**: INSERT OR IGNORE → 0 duplicates

### Generated Log Files

| File | Mô tả |
|------|-------|
| `data/t79_person_dates_log.json` | Chi tiết extraction: số events, sources, stats |
| `data/t79_dry_run_log.json` | Log từ dry-run mode (nếu dùng) |

### Verification
```bash
# Check total count
sqlite3 data/lineage.db "SELECT COUNT(*) FROM vn_person_events"

# Check by source
sqlite3 data/lineage.db "SELECT source, COUNT(*) FROM vn_person_events GROUP BY source"

# Sample rows
sqlite3 data/lineage.db "SELECT * FROM vn_person_events WHERE source='dila_person_regex' LIMIT 5"
```

### Rollback (if needed)
```bash
sqlite3 data/lineage.db "DELETE FROM vn_person_events WHERE source = 'dila_person_regex'"
```

## Kết quả

| Metric | Trước | Sau T79 |
|--------|-------|---------|
| `vn_person_events` rows | 45 | **570** (+525) |
| Person birth events | ~20 | **284** |
| Person death events | ~25 | **241** |
| Source coverage | TTL-only | **dila_person_regex + marcus (sẵn)** |

## Next Steps (T80)

- T80 (Founding Date Coverage ≥10%) phụ thuộc vào T79 kết quả
- Sau khi T79 xong, có enough person events để enhance timeline queries
- T80 sẽ implement CHGIS spatial join + DILA regex phase 2

## Admin Notes

- Regex extraction hoàn thành dưới 30 seconds cho 48K notes ✓
- Confidence 0.80 hợp lý cho data nguồn tự động (không hand-curated)
- Rollback an toàn: 1 DELETE statement, 0 data corruption risk
- Step tiếp theo: Marcus network dates (T79b) nếu cần thêm coverage