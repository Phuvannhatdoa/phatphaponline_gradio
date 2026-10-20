# QA1 REPORT - Initial System Audit

**Date:** 2026-04-12
**Project:** Đạo Ảnh - Buddhist GIS

---

## SUMMARY

| Category | Count |
|----------|-------|
| Files Scanned | 100+ |
| Python Files | 52 |
| JS Files | 33 |
| APIs Found | 68+ |
| Data Files | 40+ |
| Issues | 8 |

---

## COMPONENTS

### Backend (Flask)
- `/` - Main index
- `/daoanh/` - Daoanh index
- `/daoanh/admin/` - Admin panel
- `/daoanh/data/places.json` - Places data endpoint
- `/api/places` - Get all places
- `/api/stats` - Statistics
- `/api/places/<place_id>/lineage` - Place lineage
- `/api/gps-changes` - GPS changes tracking
- `/api/admin/places` - Admin places CRUD
- `/api/admin/sources` - Source management
- `/api/admin/dila-stats` - DILA statistics
- `/api/admin/gps-compare` - GPS comparison
- `/api/admin/verification/list` - Verification staging
- `/api/admin/staging/list` - Staging list
- `/api/persons` - Person data
- `/api/persons/search` - Person search
- `/api/persons/stats` - Person statistics
- `/api/entity/link` - Entity linking
- `/api/entity/resolve` - Entity resolution
- `/api/nexus/find` - Nexus finder
- `/api/lineage-map/<monk_name>` - Lineage map
- `/api/crawler/wiki` - Wiki crawler
- `/api/crawler/dila` - DILA crawler
- `/api/dict/search` - Dictionary search
- `/api/dict/merge` - Dictionary merge
- `/api/dict/stats` - Dictionary stats
- `/api/deepsearch` - Deep search
- `/api/sutra/<sutra_id>` - Sutra lookup
- `/api/graphdb/sparql` - SPARQL endpoint
- `/api/rag/query` - RAG query

### Frontend (JavaScript)
- `src/js/app.js` - Main application
- `src/js/map.js` - Leaflet map
- `src/js/search.js` - Search functionality
- `src/js/lineage_map.js` - Lineage visualization
- `src/js/entity_linker.js` - Entity linking
- `src/js/entity_filter.js` - Entity filtering
- `src/js/dila_authority.js` - DILA authority
- `src/js/graphdb.js` - GraphDB client
- `src/js/auth.js` - Authentication
- `src/js/security.js` - Security utilities
- `src/js/performance.js` - Performance monitoring
- `src/js/deepsearch.js` - Deep search UI
- `src/js/api_router.js` - API router
- `src/js/buddhist_icons.js` - Buddhist icons
- `src/js/popup_cards.js` - Popup cards
- `src/js/network_viewer.js` - Network viewer
- `src/js/text_comparison.js` - Text comparison
- `src/js/zero_ram_index.js` - Zero-RAM index
- `src/js/sutra_sync.js` - Sutra sync
- `src/js/pathfinding.js` - Path finding
- `src/js/timeline/manager.js` - Timeline manager
- `src/js/timeline/slider.js` - Timeline slider
- `src/js/timeline/gis_integration.js` - GIS integration
- `src/js/ai/orchestrator.js` - AI orchestrator
- `src/js/ai/rag_connector.js` - RAG connector
- `src/js/ai/fusion_engine.js` - Fusion engine
- `src/js/ai/dila_connector.js` - DILA connector
- `src/js/ai/semantic_parser.js` - Semantic parser
- `src/js/ai/intent_router.js` - Intent router
- `src/js/ai/sparql_generator.js` - SPARQL generator
- `src/js/ai/response_formatter.js` - Response formatter
- `src/js/dict/popup_renderer.js` - Dict popup renderer
- `src/js/dict/hover_detector.js` - Dict hover detector
- `src/js/dict/dict_loader.js` - Dict loader
- `src/js/search/trie_index.js` - Trie index
- `src/js/admin/dashboard.js` - Admin dashboard
- `src/js/config.js` - Configuration
- `admin/js/app.js` - Admin app

### Data (JSON)
- `data/places.json` - Main places data
- `data/persons.json` - Person data
- `data/places_full.json` - Full places
- `data/places_merged.json` - Merged places
- `data/places_cbeta.json` - CBETA places
- `data/dila_import/` - DILA imports
- `data/processed/` - Processed data
- `data/dict/` - Dictionary data

---

## ISSUES FOUND

| Issue | Severity | Location |
|-------|----------|----------|
| App.py has 1653 lines - monolithic | Medium | app.py |
| Duplicate JSON data files (places.json, places_full.json, places_merged.json) | Medium | data/ |
| No centralized logging configuration | Low | app.py |
| Multiple source files without clear documentation | Low | src_python/ |
| No input validation on some API endpoints | Medium | app.py:429+ |
| Hardcoded paths in some ETL scripts | Low | src/python/etl/ |
| Missing error handling in crawler endpoints | Medium | app.py:1317+ |
| No rate limiting on public APIs | High | app.py |

---

## RECOMMENDATIONS

1. Refactor app.py into modular Blueprints (places, persons, admin, crawler, dict)
2. Consolidate JSON data files - use single source of truth with versioning
3. Add structured logging (e.g., structlog)
4. Add input validation using marshmallow or pydantic
5. Implement rate limiting on public endpoints
6. Document API endpoints with OpenAPI/Swagger
7. Add comprehensive error handling in ETL scripts
8. Separate crawler logic from Flask app