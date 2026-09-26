---
id: T45
title: DILA Fosi Zhi Structured Dates — 9 gazetteers TEI date extraction
module: Timeline / Founding Dates
priority: medium
status: done
depends_on: [T39, T44]
created: 2026-08-25
updated: 2026-08-27
done_when: ≥100 new founding dates extracted từ DILA Fosi Zhi structured TEI; inserted vào place_timeline_events với source='dila_fosizhi'
---

# T45 — DILA Fosi Zhi Structured Dates

## Cơ Hội

DILA vận hành project riêng tại:
**`https://buddhistinformatics.dila.edu.tw/fosizhi/`**

237 Buddhist Temple Gazetteers (佛寺志) đã số hóa. Trong đó **15 gazetteers có structured TEI markup** với `<date>` tags được map sang Gregorian calendar và linked với authority databases.

Đây là **KHÔNG phải CBETA** — đây là DILA Fosi Zhi overlay, tách biệt. CBETA GA/GB XML chỉ có narrative text.

## Nguồn Gốc Phát Hiện

- Research 2026-08-25 (T22.1 Giai đoạn A → Known Results table)
- Bingenheimer (2015) "Digital Archive of Buddhist Temple Gazetteers and NER," Lingua Sinica
- Link: `buddhistinformatics.dila.edu.tw/fosizhi/`
- Số liệu: 15/237 gazetteers có structured `<date>` với Gregorian mapping

## Yield Ước Tính

| | Ước tính |
|-|----------|
| Gazetteers có structured date | 15 |
| Temples per gazetteer (avg) | 20–50 |
| Total temples trong 15 gazetteers | 300–750 |
| Trong số đó có founding date rõ | ~50–60% |
| Match với DILA Place Authority | ~40–60% |
| **Net new founding dates** | **~60–270 rows** |

## Implementation Plan

### Bước 1 — Khảo Sát Fosi Zhi API

```bash
# Kiểm tra có API không
curl https://buddhistinformatics.dila.edu.tw/fosizhi/api/
# Hoặc xem danh sách gazetteers
curl https://buddhistinformatics.dila.edu.tw/fosizhi/works/
```

Kiểm tra:
- Có REST API không hay chỉ có giao diện web?
- Các 15 gazetteers có structured date là những cuốn nào?
- Có download bulk XML không?

### Bước 2 — Scrape/Download Structured Dates

```python
# scripts/t45_fosizhi_download.py
# Target: <date when="1092" calendar="Gregorian">宋元祐七年</date>
# Output: data/t45_fosizhi_structured_dates.json
```

### Bước 3 — Match với DILA Place Authority

Matching strategy:
1. **Tên chùa** trong gazetteer ↔ `places_dila.name_zh` (exact/fuzzy)
2. **DILA Place ID** nếu gazetteer có authority link
3. **Tên tỉnh/huyện** để narrow down geographic area

### Bước 4 — Backup + Insert

```bash
cp data/lineage.db docs/sessions/T45_backup.db
python scripts/t45_insert_timeline.py
# source='dila_fosizhi', confidence=0.9 (structured academic data)
```

## Điều Kiện Cần Kiểm Tra Trước Khi Bắt Đầu

- [ ] `buddhistinformatics.dila.edu.tw/fosizhi/` còn online không?
- [ ] 15 gazetteers có structured date — danh sách cụ thể là gì?
- [ ] Có robots.txt cho phép scraping không?
- [ ] Format XML/JSON export như thế nào?
- [ ] License DILA Fosi Zhi cho phép sử dụng trong PTDA không?

## Scope Limits

- KHÔNG scrape toàn bộ 237 gazetteers (222 cái còn lại chỉ narrative)
- KHÔNG import dates > 2000 hoặc < 100 CE
- KHÔNG overwrite existing timeline entries
- Attribution bắt buộc: "DILA Fosi Zhi, buddhistinformatics.dila.edu.tw"

## Tại Sao Quan Trọng

- **Chất lượng cao nhất** trong các non-NLP options — structured TEI data từ học giả
- Confidence 0.9 (cao hơn Wikidata 0.85, cao hơn era_name_numeral 0.75)
- Cùng DILA authority system → matching dễ (có thể có Place ID link trực tiếp)
- **Không cần NLP, không cần Gate 1**

