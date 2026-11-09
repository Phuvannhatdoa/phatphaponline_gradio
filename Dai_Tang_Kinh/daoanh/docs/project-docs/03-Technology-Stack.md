# 03-Technology-Stack.md

# Technology Stack — Đạo Ảnh / Tuệ Giác Số

**Document ID:** TDS-03  
**Version:** 1.0  
**Date:** 2026-10-08  
**Status:** Draft  

---

## Backend Technologies

| Technology | Version | Purpose | Usage | Dependencies | Evidence |
|------------|---------|---------|-------|--------------|----------|
| **Flask** | Python 3 | Web framework | Main application (app.py ~2,600 lines), Auth gateway (server.py ~125 lines) | Python 3.11+, Werkzeug | app.py, server.py, overview.md |
| **Python 3** | 3.11+ | Application runtime | All backend logic, ETL scripts, API routes | Flask, sqlite3, json, re | package.json, app.py, scripts/ |
| **SQLite** | Embedded | Database | lineage.db with 4-layer architecture (RAW/STAGING/FINAL/INDEX) | None built-in | SCHEMA.md, SYSTEM_MAP.md, overview.md |
| **Gunicorn/Nginx** | Production | WSGI server + Reverse Proxy | Production deployment on VPS, SSL termination, route splitting (5001/5000) | None | AGENTS.md §10, overview.md |

---

## Frontend Technologies

| Technology | Version | Purpose | Usage | Dependencies | Evidence |
|------------|---------|---------|-------|--------------|----------|
| **React 18** | 18.x (UMD + Babel standalone) | Frontend UI framework | Admin dashboard components (placevn.html, namevimap.html, search_all.html) | Babel, Tailwind CSS | package.json, FEATURE_PLAN.md, overview.md |
| **Tailwind CSS** | 4.2.4 (CDN) | CSS framework | Styling for admin UI components | PostCSS | package.json, devDependencies |
| **Leaflet.js** | CDN | Map visualization | GIS map with markers, clusters, GPS cross-references | None | overview.md, FEATURE_PLAN.md |
| **Lucide Icons** | CDN | Icon library | UI icons for admin dashboard | None | overview.md |
| **VisJS / D3.js** | CDN | Network visualization | Lineage tree, person-place graph, TTL ontology visualization | None | AGENTS.md, FEATURE_PLAN.md |
| **Playwright** | 1.59.1 | E2E testing | Browser automation for runtime JS error checks | @playwright/test | package.json, tester agent |

---

## Database Technologies

| Technology | Version | Purpose | Usage | Dependencies | Evidence |
|------------|---------|---------|-------|--------------|----------|
| **SQLite** | Embedded | Primary database | lineage.db — persons (48,803), places (59,167+), dictionary (166,278), entity claims (447,885) | None | SYSTEM_MAP.md, SCHEMA.md, overview.md |
| **Binary Index** | Custom | O(log n) lookup | indexed/entity_master.idx — binary search index for fast entity lookup | SQLite | SYSTEM_MAP.md, overview.md (Zero-RAM principle) |
| **GraphDB** | SPARQL endpoint | RDF/TTL storage | External GraphDB at localhost:7200 for lineage data queries | SPARQL protocol | AGENTS.md, API_DOCS.md |
| **JSON files** | File-based | Data interchange | monk_names_vn.json (68KB), places data, person data | None | directory listing, SYSTEM_MAP.md |

---

## Infrastructure Technologies

