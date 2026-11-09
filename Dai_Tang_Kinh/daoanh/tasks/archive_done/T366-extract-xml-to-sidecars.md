---
id: T366
title: "Extract XML Elements → JSON Sidecars (STAGING layer)"
status: done
created: 2026-10-12
updated: 2026-10-12
parent: null
former_ids: []
depends_on: []
blocked_by: []
done_when:
  - "person_import_etl.py modified to save extracted elements to JSON sidecars"
  - "Sidecars stored at: data/dila_import/extracted/<dila_id>.json"
  - "Each sidecar contains: {dila_id, dynasty, concise_bio, places, works, cbeta_citations, wikidata, dates}"
  - "A000035 sidecar verified to contain 8 CBETA citations + 6 works + 4 places"
  - "Script tested with --dry-run and --limit 10"
  - "Audit trail created (which elements extracted, timestamp, count)"
  - "No data inserted to DB (extraction only)"
  - "Code + sidecars committed to git"
---

## Context

**Hybrid Architecture Decision (Oct 12, 2026):**
- DB (FINAL layer): 300-400 MB — person index, places, lineage (indexed)
- Sidecars (STAGING layer): 25-30 MB — extracted XML elements as JSON
- XML (RAW layer): 25 MB — Buddhist_Studies_Person_Authority.xml (immutable)

**Problem:** Current `person_import_etl.py` extracts elements (dynasty, works, CBETA, places) from XML but **discards them** (lines 142-172). If script re-runs, extracted data is lost forever → no audit trail → T365 cannot re-import later.

