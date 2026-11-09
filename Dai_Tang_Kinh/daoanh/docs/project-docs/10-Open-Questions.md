# 10-Open-Questions.md

# Open Questions — Đạo Ảnh / Tuệ Giác Số

**Document ID:** OQ-10  
**Version:** 1.0  
**Date:** 2026-10-08  
**Status:** Draft  
**Classification:** Internal — Enterprise Architecture  

---

## 1. Missing Information

The following information was not found in the analyzed markdown files and is required for complete architecture documentation:

| ID | Missing Information | Source Searched | Impact |
|----|---------------------|-----------------|--------|
| **MI-01** | Gemini API key value | All docs, AGENTS.md, opencode-directives.md | Required for translation service; currently stored as environment variable only |
| **MI-02** | SMTP configuration for admin emails | server.py, API_DOCS.md, AGENTS.md | Email notifications referenced but configuration not documented |
| **MI-03** | Nginx configuration file location | AGENTS.md §10, overview.md | Nginx routing rules described but config file path not specified |
| **MI-04** | Production VPS IP address and hostname | All docs | Referenced as `phatphaponline.org` but no IP or server details |
| **MI-05** | Database connection string format | SCHEMA.md, SYSTEM_MAP.md | SQLite file path documented but no connection string pattern |
| **MI-06** | Session timeout duration | server.py, AGENTS.md | Session management mentioned but timeout value not specified |
| **MI-07** | Rate limit enforcement mechanism | API_DOCS.md, app.py references | Rate limits documented (100/min, 60/min) but implementation not found |
| **MI-08** | GraphDB connection details | API_DOCS.md, AGENTS.md | GraphDB proxy endpoint documented but host/port not specified |
| **MI-09** | CBETA XML parser script location | roadmap.md, FEATURE_PLAN.md | CBETA pipeline planned but no script file referenced |
| **MI-10** | RAG service implementation | roadmap.md Khoá 6 | RAG architecture designed but no implementation files found |

---

## 2. Undocumented Assumptions

The following assumptions were made during architecture analysis based on available documentation:

| ID | Assumption | Evidence | Confidence | Risk if Wrong |
|----|-----------|----------|------------|---------------|
| **UA-01** | DILA ID is the canonical primary key for all entities | SYSTEM_MAP.md, SOURCE_REGISTRY.md, multiple docs | 95% | Entity linking breaks if another ID scheme is used |
| **UA-02** | SQLite is sufficient for current data volumes | SYSTEM_MAP.md (59K places, 48K persons) | 90% | Performance degradation if data grows 10x+ |
| **UA-03** | Nginx routes `/daoanh/api/login/*` to port 5001 | AGENTS.md §10, overview.md | 95% | Auth requests reach wrong server |
| **UA-04** | Gemini 2.0 Flash is the primary translation AI | overview.md, FEATURE_PLAN.md | 85% | Translation service fails if different model used |
| **UA-05** | Zero-RAM principle applies to all file operations | overview.md, AGENTS.md | 90% | Memory issues on large file processing |
| **UA-06** | All database migrations are additive-only | SCHEMA.md, AGENTS §14 | 85% | Data loss if destructive migration attempted |
| **UA-07** | No public user registration; admin-only access | API_DOCS.md, FEATURE_PLAN.md | 90% | Security gap if public registration added later |
| **UA-08** | File-level backups are sufficient for DR | SYSTEM_MAP.md, docs/backups/ | 80% | Extended downtime if database corruption occurs |
| **UA-09** | Single worktree shared across sessions | AGENTS.md §17 | 95% | Git conflicts if concurrent sessions modify same files |
| **UA-10** | Binary index is regenerable from FINAL tables | SYSTEM_MAP.md, overview.md | 85% | Index corruption requires full rebuild |

---

## 3. Technical Risks

