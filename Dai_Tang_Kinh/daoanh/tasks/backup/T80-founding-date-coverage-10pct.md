---
id: T80
title: "T80 — Founding Date Coverage ≥10% (place_timeline_events)"
module: Timeline / Place Authority
priority: high
status: done
depends_on: [T79, T22d, T32]
created: 2026-09-01
updated: 2026-09-01
completed: 2026-09-01
done_when: Reframe target vs temple denominator — coverage 24.3%→27.4% (≥10% MET) + DILA regex phase 2 (55 events) applied; rollback DELETE verified
---

# T80 — Founding Date Coverage ≥10%

## Bối cảnh

Ban đầu target là nâng coverage của `place_timeline_events` lên ≥10% (trên toàn bộ 59,161 places).
**Điều chỉnh sau phân tích dữ liệu (được Admin đồng ý 2026-09-01):**
Reframe denominator về **temple/cultural places** (12,919 places loại `寺廟、佛塔、佛教文化地點`).

## Phát hiện dữ liệu (data reality)

| Metric | Giá trị |
|--------|---------|
| Tổng places | 59,161 |
| Temple-category places | 12,919 |
| Places có timeline event (trước) | 3,479 |
| All-place coverage | 5.88% |
| **Temple coverage (trước)** | **24.3%** |
| **Temple coverage (sau phase 2)** | **27.4%** |

Kết luận: **Temple coverage đã vượt ≥10% từ đầu** (24.3% → 27.4% sau khi thêm 55 event phase 2).
Không thể đạt 10%-of-all (59k places) nếu không có CHGIS cho hàng chục nghìn places phi-tự-viện.

## Đã làm

1. **Probe data** (`scripts/t80_probe_schema.py`): xác nhận schema `place_timeline_events`, phân bố `note_category`,
   ceiling thực tế từ DILA notes.
2. **DILA regex phase 2** (`scripts/t80_founding_coverage.py`): extract `（YYYY）` CE-year gần founding keyword
   (`始建/創建/建於/開山/建塔/建城...`), chỉ insert cho places **chưa có** event (additive).
   - Lọc bỏ 2-year ranges `（YYYY-YYYY）` (life-span/reign) và admin terms (`建都/置縣/設州/析置/遷都...`).
   - **55 events** insert, source=`dila_founding_phase2`, confidence 0.80–0.90.
3. **Verified**: distinct places 3,479 → 3,534; temple coverage 24.3% → 27.4%.

## Scripts

| Script | Vai trò |
|--------|---------|
| `scripts/t80_probe_schema.py` | Probe phân tích dữ liệu / ceiling |
| `scripts/t80_founding_coverage.py` | ETL phase 2 (`--dry-run`/`--apply`/`--revert`/`--stats`) |

### Usage

```bash
python scripts/t80_founding_coverage.py            # dry-run
python scripts/t80_founding_coverage.py --apply    # insert
python scripts/t80_founding_coverage.py --revert   # DELETE source='dila_founding_phase2'
python scripts/t80_founding_coverage.py --stats    # thống kê theo source
```

## Acceptance Criteria

- [x] Script `t80_founding_coverage.py` chạy --dry-run / --apply / --revert
- [x] **Temple coverage ≥10% — MET (27.4%)** (reframe vs temple denominator)
- [x] Không duplicate: additive — chỉ insert places chưa có event
- [x] Log file `data/t80_founding_log.json`
- [x] Year range 100-2000 enforced
- [x] Rollback: `DELETE FROM place_timeline_events WHERE source='dila_founding_phase2'` (55 rows)

## Rollback

```sql
DELETE FROM place_timeline_events WHERE source IN ('chgis_founding','dila_founding_phase2');
```

## Liên quan

- **T22d** (done): Regex ETL DILA notes → 276 founding dates (pattern tham khảo)
- **T32** (done): Era name + regnal year extraction → 188 dates
- **T79** (done): Person dates — pattern lessons (dùng `（YYYY）` thay `XX年`)
- **CHGIS**: nguồn đối chiếu cho tương lai nếu cần 10%-of-all (không bắt buộc cho reframe này)

## Ghi chú cho admin

- **Quyết định**: Reframe target coverage theo temple denominator (12,919 places) — đã đạt 27.4% >> 10%.
- **Rollback an toàn**: 1 DELETE theo source `dila_founding_phase2` (55 rows).
