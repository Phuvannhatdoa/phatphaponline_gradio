# QA2 REPORT - Fresh System Scan

**Date:** 2026-04-12  
**Type:** New Findings

---

## SUMMARY
| Category | Count | Status |
|----------|-------|--------|
| Critical | 3 | 🔴 |
| Medium | 3 | 🟡 |
| Low | 3 | 🟢 |

---

## ISSUES FOUND

### Critical
| Issue | Location | Fix |
|-------|----------|-----|
| Missing `requests` import | app.py (lines 1719,1748,1760,1790,1798) | Add `import requests` at top |
| Missing crawler script | app.py:1455 references non-existent file | Create `src_python/crawler/wiki_buddhist_crawler.py` |
| Duplicate function definitions | app.py - `load_persons` at lines 192,613,842; `load_places_for_gps` at lines 200,1007 | Consolidate to single definition per function |

### Medium
| Issue | Location | Fix |
|-------|----------|-----|
| Static HTML duplication | index.html exists in both root and static/ | Use root version only or redirect |
| Empty staging/verification data | data/staging.json, data/verification.json | Populate with actual data from crawls |
| Empty crawl directory | data/crawl/ (exists but no files) | Add crawled temple data or disable feature |

### Low
| Issue | Location | Fix |
|-------|----------|-----|
| No Vietnamese translations | data/places.json (5000 places all empty nameVietnamese) | Add translation pipeline |
| DILA-only data source | data/places.json | Add more sources (CBETA, Wiki, etc.) |
| Function caching inconsistent | app.py - some load_* functions use cache, some don't | Standardize caching strategy |

---

## DATA QUALITY

### places.json
| Metric | Value |
|--------|-------|
| Total places | 5,000 |
| With GPS | 5,000 (100%) |
| With Vietnamese name | 0 (0%) |
| Sources | DILA only |

### persons.json
| Metric | Value |
|--------|-------|
| Total persons | 48,803 |
| With teacher | 9,243 (19%) |
| With student | 22,270 (46%) |
| With dynasty | 46,738 (96%) |
| With biography | 47,879 (98%) |

### Dictionary Data
| Metric | Value |
|--------|-------|
| Normalized entries | 25,012 |
| Places entities | 8,300 |
| Monks entities | 2,199 |

---

## RECOMMENDATIONS

| Priority | Task | File |
|----------|------|------|
| P0 | Add `import requests` to app.py | app.py |
| P0 | Create wiki_buddhist_crawler.py | src_python/crawler/ |
| P1 | Consolidate duplicate load_* functions | app.py |
| P1 | Add Vietnamese translations pipeline | data/ |
| P2 | Populate staging/verification with real data | data/ |
| P2 | Clean up duplicate HTML files | index.html, static/index.html |

---

## API ENDPOINTS STATUS

| Endpoint | Status | Notes |
|----------|--------|-------|
| /api/places | ✅ OK | Returns 5000 places |
| /api/persons | ✅ OK | Returns 48803 persons |
| /api/stats | ✅ OK | Returns breakdown |
| /api/lineage-map | ✅ OK | Works with GPS |
| /api/nexus/find | ✅ OK | Person-Place-Time |
| /api/entity/link | ✅ OK | Entity linking |
| /api/dict/search | ✅ OK | Dictionary search |
| /api/health | ⚠️ DEPENDS | GraphDB, RAG external |
| /api/graphdb/sparql | ⚠️ DEPENDS | GraphDB required |
| /api/rag/query | ⚠️ DEPENDS | RAG service required |
| /api/admin/crawler/run | ❌ BROKEN | Crawler file missing |

---

*Generated: 2026-04-12*