| ID | Risk | Likelihood | Impact | Mitigation Status |
|----|------|-----------|--------|-------------------|
| **TR-01** | Single point of failure (one Flask instance per server) | High | High | Documented restart procedures; no HA clustering |
| **TR-02** | Git index.lock corruption on Windows host | Medium | High | Temp-index sync pattern documented (AGENTS §14) |
| **TR-03** | `.git/index` cannot be renamed (WinError 5) | High | Medium | Workaround via GIT_INDEX_FILE; requires careful staging |
| **TR-04** | HEAD shifts between concurrent sessions | High | Medium | Careful staging discipline; --cacheinfo pattern documented |
| **TR-05** | DILA legal status change (AUDITING → BLOCKED) | Medium | High | Source registry with legal audit; 5 active sources monitored |
| **TR-06** | Gemini API rate limits or outage | Medium | Medium | Translation cache; GoogleTranslator fallback |
| **TR-07** | No automated CI/CD pipeline | Medium | Medium | npm run pipeline as manual gate; admin review required |
| **TR-08** | `entity_unified` has 8+ hardcoded if/else branches | Medium | High | Planned for Build 4+ de-lock-in (SOURCE_INTEGRATION_ARCHITECTURE.md) |
| **TR-09** | Per-source route clones in app.py (6+ locations) | Medium | High | Planned for Build 4+ consolidation |
| **TR-10** | Source-named columns in geo_cross_ref (7 columns) | Medium | Medium | Planned for Build 4+ generic entity_external_ref table |
| **TR-11** | Duplicate `*_new` tables conflicting with 3-layer model | Low | Medium | Documented in SCHEMA.md; cleanup recommended |
| **TR-12** | No Redis caching layer | Low | Medium | Future scaling consideration |
| **TR-13** | No database encryption at rest | Low | Medium | SQLite file-level permissions only |
| **TR-14** | No centralized log aggregation | Low | Low | File-based logs; manual review |
| **TR-15** | 8 data sources blocked/deferred pending legal clearance | Medium | Medium | Source registry tracks status; no new ingestion until cleared |

---

## 4. Architecture Uncertainties

| ID | Uncertainty | Options | Decision Needed By | Impact |
|----|------------|---------|-------------------|--------|
| **AU-01** | Architecture style: Monolith vs. Microservices | Current monolith; future microservices possible | Admin (Build 4+) | High — affects deployment, scaling, team structure |
| **AU-02** | Database: SQLite vs. PostgreSQL | Current SQLite; PostgreSQL for production scale | Admin (6-12 months) | High — affects concurrent users, data integrity |
| **AU-03** | Cache layer: None vs. Redis | No cache currently; Redis for API responses | Build Agent (3-6 months) | Medium — affects API response times |
| **AU-04** | Authentication: Session-based vs. OAuth2/OIDC | Current session-based; OAuth2 for future | Admin (6-12 months) | Medium — affects admin onboarding, MFA |
| **AU-05** | Search: SQLite full-text vs. Elasticsearch | Current SQLite; Elasticsearch for deep search | Build Agent (6-12 months) | Medium — affects search relevance and performance |
| **AU-06** | Message queue: None vs. RabbitMQ/Kafka | No message queue currently | Admin (12+ months) | Low — affects ETL async processing |
| **AU-07** | Containerization: None vs. Docker/Kubernetes | Current direct Python execution | DevOps (6-12 months) | Medium — affects deployment consistency |
| **AU-08** | GraphDB: Optional vs. Required | Currently optional SPARQL proxy | Admin (6-12 months) | Low — affects RDF/TTL export capabilities |
| **AU-09** | Frontend: React UMD vs. SPA build | Current React UMD via CDN | Build Agent (6-12 months) | Low — affects build process, caching |
| **AU-10** | Monitoring: File logs vs. centralized (ELK/Prometheus) | Current file-based logs | DevOps (6-12 months) | Low — affects observability, alerting |

---

## 5. Decisions Required from Admin

