# API DOCUMENTATION - Đạo Ảnh Buddhist GIS

**Version:** 1.0  
**Last Updated:** 2026-04-12

---

## Base URLs

| Environment | URL |
|-------------|-----|
| Local | http://localhost:5000 |
| Production | https://phatphaponline.org/daoanh |

---

## Public Endpoints

### GET /
Home page

### GET /daoanh/
Main GIS application

### GET /daoanh/admin/
Admin dashboard

---

## Places API

### GET /api/places
Get all places

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| page | int | 1 | Page number |
| limit | int | 50 | Results per page |
| search | string | - | Search by name |

**Response:**
```json
{
  "count": 5000,
  "places": [...]
}
```

### GET /api/stats
Get place statistics

---

## Persons API

### GET /api/persons
Get all persons

### GET /api/persons/search?q={query}
Search persons by name

### GET /api/persons/timeline
Get dynasty distribution

### GET /api/persons/by-dynasty?dynasty={dynasty}
Filter by dynasty

---

## Dictionary API

### GET /api/dict/search?q={term}
Search StarDict dictionary

### GET /api/dict/stats
Get dictionary statistics

### GET /api/dict/entities
Get extracted entities (places + monks)

---

## Admin API

### GET /api/admin/places
List all places with pagination

### PUT /api/admin/places/{id}
Update place

### GET /api/admin/dila-stats
DILA data statistics

### GET /api/admin/person-stats
Person statistics

---

## Crawler API

### POST /api/crawler/wiki
Run Wikipedia crawler

### POST /api/crawler/dila
Run DILA sync

### GET /api/admin/crawler/list
List crawled items

---

## Health & Utility

### GET /api/health
Comprehensive health check

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

### GET /api/rag/health
RAG service health

---

## GraphDB Proxy

### POST /api/graphdb/sparql
Execute SPARQL query on GraphDB

**Headers:** Content-Type: application/sparql-query

---

## Search

### GET /api/deepsearch?q={query}
Deep search across places

### GET /api/nexus/find?person=&place=
Find nexus points (person + place + time)

### POST /api/entity/link
Link entities in text

---

## Rate Limits

- **Search APIs:** 100 requests/minute
- **Admin APIs:** 60 requests/minute

---

*Generated: 2026-04-12*