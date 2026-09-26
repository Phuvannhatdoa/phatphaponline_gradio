---
id: T79
title: "T79 — Person Birth/Death Date Extraction từ DILA Bios (Cập nhật theo data thật)"
module: Timeline / Person Authority
priority: high
status: done
depends_on: [T22d]
created: 2026-08-31
updated: 2026-09-01
completed: 2026-09-01
done_when: new person events inserted vào vn_person_events với source='dila_person_regex'; confidence đúng format; log file đầy đủ; rollback bằng DELETE statement verified
---

# T79 — Person Birth/Death Date Extraction

## Bối cảnh

T78 (License Firewall) đã hoàn thành. T79 là bước tiếp theo để cải thiện dữ liệu timeline cho người trong hệ thống DILA. Hiện tại `vn_person_events` chỉ có **45 events** (từ TTL files).

> **⚠️ CẬP NHẬT 2026-09-01 (data thực tế)**: Target ban đầu ≥500 dựa trên giả định `persons_dila.note` với mật độ date cao. **Dữ liệu thật cho thấy:**
> - Bảng nguồn là **`people.bio`** (48,180 rows non-empty), KHÔNG phải `persons_dila.note` (bảng này không tồn tại).
> - Bio dùng format `（YYYY）示寂`, KHÔNG phải `生於1200年`.
> - Sinh year hiếm khi được nêu rõ → 0 birth events chính xác.
> - **203 death events chính xác** (0.92 confidence) từ pattern `（YYYY）示寂` là mức tối đa tin cậy.
> - `birth_year`/`death_year` trong `people` **bị nhiễm CBETA page numbers** → không dùng được.

## Phân tích dữ liệu cần extract

Pattern regex thực tế (đã xác minh):

| Pattern | Mục đích | Ví dụ | Số match |
|---------|----------|-------|----------|
| `（YYYY）示寂` (paren trước death keyword, ≤30 ký tự) | Death year | `文保元年（1317）示寂` | **203** (chính xác cao) |
| `示寂於（YYYY）` | Death year (fallback) | `道禪師示寂於元和十三年（818）` | fallback |
| `生於（YYYY）` | Birth year | hiếm gặp | ~0 |
| `ulatory` regnal→CE trong paren `（1274）` | Event/activity year (thuộc T80/T81) | `文永十一年（1274）` | rất nhiều, nhưng không phải birth/death |

Kết quả thực tế đạt: **203 death events** (mức chính xác cao nhất từ data có sẵn).

## Script cần viết

`scripts/t79_person_dates_regex.py`

### Logic chính

```python
import sqlite3
import re
from datetime import datetime

DB_PATH = 'data/lineage.db'

# Patterns cho birth/death extraction
BIRTH_PATTERNS = [
    (r'生於\s*(\d{3,4})\s*年', 0.85),       # 生於1200年
    (r'(\d{3,4})\s*年\s*生', 0.85),         # 1200年生
    (r'(\d{3,4})\s*年[生卒]', 0.80),         # 1200年卒 / 1200年生
]

DEATH_PATTERNS = [
    (r'卒於\s*(\d{3,4})\s*年', 0.88),       # 卒於1200年
    (r'(\d{3,4})\s*年\s*卒', 0.88),         # 1200年卒
    (r'卒(\d{3,4})\s*年', 0.85),            # 卒1200年
]

# Map dynasty regnal years to CE
DYNASTY_MAP = {
    '唐': {'start': 618, 'format': 'reign_years'},
    '宋': {'start': 960, 'format': 'reign_years'},
    '元': {'start': 1271, 'format': 'reign_years'},
    '明': {'start': 1368, 'format': 'reign_years'},
    '清': {'start': 1644, 'format': 'reign_years'},
}

def extract_year_from_note(note, patterns):
    """Extract year(s) from DILA person note using regex patterns."""
    results = []
    for pattern, confidence in patterns:
        match = re.search(pattern, note or '')
        if match:
            year_str = match.group(1)
            try:
                year = int(year_str)
                # Validate reasonable range: 100-2000 CE
                if 100 <= year <= 2000:
                    results.append({
                        'year': year,
                        'confidence': confidence,
                        'source_pattern': pattern
                    })
            except ValueError:
                continue
    return results

def parse_dynasty_reign(dynasty_name, reign_year):
    """Convert dynasty reign year to CE year."""
    if dynasty_name not in DYNASTY_MAP:
        return None
    base_year = DYNASTY_MAP[dynasty_name]['start']
    # Chinese reign years are typically 1-based offsets
    ce_year = base_year + reign_year - 1
    if 100 <= ce_year <= 2000:
        return ce_year
    return None

def main():
    """Main ETL pipeline for person birth/death date extraction."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Read all persons from DILA with notes
    cursor.execute("SELECT person_id, note FROM persons_dila WHERE note IS NOT NULL AND note != ''")
    persons = cursor.fetchall()
    
    print(f"TOTAL persons with notes: {len(persons)}")
    
    birth_events = []
    death_events = []
    
    for person_id, note in persons:
        # Extract birth year
        birth_matches = extract_year_from_note(note, BIRTH_PATTERNS)
        for match in birth_matches:
            birth_events.append({
                'person_id': person_id,
                'year': match['year'],
                'confidence': match['confidence'],
                'event_type': 'birth',
                'source': 'dila_person_regex',
                'source_ref': match['source_pattern'],
                'created_at': datetime.now().isoformat()
            })
        
        # Extract death year
        death_matches = extract_year_from_note(note, DEATH_PATTERNS)
        for match in death_matches:
            death_events.append({
                'person_id': person_id,
                'year': match['year'],
                'confidence': match['confidence'],
                'event_type': 'death',
                'source': 'dila_person_regex',
                'source_ref': match['source_pattern'],
                'created_at': datetime.now().isoformat()
            })
    
    print(f"Birth events found: {len(birth_events)}")
    print(f"Death events found: {len(death_events)}")
    
    # Insert birth events into vn_person_events
    for event in birth_events:
        cursor.execute("""
            INSERT OR IGNORE INTO vn_person_events
            (person_id, event_type, year, source, source_ref, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (event['person_id'], event['event_type'], event['year'],
              event['source'], event['source_ref'], event['confidence'], event['created_at']))
    
    # Insert death events into vn_person_events
    for event in death_events:
        cursor.execute("""
            INSERT OR IGNORE INTO vn_person_events
            (person_id, event_type, year, source, source_ref, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (event['person_id'], event['event_type'], event['year'],
              event['source'], event['source_ref'], event['confidence'], event['created_at']))
    
    conn.commit()
    
    # Verification
    cursor.execute("SELECT source, COUNT(*) FROM vn_person_events GROUP BY source")
    stats = cursor.fetchall()
    print("\n=== vn_person_events BY SOURCE ===")
    for source, count in stats:
        print(f"  {source}: {count} events")
    
    cursor.execute("SELECT COUNT(*) as total FROM vn_person_events")
    total = cursor.fetchone()[0]
    print(f"\nTotal vn_person_events: {total}")
    
    # Generate log
    log_data = {
        'date': datetime.now().isoformat(),
        'total_persons_analyzed': len(persons),
        'birth_events_extracted': len(birth_events),
        'death_events_extracted': len(death_events),
        'vn_person_events_total': total,
        'new_events_this_run': len(birth_events) + len(death_events),
        'sources': list(set([e['source'] for e in birth_events + death_events]))
    }
    
    import json
    with open('data/t79_person_dates_log.json', 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nLog file written: data/t79_person_dates_log.json")
    print(f"Inserted {len(birth_events) + len(death_events)} new person events")
    
    conn.close()

if __name__ == '__main__':
    main()
```

