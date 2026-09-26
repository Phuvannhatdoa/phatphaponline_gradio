---
id: T44
title: Era Name + Chinese Numeral Founding Extraction — Non-NLP bridge đến T22
module: Timeline / Founding Dates
priority: medium
status: blocked
depends_on: [T39]
created: 2026-08-25
updated: 2026-08-25
done_when: ≥30 new founding dates extracted từ era-name Chinese numeral patterns trong note; inserted vào place_timeline_events
---

# T44 — Era Name + Chinese Numeral Founding Extraction

## Vấn đề

Sau T39 (Wikidata) và T32 (regex note), coverage founding date vẫn ở 4.59%.
Script hiện tại (`dila_note_founding_extract.py`) chỉ nhận dạng năm CE trong ngoặc fullwidth:
`（XXXX）` — nhưng **209 temple notes** viết theo format Hán học:

```
康熙五十五年敕建          ← không có CE parens
乾隆二十三年重建
太平興國七年八月落成，以睿見主之
明洪武三年重建
```

Đây là thông tin có cấu trúc rõ ràng, **không cần NLP** — chỉ cần:
1. Dictionary lookup: era name → start year CE
2. Chinese numeral → Arabic number converter
3. Tính `start_year + ordinal - 1` = CE year

## Số Liệu (audit 2026-08-25)

| | Số lượng |
|-|----------|
| Temple notes chưa có founding date, có `年` | 574 |
| Trong đó có era name + Chinese numeral rõ ràng | **209** |
| Trong đó có era name GẦN founding keyword (創建/始建/敕建...) | **26** |
| Yield thực tế ước tính (sau lọc renovation) | **30–80 rows** |

## Cách Implement

### Bước 1 — Chinese Numeral Table

```python
CN_NUM = {
    '元': 1, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
    '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
    '百': 100, '零': 0, '兩': 2,
}

def cn_to_int(s: str) -> int:
    """'五十五' → 55, '二十三' → 23, '元' → 1"""
    # Handle 元 = 1st year
    if s in ('元', '元年'):
        return 1
    # Parse: 二十三 = 2*10+3, 五十五 = 5*10+5
    ...
```

### Bước 2 — Era Name → Start Year CE

Dùng table Chinese calendar era names đã có sẵn trong DILA era_name data hoặc hardcode top eras:

```python
ERA_START = {
    '洪武': 1368, '永樂': 1403, '宣德': 1426, '正統': 1436, '景泰': 1450,
    '天順': 1457, '成化': 1465, '弘治': 1488, '正德': 1506, '嘉靖': 1522,
    '隆慶': 1567, '萬曆': 1573, '泰昌': 1620, '天啟': 1621, '崇禎': 1628,
    '順治': 1644, '康熙': 1662, '雍正': 1723, '乾隆': 1736, '嘉慶': 1796,
    '道光': 1821, '咸豐': 1851, '同治': 1862, '光緒': 1875, '宣統': 1908,
    '貞觀': 627, '武德': 618, '開元': 713, '天寶': 742, '元和': 806,
    '建隆': 960, '開寶': 968, '太平興國': 976, '元豐': 1078,
    '紹興': 1131, '淳熙': 1174, '嘉定': 1208,
    '至元': 1264, '大德': 1297, '至正': 1341,
}
```

### Bước 3 — Scan + Filter

```python
ERA_NUMERAL_PAT = re.compile(
    r'(ERA_NAMES)([元一二三四五六七八九十百零兩]{1,6})年'
)
FOUNDING_KW = re.compile(r'創建|始建|敕建|建院|建寺|立寺|開山|草創|創立')
RENOVATION_KW = re.compile(r'重[修建葺]|重建|修繕|重修|修復')

for place in temple_notes_without_founding:
    for m in ERA_NUMERAL_PAT.finditer(note):
        era, numeral = m.group(1), m.group(2)
        ordinal = cn_to_int(numeral)
        ce_year = ERA_START[era] + ordinal - 1
        
        ctx = note[max(0, m.start()-60) : m.end()+60]
        if FOUNDING_KW.search(ctx) and not RENOVATION_KW.search(ctx):
            # High confidence founding
            INSERT(dila_id, ce_year, source='dila_note', 
                   source_ref='era_name_numeral', confidence='0.75')
```

### Bước 4 — Dry-run Review

In tất cả candidates để admin review trước khi insert (30-80 rows đủ nhỏ để check thủ công).

## Ước Tính Yield

| Scenario | Count |
|----------|-------|
| Conservative (chỉ founding keyword, không renovation) | ~30 |
| Moderate | ~55 |
| Optimistic (all era_name_numeral near 年字) | ~80 |

## Scope Limits

- KHÔNG xử lý era names NGOÀI list trên (tránh match sai)
- KHÔNG insert nếu note có 不詳/無考/年代不明
- KHÔNG overwrite existing timeline entries
- Confidence = 0.75 (thấp hơn verified 0.85, cao hơn dynasty_range)
- Script: `scripts/t44_era_numeral_extract.py`

## Blockers

**2026-08-25 audit:** Query `places_dila WHERE note_category='寺廟' AND dila_id NOT IN place_timeline_events` trả 0 rows — T32 đã extract hết era name patterns (kể cả Chinese numeral) trong tất cả temple notes. T44 không còn candidates. Đề xuất: mark blocked/cancelled.

## Tại Sao Làm Ngay (Không Cần Gate 1)

- Không cần NLP, không cần Ollama, không cần Gate 1 approval
- Là **bridge** trong khi chờ T22 (NLP) được phê chuẩn
- Ceiling từ task này: +30–80 rows → coverage ~4.60–4.62%
- Sau T44 + T45 (Fosi Zhi) → ước tính ~4.7–5.0% trước khi NLP

## Acceptance Criteria

- [ ] `scripts/t44_era_numeral_extract.py` viết xong với dry-run mode
- [ ] Dry-run output reviewed bởi admin (kiểm tra false positives)
- [ ] Backup DB trước insert
- [ ] ≥30 rows inserted, confidence 0.75
- [ ] Coverage tăng ít nhất +0.05pp

## Liên Quan

- T32: Timeline coverage expansion (predecessor)
- T39: Wikidata spatial (predecessor)
- T45: DILA Fosi Zhi (parallel non-NLP path)
- T22: NLP T22 gate — T44 là bridge trong khi chờ
