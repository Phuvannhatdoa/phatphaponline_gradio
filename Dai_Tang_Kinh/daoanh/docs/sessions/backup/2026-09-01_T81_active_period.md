---
id: 2026-09-01_T81_active_period
title: "T81 Session Log — Active Period / Flourished (Hoàn thành)"
created: 2026-09-01
updated: 2026-09-01
---

# T81 — Session Log: Active Period / Flourished

## Trạng thái
**DONE — 2026-09-01** (5,103 active/floruit events inserted)

## Bối cảnh
T79 chỉ đạt 203 death events (0 birth) do bio ít nêu sinh-năm. Để tăng phủ timeline cho person,
extract **active/flourished period** từ các `（YYYY）` activity dates có sẵn trong `people.bio`
(dịch kinh, trụ trì, giảng pháp, trước thuật).

## Phát hiện dữ liệu (probe 48,180 bios)

| Số single-year parens `（YYYY）` | Số persons | Hành động |
|---------------------------------|-----------|-----------|
| 0 | 43,077 | bỏ qua |
| 1 | 4,046 | floruit point (conf 0.55) |
| ≥2 | 1,057 | active window (conf 0.70) |

**Rút kinh nghiệm quan trọng**: 2-year parens `（YYYY-YYYY）` (vd `晦機元熙（1238-1319）`) trong bio
thường là **năm sống của sư phụ/vị được nhắc tới**, KHÔNG phải hoạt động của chủ thể.
Ví dụ A000062 `金陵龍翔笑隱大訢`: 1238 là của thầy `晦機元熙`, 1328 mới là chủ thể.
→ **Chỉ dùng single-year parens `（YYYY）`**, bỏ qua range 2 năm.

## Đã làm trong phiên này

### 1. Probe (`t81_probe*.py` temp)
- Khảo sát phân bố paren-years; phát hiện vấn đề master-lifespan; quyết định single-year only.

### 2. ETL (`scripts/t81_active_period.py`)
- `SINGLE_YEAR = re.compile(r'[（(]\s*(\d{3,4})\s*[）)]')` — bỏ qua `（YYYY-YYYY）`.
- ≥2 distinct years → `event_type='active'`, `event_year`=start, label `Hoạt động YY–YY`, conf 0.70.
- đúng 1 year → `event_type='floruit'`, `event_year`=năm đó, label `Hoạt động khoảng YY`, conf 0.55.
- `event_id`=person_id → 1 event/person (tuân UNIQUE(person_id,event_type,event_id)).
- Insert `INSERT OR IGNORE` (idempotent). Source=`dila_active_regex`.

### 3. Apply + verify
- Inserted **5,103 events** (1,057 active + 4,046 floruit).
- `vn_person_events`: 248 → **5,351** (45 pre-existing None + 203 dila_person_regex + 5,103 dila_active_regex).
- Mẫu active windows hợp lý: A000060 `Hoạt động 645–664` (dịch kinh), A000095 `720–756`, A000006 `1299–1317`.

## Files
- `scripts/t81_active_period.py` — ETL (--dry-run/--apply/--revert/--stats)
- `data/t81_active_log.json` — log
- `tasks/T81-active-period-flourished.md` — status done

## Rollback
```sql
DELETE FROM vn_person_events WHERE source = 'dila_active_regex';  -- 5,103 rows
```

## Next
- Chạy tester pipeline trước review.
- Với T79 (203 death) + T80 (temple founding) + T81 (active/floruit) — timeline person & place đã phủ tốt.
