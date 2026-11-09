# 04-Software-Design-Specification.md

# Software Design Specification (SDS) — Đạo Ảnh / Tuệ Giác Số

**Document ID:** SDS-04  
**Version:** 1.0  
**Date:** 2026-10-08  
**Status:** Draft  
**Classification:** Internal — Enterprise Architecture  

---

## 1. Introduction

### 1.1 Purpose

This Software Design Specification (SDS) describes the detailed design of the Đạo Ảnh (Tuệ Giác Số / PTDA) system. It provides technical guidance for developers, operations teams, and security teams on the system's architecture, modules, interfaces, business rules, and non-functional requirements.

### 1.2 Scope

The SDS covers:
- Main Server (app.py, port 5000) — all business logic
- Auth Gateway (server.py, port 5001) — login and session management
- Data layer — SQLite with 4-layer architecture
- Frontend — HTML templates with React 18 UMD, Tailwind CSS
- Integration layer — source adapters, ETL scripts, external APIs
- Deployment — Nginx routing, VPS hosting

### 1.3 Audience

- Enterprise Architect
- Solution Architect
- Technical Lead
- Developer (ClaudeCode Build Agent)
- Operations Team
- Security Team

---

## 2. System Design

### 2.1 Architecture Style

**Style:** Layered Monolith with Two-Server Split  
**Confidence:** 85%

The system is deployed as a single codebase split into two server processes:
- **Auth Gateway (server.py, port 5001):** Login only — Gmail check, session management, admin emails
- **Main Server (app.py, port 5000):** All business logic — Đạo Ảnh, TTL, Marcus, dossier, translation

Nginx acts as a reverse proxy, routing `/daoanh/api/login/*` to port 5001 and everything else to port 5000.

### 2.2 Data Architecture — 4-Layer Model

```
┌─────────────────────────────────────────────────────────┐
│ Layer 4: INDEX                                          │
│   Binary search index, O(log n) lookup                  │
│   indexed/entity_master.idx                             │
├─────────────────────────────────────────────────────────┤
│ Layer 3: FINAL / PUBLIC                                 │
│   Consumed by UI, exported downstream                   │
│   places, places_vps, people, canon_catalog,            │
│   dataset_sources, lexicon                              │
├─────────────────────────────────────────────────────────┤
│ Layer 2: STAGING / MAPPING                              │
│   ETL, AI mapping, deduplication                        │
│   places_pending, namevi_map_places, *_staging          │
├─────────────────────────────────────────────────────────┤
│ Layer 1: RAW                                            │
│   Source data, never modified by app                    │
│   places_dila, people_full, marcus_reference            │
└─────────────────────────────────────────────────────────┘
```

### 2.3 Zero-RAM Principle

All large file operations follow the zero-RAM principle:
- Streaming generators for large files (>50MB XML)
- Byte-offset mapping for random access
- Binary index for O(log n) lookup
- Never load entire datasets into memory

---

## 3. Functional Design

### 3.1 Module: Place Management

**Responsibilities:**
- CRUD operations for Buddhist places (DILA authority + Vietnamese temples)
- GPS coordinate storage and validation
- Cross-reference linking (Wikidata, GeoNames, OSM)
- GeoJSON export for Leaflet.js map visualization

**Interfaces:**
- `GET /api/places` — List all places with pagination (page, limit, search)
- `GET /api/places/<id>` — Get place details with claims
- `GET /api/places/map` — GeoJSON for Leaflet (planned)
- `PUT /api/admin/places/{id}` — Update place (admin only)
- `GET /api/admin/places` — List all places with pagination (admin)

**Dependencies:** SQLite (places, places_dila, places_vps tables), Binary Index

**Business Rules:**
- DILA ID is canonical primary key for places
- GPS coordinates must be within Vietnam bounding box for VN places
- Place names must have at least one alias (Vietnamese or Hán)
- Source attribution required for all place records

---

### 3.2 Module: Person Management

**Responsibilities:**
- CRUD operations for Buddhist persons (monks, teachers, scholars)
- Teacher-student lineage tracking
- Dynasty/time period association
- Nexus point queries (person-place-time)

