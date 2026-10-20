# XML Import Audit Report — Person Authority Data Gap

**Date:** 2026-10-12  
**Status:** CONFIRMED — Code gaps identified  
**Impact:** CRITICAL — CBETA citations, works, active places not imported for any person

---

## Executive Summary

The import pipeline for Buddhist_Studies_Person_Authority.xml is **INCOMPLETE**:

- ✅ **4 fields imported:** dila_id, name_zh, appellations, gender
- ❌ **9 fields extracted but DISCARDED:** dynasty, concise biography, place of origin, worksInTripitaka, worksBy, mentionedIn, activeAt, listBibl (CBETA), Wikidata

**Example: Person A000035** 
- XML contains: 8 CBETA citations, 6 works, 4 active places, 5 mentioned sources
- Database rows: 0 (all discarded during import)

---

## Root Cause Analysis

### 1. Main Import Script: `person_import_etl.py` (T253)

**Design Philosophy:** Intentionally MINIMAL
```python
# Line 11-13 (AGENTS.md rule + code comment):
# "KHÔNG BỊA: chỉ map cột 1:1 từ XML (dila_id, name_zh, appellations, gender).
#  KHÔNG được phỏng đoán (bài học T252: tự suy dynasty sai)."
# → Do NOT guess data. Only import what's 100% certain from XML.
```

**What Gets Extracted (lines 116-176):**
```python
def iter_persons(xml_path):
    # Extracts all these from XML:
    ├─ dila_id (line 122) → ✅ INSERTED
    ├─ name_zh (line 136) → ✅ INSERTED
    ├─ alts/appellations (line 134) → ✅ INSERTED
    ├─ gender (line 140) → ✅ INSERTED
    ├─ dynasty (line 150) → ❌ DISCARDED
    ├─ concise bio (line 152) → ❌ DISCARDED
    ├─ placeOfOrigin (line 154) → ❌ DISCARDED
    ├─ worksInTripitaka/worksBy (line 156) → ❌ DISCARDED
    └─ listBibl/CBETA (line 158-161) → ❌ DISCARDED
```

**Why Intentional?** Line 8-9 states this is ADDITIVE-only, status='pending':
- Not updating existing records (T223 handles merges)
- Not guessing data (prior incident T252 where dynasty auto-detection was wrong)
- Leaving fields for admin verification (status='pending')

---

### 2. Separate Import Scripts (Not Person-Specific)

| Script | Source XML | Imports To | Coverage |
|--------|-----------|-----------|----------|
| `import_person_bio.py` | **Person** Authority | `people.bio` | Only concise biography + wikidata_qid + origin_place_id |
| `import_person_origin.py` | **Person** Authority | `person_origin_link` | Place origin link only (not import itself) |
| `import_place_person_bibl.py` | **Place** Authority | `place_person_bibl` | CBETA from PLACE context, not PERSON context ⚠️ |

**Critical Gap:** NO script imports Person's `<listBibl>` (CBETA citations) into any table tied to persons.

---

## XML Elements & Their Status

### Person Authority XML Structure (Buddhist_Studies_Person_Authority.xml)

Each `<person>` element contains:

