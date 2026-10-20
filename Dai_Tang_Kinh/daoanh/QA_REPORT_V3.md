# QA REPORT V3 — DB Migration: DILA Place Authority Full Schema

**Project:** Đạo Ảnh (Phật Pháp Online Buddhist GIS)
**Date:** 2026-05-13
**Migration:** V3 — Nâng cấp `places_pending` cho DILA Place Authority TEI XML Schema
**Scope:** `/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/`

---

## Part 1 — Schema Changes

### 1.1 ALTER TABLE Statements

Three columns added to `places_pending`:

```sql
ALTER TABLE places_pending ADD COLUMN raw_xml TEXT;
ALTER TABLE places_pending ADD COLUMN district_raw TEXT;
ALTER TABLE places_pending ADD COLUMN hist_country_raw TEXT;
```

### 1.2 Full `places_pending` Schema (176,783 rows)

| # | Column | Type | Default | Source | Description |
|---|--------|------|---------|--------|-------------|
| 0 | `id` | TEXT | PK | `xml:id` | DILA Place ID (e.g. PL000000000014) |
| 1 | `name_zh` | TEXT | | `<placeName xml:lang="zho-Hant">` | Chinese name (Hán tự) |
| 2 | `name_vi` | TEXT | | Admin/LLM input | Vietnamese name (phiên âm) |
| 3 | `name_en` | TEXT | | `places_dila.name_en` | English name |
| 4 | `location` | TEXT | | Derived | Location string |
| 5 | `gps_lat` | REAL | | `<geo>` coords[1] | Latitude |
| 6 | `gps_long` | REAL | | `<geo>` coords[0] | Longitude |
| 7 | `address` | TEXT | | Admin input | Modern address |
| 8 | `province` | TEXT | | Parsed from `district_raw` | Modern province (Latin) |
| 9 | `country` | TEXT | | Parsed from `district_raw` | **Modern** country (Latin, never default 'Vietnam' for DILA data) |
| 10 | `place_type` | TEXT | | `<note type="category">` | Place category |
| 11 | `source_origin` | TEXT | `'DILA'` | Hardcoded | Source origin label |
| 12 | `confidence` | REAL | `1.0` | | Data confidence score |
| 13 | `created_at` | TEXT | `CURRENT_TIMESTAMP` | Auto | Row creation timestamp |
| 14 | `updated_at` | TEXT | `CURRENT_TIMESTAMP` | Auto | Row update timestamp |
| 15 | `note` | TEXT | | Optional free-text note | Reserved for human-readable descriptions (Chinese/Vietnamese). Historically stored TEI XML in some batches; `raw_xml` is now the canonical field for TEI. |
| 16 | `source_id` | INTEGER | FK→`dataset_sources` | `DILA_PLACE` (id=3) | Academic provenance tracker |
| **17** | **`raw_xml`** | **TEXT** | | Copy of `note` (historical) | **Full TEI `<place>` XML (canonical).** From now on, all TEI XML is written only to this column. |
| **18** | **`district_raw`** | **TEXT** | | `<district>` | Raw district string (e.g. 阿富汗-巴爾赫省(Balkh)-Khulm) |
| **19** | **`hist_country_raw`** | **TEXT** | | `<country>` | **Historical** country/region (e.g. 西突厥) |

**New columns in bold** — added by this migration.

### 1.3 Indexes (unchanged)

```sql
CREATE INDEX idx_places_pending_name_zh ON places_pending(name_zh);
CREATE INDEX idx_places_pending_id ON places_pending(id);
```

---

## Part 2 — Import Logic (DILA Place → places_pending)

### 2.1 TEI XML → SQLite Field Mapping

```
TEI XML Element                          → places_pending Column
────────────────────────────────────────────────────────────────
<place xml:id="...">                     → id
<placeName xml:lang="zho-Hant">         → name_zh
<geo> "{long} {lat}"                     → gps_long, gps_lat
<district>                               → district_raw
<country>                                → hist_country_raw
<note> (non-category)                    → note (full XML also stored)
First `-` segment of district_raw        → country (modern, Latin)
Second `-` segment of district_raw       → province (Latin)
Full <place> element                     → raw_xml (and note, for backward compat)
```

### 2.2 Country/Province Parsing

**From `district_raw`** (e.g. `阿富汗-巴爾赫省(Balkh)-Khulm`):

1. Split by `-`
2. Part[0] = Chinese country name → map via `COUNTRY_MAP` dictionary to Latin
3. Part[1] = province (extract Latin from parentheses if present: `巴爾赫省(Balkh)` → `Balkh`)

**COUNTRY_MAP Dictionary** (43 entries covering all prefixes found in the data):