**Interfaces:**
- `GET /api/persons` — List all persons (paginated)
- `GET /api/persons/<id>` — Get person details
- `GET /api/persons/search?q={query}` — Search by name
- `GET /api/persons/timeline` — Get dynasty distribution
- `GET /api/persons/by-dynasty?dynasty={dynasty}` — Filter by dynasty
- `POST/GET /daoanh/api/admin/person/import-xml` — Import person XML (T253)

**Dependencies:** SQLite (people, people_full, dila_reference tables), Marcus SNA

**Business Rules:**
- DILA ID (Axxxxx format) is canonical primary key
- Person must have at least one name (Vietnamese or Hán)
- Teacher-student relationships must not create cycles
- Dynasty association optional but recommended

---

### 3.3 Module: Dictionary & Entity Extraction

**Responsibilities:**
- StarDict dictionary search (22 dictionaries, 166,278 entries)
- Entity extraction from text (places + monks)
- Term normalization and fuzzy matching

**Interfaces:**
- `GET /api/dict/search?q={term}` — Search dictionary
- `GET /api/dict/stats` — Get dictionary statistics
- `GET /api/dict/entities` — Get extracted entities (places + monks)
- `POST /api/entity/link` — Link entities in text

**Dependencies:** SQLite (lexicon table with 15,863 ĐỊA DANH entries), Lexicon service

**Business Rules:**
- Exact match preferred over fuzzy match
- Confidence score assigned to each match (0.0-1.0)
- Terms below 0.7 confidence require manual review
- Source attribution for all dictionary entries

---

### 3.4 Module: Search & Discovery

**Responsibilities:**
- Deep search across places
- Nexus point discovery (person + place + time)
- Entity linking in CBETA text passages

**Interfaces:**
- `GET /api/deepsearch?q={query}` — Deep search across places
- `GET /api/nexus/find?person=&place=` — Find nexus points
- `GET /api/graphdb/sparql` — SPARQL query proxy to GraphDB

**Dependencies:** SQLite (places, persons, entity_hub, entity_claims), GraphDB (external)

**Business Rules:**
- Search results paginated (default 50 per page)
- Nexus queries require at least one of person/place/time
- GraphDB queries rate-limited

---

### 3.5 Module: Translation Service

**Responsibilities:**
- CBETA Han→Vietnamese translation via Gemini AI
- Translation polish (grammar correction + term normalization)
- Translation cache for performance
- Admin approval workflow for translations

**Interfaces:**
- `POST /api/translate-cbeta` — Translate CBETA passage (planned)
- `PUT /api/admin/translations/:id/approve` — Approve translation (planned)
- `GET /api/places/:place_id/translations` — Get place translations (planned)

**Dependencies:** Gemini 2.0 Flash API, Lexicon DB, Translation cache DB

**Business Rules:**
- Cache hit returns stored translation (no API call)
- Confidence score < 0.85 marks translation as "needs review"
- Terms with confidence < 0.7 displayed with <mark> for review
- Admin approval required for production use

---

### 3.6 Module: Authentication & Session

**Responsibilities:**
- Gmail-based login verification
- Session creation and management
- Admin email notifications
- Route protection

**Interfaces:**
- `GET /daoanh/login.html` — Login page
- `POST /daoanh/api/login/*` — Login API
- `GET /api/admin/emails` — Admin email management

**Dependencies:** SQLite (sessions), SMTP (for emails)

**Business Rules:**
- Only authenticated users can access admin routes
- Sessions expire after configurable timeout
- Admin email notifications sent on canonical decisions

---

## 4. Non-Functional Requirements

| Category | Requirement | Target |
|----------|-------------|--------|
| **Performance** | Place lookup response time | < 2s for 5,000+ places |
| **Performance** | API rate limit (search) | 100 requests/minute |
| **Performance** | API rate limit (admin) | 60 requests/minute |
| **Performance** | Binary index lookup | O(log n) |
| **Reliability** | Zero data loss on import | Additive + reversible with manifest + backup |
| **Reliability** | ETL idempotency | Re-apply produces same result |
| **Security** | API key secrecy | Environment variable, never committed |
| **Security** | XSS prevention | _escHtml() on all rendered content |
| **Security** | Route separation | Auth (5001) isolated from business (5000) |
| **Usability** | Admin dashboard | HITL canonical decisions with 2-minute review |
| **Maintainability** | Documentation coverage | 200+ markdown files in docs/ |
| **Scalability** | Concurrent users | Single instance; Nginx reverse proxy |