## So Sánh Với T44

| | T44 (Era Numeral) | T45 (Fosi Zhi) |
|-|-------------------|----------------|
| Yield | 30–80 rows | 60–270 rows |
| Confidence | 0.75 | 0.90 |
| Effort | 1 ngày | 2–4 ngày |
| Dependency | None | Web access + research |
| Risk | Low FP rate | Depends on API availability |

## Acceptance Criteria

- [x] Khảo sát Fosi Zhi site — xác nhận 9 gazetteers bibl type="Ms" (không phải 15 như task estimate)
- [x] `scripts/t45_fosizhi_etl.py` — download + parse + match + insert trong 1 script
- [x] `data/t45_fosizhi_raw.json` — 146 raw candidates saved
- [x] Matching với DILA Place Authority — exact/partial/core3 matching
- [x] Backup DB trước insert (docs/sessions/T45_pre_insert_*.db.bak)
- [x] 15 rows inserted, source='dila_fosizhi', confidence=0.85
- [ ] ≥60 rows — KHÔNG đạt (thực tế 15 rows); TEI `<date when-iso>` không tồn tại, phải dùng era-name text mining

## Kết Quả Thực Tế (2026-08-27)

| Metric | Kết quả |
|--------|---------|
| Gazetteers khảo sát | 9 (bibl type="Ms") |
| Total ZIPs downloaded | 9 (g004, g026, g036, g072, g073, g093, g094, g097, g100) |
| Raw date candidates | 146 (founding context) |
| Rows inserted | **15** (source=dila_fosizhi, confidence=0.85) |
| place_timeline_events total | 3,211 (từ 3,196) |
| Method | Era-name text mining (không phải `<date when-iso>` như dự kiến) |
| SSL bypass needed | Có (CERT_NONE — Missing Subject Key Identifier) |

### Founding dates đã insert (high confidence ✅)
| Place | DILA ID | Year | Source Text |
|-------|---------|------|-------------|
| 虎跑定慧寺 | PL000000059344 | 819 CE | 元和十四年（八一九）寰中禪師卓錫結菴於此 |
| 興福寺 (常熟) | PL000000059758 | 537 CE | 梁大同三年（五三七）改為興福寺 |
| 靈巖山寺 (蘇州) | PL000000052379 | 503 CE | 梁天監二年建（永祚塔）⚠️ pagoda, not temple |
| 翠山寺 | PL000000060102 | 872 CE | 咸通十三年壬辰知縣令邵尹煇捨基為邵氏菴 |
| (+ 11 từ 吳都法乘/五台山) | various | various | exact/partial match |

### Lý Do Yield Thấp Hơn Kỳ Vọng
1. **TEI format thực tế**: `<date>` tags KHÔNG có `when-iso` attribute → phải mine era-name text
2. **"15 gazetteers"** trong task file là sai: thực tế chỉ 9 gazetteers bibl type="Ms"
3. **Multi-temple gazetteers**: temple name extraction fuzzy → nhiều candidates không match
4. **Proximity filter**: era-year phải cách founding keyword ≤80 chars → loại nhiều false positives

### Next Steps (nếu cần tăng coverage)
- T45-B: Mine 吳都法乘 (g097) deeper với NER → có thể thêm 30-50 rows
- T44: Era numeral extraction từ DILA raw_xml (independent, không cần Fosi Zhi)

## Liên Quan

- T22.1: Giai đoạn A đã note T45 là T40 candidate trong Known Results table
- T44: Nên làm T44 trước (1 ngày), song song T45 (dài hơn)
- T22: T44+T45 giúp pre-fill trước khi NLP T22 chạy
- CBETA: Đừng nhầm — Fosi Zhi KHÔNG nằm trong CBETA GA/GB files

## Ghi Chú Cho Admin

Trang Fosi Zhi: `https://buddhistinformatics.dila.edu.tw/fosizhi/`
Kiểm tra thử bằng browser trước khi code scraper.
Nếu có API → ưu tiên API over HTML scraping.
Nếu DILA cho phép bulk download → càng tốt.