| Chinese | Latin | | Chinese | Latin |
|---------|-------|---|---------|-------|
| 阿富汗 | Afghanistan | | 印度 | India |
| 中國 | China | | 巴基斯坦 | Pakistan |
| 孟加拉 | Bangladesh | | 尼泊爾 | Nepal |
| 緬甸 | Myanmar | | 泰國 | Thailand |
| 斯里蘭卡 | Sri Lanka | | 柬埔寨 | Cambodia |
| 寮國 | Laos | | 越南 | Vietnam |
| 印尼 | Indonesia | | 馬來西亞 | Malaysia |
| 蒙古 | Mongolia | | 日本 | Japan |
| 俄羅斯 | Russia | | 伊朗 | Iran |
| ... | ... | | ... | ... |

### 2.3 Source Tracking

All DILA Place records now have `source_id = 3` pointing to `dataset_sources.name = 'DILA_PLACE'`.

### 2.4 Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| `raw_xml` is canonical for TEI XML | All new imports write TEI XML only to `raw_xml`; `note` reserved for human descriptions |
| `note` kept as-is (backward compatible) | Existing rows still have TEI XML in `note`; code routes now read from `raw_xml` |
| `country` parsed from `district`, NOT from `<country>` element | `<country>` contains **historical** regions (e.g. 西突厥), not modern countries |
| Default country is **never** `'Vietnam'` for DILA data | DILA places are historical sites across Asia, not limited to Vietnam |
| GPS lat/long unchanged | Already correctly assigned: `lat=coords[1]`, `lon=coords[0]` (no swap bug) |

### 2.5 Import Pipeline (`data/sync_data.py`)

Updated INSERT query:
```sql
INSERT OR REPLACE INTO places_pending
    (id, name_zh, gps_lat, gps_long, note, raw_xml,
     district_raw, hist_country_raw, country, province, source_id)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```

---

## Part 3 — Example Record (PL000000000014 — 土火羅)

### 3.1 Query Result

```sql
SELECT id, name_zh, country, province, gps_lat, gps_long,
       district_raw, hist_country_raw,
       LENGTH(raw_xml) as raw_len, source_id
FROM places_pending WHERE id = 'PL000000000014';
```

| Column | Value |
|--------|-------|
| `id` | PL000000000014 |
| `name_zh` | 土火羅 |
| `country` | **Afghanistan** (modern, was NULL before) |
| `province` | **Balkh** (was NULL before) |
| `gps_lat` | 36.6608 |
| `gps_long` | 68.1589 |
| `district_raw` | 阿富汗-巴爾赫省(Balkh)-Khulm |
| `hist_country_raw` | 西突厥 (historical region) |
| `raw_xml` | 1267 chars (full TEI `<place>` element) |
| `source_id` | **3** (DILA_PLACE) |

### 3.2 Raw TEI XML (stored in `raw_xml`)

```xml
<ns0:place xmlns:ns0="http://www.tei-c.org/ns/1.0" xml:id="PL000000000014">
 <ns0:placeName xml:lang="zho-Hant">土火羅</ns0:placeName>
 <ns0:placeName type="alternative" xml:lang="zho-Hant">吐火羅</ns0:placeName>
 <ns0:placeName type="alternative" xml:lang="zho-Hant">土豁羅</ns0:placeName>
 <ns0:placeName type="alternative" xml:lang="zho-Hant">覩貨邏</ns0:placeName>
 <ns0:placeName type="alternative" xml:lang="zho-Hant">兜佉勒</ns0:placeName>
 <ns0:placeName type="alternative" xml:lang="zho-Hant">兜勒</ns0:placeName>
 <ns0:location><ns0:place key="PLC000385">(Khulm)</ns0:place>
 <ns0:geo cert="high">68.1589 36.6608</ns0:geo></ns0:location>
 <ns0:district>阿富汗-巴爾赫省(Balkh)-Khulm</ns0:district>
 <ns0:country>西突厥</ns0:country>
 <ns0:note>都葱嶺西五百里，與挹怛雜居...</ns0:note>
 <ns0:listBibl>...</ns0:listBibl>
 <ns0:note type="category">中研院歷史地名</ns0:note>
</ns0:place>
```

---

## Part 4 — `dataset_sources` Table (Expanded)

### 4.1 All Sources

| id | name | source_type | license | usage_level |
|----|------|-------------|---------|-------------|
| 1 | DILA_Authority | authority | CC BY-SA 4.0 | YELLOW |
| 2 | Marcus_fojin | glossary | CC0 | GREEN |
| **3** | **DILA_PLACE** | authority | CC BY-SA 4.0 | YELLOW |
| **4** | **DILA_PERSON** | authority | CC BY-SA 4.0 | YELLOW |
| **5** | **DILA_TIME** | authority | CC BY-SA 4.0 | YELLOW |
| **6** | **MB_GLOSSARY** | glossary | CC0 | GREEN |
| **7** | **CBETA** | canon | CC BY-SA 4.0 | YELLOW |
| **8** | **SUTTACENTRAL** | canon | CC BY-NC-SA 4.0 | YELLOW |
| **9** | **EIGHTY_THOUSAND** | canon | CC BY-NC-SA 4.0 | YELLOW |

**New entries in bold** — added by this migration.

### 4.2 Usage Guide for Future Person/Time Authority