---

## 5. Architectural Decisions

| Decision | Description | Rationale | Status |
|----------|-------------|-----------|--------|
| **AD-01** | Two-server split (auth on 5001, business on 5000) | Security isolation of login from business logic | ✅ Implemented |
| **AD-02** | DILA as canonical primary key | Single source of truth for person/place IDs | ✅ Implemented |
| **AD-03** | 4-layer data architecture (RAW/STAGING/FINAL/INDEX) | Zero-RAM principle; raw data protection | ✅ Implemented |
| **AD-04** | Additive-only database migrations | Prevent data loss; enable rollback | ✅ Implemented |
| **AD-05** | Source-agnostic adapter pattern | Add new sources without modifying core | ⚠️ Partial (G1 done, G2 planned) |
| **AD-06** | SQLite as primary database | Simplicity; sufficient for current scale (59K places, 48K persons) | ✅ Implemented |
| **AD-07** | Binary index for O(log n) lookup | Fast entity search without loading full dataset | ✅ Implemented |
| **AD-08** | HITL for canonical decisions | Admin oversight on entity conflicts | ✅ Implemented |
| **AD-09** | No `git init` in daoanh/ subdirectory | Preserve single repo history | ✅ Enforced |
| **AD-10** | Temp-index sync for concurrent sessions | Workaround for .git/index rename limitation | ✅ Documented |

---

## 6. Module Design

### 6.1 Main Server (app.py)

**File:** `app.py` (~2,600 lines)  
**Port:** 5000  
**Responsibilities:** All business logic — Đạo Ảnh, TTL, Marcus, dossier, translation