**Solution:** Save extracted elements to JSON sidecars before discarding. Enables:
1. Audit trail (what was extracted, when, from which persons)
2. T365 (Phase 4) to re-import from sidecars without re-parsing XML
3. Lazy-load CBETA/works when needed (don't bloat DB)

---

## Scope

### 1. Modify `person_import_etl.py`

**Lines 142-172 (iter_persons):** Currently extract but don't save:
```python
dynasty = ''
concise = ''
origin = []
works = []
bibl = []
for n in el.iter(NOTE):
    t = n.get('type') or ''
    txt = (n.text or '').strip()
    if t == 'dynasty':
        dynasty = txt
    elif t == 'concise':
        concise = txt
    elif t == 'placeOfOrigin' and txt:
        origin.append(txt)
    elif t in ('worksInTripitaka', 'worksBy') and txt:
        works.append(txt)
for b in el.iter(BIBL):
    txt = (b.text or '').strip()
    if txt:
        bibl.append(txt)
```

**Change:** Add function to save to JSON:
```python
def save_sidecar_json(dila_id, dynasty, concise, places, works, bibl, wikidata, dates, sidecar_dir):
    """Save extracted elements to JSON sidecar (STAGING layer)."""
    sidecar = {
        'dila_id': dila_id,
        'dynasty': dynasty,
        'concise_bio': concise,
        'places_of_origin': places,
        'works_in_tripitaka': works,  # note: may include both worksInTripitaka + worksBy
        'cbeta_citations': bibl,  # listBibl entries
        'wikidata_qid': wikidata,
        'birth_death_dates': dates,
        'extracted_at': _now_iso(),
        'source': 'Buddhist_Studies_Person_Authority.xml',
    }
    sidecar_path = os.path.join(sidecar_dir, f'{dila_id}.json')
    with open(sidecar_path, 'w', encoding='utf-8') as f:
        json.dump(sidecar, f, ensure_ascii=False, indent=2)
    return sidecar_path
```

### 2. Create Sidecar Directory

Path: `data/dila_import/extracted/`
- Contains: `<dila_id>.json` files (e.g., `A000035.json`, `A000094.json`)
- Gitignore: Add `data/dila_import/extracted/` to `.gitignore` (sidecars are ephemeral, regenerated per run)

### 3. Modify `validate()` and `commit()` Functions

In `validate()`: Call `save_sidecar_json()` for each person (dry-run, no DB insert)
In `commit()`: Call `save_sidecar_json()` during actual run

Report statistics:
- Total persons processed
- Total sidecars created
- Sample A000035: {dynasty: '唐', works: [...], cbeta: [...]}

### 4. CLI Changes

Add flag `--preserve-sidecars` (default True):
```bash
python -X utf8 scripts/person_import_etl.py --action validate --preserve-sidecars
python -X utf8 scripts/person_import_etl.py --action commit --preserve-sidecars
```

---

## Example Output

**File: `data/dila_import/extracted/A000035.json`**
```json
{
  "dila_id": "A000035",
  "dynasty": "唐",
  "concise_bio": "釋該僧，俗姓章，嘉興人也。...",
  "places_of_origin": [
    "少林寺"
  ],
  "works_in_tripitaka": [
    "T50n2060",
    "楞嚴經疏"
  ],
  "cbeta_citations": [
    "( CBETA T50n2060_p0457c16 ) 唐高僧傳: 釋該僧傳 {少林寺}",
    "( CBETA T48n2012_p0123a01 ) 景德傳燈錄: 該僧章 {南嶺}",
    "..."
  ],
  "wikidata_qid": null,
  "birth_death_dates": {},
  "extracted_at": "2026-10-12T14:30:45Z",
  "source": "Buddhist_Studies_Person_Authority.xml"
}
```

---

## Implementation Steps

1. **Backup:** Copy `person_import_etl.py` → `docs/sessions/2026-10-12/person_import_etl.py.bak`
2. **Modify:** Add `save_sidecar_json()` function + call in `iter_persons()`, `validate()`, `commit()`
3. **Test (dry-run):**
   ```bash
   python -X utf8 scripts/person_import_etl.py --action validate --limit 10
   # Check: data/dila_import/extracted/A000035.json created ✓
   ```
4. **Verify:** Check A000035 sidecar contains 8 CBETA + 6 works
5. **Commit:** `git add scripts/person_import_etl.py data/dila_import/extracted/A000035.json ...`

---

## Data Verification Checklist

- [ ] A000035 sidecar has `"dynasty": "唐"` ✓
- [ ] A000035 sidecar has 8 items in `"cbeta_citations"` ✓
- [ ] A000035 sidecar has 6 items in `"works_in_tripitaka"` ✓
- [ ] A000035 sidecar has `"extracted_at"` timestamp ✓
- [ ] No data inserted to DB (validation only) ✓
- [ ] Sidecars are valid JSON ✓
- [ ] All 48,803 persons (or batch if --limit) have sidecars ✓

---

## Timeline

- **Code modification:** 1-2 hours
- **Testing & verification:** 1 hour
- **Documentation:** 30 minutes
- **Commit:** 15 minutes
- **Total:** 3 hours (1 working day)

---

## Deliverables

- Modified `scripts/person_import_etl.py` (with sidecar extraction)
- Sample sidecars: `data/dila_import/extracted/A000035.json`, etc.
- Test run report: `docs/sessions/2026-10-12/T366_sidecar_extraction_report.md`
- Commit message: "T366: Extract XML elements to JSON sidecars (STAGING layer)"

---

## Dependencies & Unblocks

**Depends on:** None (independent task)  
**Unblocks:** T365 (Phase 4 re-import), T359b (Fix 4-6 CBETA/works)

---

## Người Phụ Trách

- **Thực hiện:** daoanh-debugger
- **Kiểm chứng:** daoanh-qa (verify sidecars created, A000035 has 8 CBETA)
- **Điều phối:** Coordinator (me)

---

## References

- [XML_IMPORT_AUDIT_REPORT.md](../docs/XML_IMPORT_AUDIT_REPORT.md) — Full audit findings
- [Architecture 4-Layer Model](../docs/overview.md#data-architecture--4-layer-model)
- [T365 Phase 4](./T365-phase4-data-integrity.md) — Full re-import (depends on T366)
- [AGENTS.md §2](../AGENTS.md#2-technical-constraints-bắt-buộc-tuân-thủ) — Zero-RAM principle
