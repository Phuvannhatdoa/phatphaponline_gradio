---
id: T361
title: "Phase 1 Stabilization: Add API Versioning (v1/v2 routes)"
status: pending
created: 2026-10-12
updated: 2026-10-12
parent: null
former_ids: []
depends_on: []
done_when:
  - "Tất cả endpoint thêm /v1/ prefix: /daoanh/api/v1/persons, /v1/places, etc."
  - "Old routes (/daoanh/api/persons) redirect → /v1/ with deprecation warning"
  - "Reserve /v2/ for future enhancements (không implement, chỉ chuẩn bị)"
  - "Update CLAUDE.md + API docs với version info"
  - "Test: curl /daoanh/api/v1/persons/A000035 → works; /daoanh/api/persons/A000035 → deprecation warning"
---

## Context

Sau audit, phát hiện **Issue #6: No API Versioning**.

Vấn đề: Không thể evolve API contracts mà không break clients.
→ Khóa Admin vào fixed API shape.

---

## Phạm Vi

### 1. Code Changes (app.py)

**Add version prefix:**
```python
@app.route('/daoanh/api/v1/persons/<person_id>', methods=['GET'])
def get_person_v1(person_id):
    # Current implementation (keep as-is)

@app.route('/daoanh/api/persons/<person_id>', methods=['GET'])
def get_person_legacy(person_id):
    # Redirect to v1 with warning header
    response = jsonify(...)
    response.headers['Deprecation'] = 'true'
    response.headers['Sunset'] = '2026-12-31'
    return response, 301
```

### 2. Update All Routes (322 endpoints)

- Pattern: `/daoanh/api/{endpoint}` → `/daoanh/api/v1/{endpoint}`
- Create redirect for old routes
- Add to nginx config (if VPS deploy)

### 3. Documentation

- Update CLAUDE.md: API versioning strategy
- Add `docs/API_VERSIONING.md`
- Update swagger/API docs (if exist)

---

## Timeline: 4-6 hours

---

## Dependency

- Non-blocking (parallel with T360)