| XML Element | Type | Example | Imported? | Target Table | Issue |
|-------------|------|---------|-----------|--------------|-------|
| `@xml:id` | attribute | `A000035` | ✅ YES | `vn_person_authority.dila_id` | — |
| `<persName>` | element | 該僧 | ✅ YES | `vn_person_authority.name_zh` | — |
| `<persName type='alternative'>` | element | 僧侶, etc | ✅ YES | `vn_person_authority.appellations` | — |
| `<sex value='1'/>` | attribute | Male=1, Female=2 | ✅ YES | `vn_person_authority.gender` | — |
| `<note type='dynasty'>` | element | 唐 | ❌ EXTRACTED, DISCARDED | — | Will need T365 for full import |
| `<note type='concise'>` | element | biography text | ⚠️ PARTIALLY | `people.bio` (only via import_person_bio.py) | Separate table, not in vn_person_authority |
| `<note type='placeOfOrigin'>` | element | 少林寺 | ⚠️ PARTIALLY | `person_origin_link` + `places` | Only extracted, not linked |
| `<note type='worksInTripitaka'>` | element | T48n2012 | ❌ EXTRACTED, DISCARDED | — | MISSING |
| `<note type='worksBy'>` | element | 楞嚴經 | ❌ EXTRACTED, DISCARDED | — | MISSING |
| `<note type='mentionedIn'>` | element | source reference | ❌ EXTRACTED, DISCARDED | — | MISSING |
| `<note type='activeAt'>` | element | place + dates | ❌ EXTRACTED, DISCARDED | — | MISSING (planned T365) |
| `<listBibl/><bibl>` | element | CBETA T50n2060_p0457c16 | ❌ EXTRACTED, DISCARDED | — | CRITICAL GAP |
| `<listRelation>` | element | teacher/student | ⚠️ EXTERNAL | `dharma_lineage_base` | From TTL/RDF, not Person XML |
| `<idno type='Wikidata'>` | element | Q12345 | ⚠️ PARTIALLY | Not stored (extracted in import_person_bio.py but unused) | MISSING |
| Birth/Death dates | element | year info | ❌ EXTRACTED, DISCARDED | — | MISSING |

---

## Data Verification: A000035 Case Study

**Person A000035 (該僧) in XML:**
```xml
<person xml:id="A000035">
  <persName>該僧</persName>
  <persName type="alternative">...</persName>
  <sex value="1"/>
  <note type="dynasty">唐</note>
  <note type="concise">釋該僧，俗姓章，嘉興人也。...</note>
  <note type="placeOfOrigin"><ref target="PL000001234">少林寺</ref></note>
  <note type="worksInTripitaka">T50n2060</note>
  <note type="worksBy">楞嚴經疏</note>
  <listBibl>
    <bibl>( CBETA T50n2060_p0457c16 ) 唐高僧傳: 釋該僧傳 {少林}</bibl>
    <bibl>( CBETA T50n2061_p0480b14 ) ...</bibl>
    ... (8 total)
  </listBibl>
  <listRelation>
    <relation name="teacher" target="..."/>
    ...
  </listRelation>
</person>
```

**Database Status (lineage.db):**
```sql
-- vn_person_authority:
SELECT * FROM vn_person_authority WHERE dila_id='A000035';
→ 1 row (dila_id, name_zh="該僧", appellations, gender)

-- people table:
SELECT * FROM people WHERE dila_id='A000035';
→ No related bio/place/works data

-- person_origin_link:
SELECT * FROM person_origin_link WHERE person_id LIKE '%A000035%';
→ 0 rows (not imported)

-- CBETA by person:
SELECT * FROM <??> WHERE person_id='A000035';
→ NO TABLE EXISTS for person-centric CBETA
```

**Conclusion:** XML has 8 CBETA citations + 6 works + 4 places, but 0 rows in DB.

---

## Architecture Decision: Intentional Deferral

**Task T253 (Person Import ETL)** explicitly chose MINIMAL import to avoid:
1. **Data corruption:** guessing dynasty (T252 incident)
2. **Update complexity:** only ADDITIVE (no merges, no updates)
3. **Verification burden:** admin must review before using

**Task T365 (Phase 4: Data Integrity)** planned to handle full import after:
1. Schema consolidation (places_dila + places_pending → unified places table)
2. Creating entity tables (person_activity, passage_entity_mention)
3. CBETA mapping fixes
4. Re-importing Works/activeAt

**BUT:** The extracted data is stored NOWHERE interim. If T253 runs again, extracted elements are lost.

---

## Required Actions

### Phase 0 (Immediate): Preserve Extracted Data
**Task:** T366 — Create interim storage for extracted elements (not inserted):
- Modify `person_import_etl.py` to save extracted elements to JSON sidecar files
- Add logging (lines 142-161 → save to `data/dila_import/extracted/<dila_id>.json`)
- Allows audit trail + enables T365 to re-import later

### Phase 4: Full Import (T365)
**Task:** T365 — Data Integrity & Schema Rebuild
- Create missing tables: `person_works`, `person_mentions`, `person_activity`, `passage_entity_mention`
- Write import script for Person's listBibl → CBETA passage links
- Write import script for Person's worksInTripitaka/worksBy → person_works table
- Re-import activeAt places → person_activity table
- Link dynasty → person records (post T223 merge completion)

