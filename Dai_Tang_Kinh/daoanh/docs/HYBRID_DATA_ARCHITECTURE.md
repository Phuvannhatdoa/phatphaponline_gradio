# Hybrid Data Architecture — RAW + STAGING + FINAL Layers

**Date:** 2026-10-12  
**Decision:** Option 3 — Hybrid approach approved by Admin  
**Impact:** Optimizes storage, performance, and maintainability per AGENTS.md Zero-RAM principle

---

## 🎯 Problem Solved

| Approach | DB Size | Startup | Query Speed | Zero-RAM? | Maintenance |
|----------|---------|---------|------------|-----------|-------------|
| Full Import | 3GB | 30s | 1-5ms ⚡⚡⚡ | ❌ | Hard |
| Pure Lazy-Load | 150MB | 3s ⚡⚡⚡ | 500-2000ms | ✅ | Medium |
| **Hybrid (Selected)** | 400MB | 5s ⚡⚡ | 1-500ms | ✅ | Easy |

---

## 📐 Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   UI Layer (React)                       │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │  FINAL/PUBLIC Layer (SQLite DB)                 │   │
│  │  - person index (name, dila_id, sex, gender)    │   │
│  │  - places (canonical, deduplicated)             │   │
│  │  - lineage_edges (teacher → student, indexed)   │   │
│  │  - **NOT CBETA directly** (too bulky)           │   │
│  │  Size: 300-400 MB                               │   │
│  │  Access: Fast (1-2ms) via indexed SQL queries   │   │
│  └──────────────────────────────────────────────────┘   │
│                         ↑                                 │
│                    [ETL pipeline]                        │
│                         ↑                                 │
│  ┌──────────────────────────────────────────────────┐   │
│  │  STAGING Layer (JSON Sidecars)                   │   │
│  │  - Location: data/dila_import/extracted/         │   │
│  │  - Files: A000035.json, A000094.json, ...        │   │
│  │  - Content: {dynasty, works, cbeta, places, ...} │   │
│  │  - Size: 25-30 MB                                │   │
│  │  - Access: On-demand (lazy-load, 50-500ms)      │   │
│  │  - Purpose: Preserve extracted data for Phase 4 │   │
│  └──────────────────────────────────────────────────┘   │
│                         ↑                                 │
│                  [Extract on import]                     │
│                         ↑                                 │
│  ┌──────────────────────────────────────────────────┐   │
│  │  RAW Layer (Source Files)                        │   │
│  │  - Buddhist_Studies_Person_Authority.xml (DILA)  │   │
│  │  - 25 MB, 48,803 persons                         │   │
│  │  - Immutable — never modified                    │   │
│  │  - Purpose: Single Source of Truth (SSOT)        │   │
│  └──────────────────────────────────────────────────┘   │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 Layer Details

### RAW Layer (Source)
**Purpose:** Immutable source of truth  
**Files:**
- `data/dila_import/Authority-Databases/authority_person/Buddhist_Studies_Person_Authority.xml` (25MB, 48,803 monks)

**Elements per person:**
```xml
<person xml:id="A000035">
  <persName>該僧</persName>                    ← DB: name_zh
  <sex value="1"/>                             ← DB: gender
  <note type="dynasty">唐</note>               ← STAGING: sidecar
  <note type="concise">釋該僧，俗姓...</note> ← STAGING: sidecar
  <note type="placeOfOrigin">...</note>       ← STAGING: sidecar
  <note type="worksBy">楞嚴經疏</note>        ← STAGING: sidecar
  <listBibl>
    <bibl>T50n2060_p0457c16</bibl>            ← STAGING: sidecar (8 total)
    ...
  </listBibl>
</person>
```

**Query:** XML is sequential (no index), used only at import time

---

### STAGING Layer (Processing)
**Purpose:** Preserve extracted elements, enable audit trail, support Phase 4 re-import  
**Location:** `data/dila_import/extracted/`

**File Format:** JSON sidecars
```json
{
  "dila_id": "A000035",
  "dynasty": "唐",
  "concise_bio": "釋該僧，俗姓章...",
  "places_of_origin": ["少林寺"],
  "works_in_tripitaka": ["T50n2060", "楞嚴經疏"],
  "cbeta_citations": [
    "( CBETA T50n2060_p0457c16 ) 唐高僧傳: 釋該僧傳 {少林寺}",
    "( CBETA T48n2012_p0123a01 ) 景德傳燈錄: 該僧章 {南嶺}",
    ... (8 total)
  ],
  "wikidata_qid": null,
  "birth_death_dates": {},
  "extracted_at": "2026-10-12T14:30:45Z",
  "source": "Buddhist_Studies_Person_Authority.xml"
}
```

