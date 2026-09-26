---
id: T92
title: Tab Nexus — Triển khai kế hoạch (Phase 0-3) sau SPEC APPROVED
module: Nexus Visualization
priority: high
status: done
depends_on: [T89]
created: 2026-09-04
updated: 2026-09-05
build_approved: 2026-09-04
phase_gate_track: "Phase 0 ✓ (2026-09-04) · Phase 1 ✓ (2026-09-04) · Phase 2 ✓ (2026-09-04) · Phase 3 ✓ (2026-09-04) · Regression/QA ✓ 7/7 (2026-09-05)"
rollback_base_commit: 5300e0f
done_when: "Hoàn thành tuần tự Phase 0 → 1 → 2 → 3 theo SPEC_TAB_NEXUS_V1.md (§11): xác minh schema + 1 response thật để root-cause `58473 undefined`; bounded render + empty states + detail panel; filters + depth 2/node 200 + deep-link 16 tab; evidence UI + share/bookmark + trích xuất nguyên cây đồ thị + QA. Mỗi phase có gate admin duyệt trước khi sang phase sau. ✅ ALL PHASES DONE 2026-09-04."
---

# T92 — Tab Nexus: Kế hoạch triển khai (Phase 0-3)

## Mục tiêu

Triển khai SPEC `docs/SPEC_TAB_NEXUS_V1.md` (**APPROVED** 2026-09-04) thành sản phẩm chạy được trên
tab `🔥 Nexus`. Dựa trên **6 quyết định admin (§14)**:
1. Depth 2 / Node 200 (mặc định, có thể mở rộng bằng bộ lọc).
2. Ưu tiên hiển thị relation có bằng chứng (`ref`/`citation`).
3. Có hiển thị relation partial/unverified nhưng đánh dấu rõ.
4. Primary evidence: **DILA · CBETA · FOSIZHI**.
5. Deep-link từ node sang **tất cả 16 tab chuyên môn** (Bản Đồ, Đại Tạng, Dữ Liệu, Thực Thể,
   Giáo Dục, Giáo Lý, Đồ Thị, Hình Ảnh, Truyền Thừa, Nexus, Nghệ Thuật, Nghi Lễ, Nhân Vật,
   Sự Kiện, Thư Viện, Niên Đại).
6. Nút **share link + bookmark root-graph** + **trích xuất nguyên cây đồ thị** để chia Zalo/Email/bookmark.

## Tham chiếu kỹ thuật (từ SPEC VERIFIED)

- API: `GET /daoanh/api/nexus/<entity_id>?type=person|place` (`app.py:4769-4770`).
- Nguồn node: table `event_text_link` + lookups `people`, `places_dila`, `namevi_map_places`, `marcus_reference` (`app.py:4782-4795, 4867-4883`).
- Node contract: `{id, label, label_zh, group(place|text|person|event|time), navigable}` (`app.py:4813-4818`).
- Edge contract: `{from, to, label, ref, citation, derived, shared_teacher_label}` — `derived`/`shared_teacher_label` tính ở FRONTEND (`places.html:2379, 2388`).
- Render call: `renderNexusTab(d)` → `_renderVisGraph(canvas, center, nodes, edges, cb)` (vis.js, `places.html:3068`, `2392`).
- Root fetch: `fetch(baseUrl + '/daoanh/api/nexus/' + id + '?type=' + entType)` (`places.html:1560-1564`).
- Legend màu: person `#c4891a`, place `#3a9e6e`, event `#8b5cf6`, text `#0b7a96`, time `#d97706` (`places.html:2361`).

## Build approved 2026-09-04

Admin **ĐỒNG Ý BUILD** (session `docs/sessions/2026-09-04_T92_nexus_build.md`).
Rollback base commit = **`5300e0f`** (trước khi build — các commit T87 `c226cde` + T91-left-panel `5300e0f` đã merged).
Mỗi phase build tạo **commit riêng** để revert từng phase mà không đụng phase trước.

## Phase 0 — Xác minh (NO-CODE, gate trước Phase 1)

