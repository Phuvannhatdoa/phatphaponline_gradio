---
id: T81
title: "T81 — Active Period / Flourished (active_period extraction)"
module: Timeline / Person Authority
priority: high
status: done
depends_on: [T79]
created: 2026-09-01
updated: 2026-09-01
completed: 2026-09-01
done_when: 5,103 active/floruit events inserted (1,057 active windows + 4,046 floruit); log file data/t81_active_log.json; rollback DELETE verified
---

# T81 — Active Period / Flourished

## Bối cảnh

T79 chỉ extract được **203 death events** (và 0 birth) do bio ít nêu sinh-năm rõ ràng. Để tăng phủ timeline, helper: extract **active/flourished (xướng) period** — giai đoạn hoạt động tích cực của nhân vật (dựa trên các sự kiện có niên đại `（YYYY）` trong bio: dịch kinh, trụ trì, giảng pháp, trước thuật).

## Nguồn tín hiệu

| Nguồn | Pattern | Ví dụ |
|-------|---------|-------|
| Bio bio events | `（YYYY）` xuất hiện trong bio | `皇祐五年（1053）與智吉祥...共事翻譯` |
| dynasty+regnal CE | `年號XX年（YYYY）` | `文永十一年（1274）` |
| Active window | min/max của các `（YYYY）` trong bio | active_period = 1053–1274 |
| Floruit proxy | Krishna (thay cho birth khi không rõ) | active-period midpoint |

## Phát hiện dữ liệu (data reality — rút kinh nghiệm từ probe)

- 48,180 persons có bio.
- **Quan trọng**: 2-year parens `（YYYY-YYYY）` (vd `晦機元熙（1238-1319）`, `雲棲袾宏（1535-1615）`)
  là **năm sống của sư phụ/vị khác**, KHÔNG phải hoạt động của chủ thể → **BỎ QUA**.
- Chỉ dùng **single-year parens `（YYYY）`** — thường là sự kiện của chủ thể (năm dịch kinh,
  trụ trì, khai sơn, tịch...).
- Yield: ≥2 single years → **1,057 active windows**; đúng 1 single year → **4,046 floruit**; 0 → 43,077.

## Logic đã triển khai

```python
SINGLE_YEAR = re.compile(r'[（(]\s*(\d{3,4})\s*[）)]')   # bỏ qua （YYYY-YYYY）

def build_events(person_id, years):
    years = sorted(dedup(single_years))
    if len(years) >= 2:
        return event_type='active',  event_year=years[0],
               label='Hoạt động YY–YY', conf=0.70
    if len(years) == 1:
        return event_type='floruit', event_year=years[0],
               label='Hoạt động khoảng YY', conf=0.55
```

- event_id = person_id → 1 event/person (UNIQUE(person_id,event_type,event_id)).
- Insert `INSERT OR IGNORE` (idempotent).

## Acceptance Criteria

- [x] Script `scripts/t81_active_period.py` trích active period cho person có ≥2 events niên đại
- [x] Insert vào `vn_person_events` với event_type='active' (floruit nếu 1 năm)
- [x] Confidence: 0.70 (active window), 0.55 (floruit) — lower vì estimate
- [x] Không duplicate (1 event mỗi person, event_id=person_id)
- [x] Log file `data/t81_active_log.json`
- [x] Rollback: DELETE theo source T81

## Kết quả

| Metric | Giá trị |
|--------|---------|
| Active windows (≥2 years, conf 0.70) | 1,057 |
| Floruit (1 year, conf 0.55) | 4,046 |
| **Tổng new events** | **5,103** |
| `vn_person_events` total (trước → sau) | 248 → 5,351 |

### Usage

```bash
python scripts/t81_active_period.py            # dry-run
python scripts/t81_active_period.py --apply    # insert
python scripts/t81_active_period.py --revert   # DELETE source='dila_active_regex'
python scripts/t81_active_period.py --stats    # thống kê
```

## Rollback

```sql
DELETE FROM vn_person_events WHERE source = 'dila_active_regex';  -- 5,103 rows
```

## Liên quan

- **T79** (done): Person dates — lessons (bio có nhiều `（YYYY）` activity dates; bỏ range 2 năm)
- **T51g** (done): Curate top 200 tổ sư — có birth/death chính xác
- **T80** (done): Founding date coverage (reframe temple denominator)

## Ghi chú cho admin

- Active period là **estimate** (confidence thấp hơn birth/death) — dùng cho timeline xu hướng hoạt động, không phải ngày chính xác.
- Giá trị cho dashboard "thời kỳ hoạt động" của person.
- Rollback an toàn bằng 1 DELETE theo source `dila_active_regex`.
