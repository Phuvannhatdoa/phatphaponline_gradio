# T45 — DILA Fosi Zhi ETL Session Log
**Date:** 2026-08-27  
**Task:** T45 — Fosi Zhi Structured Dates

## Summary

Downloaded and processed 9 DILA Fosi Zhi TEI gazetteers (bibl type="Ms").
Extracted founding dates from classical Chinese era-name text patterns.
Inserted 15 rows into `place_timeline_events` (source='dila_fosizhi', confidence=0.85).

## Key Findings

1. **TEI format reality**: `<date when-iso>` attributes do NOT exist in Fosi Zhi XML.
   Dates are embedded as reign-era text (e.g. "元和十四年（八一九）").
   Had to pivot from tag-parsing to era-name regex mining.

2. **Gazetteer count**: 9 gazetteers bibl type="Ms" (not 15 as task file stated).

3. **SSL**: DILA server has missing Subject Key Identifier → ssl.CERT_NONE required.

## Inserted Rows (15 total)

| DILA ID | Year | Gazetteer | Founding Text |
|---------|------|-----------|---------------|
| PL000000059344 | 819 | g026 | 元和十四年（八一九）寰中禪師卓錫結菴 |
| PL000000059758 | 537 | g036 | 梁大同三年（五三七）改為興福寺 |
| PL000000052379 | 503 | g073 | 梁天監二年建（永祚塔）⚠️ |
| PL000000060102 | 872 | g093 | 咸通十三年壬辰...捨基為邵氏菴 |
| PL000000012187 | 537 | g097 | 梁大同三年剏建（延福禪院） |
| PL000000059069 | 760 | g097 | 乾元三年，諸葛氏捨宅創建（廣化寺） |
| PL000000057664 | 766 | g097 | 大曆元年，僧不空建（天王寺） |
| PL000000058996 | 861 | g097 | 咸通二年易其幢塔（永安寺） |
| PL000000027782 | 1103 | g097 | 宋崇寧二年建（報慈寺） |
| PL000000051659 | 1106 | g097 | 宋崇寧五年建（能仁寺） |
| PL000000018705 | 1266 | g097 | 宋咸淳二年，僧妙攝建（真如菴） |
| PL000000059182 | 1344 | g097 | 元至正四年僧寶林建（銘心菴） |
| PL000000010076 | 1325 | g097 | 泰定二年，僧法光建（圓照菴） |
| PL000000048330 | 758 | g100 | 肅宗乾元元年，勅建寺（五台山） |
| PL000000059364* | — | g094 | No match found |

*g094 淨居寺: 1 candidate found but not meeting quality threshold.

## Files Changed

- `scripts/t45_fosizhi_etl.py` — NEW: complete ETL pipeline
- `data/t45_fosizhi_catalog.xml` — (from previous session, 9 gazetteers catalog)
- `data/t45_fosizhi_raw.json` — NEW: 146 raw candidates
- `data/t45_cache/*.zip` — NEW: 9 ZIP archives cached (~700MB)
- `tasks/T45-dila-fosizhi-structured-dates.md` — status: pending → done
- `docs/tasktodo.md` — T45 marked done
- `data/progress_data.json` — rebuilt

## DB State

- place_timeline_events: 3,196 → **3,211 rows** (+15)
- Backup: `docs/sessions/T45_pre_insert_20260827_*.db.bak`

## Algorithm Details

1. Download ZIP via urllib with ssl.CERT_NONE
2. Extract *.tei.xml only (skip JPEG images)
3. Parse XML body to plain text (collapse whitespace — critical for `<lb/>` handling)
4. For each ERA_START name: find `[era][year]年` patterns
5. Check founding keywords within ±80 chars of match
6. Extract temple name from 200 chars before year
7. Match temple name to places_dila (note_category LIKE '%寺廟%')
8. Keep earliest year per DILA ID (founding ≠ later events)
9. Insert with confidence=0.85

## Era Start Table
632 entries in ERA_START covering Han through Qing (140 BCE – 1912 CE).
Includes fix: '元' = 1 in CN_NUM for 元年 (Year 1 of reign).
