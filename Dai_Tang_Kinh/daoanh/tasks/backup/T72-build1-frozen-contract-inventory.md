---
id: T72
title: "Build 1 Inventory + Frozen Contract (docs) — chốt ke hoach Build 2"
module: Hạ tầng / Docs
priority: high
status: done
depends_on: [T67]
created: 2026-08-30
updated: 2026-08-30
done_when: >
  Tạo docs/build1_inventory.md (bảng capability → file/API/bảng/status, chỉ ghi đã verify,
  không bịa) + docs/build1_frozen_contract.md (tuyên bố BUILD 1 FROZEN). Cập nhật tasktodo +
  dashboard + session log + git commit. Đây là nền để Build 2 (T68-T70) KHÔNG xây trùng identity.
---

# T72 — Build 1 Inventory + Frozen Contract (docs)

## Mục tiêu
Đáp ứng phần audit-first + frozen contract của directive "Build 2" theo đúng hiện trạng repo:
xác nhận rằng **tầng canonical entity / source identity đã IMPLEMENTED (T23 Identity Hub)**,
nên Build 2 = hoàn tất T67→T70 (reuse + extend), KHÔNG xây lại identity.
Sản xuất 2 tài liệu theo convention repo để mọi agent sau không duplicate.

## Hiện Trạng (đã verify 2026-08-30)
- Canonical entity: `entity_hub` (167,006: entity_id INT surrogate, entity_type, canonical_label='PL…', status, created_at, updated_at) + `entity` (entity_id TEXT, dila_id).
- Source identity mapping: `entity_source_ids` (167,009) + `entity_claims` (411,472: 177,445 NAME / 175,441 COORDINATE / 58,586 ADMIN_UNIT; authority_role='PRIMARY' 100%; unverified 100%).
- Provenance: `canonical_decision` + `en_audit_log` → **T67 done** (commit a5bb07f).
- SQLite mapping: `namevi_map_places` (118,296) source='manual'=3; Đạo Ảnh dashboard `admin/placevn.html` (React 18); save `/daoanh/api/admin/namevi-map-places/save`; search `/daoanh/api/admin/places_search` + `places_auto_names` + `ai_judge`.
- GIS: Leaflet (trong placevn.html). Search infra: **SQLite FTS5** (`places_search_fts`, `places_pending_fts`).
- **OpenSearch / Fuseki / GraphDB: KHÔNG có trong app daoanh** (0 refs) — chỉ tồn tại ở parent visjs-app (thientong.py). Ghi trung thực, không bịa.
- 61 route `/daoanh/api/admin/*`, 57 route `/api/*`.

## Thiết Kế (docs, additive, reversible)
### `docs/build1_inventory.md` — bảng `| Capability | Existing file/API/table | Status | Build |`
Chỉ ghi ĐÃ VERIFY. Ghi rõ "ALREADY IMPLEMENTED" cho DILA ID / SQLite mapping / Đạo Ảnh / GIS / save / search / canonical entity / source identity / provenance.

### `docs/build1_frozen_contract.md` — theo directive §4
BUILD 1 COMPONENTS ARE FROZEN. Future Builds may: consume/extend/add adapters/add tables/add services/add APIs/add evidence layers. Must NOT: duplicate/replace/parallel identity/mapping/admin.

## Subtasks
- [x] T72a: Tao `docs/build1_inventory.md`
- [x] T72b: Tao `docs/build1_frozen_contract.md`
- [x] T72c: Update tasktodo.md + dashboard (progress_data.json) + session log
- [ ] T72d: git commit (reversible, docs-only)

## Revert
Docs-only — `git revert <commit>` hoặc `git rm` 2 file. Không đụng code/DB.

## Kiem-chung acceptance (regression — directive §14)
- Dashboard/SQLite/DILA ID/save/GIS/search còn chạy (không thay đổi code, chỉ thêm docs).
- Không tạo identity/mapping/admin song song.
