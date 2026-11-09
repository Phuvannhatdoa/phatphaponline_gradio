# 01-System-Overview.md

# System Overview — Đạo Ảnh (Tuệ Giác Số / PTDA)

**Document ID:** SAD-01  
**Version:** 1.0  
**Date:** 2026-10-08  
**Status:** Approved for Review  
**Classification:** Internal — Enterprise Architecture  

---

## Executive Summary

Đạo Ảnh (Phật Tổ Đạo Ảnh / Tuệ Giác Số) is a Buddhist Geographic Information System (GIS) and knowledge management platform designed to map, link, and query Buddhist entities—places, persons, texts, and time periods—across multiple authority sources. The system serves as a digital research hub for Buddhist studies, integrating data from DILA (Dharma Drum Institute of Liberal Arts), CBETA (Chinese Buddhist Electronic Text Association), Marcus SNA, Wikidata, GeoNames, and internal Vietnamese TTL (Thiền Tuệ Luận) corpora.

The system employs a **two-server architecture**: an Authentication Gateway (port 5001) handling login and session management, and a Main Server (port 5000) handling all business logic including place-person mapping, TTL ontology visualization, search, and translation services. Data follows a **zero-RAM principle** with a 4-layer architecture (RAW → STAGING → FINAL → INDEX) enabling O(log n) lookup via binary indexes without loading full datasets into memory.

---

## Project Purpose

The primary purpose of Đạo Ảnh is to:

1. **Map Buddhist entities** across authoritative sources (DILA, CBETA, Marcus, Wikidata, GeoNames) using DILA ID as the canonical primary key.
2. **Provide GIS visualization** of Buddhist places with GPS coordinates and cross-reference overlays.
3. **Enable person-place-time (nexus) queries** for Buddhist historical research.
4. **Support Vietnamese Buddhist studies** through TTL corpus integration, person authority databases, and lineage visualization.
5. **Maintain data governance** with legal licensing audit, source authority scoring, and additive-only migration patterns.

---

## Business Objectives

| Objective | Description | Success Metric |
|-----------|-------------|----------------|
| **BO-01** | Consolidate Buddhist place/person authority from 13+ sources | 59,167+ DILA places mapped; 48,803 persons indexed |
| **BO-02** | Provide zero-latency GIS search with GPS | Sub-2s query response for 5,000+ geocoded places |
| **BO-03** | Enable TTL Vietnamese Buddhist corpus ETL | 2,000+ TTL files processed into person/place/graph entities |
| **BO-04** | Maintain legal compliance for all data sources | 13 sources audited; 5 active, 8 blocked/deferred |
| **BO-05** | Support administrative curation workflow | Admin dashboard with HITL (Human-in-the-Loop) canonical decisions |
| **BO-06** | Export Buddhist knowledge graph as TTL/RDF | 1,037+ TTL v2 files exported with SHA verification |

---

## Scope

### In Scope

- **Place Authority:** DILA places (59,167 records), CBETA places, Vietnamese temple GPS (6,002+ records via Wikidata/OSM/disantongiao.vn)
- **Person Authority:** DILA persons (48,803 records), Marcus SNA network, Vietnamese TTL person authority (planned)
- **Time Authority:** Chinese/Vietnamese dynasty periods, era names, JDN conversion
- **Text Authority:** CBETA canon texts, passages, citations (planned pipeline)
- **Nexus Points:** Person-place-time relationship queries
- **GIS Visualization:** Leaflet.js map with markers, clusters, and cross-reference overlays
- **Translation Services:** Gemini AI-powered CBETA→Vietnamese translation with polish and cache
- **Authentication:** Gmail-based login, session management, admin email notifications
- **API Ecosystem:** RESTful endpoints for places, persons, dictionary, deep search, nexus queries, GraphDB SPARQL proxy

### Out of Scope

- Bulk re-hosting of copyrighted images (FROGBEAR, BDRC)
- Full-text hosting of CBETA corpus (only metadata and citations)
- Public-facing user registration (admin-only curation)
- Real-time collaboration or multi-user editing
- Mobile native applications (web-responsive only)

---

## Stakeholders

