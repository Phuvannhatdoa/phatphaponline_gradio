---
id: T362
title: "Phase 1 Stabilization: Standardize Error Responses (all 322 routes)"
status: pending
created: 2026-10-12
updated: 2026-10-12
parent: null
former_ids: []
depends_on: []
done_when:
  - "Tất cả 322 routes trả về error format thống nhất: {error: {code, message, timestamp}}"
  - "No more inconsistency: error vs success vs status fields"
  - "Admin error log ghi rõ error_code + timestamp + endpoint → dễ debug"
  - "Test: Try 5 different error cases (404, 500, validation) → format thống nhất"
---

## Context

Audit phát hiện **Issue #10: No Error Handling Standardization**.

Vấn đề: 322 routes trả về error format khác nhau → Frontend khó parse.

---

## Phạm Vi

### 1. Create APIError Class

```python
class APIError(Exception):
    def __init__(self, code, message, http_code=400, details=None):
        self.code = code          # e.g., 'NOT_FOUND', 'INVALID_INPUT'
        self.message = message    # e.g., 'Monk không tồn tại'
        self.http_code = http_code
        self.details = details
    
    def to_json(self):
        return {
            'error': {
                'code': self.code,
                'message': self.message,
                'details': self.details,
                'timestamp': datetime.now().isoformat()
            }
        }

@app.errorhandler(APIError)
def handle_api_error(e):
    return jsonify(e.to_json()), e.http_code
```

### 2. Replace All Error Responses

**Before:**
```python
if not person:
    return jsonify({'error': 'Not found'}), 404
```

**After:**
```python
if not person:
    raise APIError('NOT_FOUND', 'Monk A000035 không tồn tại', 404)
```

### 3. Add Error Codes Registry

```python
# daoanh/lib/error_codes.py
ERROR_CODES = {
    'NOT_FOUND': 404,
    'INVALID_INPUT': 400,
    'UNAUTHORIZED': 401,
    'DB_ERROR': 500,
    'CONFLICT': 409,
    ...
}
```

---

## Timeline: 6-8 hours (audit all routes + refactor)

---

## Dependency

- Non-blocking (parallel)