### Schema insert (verified)

```sql
INSERT OR IGNORE INTO vn_person_events
    (person_id, event_type, year, label_vi, source, source_ref, confidence, created_at)
VALUES (?, ?, ?, ?, ?, ?, ?)
```

Where:
- `event_type` = `birth` hoặc `death`
- `year` = integer (100-2000 CE)
- `source` = `dila_person_regex` hoặc `marcus_person`
- `source_ref` = tên pattern (e.g. `'gongyan'`, `'jian_yu'`)
- `confidence` = 0.80 cho regex, 0.85 cho wikidata, 0.75 cho marcus

## Acceptance Criteria

- [x] Script `t79_person_dates_regex.py` chạy với --dry-run / --apply / --revert / --stats
- [x] Chạy qua toàn bộ 48,180 persons có bio
- [x] **203 rows inserted** vào `vn_person_events` với `source='dila_person_regex'` (death events, confidence 0.92)
- [x] `event_type` rõ ràng: `death` (birth không có trong data — 0 chính xác)
- [x] `confidence` đúng format (0.92 cho `（YYYY）示寂`)
- [x] Log file `data/t79_person_dates_log.json`
- [x] 0 rows ngoài range 100-2000 (year range 191–1951 verified)
- [x] Không duplicate (203 distinct persons)
- [x] Idempotent với --revert flag (DELETE theo source)
- [ ] ~~≥500 events~~ — **KHÔNG khả thi** với data thật ở mức chính xác cao; đạt 203. Cần nguồn đối chiếu khác (CHGIS/Wikidata) để tăng — chuyển sang T80/T81.

## Rollback

```sql
DELETE FROM vn_person_events WHERE source = 'dila_person_regex';
```

## Liên quan

- **T22d** (done): Regex ETL đã thành công cho places founding dates (276 rows)
- **T51**: Person portal - cần dữ liệu dates để populate
- **T73**: Admin review bio - dates field cần có trước
- **T80**: Founding date coverage - phụ thuộc kết quả T79
- **DILA persons**: 48,180 rows trong `people.bio` (KHÔNG phải `persons_dila.note` như spec gốc)
- **vn_person_events**: 45 events cũ (từ TTL import) + 203 T79 = 248

## Ghi chú cho admin

- Regex extraction là step 1 - nhanh, không cần GPU ✓
- Step 2 (Wikidata) bỏ qua do không có SPARQL endpoint
- Step 3 (Marcus network) implement sau nếu cần
- Rollback hoàn toàn bằng 1 DELETE statement - an toàn cho production
- **Data reality**: `birth_year`/`death_year` trong `people` nhiễm CBETA page numbers — đừng dùng làm giá trị chính xác
- Sinh year không nêu trong bio → cần nguồn khác (T80/T81)
- Xem chi tiết: `docs/sessions/2026-09-01_T79_person_dates.md`