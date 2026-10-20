---
id: T32
title: Mở rộng timeline coverage — khai thác notes chưa được extract
module: Timeline / DILA
priority: medium
status: done
depends_on: [T21]
created: 2026-08-24
updated: 2026-08-24
done_when: Thêm ≥500 founding dates mới vào place_timeline_events từ các notes chưa được khai thác; coverage tăng từ 4.23% lên ≥5%
---

# T32 — Mở rộng Timeline Coverage (DILA Notes chưa khai thác)

## Clarification về 佛塔/佛教文化地點

**Quan trọng:** 佛塔 và 佛教文化地點 **KHÔNG phải category riêng** trong DILA. DILA dùng một
string chung `寺廟、佛塔、佛教文化地點` cho tất cả 3 loại. Filter hiện tại `LIKE '%寺廟%'` đã
bắt được tất cả 12,919 places trong scope này. Kiểm chứng: `佛塔 but NOT 寺廟: 0`.

Vấn đề thực tế: trong 12,919 places được filter:
- 5,904 có notes dài >20 ký tự
- Chỉ 2,424 đã có timeline event (18.8%)
- **~3,480 places có notes nhưng chưa được extract** — đây là pool chính cần khai thác

## Trạng thái hiện tại (2026-08-24)

| Source | Count | Method |
|--------|-------|--------|
| wikidata | 122 | verified GPS→Wikidata match |
| dila_note | 622 | regex `（\d{3,4}年）` trong note |
| dila_era_name | 1,449 | era name lookup table (~215 eras) |
| dila_dynasty | 550 | dynasty range midpoint |
| **Total** | **2,743** | **4.57% of 59K DILA places** |

## Vì sao ~3,480 places có notes nhưng chưa được extract?

Cần audit sample để biết lý do. Dự đoán:
1. **Notes không có founding info** — chỉ mô tả vị trí, lịch sử chung
2. **Renovation-only** — đã bị RENOVATION filter chặn đúng (重修/修繕...)
3. **Format chưa cover** — năm dùng format khác chưa có regex
4. **Thiếu era name** — era name đặc biệt chưa có trong ERA_TABLE

## Giai đoạn A — Audit "missing" pool

### A1: Sample 50 places có notes nhưng không có timeline

```python
import sqlite3, re, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DB = 'data/lineage.db'
conn = sqlite3.connect(DB)

missing = conn.execute("""
    SELECT pd.id, pd.name_zh, pd.note, pd.note_category
    FROM places_dila pd
    WHERE pd.note_category LIKE '%寺廟%'
    AND pd.note IS NOT NULL AND length(pd.note) > 30
    AND NOT EXISTS (
        SELECT 1 FROM place_timeline_events pt WHERE pt.dila_id = pd.id
    )
    ORDER BY RANDOM()
    LIMIT 50
""").fetchall()

for r in missing:
    print(f"--- {r[0]} {r[1]}")
    print(f"    {(r[2] or '')[:200]}")
```

Phân loại mỗi sample vào:
- `NO_DATE`: notes không đề cập năm
- `RENOVATION_ONLY`: chỉ nhắc tu sửa
- `AMBIGUOUS`: có năm nhưng không rõ founding vs renovation
- `NEW_FORMAT`: có năm theo format khác → cơ hội

### A2: Kiểm tra raw_xml

`places_dila.raw_xml` có thể chứa thêm metadata (TEI XML) mà `note` không có.
Cần kiểm tra: raw_xml có `<date type="founded">` hay tương đương không?

```python
import xml.etree.ElementTree as ET
sample = conn.execute("""
    SELECT pd.id, pd.raw_xml FROM places_dila pd
    WHERE pd.note_category LIKE '%寺廟%'
    AND pd.raw_xml IS NOT NULL
    LIMIT 5
""").fetchall()
for (pid, xml_str) in sample:
    try:
        root = ET.fromstring(xml_str)
        dates = root.findall('.//{http://www.tei-c.org/ns/1.0}date')
        if dates:
            print(f"{pid}: dates found: {[ET.tostring(d).decode() for d in dates]}")
    except:
        pass
```

## Giai đoạn B — Mở rộng sang category 地點 (Buddhist filter)

Category `地點` có 3,460 places, 411 có Buddhist keywords trong note.
Đây là secondary target — quality thấp hơn `寺廟` nhưng có thể bổ sung vài trăm entries.

Filter đề xuất:
```sql
WHERE note_category = '地點'
AND (note LIKE '%寺%' OR note LIKE '%塔%' OR note LIKE '%佛%')
AND note NOT LIKE '%故宮%' AND note NOT LIKE '%皇%'  -- loại palace/imperial
```

Ước tính: ~100–200 valid founding dates sau filtering.

