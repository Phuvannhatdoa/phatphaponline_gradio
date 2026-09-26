# Session: TGS Build 2 — Phase C (Evidence API + UI)

**Date:** 2026-08-30
**Branch/Task:** TGS Build 2 Phase C (evidence đa-nguồn)
**Status:** DONE

## Objective
Cung cấp API + giao diện hiển thị các claim (evidence) đa-nguồn cho từng địa danh,
ưu tiên theo authority score và confidence, kèm provenance (source_url, retrieved_at).

## Backend (`app.py`)
- Added route `GET /daoanh/api/places/<place_id>/claims` → `api_places_claims(place_id)`
  (inserted after `/pali` route, before `# T57 — Glossary Đa Ngôn lookup`).
- Logic:
  - Resolve `place_id` (PL… hoặc DILA id) → `entity_id` INT via `_resolve_entity_id`.
  - Build `authority_map` from `source_authority`.
  - Query:
    `entity_claims c LEFT JOIN data_sources d ON d.source_id=c.source_id
     LEFT JOIN source_authority sa ON sa.source_code=d.source_code`
    `ORDER BY sa.authority_score DESC NULLS LAST, c.confidence DESC`.
  - Returns `{ok, place_id, resolved_entity_id, claims[], claims_count}`.
  - Each claim includes `source{code,name,authority_score,precedence_order,implemented}`,
    `source_url`, `retrieved_at`, `confidence`, `verification_status`.
- Verified: `python -m py_compile app.py` OK.

## Frontend (`admin/placevn.html`)
- Added state: `claimsData`, `claimsLoading`.
- Added `useEffect` on `selectedId` change → `safeFetch(base + '/daoanh/api/places/' + encodeURIComponent(selectedId) + '/claims')`.
- Inserted **"Evidence đa-nguồn (authority)"** panel `<section>` before the Wikipedia section:
  - Header (scale icon) + claim count badge.
  - Table: Nguồn (code + authority score) | Loại | Giá trị (+ source_url hyperlink, external-link icon) | Conf | Kiểm chứng (status pill) + retrieved_at date.
  - Loading / empty / error states.
- Icons: `scale` (exists L91) and `external-link` (already used in file) — both in Lucide mapping.
- Verified `npm run e2e`: placevn.html Script block 1 & 2 Syntax OK.

## Verification
- `npm run lint` → exit 0 (known ESM environmental false-positive only)
- `npm run test` → exit 0 (Tests passed)
- `npm run e2e` → exit 0 (All pages passed)
- Flask test client: `GET /daoanh/api/places/PL000000008975/claims`
  → status 200, ok:true, claims_count:206, resolved_entity_id:167900,
  first claim source DILA / COORDINATE / auth_score 100.

## Files Changed
- `app.py` (backend route)
- `admin/placevn.html` (evidence panel + state + fetch)
- `docs/sessions/2026-08-30_TGS_B2_PhaseC_evidence_api.md` (this log)

## Next Steps
- Phase D: cross-ref sources queue (SAT→Kanripo→SuttaCentral/VRI→84000 Toh→CHGIS/TGAZ),
  keep `implemented=0` until real pipeline + data.
- Phase E: refresh `docs/build1_inventory.md` + `docs/trusted-sources.md`, add session logs.