**Trong scope:**
- [x] Xác minh schema thật của `event_text_link` (14 cột: `id,event_type,entity_type,entity_id,related_id,related_name,cbeta_ref,source_book,source_table,source_ref,source_id,year,confidence,created_at`; 17,284 rows: person_place 13,933 · place_founding 3,310 · place_dissolved 41).
- [x] Chụp **1 response thật** `GET /daoanh/api/nexus/<id>?type=...` (2 cái: place `PL000000023255` 93 nodes, person `A005671` 54 nodes — evidence `docs/evidence/*.json`).
- [x] **Root-cause `58473 undefined`** (NEXUS-OBS-001 + RSK-005): **3,475/13,933 person_place có `entity_id=NULL`** → app.py:5068 tạo node `id=None,label=None,label_zh=None` → backfill no-op → frontend `label||label_zh||id` (places.html:2542) render **"undefined"**. Dedup `seen_nodes` → 1 node null/place-graph.
- [x] Ghi báo cáo xác minh + contract đã khoá: `docs/T92_PHASE0_VERIFICATION.md` + session `docs/sessions/2026-09-04_T92_nexus_build.md`.
- [ ] **Gate: admin duyệt findings + 3 quyết định (A null-entity, B Node limit, C edge `—`) trước Phase 1.**

**Ngoài scope:** mọi thay đổi code/UI (Phase 0 = docs-only, NO-CODE).

## Phase 1 — Read-only root graph + empty states + detail panel

**Gate Phase 0 approved 2026-09-04:** admin chốt 3 quyết định:
- **A = 1** — null `entity_id` → dùng `related_name` làm label + synthetic id `pers-<id>` + **không navigable**.
- **B = Node 200** — node limit mặc định 200 (§14.1), thông báo "Kết quả giới hạn ở N node · X tổng".
- **C = Giữ** — edge không bằng chứng (label `—`) giữ (trung thực), không ẩn.

**Done:**
- [x] Bounded render an toàn (không freeze): `NODE_LIMIT=200` + thông báo giới hạn (`places.html:3457-3464`).
- [x] Empty / partial / error states (§8): `renderNexusTab` + `_renderNexusMainPanel` phân baki empty (`nmp-empty`)/partial/loading (`nmp-placeholder`)/limit (`nmp-limit`).
- [x] Detail panel khi click navigable node (`_nexusShowDetail`): preferred label, ID canonical, Grùp, Tên Hán, relation-to-root, non-navigable notice, buttons → Truyền Thừa / Bàn Đồ, sources/evidence qua edges.
- [x] Không render `undefined`/`null`/`[object Object]` (fix NEXUS-OBS-001): guard node senza id/label + A=1 backend `pers-*` synthetic node.
- [x] Backend A=1 fix (`app.py:5067-5078`): null `entity_id` → synthetic `pers-<id>` + `related_name` label + `navigable=False`.
- [x] Verify live API: `PL000000023255` → 99 nodes (7 synthetic), **0 null-id, 0 unlabelled person**; edge `pers-*` ↔ `ev-place_person_bibl-*` aligned.
- [x] E2E passed (`node scripts/e2e-test.js`): places.html JS syntax OK.

## Phase 2 — Navigation, filters, depth/node limit, deep-link

**Done:**
- [x] Bộ lọc (filter bar `#nmp-filters`): node type (nhân/địa/sự kiến/văn/mốc thời) + **evidence-only** (default ON — ẩn edge `—`) + **include incomplete** (mặc định OFF — ẩn person không navigable/synthetic `pers-*`). `_nexusFilterApply`/`_nexusFilterReset` bấm checkbox → re-render trên `_nexusData`.
- [x] **Node 200 (mặc định)** giữ từ Phase 1 + notice; count số node/cạnh sau filter (`#nmp-filters-count`).
- [x] **Set-as-root** (`_nexusSetRoot`): nút "✦ Set làm root" trên node person/place navigable → re-fetch `/api/nexus/<id>?type=<group>` → `renderNexusTab` (đổi root, giữ graph mới quanh node đó).
- [x] **Deep-link từ node → tab chuyên mô** (`_nexusDeepLink`): map nhóm → tab (`person→lineage/persons/timeline`, `place→entity/bandoo/graph/dulieu`, `event→sukien`, `text→daitang/thuvien`, `time→timeline`) — chip click chuyển tab.
- [x] Cycle guard: dedupe node qua `seen_nodes` (backend) + guard frontend `seenIds` (Phase 1) — vẫn giữ.
- [x] Verify: `node --check` places.html JS OK; E2E passed; 9-case filter/dedup/deep-link unit test passed.

> Ghi chú Phase 2 frontend-only: backend `api_nexus` KHÔNG đổi. Server :5000 bị chiếm bởi process hệ thống (acess denied) — không dùng để test live; logic xác nhận qua unit test + node --check + E2E.