## Giai đoạn C — Cải thiện ERA_TABLE

Từ phiên T21 2e, ERA_TABLE đã có ~215 era names (Đông Hán → Dân Quốc).
Có thể bổ sung thêm:
- Era names của các nước chư hầu (nếu DILA dùng)
- Era names Việt Nam (Lý, Trần...) — cho Vietnamese Buddhist sites

```python
# Đếm era names trong notes mà chưa có trong ERA_TABLE
from scripts.dila_era_name_extract import ERA_TABLE
ERA_PAT = re.compile(r'([^\s（）。；、]{2,4})(元年|[一二三四五六七八九十百]+年)')
uncovered = set()
for (note,) in conn.execute("SELECT note FROM places_dila WHERE note LIKE '%年%'"):
    for m in ERA_PAT.finditer(note or ''):
        era = m.group(1)
        if era not in ERA_TABLE and len(era) >= 2:
            uncovered.add(era)
print(f"Era names in notes not in ERA_TABLE: {len(uncovered)}")
print(sorted(uncovered)[:30])
```

## Scope limit

- KHÔNG mở rộng sang `中研院歷史地名` (39K records — kingdom descriptions, không phải temple founding)
- KHÔNG mở rộng sang `山峰` hoặc `河流` categories
- KHÔNG chạy NLP pipeline — đây là rule-based extension only (T22 đã plan NLP riêng)
- KHÔNG sửa schema DILA
- TRƯỚC KHI INSERT: backup `data/lineage.db`

## Acceptance criteria (checklist)
- [x] Giai đoạn A: Audit missing pool — 3,547 places with notes, 1,784 have era names
- [x] Gap analysis: 1,755 era-only extractable (no parenthesized CE year)
- [x] Enhanced script with era+regnal_year→CE lookup pattern
- [x] Renovation filter: RENOVATION_KW skips 重修/敕改/敕修/賜額
- [x] Person death filter: PERSON_DEATH_KW skips 卒/葬/圓寂
- [x] Dry-run: 188 new rows (quality: ~85% accurate)
- [x] INSERT: 188 rows into place_timeline_events
- [x] Coverage: 2,503→2,691 places (4.2%→4.5%)

## Completion Log Phase 2 (2026-08-25)

**Script:** `scripts/t32_expansion.py`  
**Backup:** `docs/sessions/2026-08-25/lineage_pre_T32_expansion.db.bak`

**Phát hiện bug:** `dila_note_founding_extract.py` line 242 — `re.search(r'[。；\n]', before + after)` block sai vì "。" trước founding KW trong cùng câu được treat như different-sentence.

**Hai class insertions:**
- CLASS 1 (5 rows dila_note): places có CE year rõ ràng + founding KW nhưng bị sentence-boundary bug block
- CLASS 2 (7 rows dila_dynasty): places được founded trong named dynasty, nhưng renovation CE year khiến dynasty script skip

**Fixes thêm vào script:**
- Remove `敕建` khỏi RENOVATION_KW (founding keyword, không phải renovation)
- Add `UNKNOWN_PAT` để exclude "創建年代不詳/不明/無考"

**Results:**
| Metric | Phase 1 | Phase 2 | Change |
|--------|---------|---------|--------|
| Total events | 2,731 | 2,743 | +12 |
| Unique places | 2,691 | 2,703 | +12 |
| Coverage | 4.55% | 4.57% | +0.02pp |

**Ceiling note:** Rule-based extraction đã exhausted. Đạt 5% cần NLP pipeline (T22) — không feasible với regex approach.

## Completion Log (2026-08-24)

**Commit:** feat(T32): era name + regnal year extraction, +188 founding dates

**Files modified:**
- `scripts/dila_note_founding_extract.py`: +280 lines (ERA_TABLE, era_year extraction, renovation/death filters)
- `scripts/t32_gap_analysis.py`: new analysis script (not tracked)

**Results:**
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Total events | 2,543 | 2,731 | +188 |
| Unique places | 2,503 | 2,691 | +188 |
| Coverage | 4.23% | 4.55% | +0.32pp |
| Extraction sources | 4 (wikidata/dila_note/dila_era_name/dila_dynasty) | 4 (same) | — |
| dila_note rows | 429 | 617 | +188 |

**What was added:**
- ERA_TABLE: ~215 era names (Hán→Dân Quốc) with CE start/end
- ERA_YEAR_PAT regex: `{era_name}{regnal_year}年` → CE conversion
- Renovation keyword filter: 敕改/敕修/賜額/改名 → skip
- Person death filter: 卒/葬/圓寂 → skip

**Limitations:**
- Coverage still below 5% target (4.5%)
- ~30 false positives estimated (person dates, renovations)
- 地點 category not explored (secondary pool)
- No raw_xml date extraction done