**Key Components:**
- Place API blueprint (/api/places/*)
- Person API blueprint (/api/persons/*)
- Dictionary API blueprint (/api/dict/*)
- Admin API blueprint (/api/admin/*)
- Crawler API blueprint (/api/crawler/*)
- Health API (/api/health)
- GraphDB proxy (/api/graphdb/sparql)
- Search API (/api/deepsearch, /api/nexus/find)
- Entity linking API (/api/entity/link)
- ETL script integration
- Translation service integration

**Dependencies:** SQLite, Binary Index, Gemini API, GraphDB

---

### 6.2 Auth Gateway (server.py)

**File:** `server.py` (~125 lines)  
**Port:** 5001  
**Responsibilities:** Login only — Gmail check, session management, admin emails

**Key Components:**
- Login handler (Gmail verification)
- Session manager
- Email service (admin notifications)
- Route protection middleware

**Dependencies:** SQLite (sessions), SMTP

---

### 6.3 ETL Scripts (scripts/)

**Directory:** `scripts/`  
**Responsibilities:** Source ingestion, data migration, validation

**Key Scripts:**
- `build_progress_data.py` — Task progress tracking, duplicate ID check
- `repo_guard.py` — SSOT repo root guard
- `person_import_etl.py` — Person XML import (T253)
- `vn_places_t0/t1/t2/` — Vietnamese temple GPS ETL (T241-T242)
- `vn_places_t243_normalize.py` — Name normalization (T243)
- `vn_places_t244_matching.py` — Place matching engine (T244)
- `t251_ld2_era_gap.py` — Era gap filling (T251)
- `t252_w1/w3/w4_*.py` — H3 fixes (T252)
- `t230_source_catalog_audit.py` — Source catalog audit (T230)
- `t210_ttl_file_report.py` — TTL file status report

**Dependencies:** SQLite, XML parser, SPARQL client, HTTP client

---

### 6.4 Frontend Modules

| Module | File | Purpose | Tech |
|--------|------|---------|------|
| Place Mapping | admin/placevn.html | Admin place mapping dashboard | HTML + Tailwind |
| TTL Visualization | admin/panorama.html | TTL ontology graph | HTML + VisJS/D3 |
| Name-Vi Mapping | admin/namevimap.html | Bulk name-vi mapping | HTML + Tailwind |
| Cross-Table Search | admin/search_all.html | Cross-table search | HTML + Tailwind |
| Login | admin/login.html | Auth gateway login | HTML |
| Person Import | admin/person_import.html | Person XML import UI | HTML + Tailwind |

**Dependencies:** React 18 (UMD), Tailwind CSS (CDN), Leaflet.js (CDN), Lucide Icons (CDN)

---

## 7. Error Handling

| Error Type | Handling Strategy | Example |
|------------|------------------|---------|
| **404 Not Found** | Return JSON with error message | Entity not found in DB |
| **500 Internal Error** | Log error, return generic message | Database connection failure |
| **Validation Error** | Return 400 with field details | Invalid place ID format |
| **Authentication Error** | Return 401, redirect to login | Missing or invalid session |
| **Authorization Error** | Return 403, access denied | Non-admin accessing admin route |
| **Rate Limit Exceeded** | Return 429 with retry-after | >100 req/min (search), >60 req/min (admin) |
| **External API Failure** | Fallback to cache or GoogleTranslator | Gemini API unavailable |
| **XSS Prevention** | _escHtml() on all rendered content | User-generated translation text |

---

## 8. Logging

| Log File | Purpose | Location |
|----------|---------|----------|
| `flask.log` | Main application log | Root directory |
| `app.log` | Application output | Root directory |
| `app_err.log` | Application errors | Root directory |
| `gateway_local.err` | Auth gateway errors | Root directory |
| `gateway_local.out` | Auth gateway output | Root directory |
| `session.md` | Session state log | Root directory |
| `docs/sessions/` | Session documentation | docs/sessions/YYYY-MM-DD/ |

**Logging Strategy:** File-based logging; no centralized log aggregation; logs rotated implicitly by file size

---

## 9. Monitoring

| Monitor | Tool | Method | Frequency |
|---------|------|--------|-----------|
| **Server health** | GET /api/health | HTTP endpoint | On demand |
| **RAG service health** | GET /api/rag/health | HTTP endpoint | On demand |
| **Pipeline status** | npm run pipeline | npm script | Before each review |
| **Duplicate IDs** | npm run dup:ids | npm script | Before each commit |
| **Test suite** | npm run tester:agent | npm script | Before each review |
| **E2E runtime** | node scripts/run-runtime-tests.cjs | Node script | Before each review |

---

## 10. Security Controls

| Control | Implementation | Location |
|---------|---------------|----------|
| **Authentication** | Gmail-based login + server-side sessions | server.py:5001 |
| **Authorization** | Route protection; admin-only routes | app.py:5000 |
| **API Key Secrecy** | Environment variable (never committed) | opencode-directives.md R6 |
| **XSS Prevention** | _escHtml() on all rendered content | places.html, app.py |
| **Route Separation** | Nginx routes /daoanh/api/login/* to 5001 | Nginx config |
| **Session Security** | HttpOnly, SameSite cookies | server.py |
| **Rate Limiting** | 100 req/min (search), 60 req/min (admin) | app.py |
| **Data Validation** | Input validation on all API endpoints | app.py |

---

## 11. Performance Considerations

| Area | Strategy | Target |
|------|----------|--------|
| **Entity Lookup** | Binary index O(log n) | < 10ms |
| **Place Search** | Paginated results (default 50) | < 2s |
| **Translation** | Cache DB prevents redundant API calls | Cache hit: < 50ms |
| **GIS Rendering** | Leaflet.js marker clustering | < 3s for 5,000 places |
| **Large File Processing** | Streaming generators | Constant memory |
| **Database Queries** | Indexed columns on DILA ID | < 50ms |

---

## 12. Extensibility Strategy

| Extension Point | Mechanism | Example |
|-----------------|-----------|---------|
| **New Data Source** | Source registry + adapter pattern | Add BDRC, Kanripo, SuttaCentral |
| **New API Endpoint** | Flask blueprint registration | Add /api/rag/vi/chat |
| **New Frontend Module** | HTML template + Tailwind | Add admin/report.html |
| **New ETL Script** | Python script in scripts/ | Add CBETA XML parser |
| **New Database Table** | Additive migration with manifest | Add place_media_refs table |
| **New Translation Model** | Gemini client wrapper | Switch to different LLM provider |

---