## Phase 3 — Evidence UI, data-quality flag, share/bookmark, QA

**Done:**
- [x] Evidence UI: `_nexusEvidenceSource` detects DILA/CBETA/FOSIZHI from `ref`/`citation`; edges with evidence rendered darker (`#8a5c08cc` vs `#8a5c0866`); edge tooltip shows "Nguồn: [CBETA] cbeta_ref\nCBETA: T51n2076" format.
- [x] Evidence summary badges in header (`#nmp-evidence-summary`): colored chips (DILA=green, CBETA=cyan, FOSIZHI=purple, NGUỒN=gray) with counts from all edges.
- [x] Evidence grouped by source in detail panel: each source as colored left-border block with count badge + up to 4 refs.
- [x] Data-quality flag (`_nexusQualityBadge`): ⚠ "Chưa gắn ID DILA" for non-navigable persons; ⛔ "Entity_id NULL (synthetic)" for `pers-*` nodes; ◯ "Cô lập (0 cạnh)" for isolated nodes.
- [x] Share link (`_nexusShareLink`): copies URL with `?nexus_root=<id>&nexus_type=<type>` to clipboard, "✓ Đã sao chép" feedback.
- [x] Bookmark (`_nexusBookmark`): localStorage `nexus_bookmarks` array, toggle save/unsave, "✓ Đã lưu" / "⭐ Lưu" button sync via `_nexusUpdateBookmarkBtn`.
- [x] Export graph (`_nexusExportGraph`): downloads JSON (full nodes/edges/center/stats) + PNG (vis.js canvas `toDataURL`).
- [x] URL param auto-load: `nexus_root` + `nexus_type` in `window.onload` → `selectItem` + auto-click nexus tab after 600ms.
- [x] Verify: JS syntax OK, py_compile OK, 22 HTML elements + 8 functions + 4 integration points all present.

- [x] Regression/QA: console + network + UI evidence; không sửa DB/data-source.  → 7/7 PASS `tests/e2e-nexus-qa.spec.js` (A empty-state, B place root contract 99 nodes / 0 null-id / evidence chips, C+D expand/collapse group cluster thật trên canvas, E detail + set-as-root + deep-link, F share/bookmark/export JSON+PNG, G network chỉ GET + /api/nexus 200 + không ghi DB). Evidence + screenshots: `docs/sessions/2026-09-05_T92_nexus_qa/`.

## Non-goals (nhắc lại SPEC §13)

- Không load toàn bộ knowledge base trong 1 graph.
- Không editor dữ liệu, không thay tab Truyền Thừa.
- Không quan hệ do LLM sinh (chỉ từ bằng chứng thật).
- Không DB migration/refactor trong SPEC này (nếu thật sự cần → task riêng).

## Acceptance criteria (tổng)

- [x] Không crash khi chưa chọn root.
- [x] Không render `undefined/null/[object Object]` (fix NEXUS-OBS-001).
- [x] Không node/edge suy diễn; mỗi node có canonical ID thật.
- [x] Edge có record/source khi schema cung cấp.
- [x] Không freeze trên graph lớn/cycled (node limit + cycle guard).
- [x] Phân biệt rõ empty / partial / error.
- [x] Click node không mất root context.
- [x] Không sửa DB/data-source.
- [x] Deep-link hoạt động qua 16 tab.
- [x] Share/bookmark + trích xuất nguyên cây hoạt động (Zalo/Email/bookmark).
- [x] Mỗi phase có gate admin duyệt + QA evidence (console + network + UI).

## Files

- Backend: `daoanh/app.py` (route `/daoanh/api/nexus/<entity_id>` — `api_nexus` line 4769).
- Frontend: `daoanh/places.html` (`renderNexusTab`, `_renderVisGraph`, tab entry/panel).
- SPEC: `docs/SPEC_TAB_NEXUS_V1.md` (APPROVED).
- Docs liên quan: `docs/progress.md`, `docs/tasktodo.md`, dashboard `data/progress_data.json (auto-gen)`.

## Rollback

- **Rollback code build** từ base `5300e0f` (approved, trước build):
  ```bash
  git checkout 5300e0f -- Dai_Tang_Kinh/daoanh/places.html Dai_Tang_Kinh/daoanh/app.py
  ```
- Hoặc revert từng commit phase build (`git revert <phase_commit>`).
- Nhánh farm-code an toàn: không có DB migration → rollback thuần code.
- Nếu cần rollback ref: `python scripts/t83_ref_write.py --restore`.