---

## Recommended Code Changes

### For T366 (Immediate):
```python
# person_import_etl.py — modify iter_persons() to save extracted data
def save_extracted_elements(dila_id, dynasty, concise, origin, works, bibl, sidecar_dir):
    """Save extracted-but-not-imported elements to JSON sidecar."""
    sidecar = {
        'dila_id': dila_id,
        'dynasty': dynasty,
        'concise_bio': concise,
        'place_of_origin': origin,
        'works': works,
        'cbeta_citations': bibl,
        'saved_at': datetime.now(timezone.utc).isoformat(),
    }
    sidecar_path = os.path.join(sidecar_dir, f'{dila_id}.json')
    with open(sidecar_path, 'w', encoding='utf-8') as f:
        json.dump(sidecar, f, ensure_ascii=False, indent=2)
    return sidecar_path

# In validate() and commit() functions, call save_extracted_elements()
```

### For T365 (Phase 4):
```python
# New script: import_person_works.py
# Input: extracted worksInTripitaka + worksBy from sidecar JSON files
# Output: person_works table with CBETA passage links

# New script: import_person_cbeta.py  
# Input: extracted listBibl from sidecar JSON files
# Output: passage_entity_mention linking person → CBETA passages

# New script: import_person_activity.py
# Input: extracted placeOfOrigin + notes with dates
# Output: person_activity table (ordained, taught, died, born, active at places)
```

---

## Timeline Impact

| Task | Dependency | Blocked By | Duration |
|------|-----------|-----------|----------|
| **T366** (preserve extracted data) | None | Can start immediately | 2 hours |
| **T365** (full import) | T364 (modularity) | Phase 3 completion | 4 weeks |
| **T359b** (person.html Fix 4-6) | T365 completion | T365 | +2 weeks |

---

## Data Integrity Concerns

⚠️ **CRITICAL:** If T253 import is re-run without sidecar preservation:
- All extracted elements (dynasty, works, CBETA, etc.) are re-extracted from XML but discarded again
- No audit trail of what was extracted
- T365 cannot access historical extractions if XML file changes

**Mitigation:** Save extracted elements to JSON sidecars (T366) before running T253 again.

---

## References

- [AGENTS.md §2 Technical Constraints](../AGENTS.md#2-technical-constraints-bắt-buộc-tuân-thủ)
- [T253 Person Import ETL](../tasks/T253-person-import-etl.md)
- [T365 Phase 4 Data Integrity](../tasks/T365-phase4-data-integrity.md)
- [T359 person.html Fixes](../tasks/T359-person-html-fixes.md)
- XML structure: `data/dila_import/Authority-Databases/authority_person/Buddhist_Studies_Person_Authority.xml` (25MB, 48,803 persons)

---

## Appendix: Import Script Inventory

| File | Purpose | Source XML | Target Table(s) | Covered Elements |
|------|---------|-----------|-----------------|------------------|
| `person_import_etl.py` (T253) | Main ETL | Person Authority | `vn_person_authority` | dila_id, name_zh, appellations, gender |
| `import_person_bio.py` | Biography only | Person Authority | `people.bio` | concise_bio, wikidata_qid, origin_place_id |
| `import_person_origin.py` | Origin place link | Person Authority | `person_origin_link` | place of origin (partial) |
| `import_place_person_bibl.py` | Place context CBETA | Place Authority | `place_person_bibl` | CBETA from places, NOT persons ⚠️ |
| **[MISSING]** | Person works import | Person Authority | `[NO TABLE]` | worksInTripitaka, worksBy |
| **[MISSING]** | Person CBETA import | Person Authority | `[NO TABLE]` | listBibl entries |
| **[MISSING]** | Person mentions import | Person Authority | `[NO TABLE]` | mentionedIn entries |
| **[MISSING]** | Person activity import | Person Authority | `[NO TABLE]` | activeAt places + dates |

---

**Conclusion:** XML import pipeline is **intentionally incomplete by design** but **lacks preservation mechanism** for deferred elements. **Immediate action needed: T366 (save extracted data) before T365 (full import).**