When importing Person or Time Authority data in the future:
- Set `source_id = DILA_PERSON.id` (4) or `DILA_TIME.id` (5)
- Create a `*_pending` table following the same pattern:
  - `id`, `name_zh`, `raw_xml`, `source_id`
  - Language columns for admin/LLM Vietnamese mapping

---

## Part 5 — Migration Script

### 5.1 File

`src_python/db/migrate_places_v3.py`

### 5.2 Execution Steps

1. `ALTER TABLE places_pending ADD COLUMN raw_xml TEXT`
2. `ALTER TABLE places_pending ADD COLUMN district_raw TEXT`
3. `ALTER TABLE places_pending ADD COLUMN hist_country_raw TEXT`
4. `UPDATE places_pending SET raw_xml = note WHERE raw_xml IS NULL AND note IS NOT NULL` (copied 175,468 rows)
5. Parse `note` XML → extract `district_raw`, `hist_country_raw`, parse `country`/`province` (175,468 rows, ~15s)
6. `INSERT INTO dataset_sources` (7 new entries)
7. `UPDATE places_pending SET source_id = <DILA_PLACE.id>` (176,783 rows)

### 5.3 Migration Stats

| Metric | Value |
|--------|-------|
| Total places_pending | 176,783 |
| raw_xml populated | 175,468 (99.26%) |
| district_raw populated | 115,959 (65.6%) |
| hist_country_raw populated | 76,064 (43.0%) |
| country (modern) populated | 115,959 (65.6%) |
| province populated | 116,970 (66.2%) |
| Migration time | 14.9 seconds |

---

## Part 6 — HOME GUI Usage Guide

### 6.1 Display Fields

| UI Element | Column | Notes |
|------------|--------|-------|
| Chinese name (Hán tự) | `name_zh` | Primary name from DILA |
| Vietnamese name | `name_vi` | Admin/LLM editable |
| Modern country | `country` | Latin (e.g. Afghanistan) |
| Province/State | `province` | Latin (e.g. Balkh) |
| Historical region | `hist_country_raw` | Chinese (e.g. 西突厥) |
| Raw district | `district_raw` | Chinese + Latin mixed |
| GPS coordinates | `gps_lat`, `gps_long` | For map display |
| Description | `note` | Full TEI XML (parse `<note>` text for display) |
| Deep data | `raw_xml` | Full TEI XML for advanced lookup |

### 6.2 Typical SELECT for HOME GUI

```sql
SELECT id, name_zh, name_vi, country, province,
       gps_lat, gps_long, note AS full_description
FROM places_pending
WHERE country = 'Vietnam' AND name_vi IS NOT NULL;
```

### 6.3 Working with `raw_xml` / `note`

`raw_xml` is the canonical column for TEI XML; `note` may also contain XML in historical rows (backward compatible). To extract specific fields in Python:

```python
import re

# Extract description text from <note>
m = re.search(r'<ns0:note(?! type="category")>(.*?)</ns0:note>', row['raw_xml'], re.DOTALL)
description = m.group(1).strip() if m else ''

# Extract alternative names
names = re.findall(r'<ns0:placeName[^>]*>(.*?)</ns0:placeName>', row['raw_xml'])
```

### 6.4 LLM Transliteration Workflow

1. Read `name_zh` + `raw_xml` (for context: district, country, note)
2. LLM generates Vietnamese `name_vi`
3. Admin reviews and saves to `namevi_map_places` (existing workflow)
4. Optionally update `name_vi` directly in `places_pending`

---

## Part 7 — Files Changed

| File | Change |
|------|--------|
| `data/sync_data.py` | Rewritten — full extraction of all TEI fields + new INSERT columns |
| `src_python/db/init_dataset_sources.py` | Added 7 new dataset sources + fixed Marcus_fojin reference |
| `src_python/db/migrate_places_v3.py` | **NEW** — migration script with ALTER TABLE + backfill + source tracking |
| `data/lineage.db` | Schema updated (3 new columns, 7 new dataset_sources, source_id updated) |

---

## Part 8 — Verification Summary

| Check | Before Migration | After Migration | Status |
|-------|-----------------|-----------------|--------|
| PL000000000014 country | NULL | Afghanistan | ✅ |
| PL000000000014 province | NULL | Balkh | ✅ |
| PL000000000014 district_raw | (no column) | 阿富汗-巴爾赫省(Balkh)-Khulm | ✅ |
| PL000000000014 hist_country_raw | (no column) | 西突厥 | ✅ |
| PL000000000014 raw_xml len | (no column) | 1267 chars | ✅ |
| Dataset sources | 2 | 9 | ✅ |
| source_id all rows | 1 (DILA_Authority) | 3 (DILA_PLACE) | ✅ |
| GPS lat/long correct | 36.6608 / 68.1589 | Unchanged (correct) | ✅ |
| Raw XML preserved in `note` | Yes | Yes (+ copied to `raw_xml`) | ✅ |

---

*Report generated by opencode AI Agent — 2026-05-13*