| Technology | Version | Purpose | Usage | Dependencies | Evidence |
|------------|---------|---------|-------|--------------|----------|
| **Nginx** | Production | Reverse proxy | Routes /daoanh/api/login/* to port 5001, everything else to port 5000 | None | AGENTS.md §10, overview.md |
| **VPS** | Production | Hosting | Production server running Flask, Nginx, SQLite | systemd/pm2 (planned) | AGENTS.md, FEATURE_PLAN.md |
| **Git** | Version control | Source code management | Single repo at visjs-app level; daoanh is subdirectory | None | AGENTS.md §13, §14 |
| **Docker** | Not used | Containerization | Not currently used; deployment via direct Python execution | None | Not detected |
| **Kubernetes** | Not used | Orchestration | Not currently used | None | Not detected |
| **Terraform** | Not used | IaC | Not currently used | None | Not detected |

---

## Messaging Technologies

| Technology | Version | Purpose | Usage | Dependencies | Evidence |
|------------|---------|---------|-------|--------------|----------|
| **None** | N/A | No message queue detected | No Kafka, RabbitMQ, or similar messaging infrastructure | N/A | No evidence found |
| **HTTP REST** | 1.1 | API communication | All inter-service communication via HTTP REST | Flask | API_DOCS.md |
| **SPARQL** | 1.1 | Graph database queries | GraphDB proxy for ontology queries | GraphDB | API_DOCS.md |

---

## Authentication Technologies

| Technology | Version | Purpose | Usage | Dependencies | Evidence |
|------------|---------|---------|-------|--------------|----------|
| **Flask Sessions** | Built-in | Session management | Server-side sessions for auth gateway | Flask | server.py, AGENTS.md §10 |
| **Gmail Verification** | External | Login authentication | Gmail-based login check for admin access | Gmail API (implicit) | AGENTS.md §10, API_DOCS.md |
| **Secure Cookies** | Browser | Session persistence | HttpOnly, SameSite cookies for session tokens | Browser | AGENTS.md §10 |
| **Environment Variables** | OS | Secret storage | Gemini API key stored in env var, never committed | None | opencode-directives.md R6 |

---

## Observability Stack

| Technology | Version | Purpose | Usage | Dependencies | Evidence |
|------------|---------|---------|-------|--------------|----------|
| **Flask Logs** | Built-in | Application logging | flask.log, app.log, app_err.log files | None | directory listing |
| **Gateway Logs** | Built-in | Gateway logging | gateway_local.err, gateway_local.out | None | directory listing |
| **Tester Agent** | Custom | Automated testing | npm run tester:agent (lint, test, e2e, runtime) | Playwright, ESLint | AGENTS.md §11, package.json |
| **Pipeline** | npm script | CI/CD gate | npm run pipeline (guard + dup:ids + lint + test + e2e + runtime) | All test tools | package.json |
| **Error Logs** | File-based | Error tracking | app_err.log, app_error.log, server_local.err | None | directory listing |

---

## Detected Technology Summary

**Backend:** Flask (Python 3), SQLite, Gunicorn/Nginx (production)  
**Frontend:** React 18 (UMD), Tailwind CSS, Leaflet.js, VisJS/D3.js, Lucide Icons  
**Database:** SQLite (primary), GraphDB (external SPARQL), Binary Index (custom)  
**Infrastructure:** Nginx (reverse proxy), VPS hosting  
**Messaging:** None (HTTP REST only)  
**Authentication:** Flask Sessions, Gmail verification, Secure Cookies  
**Observability:** File-based logs, Tester Agent, npm pipeline  
**AI/LLM:** Gemini 2.0 Flash (translation), GoogleTranslator (fallback)  
**Testing:** Playwright (E2E), ESLint (lint), Custom Python tests  

---

## Evidence Sources

- `overview.md` — Tech stack, two-server architecture, data architecture
- `API_DOCS.md` — API endpoints, base URLs, rate limits
- `SYSTEM_MAP.md` — 4-layer data model, key statistics
- `SCHEMA.md` — 3-layer database model, table definitions
- `package.json` — npm dependencies, scripts, devDependencies
- `app.py` — Main application (~2,600 lines)
- `server.py` — Auth gateway (~125 lines)
- `AGENTS.md` — Server architecture, route ownership, Nginx routing
- `opencode-directives.md` — OpenCode integration directives
- `SOURCE_REGISTRY.md` — Data source registry with legal audit
- `SOURCE_INTEGRATION_ARCHITECTURE.md` — Source integration patterns

---
