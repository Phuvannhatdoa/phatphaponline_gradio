# 05-API-Specification.md

# API Specification — Đạo Ảnh / Tuệ Giác Số

**Document ID:** API-05  
**Version:** 1.0  
**Date:** 2026-10-08  
**Status:** Draft  
**Classification:** Internal — Enterprise Architecture  

---

## Base URLs

| Environment | URL | Notes |
|-------------|-----|-------|
| **Local Development** | http://localhost:5000 | Main server (business logic) |
| **Auth Gateway (Local)** | http://localhost:5001 | Login and session management |
| **Production** | https://phatphaponline.org/daoanh | Production via Nginx reverse proxy |

---

## Rate Limits

| API Category | Limit | Scope |
|--------------|-------|-------|
| Search APIs | 100 requests/minute | /api/places, /api/persons/search, /api/deepsearch |
| Admin APIs | 60 requests/minute | /api/admin/*, /daoanh/api/admin/* |
| Authentication | Not rate-limited | /daoanh/api/login/* |

---

## Public Endpoints

### 1. GET /

**Purpose:** Home page  
**Authentication:** None  
**Request:** None  
**Response:** HTML (index.html)  
**Error Codes:** None  

---

### 2. GET /daoanh/

**Purpose:** Main GIS application  
**Authentication:** None  
**Request:** None  
**Response:** HTML (placevn.html)  
**Error Codes:** None  

---

### 3. GET /daoanh/admin/

**Purpose:** Admin dashboard  
**Authentication:** Admin session required  
**Request:** None  
**Response:** HTML (placevn.html via app.py:5000)  
**Error Codes:** 401 if not authenticated  

---

## Places API

### 4. GET /api/places

**Purpose:** Get all places with pagination and search  
**Authentication:** None  
**Rate Limit:** 100 requests/minute  

**Query Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| page | int | 1 | Page number |
| limit | int | 50 | Results per page |
| search | string | - | Search by place name |

**Request:** None  

**Response:**
```json
{
  "count": 5000,
  "places": [
    {
      "id": "PL000000023255",
      "name": "Thiếu Lâm Tự",
      "province": "Hồ Chí Minh",
      "lat": 11.4233,
      "lng": 106.4953,
      "source": "DILA",
      "verified": true
    }
  ]
}
```

**Error Codes:**
- 400: Invalid page or limit parameter
- 500: Database query failure

---

### 5. GET /api/stats

**Purpose:** Get place statistics  
**Authentication:** None  
**Rate Limit:** 100 requests/minute  

**Request:** None  

**Response:** JSON with place count, source distribution, geographic coverage  
**Error Codes:** 500: Database query failure  

---

## Persons API

### 6. GET /api/persons

**Purpose:** Get all persons  
**Authentication:** None  
**Rate Limit:** 100 requests/minute  

**Request:** None  

**Response:** JSON array of person records with DILA ID, names, dynasty, lineage  
**Error Codes:** 500: Database query failure  

---

### 7. GET /api/persons/search?q={query}

**Purpose:** Search persons by name  
**Authentication:** None  
**Rate Limit:** 100 requests/minute  

**Query Parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| q | string | Yes | Search query (person name) |

**Request:** None  

**Response:** JSON array of matching persons  
**Error Codes:**
- 400: Missing q parameter
- 500: Database query failure  

---

### 8. GET /api/persons/timeline

**Purpose:** Get dynasty distribution  
**Authentication:** None  
**Rate Limit:** 100 requests/minute  

**Request:** None  

**Response:** JSON with dynasty distribution statistics  
**Error Codes:** 500: Database query failure  

---

### 9. GET /api/persons/by-dynasty?dynasty={dynasty}

**Purpose:** Filter persons by dynasty  
**Authentication:** None  
**Rate Limit:** 100 requests/minute  

**Query Parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| dynasty | string | Yes | Dynasty name (e.g., "Táng", "Đinh") |

**Request:** None  

**Response:** JSON array of persons from specified dynasty  
**Error Codes:**
- 400: Missing dynasty parameter
- 500: Database query failure  

---

## Dictionary API

### 10. GET /api/dict/search?q={term}

**Purpose:** Search StarDict dictionary  
**Authentication:** None  
**Rate Limit:** 100 requests/minute  

**Query Parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| q | string | Yes | Search term |

**Request:** None  

**Response:** JSON with dictionary entries (term, definition, source)  
**Error Codes:**
- 400: Missing q parameter
- 500: Database query failure  

---

### 11. GET /api/dict/stats

**Purpose:** Get dictionary statistics  
**Authentication:** None  
**Rate Limit:** 100 requests/minute  

**Request:** None  

**Response:** JSON with dictionary count, term count, source distribution  
**Error Codes:** 500: Database query failure  

---

### 12. GET /api/dict/entities

**Purpose:** Get extracted entities (places + monks)  
**Authentication:** None  
**Rate Limit:** 100 requests/minute  

**Request:** None  

**Response:** JSON with extracted entities from dictionary  
**Error Codes:** 500: Database query failure  

---

## Admin API

### 13. GET /api/admin/places

**Purpose:** List all places with pagination (admin)  
**Authentication:** Admin session required  
**Rate Limit:** 60 requests/minute  

**Request:** None  

**Response:** JSON with paginated place list  
**Error Codes:**
- 401: Not authenticated
- 403: Not admin
- 500: Database query failure  

---

### 14. PUT /api/admin/places/{id}

**Purpose:** Update place  
**Authentication:** Admin session required  
**Rate Limit:** 60 requests/minute  

**Path Parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Place ID (DILA format: PLxxxxxx) |

**Request Body:**
```json
{
  "name": "Thiếu Lâm Tự",
  "province": "Hồ Chí Minh",
  "lat": 11.4233,
  "lng": 106.4953,
  "source": "DILA"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Place updated"
}
```

**Error Codes:**
- 400: Invalid request body
- 401: Not authenticated
- 403: Not admin
- 404: Place not found
- 500: Database update failure  

---

### 15. GET /api/admin/dila-stats

**Purpose:** DILA data statistics  
**Authentication:** Admin session required  
**Rate Limit:** 60 requests/minute  

**Request:** None  

**Response:** JSON with DILA source statistics  
**Error Codes:**
- 401: Not authenticated
- 403: Not admin
- 500: Database query failure  

---

### 16. GET /api/admin/person-stats

**Purpose:** Person statistics  
**Authentication:** Admin session required  
**Rate Limit:** 60 requests/minute  

**Request:** None  

**Response:** JSON with person statistics  
**Error Codes:**
- 401: Not authenticated
- 403: Not admin
- 500: Database query failure  

---

## Crawler API

### 17. POST /api/crawler/wiki

**Purpose:** Run Wikipedia crawler  
**Authentication:** Admin session required  
**Rate Limit:** 60 requests/minute  

**Request Body:**
```json
{
  "query": "Buddhist temple Vietnam",
  "limit": 50
}
```

**Response:**
```json
{
  "status": "success",
  "crawled": 50,
  "message": "Wikipedia crawl completed"
}
```

**Error Codes:**
- 401: Not authenticated
- 403: Not admin
- 500: Crawler failure  

---

### 18. POST /api/crawler/dila

**Purpose:** Run DILA sync  
**Authentication:** Admin session required  
**Rate Limit:** 60 requests/minute  

**Request:** None  

**Response:**
```json
{
  "status": "success",
  "synced": 1000,
  "message": "DILA sync completed"
}
```

**Error Codes:**
- 401: Not authenticated
- 403: Not admin
- 500: Sync failure  

---

### 19. GET /api/admin/crawler/list

**Purpose:** List crawled items  
**Authentication:** Admin session required  
**Rate Limit:** 60 requests/minute  

**Request:** None  

**Response:** JSON array of crawled items  
**Error Codes:**
- 401: Not authenticated
- 403: Not admin
- 500: Database query failure  

---

## Health & Utility

### 20. GET /api/health

**Purpose:** Comprehensive health check  
**Authentication:** None  

**Request:** None  

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-04-12T...",
  "checks": {
    "data_files": {...},
    "services": {...}
  }
}
```

**Error Codes:**
- 503: Service unhealthy  

---

### 21. GET /api/rag/health

**Purpose:** RAG service health  
**Authentication:** None  

**Request:** None  

**Response:** JSON with RAG service status  
**Error Codes:** 503: RAG service unhealthy  

---

## GraphDB Proxy

### 22. POST /api/graphdb/sparql

**Purpose:** Execute SPARQL query on GraphDB  
**Authentication:** None  
**Headers:** Content-Type: application/sparql-query  

**Request Body:** SPARQL query string  

**Response:** JSON with SPARQL query results  
**Error Codes:**
- 400: Invalid SPARQL query
- 500: GraphDB query failure  

---

## Search

### 23. GET /api/deepsearch?q={query}

**Purpose:** Deep search across places  
**Authentication:** None  
**Rate Limit:** 100 requests/minute  

**Query Parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| q | string | Yes | Search query |

**Request:** None  

**Response:** JSON with deep search results  
**Error Codes:**
- 400: Missing q parameter
- 500: Search failure  

---

### 24. GET /api/nexus/find?person=&place=

**Purpose:** Find nexus points (person + place + time)  
**Authentication:** None  
**Rate Limit:** 100 requests/minute  

**Query Parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| person | string | No | Person DILA ID |
| place | string | No | Place DILA ID |

**Request:** None  

**Response:** JSON with nexus point results  
**Error Codes:**
- 400: Neither person nor place provided
- 500: Nexus query failure  

---

### 25. POST /api/entity/link

**Purpose:** Link entities in text  
**Authentication:** None  

**Request Body:**
```json
{
  "text": "...",
  "entity_types": ["person", "place", "time"]
}
```

**Response:** JSON with linked entities and offsets  
**Error Codes:**
- 400: Invalid request body
- 500: Entity linking failure  

---

## Authentication Endpoints

### 26. GET /daoanh/login.html

**Purpose:** Login page  
**Authentication:** None  
**Handled By:** server.py:5001  

**Request:** None  

**Response:** HTML login page  
**Error Codes:** None  

---

### 27. POST /daoanh/api/login/*

**Purpose:** Login API (Gmail verification)  
**Authentication:** None  
**Handled By:** server.py:5001  

**Request:** Login credentials  

**Response:** Session token or error  
**Error Codes:**
- 401: Invalid credentials
- 500: Authentication service failure  

---

### 28. GET /api/admin/emails

**Purpose:** Admin email management  
**Authentication:** Admin session required  
**Handled By:** server.py:5001  

**Request:** None  

**Response:** JSON with admin email list  
**Error Codes:**
- 401: Not authenticated
- 403: Not admin  

---

## Static Assets

### 29. GET /daoanh/static/*

**Purpose:** Serve static files  
**Authentication:** None  
**Handled By:** app.py:5000  

**Request:** None  

**Response:** Static file (CSS, JS, images)  
**Error Codes:** 404: File not found  

---

## Error Code Summary

| Code | Meaning | Applies To |
|------|---------|------------|
| 200 | Success | All endpoints |
| 400 | Bad Request | Invalid parameters, missing required fields |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions (non-admin) |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Database failure, external API failure |
| 503 | Service Unavailable | Health check failure, RAG service down |

---

## Assumed APIs

The following APIs are referenced in documentation (roadmap.md, FEATURE_PLAN.md) but may not be fully implemented:

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| /api/places/map | GET | GeoJSON for Leaflet map | ASSUMED — planned in FEATURE_PLAN.md Phase 2 |
| /api/translate-cbeta | POST | CBETA Han→Vietnamese translation | ASSUMED — planned in Roadmap Phase 7 |
| /api/admin/translations/:id/approve | PUT | Approve translation | ASSUMED — planned in Roadmap Phase 2 |
| /api/places/:place_id/translations | GET | Get place translations | ASSUMED — planned in Roadmap Phase 1 |
| /api/rag/vi/chat | POST | Vietnamese RAG chat | ASSUMED — planned in Roadmap Khoá 6 |
| /api/persons/<id>/lineage | GET | Person lineage graph | ASSUMED — referenced in FEATURE_PLAN.md |
| /api/persons/<id>/timeline | GET | Person timeline | ASSUMED — referenced in FEATURE_PLAN.md |

---
