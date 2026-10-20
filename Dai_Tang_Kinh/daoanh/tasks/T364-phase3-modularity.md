---
id: T364
title: "Phase 3 Planning: Modularize app.py (Weeks 6-8)"
status: pending
created: 2026-10-12
updated: 2026-10-12
parent: null
former_ids: []
depends_on: [T363]
done_when:
  - "app.py split into 5 feature blueprints (persons, places, admin, search, export)"
  - "Shared utilities extracted to daoanh/lib/ modules"
  - "Unit tests added: 80%+ coverage on each blueprint"
  - "Deployment tested: features work independently"
  - "CLAUDE.md updated with new architecture"
---

## Context

Phase 2 improves performance.
Phase 3 improves maintainability by splitting monolithic app.py (1.1MB, 322 routes).

Current problem:
- Single 1.1MB file makes code review difficult
- Reloader slow (5+ seconds per change)
- Cannot test individual features without full import
- Merge conflicts inevitable with concurrent development

---

## Scope

### 1. Blueprint Architecture

Split app.py into:
```
daoanh/
├── app.py (app factory + config)
├── api/
│   ├── __init__.py
│   ├── persons.py (person/lineage/bio routes)
│   ├── places.py (place/geo routes)
│   ├── admin.py (admin/auth routes)
│   ├── search.py (lexicon/search routes)
│   └── export.py (RDF/TTL export routes)
├── lib/
│   ├── db_pool.py (connection pooling)
│   ├── error_handler.py (APIError class)
│   ├── auth.py (session/token validation)
│   └── utils.py (common functions)
└── tests/
    ├── test_persons.py
    ├── test_places.py
    ├── test_admin.py
    ├── test_search.py
    └── test_export.py
```

### 2. Application Factory Pattern

```python
# daoanh/app.py
def create_app(config=None):
    app = Flask(__name__)
    
    # Register blueprints
    from daoanh.api import persons, places, admin, search, export
    app.register_blueprint(persons.bp)
    app.register_blueprint(places.bp)
    app.register_blueprint(admin.bp)
    ...
    
    return app
```

### 3. Unit Tests

- Target: 80%+ coverage per blueprint
- Test: API endpoints (happy path + error cases)
- Test: DB interactions (mocked)
- Framework: pytest

---

## Deliverables

- Split app.py into 5 blueprints (persons, places, admin, search, export)
- daoanh/lib/ utilities extracted
- Unit tests (test/ directory)
- CLAUDE.md architecture update
- Deployment testing docs

---

## Timeline: 3 weeks (Phase 3)

---

## Dependencies

- Depends on: Phase 2 completion
- Can start: Parallel with Phase 2 (if blueprints designed early)
