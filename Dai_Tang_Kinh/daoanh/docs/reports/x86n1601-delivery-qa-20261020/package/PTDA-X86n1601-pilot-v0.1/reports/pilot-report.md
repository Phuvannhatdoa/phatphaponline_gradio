# Pilot Dataset Report: Thiền Đăng Thế Phổ (X86n1601)

## Executive Summary

Successfully extracted **34 patriarchs** and **9 transmission relations** from juan 001 of CBETA X86n1601 (Thiền Đăng Thế Phổ). Dataset is candidate-status, pending human review. All extraction and validation tests pass.

## Processing Details

| Metric | Value |
|--------|-------|
| **Work ID** | X86n1601 (禪燈世譜) |
| **Juan Processed** | 001 (Patriarchal lineage chart) |
| **Source File** | X86n1601.source.xml |
| **Source Size** | 778 KB, 7,564 lines |
| **Download Date** | 2026-10-20T06:28:47Z |
| **Source SHA-256** | 60a282bf78795048395dfdb6ab2ac0d7912bbd6b527338d9664f58994e84f178 |

## Extraction Results

### Persons Extracted

**34 patriarchs** from the "三十三祖世系圖" (33 Patriarchs Genealogy):

| # | Gen Label | Name (Han) | Bio Length | Notes |
|---|-----------|-----------|-----------|-------|
| 0 | 始祖 | 釋迦牟尼佛 | 251 chars | Shakyamuni Buddha |
| 1 | 第一祖 | 摩訶迦葉 | 84 chars | Mahakashyapa |
| 2 | 二祖 | 阿難尊者 | 76 chars | Ananda |
| 3 | 三祖 | 商那和修 | 84 chars | Shannavara |
| 4 | 四祖 | 優波毱多 | 82 chars | Upagupta |
| ... | ... | ... | ... | ... |
| 33 | 三十三祖 | 菩提達摩 | 51 chars | Bodhidharma |

### Relations Extracted

**9 transmission relations** identified:

| # | Subject | Object | Evidence | Status |
|---|---------|--------|----------|--------|
| claim_0001 | 釋迦牟尼佛 | 摩訶迦葉 | "乃以大法印付囑摩訶迦葉" | pending |
| claim_0002 | 摩訶迦葉 | 阿難尊者 | "後付阿難" | pending |
| claim_0003 | 阿難尊者 | 商那和修 | [From bio text] | pending |
| ... | ... | ... | ... | pending |

**Total relations**: 9 (all with status = "pending")

## Unmapped Gaps

**Relations NOT extracted** (selective pilot scope):

1. **Branch lineages** (juan 002-009): Not processed
2. **Complex genealogies**: If multiple transmission lines exist within juan 001, only sequential patriarchal chain extracted
3. **Implicit transmissions**: If successor listed without explicit "transmitted to" language, relation not marked

**Estimate**: 100–200 additional relations likely exist in juan 002-009.

## Data Quality Assurance

### Validation
✓ XML schema compliance (XSD)  
✓ All ID/IDREF references valid  
✓ No self-loops or duplicate edges  
✓ SHA-256 verified  

### Testing
✓ 8/8 unit tests passed  
✓ Evidence fragments verified non-empty  
✓ Extraction rule consistency checked  

### Limitations
- **Vietnamese translation**: Not included (scope: Han names only)
- **DILA ID linkage**: Not performed (source is CBETA; no DILA alignment in pilot)
- **Generation numbering (PTDA)**: Not assigned (source labels kept as-is)
- **Alternative names**: Secondary names in parentheses not extracted

## Deliverables

```
PTDA-X86n1601-pilot-v0.1/
├── README-VI.md              (Vietnamese guide)
├── source/
│   └── X86n1601.source.xml   (Original CBETA source, byte-exact)
├── derived/
│   └── X86n1601.pilot.claims.xml  (Extracted relations, PTDA XML)
├── schema/
│   └── ptda-lineage-v1.xsd   (XSD validation schema)
├── manifests/
│   ├── source-manifest.json  (Source provenance)
│   └── run-manifest.json     (Extraction metadata)
├── scripts/
│   ├── extract_pilot.py      (Main extraction)
│   └── validate_package.py   (Validation & tests)
├── tests/
│   ├── test_extraction.py    (Test suite)
│   └── test-results.txt      (Test output)
├── reports/
│   ├── structure-report.md   (XML structure analysis)
│   ├── extraction-rules.md   (Rule documentation)
│   ├── pilot-report.md       (This file)
│   └── rights-report.md      (License & rights)
├── requirements.txt          (Python deps)
└── SHA256SUMS.txt            (Integrity checksums)
```

## Next Steps (for QA review)

1. **Admin verification**: Review 9 extracted relations against source
2. **Scope expansion**: Decide whether to process juan 002-009
3. **DILA integration** (optional): If needed, link DILA person IDs
4. **Vietnamese annotation** (optional): Transliterate Han names

## Rights & License

**Source**: CBETA 佛典寶藏 (Buddhist Canon Databases)  
**License**: CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/)  
**Derivative Work**: PTDA pilot dataset (candidate status)  
**License**: CC BY-NC-SA 4.0 (same)

---
**Report Generated**: 2026-10-20  
**Package Version**: PTDA-X86n1601-pilot-v0.1  
**Status**: Candidate (pending human review)
