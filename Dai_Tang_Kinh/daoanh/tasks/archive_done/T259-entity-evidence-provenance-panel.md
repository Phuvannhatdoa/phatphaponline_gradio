---
id: T259
title: Entity Evidence & Provenance Panel — Bằng Chứng & Nguồn Gốc
status: done
priority: high
created: 2026-10-07
completed: 2026-10-07
---

## Mục tiêu

Researcher nhìn thấy bằng chứng và nguồn gốc dữ liệu cho mỗi nhân vật:
liên kết truyền thừa từ Marcus + đồng hiện trong kinh điển từ CBETA.

## Phase 0 — Contract Inspection (CASE A)

| Item | Kết quả |
|------|---------|
| CASE | **CASE A** — existing API đủ, không cần backend thay đổi |
| entity_hub.entity_id | INTEGER (100001...) cho cả PLACE + PERSON |
| entity_claims.entity_id | INTEGER FK → entity_hub |
| A001897 entity_hub_id | 220093 |
| A001897 claims | 34 rows, NETWORK_EVIDENCE/unverified |
| A001897 co_mentions | 5 rows (event_text_link) |
| A001897 events | 0 (event_entities dùng place IDs) |
| source_reference format | `T69:marcus:A001897:A000490` — NOT a URL |
| PERSON verification_status | 100% 'unverified' (22,332 total) |
| PLACE verification_status | COORDINATE = 'verified' |

### _resolve_entity_id flow cho A001897
1. `entity_hub WHERE canonical_label='A001897'` → entity_id=220093 ✓
2. `entity_claims WHERE entity_id=220093` → 34 NETWORK_EVIDENCE claims

## Implementation

### Backend
- **Không thay đổi** — `/daoanh/api/evidence/<subject_id>` đã có đủ data.

### Frontend (places.html)

- `#entityEvidenceBlock` — `da-block hidden`, chèn sau `#personsInEntityBlock`, trước `#licenseBlock`
- `loadEntityEvidence(dilaId)` — async fetch, AbortController race guard, follows T235 pattern
  - Claims section: `<details>` collapse, predicate label map, source_reference as `<span>` (NOT `<a>`)
  - Co-mentions section: cbeta_ref + related_name + source_book as text
  - Events section: shown if events > 0 (rare for persons currently)
- Call site: sau `loadCbetaCitations(dilaId)` trong person load flow

### XSS
- Tất cả DB content qua `_escHtml()`
- source_reference rendered as `<span>` monospace, KHÔNG bao giờ là `<a href>`

## Tests

File: `tests/test_t259_entity_evidence_panel.py`

**23/23 PASS** (A-X):
- A: ok=True cho valid subject_id
- B: resolved entity info present
- C: claims non-empty cho A001897
- D: co_mentions non-empty cho A001897
- E: source_reference NOT http URL
- F: verification_status trong allowed set
- G: NETWORK_EVIDENCE claim_type cho persons
- H: object_text non-empty
- I: confidence float [0,1]
- J: data_status.claims.total = len(claims)
- K: data_status.co_mentions.total = len(co_mentions)
- L: persona_level in {L1,L2,L3}
- M: unknown subject → ok=True, empty arrays
- N: co_mentions có cbeta_ref field
- O: predicate field present
- P: ok=True khi claims=[]
- Q: source_reference dùng internal format
- R: ast.parse app.py PASS
- T: #entityEvidenceBlock trong places.html
- U: loadEntityEvidence function defined
- V: loadEntityEvidence(dilaId) call site present
- W: source_reference NOT rendered as <a href
- X: real DB — A001897 >= 30 claims (regression guard)

## Done when

- [x] Phase 0 contract inspection hoàn tất (CASE A)
- [x] `#entityEvidenceBlock` DOM block trong places.html
- [x] `loadEntityEvidence(dilaId)` JS function
- [x] Call site trong person load flow
- [x] Claims: source_reference as text only, không phải URL
- [x] Co-mentions: cbeta_ref as text only
- [x] AbortController race guard
- [x] XSS: tất cả content qua _escHtml()
- [x] 23/23 T259 tests PASS
- [x] NO backend change, NO schema change, NO DB mutation
- [x] ast.parse PASS

## Commit

`feat(T259): Entity Evidence & Provenance Panel`
