---
id: T64b
title: "Wikidata P571 Phase 2 — Name Match (s2t convert + GPS verify)"
module: Timeline / GIS
priority: medium
status: done
depends_on: [T64]
created: 2026-08-28
updated: 2026-08-28
done_when: Script với hard GPS filter; 6 high-confidence rows inserted; false positive rate = 0
---

# T64b — Wikidata P571 Phase 2: Name Match

## Bối cảnh

T64 Phase 1 (GPS ±0.5km) chỉ match được 24 rows vì DILA dùng toạ độ lịch sử. T64b
thử name_zh matching sau khi phát hiện root cause thực sự: **Wikidata dùng giản thể (龙),
DILA dùng phồn thể (龍)**.

## Root Cause

| Hệ thống | Ký tự | Ví dụ |
|----------|-------|-------|
| Wikidata label | Giản thể (简体) | 龙华寺, 灵隐寺 |
| DILA name_zh | Phồn thể (繁體) | 龍華寺, 靈隱寺 |

Giải pháp: `opencc s2t` convert trước → exact match.

## Kết quả thực tế (2026-08-28)

| Metric | Giá trị |
|--------|---------|
| Temples thử | 2,028 (chưa match từ Phase 1) |
| Exact match sau s2t | 33 candidates |
| Unambiguous + GPS OK (<50km) | **6 rows** |
| Ambiguous không GPS | 15 |
| GPS mâu thuẫn (>50km) | 12 false positives → skipped |
| Inserted | **6** |
| False positive rate | **0%** |

6 rows đã insert:

| DILA ID | Tên (phồn thể) | Năm | GPS dist | Conf |
|---------|---------------|-----|----------|------|
| PL000000058751 | 夏瓊寺 | 1349 | 0.6 km | 0.80 |
| PL000000046748 | 塔爾寺 | 1560 | 1.7 km | 0.80 |
| PL000000047062 | 都蘭寺 | 1584 | 3.7 km | 0.80 |
| PL000000046712 | 沙溝寺 | 1222 | 6.3 km | 0.80 |
| PL000000046768 | 東科爾寺 | 1648 | 5.8 km | 0.72 |
| PL000000045179 | 石門寺 | 1500 | 6.4 km | 0.72 |

## Acceptance Criteria

- [x] Script `t64b_wikidata_name_match.py` với --dry-run / --apply
- [x] opencc s2t conversion
- [x] Hard GPS filter: >50km → skip (false positive protection)
- [x] Dedup: cùng (dila_id, year) giữ conf cao nhất
- [x] 0 false positives trong 6 rows được insert
- [x] Log `data/t64b_import_log.json`

## Tổng kết T64 + T64b

| Phase | Script | Method | Rows | wikidata_p571 total |
|-------|--------|--------|------|---------------------|
| Baseline | — | — | 0 new | 116 |
| T64 Phase 1 | t64_wikidata_p571_import.py | GPS ±0.5km | +24 | 140 |
| T64b Phase 2 | t64b_wikidata_name_match.py | s2t + GPS verify | +6 | **146** |

Coverage: 5.32% → **5.50%** (+0.18pp)

## Giới hạn — Tại sao không thể đạt 1,000 rows

Wikidata và DILA index các thực thể **khác nhau về bản chất**:
- Wikidata: chùa vật lý hiện đại, GPS chính xác, tên giản thể
- DILA: địa danh trong văn bản Phật học cổ (đa số Tang-Tống), nhiều là tên hành chính/vùng,
  không phải tên riêng của ngôi chùa

Overlap thực tế (có tên giống nhau, GPS xác nhận <50km): chỉ ~30 entities trong toàn bộ dataset.

## Rollback

```sql
DELETE FROM place_timeline_events
WHERE source = 'wikidata_p571'
  AND created_at > '2026-08-28T12:00:00'
  AND source_ref IN ('Q...·P571', ...)
```

Hoặc đơn giản hơn — xem log `data/t64b_import_log.json` lấy timestamp rồi delete theo `created_at`.

## Liên quan

- T64 (Done): Phase 1 GPS match
- Script: `scripts/t64b_wikidata_name_match.py`
- Log: `data/t64b_import_log.json`