**Key advantages:**
- ✅ Preserves extracted data that would otherwise be discarded
- ✅ Enables audit trail (what was extracted, when, from which source)
- ✅ Supports lazy-load (load JSON sidecar only when user requests CBETA/works)
- ✅ Enables Phase 4 re-import without re-parsing XML
- ✅ Separates concerns: extraction ≠ storage ≠ indexing

**Query:** JSON.parse() on-demand, cached (LRU cache 5-10 min TTL)

---

### FINAL/PUBLIC Layer (Consumption)
**Purpose:** Indexed, queryable, consumed by UI  
**Database:** SQLite `data/lineage.db`

**Tables in FINAL layer:**
```sql
vn_person_authority
├─ id (alias_A000035)
├─ dila_id (A000035)
├─ name_zh (該僧)
├─ gender (Male)
└─ status (pending | verified)

places
├─ id (PL000000023255)
├─ name_zh (少林寺)
├─ name_vi (Thiếu Lâm Tự)
└─ source (DILA | VPS | TTL)

dharma_lineage_base
├─ teacher_id
├─ student_id
├─ source (DILA | TTL)
└─ confidence (1.0 | 0.8)
```

**Not in FINAL layer (instead in STAGING):**
- ❌ CBETA citations (too many, rarely queried)
- ❌ Detailed works list (use sidecars instead)
- ❌ Birth/death dates with context (use sidecars)
- ❌ Dynasty info (use sidecars)

**Query:** SQL indexed queries, O(log n) seek time, 1-5ms per query

---

## 🔄 Data Flow

### Import Flow (T253 + T366)
```
XML (RAW)
   ↓
[person_import_etl.py]
   ├─→ Extract {dila_id, name_zh, appellations, gender} → DB
   ├─→ Extract {dynasty, works, cbeta, places, ...} → JSON sidecars (STAGING)
   ├─→ Extract {lineage edges} → lineage_base table (FINAL)
   ↓
DB (FINAL) — indexed, fast queries
Sidecars (STAGING) — lazy-load on demand
```

### Query Flow (at Runtime)
```
User requests person A000035
   ↓
/api/persons/A000035 (Flask)
   ├─→ Query DB for basic info (1-2ms) ⚡
   │   └─ Returns: {id, name_zh, gender, dynasty_from_UI_hint}
   ├─→ Check: Does user want CBETA/works?
   │   ├─ YES: Load JSON sidecar from disk (50-500ms) + cache
   │   │   └─ Returns: {cbeta_citations: [...], works: [...]}
   │   └─ NO: Skip, return basic info only
   ↓
Browser renders person page
```

---

## 📈 Storage & Performance

### Storage Breakdown
```
Before (Full Import):
├─ SQLite DB: 3.0 GB (48,803 persons + all CBETA + all works)
├─ XML file:  0.025 GB
├─ Backup:    3.0 GB
└─ TOTAL:     6.025 GB

After (Hybrid):
├─ SQLite DB: 0.4 GB (1,074 persons indexed + places + lineage)
├─ JSON sidecars: 0.03 GB (extracted elements)
├─ XML file:  0.025 GB
├─ Backup:    0.4 GB
└─ TOTAL:     0.855 GB (-86% storage!)
```

### Performance Comparison
```
Query: Find A000035 basic info (name, lineage)
├─ Full Import: 1-2ms (from indexed DB)
├─ Lazy-Load: 1-2ms (from indexed DB, since person exists)
└─ Hybrid: 1-2ms (same as both!)

Query: Find A000035 CBETA citations (8 items)
├─ Full Import: 1-2ms (from indexed DB)
├─ Lazy-Load: 500-2000ms (sequential JSON scan)
└─ Hybrid: 50-500ms (cached JSON sidecar) ← **balance**
```

---

## 🔐 Data Integrity & Consistency

### SSOT (Single Source of Truth)
```
RAW layer (XML) = SSOT
  ↓
STAGING layer (sidecars) = audit trail + transformation log
  ↓
FINAL layer (DB) = indexed, queryable, consistency-checked
```

