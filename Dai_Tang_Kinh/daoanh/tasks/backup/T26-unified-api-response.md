---
id: T26
title: Unified API Response — backend consolidate trước khi gửi frontend
module: Identity Hub / API
priority: medium
status: done
depends_on: [T23, T24]
created: 2026-08-20
updated: 2026-08-24
done_when: GET /daoanh/api/entity/<id> trả unified response object đầy đủ với sources[] + claims[], frontend không query trực tiếp places_dila/entity_claims
---

# T26 — Unified API Response Object

## Vấn Đề

Hiện tại `/daoanh/api/places/<id>` (và `/daoanh/api/entity/<id>`) trả dữ liệu DILA-centric trực tiếp từ `places_dila`. Frontend phải tự tổng hợp từ nhiều endpoint khác nhau (entity, Marcus network, BDRC, v.v.).

**Mission doc:** "Frontend chỉ consume unified object này. Frontend KHÔNG truy cập trực tiếp DILA/BDRC/CBETA để tự quyết định authority. Backend mới là nơi resolve."

## Response Object Chuẩn

```json
{
  "entity": {
    "entity_id": "PL023255",
    "entity_type": "PLACE",
    "canonical_name": "少林寺",
    "canonical_name_vi": "Thiếu Lâm Tự"
  },
  "sources": {
    "dila":    {"active": true,  "source_record_id": "PL023255", "url": "authority.dila.edu.tw/..."},
    "cbeta":   {"active": true,  "refs": ["T50n2060_p0457c16"]},
    "bdrc":    {"active": false, "note": "T25 pending"},
    "marcus":  {"active": true,  "network_id": "..."},
    "zqlocal": {"active": true,  "vi_name": "Thiếu Lâm Tự"}
  },
  "claims": [
    {
      "claim_type": "COORDINATE",
      "value": "34.507018, 112.935331",
      "source": "DILA",
      "authority_role": "PRIMARY",
      "confidence": 1.0,
      "source_ref": "PL023255",
      "verified": true
    },
    {
      "claim_type": "TEXTUAL_REF",
      "value": "T50n2060_p0457c16",
      "source": "CBETA",
      "authority_role": "PRIMARY",
      "confidence": 0.9,
      "source_ref": "cbeta_listbibl"
    },
    {
      "claim_type": "NAME",
      "predicate": "vietnameseName",
      "value": "Thiếu Lâm Tự",
      "source": "ZQLOCAL",
      "authority_role": "PRESENTATION",
      "confidence": 0.8
    }
  ],
  "conflicts": [],
  "meta": {
    "generated_at": "2026-08-20T...",
    "claims_count": 12,
    "sources_active": ["dila", "cbeta", "zqlocal"]
  }
}
```

## Backend Service

```python
# app.py — new endpoint /daoanh/api/entity/<entity_id>/unified
def get_unified_entity(entity_id):
    # 1. Resolve entity
    entity = resolve_entity(entity_id)
    if not entity:
        return 404

    # 2. Lấy source mappings
    sources = get_entity_sources(entity_id)

    # 3. Lấy claims (từ entity_claims, sau T23)
    claims = get_entity_claims(entity_id)

    # 4. Lấy conflicts nếu có
    conflicts = get_entity_conflicts(entity_id)

    # 5. Assemble unified response
    return {
        "entity": entity,
        "sources": sources,
        "claims": claims,
        "conflicts": conflicts,
        "meta": {...}
    }
```

## Compatibility

**Không xóa endpoint cũ.** `/daoanh/api/places/<id>` giữ nguyên. Thêm `/daoanh/api/entity/<id>/unified` là endpoint mới:

```python
# Existing: /daoanh/api/places/<place_id>  → giữ nguyên
# New:      /daoanh/api/entity/<id>/unified → unified response
# Frontend places.html: dùng endpoint mới nếu có, fallback cũ nếu unified 404
```

## Acceptance Criteria

- [x] `GET /daoanh/api/entity/<id>/unified` trả unified response object
- [x] `sources[]` có >=3 sources (DILA/CBETA/ZQLOCAL/Wikidata + 84000/Kanripo/SAT/VRI)
- [x] `claims[]` có COORDINATE + NAME + ADMIN_UNIT claims (411K rows from T23)
- [x] `conflicts[]` phản ánh `lineage_conflicts_v2` data (40K rows)
- [x] places.html 7 source chips hiển thị từ unified response
- [x] Endpoint cũ không break (legacy fallback implemented)
- [x] Test case: PL022435 trả đủ 4+ sources với claims

## Completion Log (2026-08-24)

**Commits:**
1. `6c53a76` feat(T26): add unified entity endpoint /api/entity/<id>/unified
2. `4f6eaff` feat(T26): add 7 source chips (DILA/CBETA/Wikidata/84000/Kanripo/SAT/VRI)
3. `f260566` feat(T26): selectItem uses unified endpoint with legacy fallback

**Files changed:**
- `app.py`: +180 lines (unified endpoint at line 10097)
- `places.html`: +192 lines (chips + unified fetch + legacy fallback)

**Route:** `GET /daoanh/api/entity/<entity_id>/unified`
**Response:** `{ok, entity, sources, claims, claims_count, conflicts, conflicts_count, founding, meta}`

## Depends On

- **T23 phải xong trước**: `entity_claims` cần có data thì unified response mới có `claims[]` thật
- **T24 nên xong trước**: ZQLOCAL source tag cần rõ ràng
