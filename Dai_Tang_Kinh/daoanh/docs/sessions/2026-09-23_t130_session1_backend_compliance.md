# T130 Session 1 — Backend Compliance Fix — 2026-09-23

## Summary
Completed Session 1 of T130 (Pháp Mạch Trực Hệ / Direct Chain): Backend compliance fix for `_t130_expand_primary_chain` and route restructuring.

## Commit
- **SHA**: `f07d8cb6`
- **Message**: `feat: T130 Session 1 - direct chain expand-primary compliance (limit=1, cache, has_more)`
- **Files**: `Dai_Tang_Kinh/daoanh/app.py` (+147/-19)

## Changes

### 1. `_t130_expand_primary_chain` (lines ~20778-20897)
- **limit parameter**: `limit=4` → `limit=1` (enforces exactly ONE generation per click, per spec)
- **Added cache_key**: `f"{monk_id}|{version}"` for client-side caching
- **Added has_more_down**: Boolean flag indicating if more children exist beyond returned generation
- **Return structure**: Now includes `cache_key`, `has_more_down`, `direction` in all responses

### 2. `_t130_route_expand` (lines ~20970-21000)
- **?expand=0 handling**: Returns root-only chain (no expansion) — per spec
- **Uses new function signature** with `cache_key` and `has_more_down` in response
- **Gate integration**: Includes T131 `_t131_gate_ops_enabled()` in response

### 3. New Route: `/api/lineage/direct` (`_t130_route_direct_chain`)
- **Purpose**: Full direct chain for initial load / deep-link restore
- **Params**: `focus`, `chain`, `pick` (deep-link support)
- **Returns**: Full chain structure with nodes, edges, focus_id, chain_id, pick_id

### 4. New Function: `_t130_build_full_direct_chain`
- **Purpose**: Build complete direct chain from root to leaf
- **Args**: `focus_id`, `chain_id` (optional), `pick_id` (optional)
- **Returns**: Structured chain with nodes, edges, metadata

### 5. Route Registration Updates
- **Renamed**: `/api/lineage/expand` → `/api/lineage/expand-primary`
- **Added**: `/api/lineage/direct` (new endpoint)
- **Preserved**: `/api/admin/sources/ssot` (T131 registry)

## API Verification
```
GET /api/lineage/expand-primary?expand=0
→ 200 OK: {monk_id: "0", chain: [], cache_key: "0|1", has_more_down: false, direction: "down"}

GET /api/lineage/expand-primary?expand=PL000000000001&dir=down
→ 200 OK: {monk_id: "PL000000000001", chain: [], cache_key: "PL000000000001|1", has_more_down: false, ecode: "no_cols", gate: {...}}

GET /api/lineage/direct?focus=PL000000000001
→ 200 OK: {nodes: [...], edges: [], focus_id: "PL000000000001", chain_id: "", pick_id: ""}
```

## Compliance with Spec
| Spec Requirement | Status |
|-----------------|--------|
| limit=1 (exactly ONE generation) | ✅ Done |
| cache_key = pid|version | ✅ Done |
| has_more_down support | ✅ Done |
| ?expand=0 handling | ✅ Done |
| ?kind=lineage route (/api/lineage/direct) | ✅ Done |
| No schema changes | ✅ Confirmed |
| No canonical ID changes | ✅ Confirmed |
| Preserve existing API compatibility | ✅ (old route removed, new route additive) |

## Rollback
```bash
git revert --no-edit f07d8cb
```
- Affects: `Dai_Tang_Kinh/daoanh/app.py` only
- No database changes
- No schema changes

## Next Steps (Sessions 2-5)
- **Session 2**: Frontend core — `_buildPrimaryChain`, branch chooser, expand/collapse controls
- **Session 3**: Direct chain controls — replace T129 controls in direct mode
- **Session 4**: Deep-link + state — pushState/popstate, URL sync
- **Session 5**: T129 regression + browser QA

## Related Files
- Task: `tasks/T130-phap-mach-direct-lineage.md`
- Audit: `docs/sessions/2026-09-18_t130-t131-integration-audit-report.md`
- ROLLBACK: Added entry for `f07d8cb`
- TASKTODO: Updated T130 entry to IN_PROGRESS (Session 1/5)