| ID | Decision | Options | Recommended | Deadline |
|----|----------|---------|-------------|----------|
| **D-01** | Activate blocked data sources (8 sources) | Keep BLOCKED / Activate one by one / Activate all | Keep BLOCKED until legal clearance | Before next source integration |
| **D-02** | Person import commit (47,541 rows from T253) | Commit via UI / Commit via CLI / Defer | Commit via UI (admin action) | Before T253 follow-up tasks |
| **D-03** | Vietnamese temple GPS (places_vn) acceptance | Accept 6,002 rows / Require more validation / Reject | Accept with YELLOW source for DISANTONGIAO_VN | Before T245-T250 |
| **D-04** | H3 remaining 132 rows policy | Sięt (hundreds FAIL) / Leave as-is / Partial fix | Leave as-is; cosmetic only | Before T252 follow-up |
| **D-05** | Duplicate ID renumbering (T254 completed) | Verify no regressions / Run full pipeline | Run full pipeline to confirm | Immediate |
| **D-06** | Build 4+ de-lock-in scope | Full de-lock-in / Partial / Defer | Partial de-lock-in (entity_unified + route clones) | Build 4 planning |
| **D-07** | CI/CD automation | Manual pipeline / GitHub Actions / GitLab CI | Manual pipeline (current) | Before team scaling |

---

## 6. Unresolved Items

| ID | Item | Description | Blocker |
|----|------|-------------|---------|
| **UI-01** | CBETA XML parser not implemented | Pipeline XML → text_entities_raw → canon_citations planned but no script | No developer assigned |
| **UI-02** | Translation service not implemented | Phase 1-2 translation polish/cache planned but no code | Gemini API key not configured |
| **UI-03** | RAG Vietnamese service not designed | Khoá 6 architecture designed but no implementation | No LLM integration plan |
| **UI-04** | RDF/TTL export endpoint not available | File export works (1,037 files) but no API endpoint | Not prioritized |
| **UI-05** | Person authority DB not populated | 47,541 person records ready but not imported | Admin commit action pending |
| **UI-06** | Vietnamese temple GPS acceptance pending | 6,002 rows ready but DISANTONGIAO_VN source YELLOW | Admin legal verification |
| **UI-07** | Source legal status unresolved | 8 sources BLOCKED/DEFERRED pending legal clearance | Admin legal review |

---

## 7. Questions for Next Session

1. **Admin:** Should we activate any of the 8 blocked data sources (SAT, CHGIS, TGAZ, FoJin, BDRC, Kanripo, SuttaCentral, 84000)?
2. **Admin:** When will the 47,541 person records from T253 be committed to the database?
3. **Build Agent:** What is the timeline for Build 4+ de-lock-in (entity_unified, route clones, geo_cross_ref)?
4. **Admin:** Should we implement Redis caching for API responses?
5. **Security Team:** Should we add WAF rules on Nginx for SQL injection/XSS protection?
6. **Admin:** What is the preferred database upgrade path (SQLite → PostgreSQL) and timeline?
7. **Build Agent:** Should we containerize the application with Docker?
8. **Admin:** Should we implement OAuth2/OIDC for admin authentication?

---

## 8. Assumption Validation Plan

| ID | Assumption | Validation Method | Owner | Target Date |
|----|-----------|-------------------|-------|-------------|
| **VA-01** | DILA is canonical primary key | Cross-reference 100 random entities across sources | Build Agent | 2026-10-15 |
| **VA-02** | SQLite sufficient for current load | Load test with 59K places query | Build Agent | 2026-10-20 |
| **VA-03** | Binary index regenerable | Delete index, rebuild from FINAL tables | Build Agent | 2026-10-25 |
| **VA-04** | Additive-only migrations safe | Test revert on copy of lineage.db | Build Agent | 2026-10-30 |
| **VA-05** | Translation cache effective | Measure cache hit rate over 1 week | Build Agent | 2026-11-15 |

---
