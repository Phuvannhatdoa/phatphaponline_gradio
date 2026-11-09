# Extraction Rules and Methodology

## Pilot Scope

**Text**: Thiền Đăng Thế Phổ (禪燈世譜), CBETA X86n1601  
**Juan Processed**: 001 (Patriarchal lineage chart only)  
**Candidate Relations**: 9  
**Persons Extracted**: 34 (33 Indian patriarchs + 1 beginning patriarch name)

## Extraction Rules Applied

### Rule 1: Sequential Patriarchal Transmission
- **Trigger**: Current patriarch's biography mentions the next patriarch's name
- **Logic**: Search each person's biographical text for succeeding persons' names
- **Confidence**: High (direct textual evidence)
- **Example**: Shakyamuni mentions "付囑摩訶迦葉" → relation to Mahakashyapa
- **Relations Found**: 9

### Rule 2: Person Identification
- **Trigger**: `<tei:note place="inline">` containing generation label + following text node
- **Extraction**: First "word" from note's tail text (split on whitespace)
- **Normalization**: Remove secondary names; keep main appellation
- **Stability**: Persons assigned stable internal IDs (person_000, person_001, ...)

### Rule 3: Evidence Extraction
- **Source**: Recursive text extraction from nested `<tei:item>` → `<tei:list>` → all descendants
- **Context Window**: ±100 characters around mentioned name
- **Normalization**: Whitespace normalized; no character substitution
- **Preservation**: Raw text stored; display normalization documented separately

## Cases NOT Extracted (Limitations)

1. **Branch lineages in juan 002-009**: Not processed (scope limit)
2. **Horizontal relations**: Brother-patriarch relationships (if encoded) not extracted
3. **Study relations vs transmission**: Cannot distinguish "studied under" from "transmitted to"; all marked as "dharma_transmission" with direction preserved
4. **Implicit transmission**: If a patriarch dies without explicitly naming successor but successor implicitly follows, not marked as candidate relation
5. **Women patriarchs or alternate lineages**: Not verified in juan 001; may exist in later juan

## Extraction Statistics

| Category | Count | Notes |
|----------|-------|-------|
| Persons extracted | 34 | All from juan 001 patriarchal list |
| Direct mentions | 34 | Each person mentioned at least once |
| Transmission mentions | 9 | Names found in biographical text of predecessor |
| Evidence fragments | 9 | One per relation claim |
| Self-loops | 0 | By design: no relation to self |
| Undirected relations | 0 | All marked subject_to_object (predecessor → successor) |

## Test Results

**Validation Tests**: 8/8 passed
- XML structure valid ✓
- All references consistent ✓
- No self-loops ✓
- All persons referenced ✓
- Evidence non-empty ✓
- Review status all "pending" ✓
- SHA-256 valid ✓
- No spurious cross-generational jumps ✓

---
**Extraction Script**: extract_pilot_final.py  
**Validator**: validate_package.py  
**Date**: 2026-10-20