**Invariants:**
- `RAW == STAGING` (extraction is lossless)
- `STAGING ⊆ FINAL` (only index-worthy data in DB)
- `FINAL ⊂ RAW` (DB is subset of XML, not modified separately)

**Conflict resolution:** If RAW changes, re-run T366 to regenerate sidecars.

---

## 🚀 Roadmap

### Phase 0 (T366 — Now)
**Extract XML → JSON sidecars**
- Modify `person_import_etl.py` to save sidecars
- Preserve all extracted elements
- Create audit trail
- Timeline: 3 hours

### Phase 1 (T360-362 — Weeks 1-2)
**Code quality improvements**
- T360: Vietnamese source badges ✅
- T361: API versioning
- T362: Error standardization

### Phase 2 (T363 — Weeks 3-5)
**Performance optimization**
- Audit N+1 queries
- Implement SQLite FTS for lexicon
- Connection pooling

### Phase 3 (T364 — Weeks 6-8)
**Modularity improvements**
- Split app.py into blueprints
- Unit tests (80%+ coverage)

### Phase 4 (T365 — Weeks 9-12)
**Full import from sidecars**
- Create `person_works` table
- Create `passage_entity_mention` table
- Create `person_activity` table
- Re-import all CBETA + works + dynasty + places
- Update DB from 400MB → 2-3GB (optional, depends on needs)

---

## ✅ Migration Path: Current State → Phase 4

### Current (Oct 12, 2026)
```
DB:        1.4 GB (1,074 persons + selective CBETA)
XML:       25 MB (RAW, untouched)
Sidecars:  None
```

### After T366 (Oct 12, end of day)
```
DB:        1.4 GB (unchanged)
XML:       25 MB (unchanged)
Sidecars:  25-30 MB (new! A000035 + Top 1000 monks)
```

### After T365 (Phase 4, ~4 weeks)
```
Option A (Full Import):
  DB:        2.5-3.5 GB (48,803 persons + all CBETA + all works)
  Sidecars:  archived
  
Option B (Hybrid, maintain):
  DB:        400-500 MB (keep selective indexing)
  Sidecars:  25-30 MB (keep for lazy-load)
```

---

## 📋 Design Decisions Rationale

### Q: Why not import CBETA directly into DB?
**A:** 72,628 CBETA rows = 10-20MB of data that:
- Are rarely queried individually (users mostly want person bio)
- Don't need index (sequential CBETA list)
- Bloat DB with redundancy (each person → 8-10 CBETA mentions)
- Violate Zero-RAM principle (can't fit in cache)

**Better:** Lazy-load from JSON (50-500ms is acceptable for rare queries)

### Q: Why JSON sidecars instead of separate table?
**A:** JSON sidecars:
- ✅ Simple extraction (one file per person)
- ✅ Easy to re-generate (just re-parse XML)
- ✅ Portable (can version control, backup separately)
- ✅ No schema friction (flexible structure)
- ❌ Slower to query (JSON parse vs SQL)

**Tradeoff:** Acceptable because sidecars are lazy-loaded

### Q: Why not keep XML in folder instead of sidecars?
**A:**
- Sidecars have **extracted** data (parsed, structured JSON)
- XML is raw XML (need to parse each access)
- Sidecar access: JSON.parse() = 50-100ms
- XML access: XML parse + find A000035 = 500-2000ms

**Better:** Sidecars reduce latency 10x

---

## 🔧 Implementation Checklist

- [x] Decide on hybrid approach ✓
- [x] Create T366 task ✓
- [ ] Modify person_import_etl.py (daoanh-debugger)
- [ ] Test with --limit 10 (daoanh-debugger)
- [ ] Verify A000035 sidecar has 8 CBETA (daoanh-qa)
- [ ] Update API to load sidecars on-demand (T359 Fix 4-6 or Phase 4)
- [ ] Document API contract (sidecars endpoint)
- [ ] Update dashboard with T366 progress
- [ ] Commit + session log

---

## References

- [AGENTS.md §2 Zero-RAM Principle](../AGENTS.md)
- [overview.md — 4-Layer Architecture](./overview.md#data-architecture--4-layer-model)
- [XML_IMPORT_AUDIT_REPORT.md](./XML_IMPORT_AUDIT_REPORT.md)
- [T366 Task](../tasks/T366-extract-xml-to-sidecars.md)
- [T365 Task](../tasks/T365-phase4-data-integrity.md)
