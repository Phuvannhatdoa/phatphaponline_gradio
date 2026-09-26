---
id: T42
title: CBETA Ref Pivot — Tìm person_id cho 5,663 tên chưa match trong place_person_bibl
module: Person Authority
priority: high
status: done
depends_on: [T40]
created: 2026-08-25
updated: 2026-08-25
done_when: Tỷ lệ match trong place_person_bibl tăng từ 60.7% lên ≥70%; ≥1,000 rows được resolve thêm person_id
---

# T42 — CBETA Ref Pivot

## Mục tiêu

5,663 entries trong `place_person_bibl` có `person_id = NULL` vì tên không khớp `people.name_zh`.
Nhiều tên này thuộc danh tăng nổi tiếng (鳩摩羅什, 釋智顗, 竺佛圖澄...) — họ CÓ trong
Person Authority XML nhưng DILA lưu tên biến thể khác trong `people` table của ta.

**CBETA Ref là pivot key:** cùng 1 đoạn văn CBETA (T50n2060_p0457c16) vừa được trích dẫn trong
Person Authority (để nói "người này xuất hiện trong văn bản đó") vừa được trích dẫn trong
Place Authority (để nói "địa danh này xuất hiện trong văn bản đó"). Join = person↔place.

## Background — Số liệu từ Diagnosis 2026-08-25

- `place_person_bibl`: 5,663 unmatched entries (person_id=NULL)
- Person Authority: 2,000 persons sample có 3,195 unique CBETA refs
- Overlap với place_person_bibl: **909 shared CBETA refs** → anchor points cho pivot
- Match rate hiện tại: 60.7% → target ≥70%

## Cơ chế chi tiết

```
place_person_bibl row:
  place_id="PL000000023255" (少林寺)
  person_name_raw="鳩摩羅什"
  cbeta_ref="T50n2059_p0419b04"
  person_id=NULL  ← cần resolve

Person Authority XML:
  <person xml:id="A001234">
    <persName>鳩摩羅什</persName>       ← tên KHÁC với "people.name_zh" của ta
    <listBibl>
      <bibl>T50n2059_p0419b04</bibl>  ← SAME cbeta_ref!
    </listBibl>
  </person>

→ UPDATE place_person_bibl SET person_id='A001234'
   WHERE cbeta_ref='T50n2059_p0419b04' AND person_id IS NULL
```

## Tại sao 鳩摩羅什 không trong `people`?

Khả năng 1: `people.name_zh` lưu tên khác (羅什, 鸠摩罗什, 佛教師鳩摩羅什...)
Khả năng 2: DILA Person Authority ID cho 鳩摩羅什 tồn tại nhưng `people` table chưa import đủ
Khả năng 3: `people` table được import từ nguồn khác với tên biến thể

→ T42 bypass vấn đề này bằng cách JOIN qua CBETA ref, không cần khớp tên.

## Cách tiếp cận

### Script `scripts/t42_cbeta_pivot.py`

**Bước 1**: Build index từ Person Authority XML
```python
cbeta_to_persons = defaultdict(list)
for person in persons:
    pid = person.get(XML_ID)
    for bibl in person.findall('.//tei:bibl', NS):
        cbeta_ref = extract_cbeta_ref(bibl_text)
        if cbeta_ref:
            cbeta_to_persons[cbeta_ref].append(pid)
```

**Bước 2**: Join với unmatched entries
```python
unmatched = conn.execute(
    "SELECT id, cbeta_ref, person_name_raw FROM place_person_bibl WHERE person_id IS NULL AND cbeta_ref IS NOT NULL"
).fetchall()

for row in unmatched:
    candidates = cbeta_to_persons.get(row['cbeta_ref'], [])
    if len(candidates) == 1:
        # Unambiguous match → update
        conn.execute("UPDATE place_person_bibl SET person_id=?, confidence=0.8 WHERE id=?",
                    (candidates[0], row['id']))
    elif len(candidates) > 1:
        # Multiple persons in same passage → fuzzy name filter
        best = fuzzy_name_match(row['person_name_raw'], candidates)
        if best:
            conn.execute("UPDATE place_person_bibl SET person_id=?, confidence=0.7 WHERE id=?",
                        (best, row['id']))
```

**Bước 3**: Fuzzy name matching cho ambiguous cases
- Strip 釋/尼/俗 prefix từ cả hai phía
- Levenshtein distance ≤ 1 hoặc substring match
- Chỉ accept khi similarity ≥ 0.8

### Confidence scoring
```
1.0 = name exact match (đã có từ T40)
0.9 = name match after strip prefix (đã có từ T40)
0.8 = CBETA ref pivot, unambiguous (1 person per ref)
0.7 = CBETA ref pivot, ambiguous (fuzzy name filter)
0.0 = unmatched (giữ NULL)
```

## Caveat quan trọng

Cùng CBETA passage có thể đề cập NHIỀU người → cbeta_ref pivot không 100% chính xác.
Ví dụ: T50n2060_p0457c16 nói về "khi 鳩摩羅什 đến 長安, đã gặp 道安..."
→ cả 鳩摩羅什 lẫn 道安 đều có CBETA ref này.

Giải pháp: chỉ accept `confidence=0.8` khi `len(candidates)==1` (unique person per passage).
Khi `len(candidates)>1` → cần fuzzy name match để giảm nhầm.

## Acceptance criteria
- [x] Script `scripts/t42_cbeta_pivot.py` chạy, idempotent
- [x] `place_person_bibl` rows với person_id IS NOT NULL tăng từ 8,513 → 10,458 (+1,945)
- [x] Match rate tổng thể: 61.1% → 75.1% (vượt target ≥70%)
- [x] ETL log với breakdown: unambiguous_matched=1,795, fuzzy_matched=150, still_unmatched=3,475
- [x] Spot check: 鳩摩羅什 (A002515 ✓), 釋智顗 (A004413 ✓), 竺佛圖澄 (A002776 ✓)
- [ ] Confidence 0.8/0.7 entries được UI hiển thị với badge "CBETA Pivot" khác biệt (UI chưa phân biệt confidence level)

## Kết quả thực tế (2026-08-25)

| Metric | Trước | Sau |
|---|---|---|
| person_id IS NOT NULL | 8,513 | 10,458 |
| Match rate | 61.1% | 75.1% |
| Unambiguous pivot (conf=0.8) | - | +1,795 |
| Fuzzy name match (conf=0.7) | - | +150 |
| Still unmatched | - | 3,475 (3,061 không có cbeta_ref trong Person Authority) |

**Key bug fix:** index cần dùng full ref format `T50n2060_p0447c17` (không strip page suffix), vì cùng 1 cuốn sách có nhiều nhân vật ở các trang khác nhau.

Script: `daoanh/scripts/t42_cbeta_pivot.py`  
Log: `daoanh/docs/sessions/2026-08-25/t42_etl.log`