| Stakeholder | Role | Responsibilities |
|-------------|------|------------------|
| **Admin (No-coding)** | System Owner | Approves source integration, legal checks, canonical decisions, data imports |
| **Build Agent (ClaudeCode)** | Developer | Implements features, fixes bugs, runs ETL scripts, maintains codebase |
| **Plan Agent** | Architect | Designs system architecture, creates specs, reviews technical debt |
| **Tester Agent** | QA | Runs lint, test, e2e, runtime checks before review |
| **Buddhist Researchers** | End Users | Query places/persons/texts, use GIS map, read translations |
| **DILA Authority** | Data Partner | Provides canonical place/person/time authority data |

---

## Assumptions

1. **DILA is the canonical authority** for place/person IDs; external IDs are cross-references only.
2. **SQLite is sufficient** for current data volumes (59K places, 48K persons, 166K dictionary terms).
3. **Zero-RAM principle** applies to all large file operations (streaming + binary indexes).
4. **Additive-only database migrations** — no destructive schema changes without backup.
5. **Nginx routes** `/daoanh/api/login/*` to port 5001 and everything else to port 5000.
6. **Gemini API key** is configured via environment variable, never committed to code.
7. **All sessions** share a single worktree; HEAD may shift between sessions.

---

## Constraints

| Constraint | Description | Impact |
|------------|-------------|--------|
| **C1** | No `git init` inside `daoanh/` subdirectory | Preserves single repo history at `visjs-app` level |
| **C2** | Git operations must run from repo root (`visjs-app`) | Prevents history splitting and revert failures |
| **C3** | `.git/index` cannot be renamed on this host (WinError 5) | Requires temp-index sync pattern for concurrent sessions |
| **C4** | DILA only supports Vietnamese monks as primary | Vietnamese monk data requires supplementary scanning |
| **C5** | 13 data sources under legal audit; 8 blocked/deferred | Limits new source integration until legal clearance |
| **C6** | No bulk CBETA text hosting | Only metadata and citation-level access |
| **C7** | Single worktree shared across sessions | HEAD shifts require careful staging discipline |

---

## Key Features

| Feature | Module | Status |
|---------|--------|--------|
| Place-Person Mapping | Đạo Ảnh Dashboard (placevn.html) | ✅ Complete |
| GIS Visualization with Leaflet | M7 GIS Maps | ✅ Complete (global), In Progress (VN) |
| TTL Ontology Visualization | Panorama (panorama.html) | ✅ Complete |
| Name-Vi Bulk Mapping | namevimap.html | ✅ Complete |
| Cross-Table Search | search_all.html | ✅ Complete |
| Authentication & Session Mgmt | server.py:5001 | ✅ Complete |
| Admin Email Notifications | server.py:5001 | ✅ Complete |
| Vietnamese Temple GPS (Wikidata/OSM) | M7-VN (T241-T250) | ⚠️ Partial (T0-T2 done) |
| Person Authority DB (XML DILA → DB) | T253 | ✅ Built, awaiting admin commit |
| Evidence & Provenance Panel | T259/T260 | ✅ Complete |
| Translation Polish & Cache | Phase 1-2 | ⚠️ Planned |
| RDF/TTL Export | T227 | ✅ Complete (1,037 files) |

---

## Terminology

| Term | Definition |
|------|------------|
| **DILA ID** | Canonical primary key (format: A000001 for persons, PLxxxxxx for places) |
| **PTDA** | Phật Tổ Đạo Ảnh — the Buddhist Patriarch Mapping system |
| **TGS** | Tuệ Giác Số — Digital Wisdom center for Buddhist studies |
| **TTL** | Thiền Tuệ Luận — Vietnamese Zen corpus (~2,000 files) |
| **Nexus Point** | Intersection of person + place + time in Buddhist history |
| **HITL** | Human-in-the-Loop — admin canonical decision workflow |
| **Zero-RAM** | Principle of never loading full datasets into memory; uses streaming + binary indexes |
| **Additive Migration** | Database change pattern that only adds columns/tables, never drops |
| **Source Authority Score** | Numeric ranking (0-100) determining data source precedence |
| **Legal Status** | Source compliance state: AUDITING, ACTIVE, BLOCKED, DEFERRED, REFERENCE_ONLY, LEGACY |
| **Entity Hub** | Central table (167,006 entities) unifying persons, places, texts |
| **Claim** | A data assertion linking an entity to a source with provenance |

---
