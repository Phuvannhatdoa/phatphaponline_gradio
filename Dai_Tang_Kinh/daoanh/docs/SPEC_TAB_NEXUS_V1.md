# Tab Nexus — Product and Technical Specification (SPEC_TAB_NEXUS_V1)

> Status: **APPROVED + BUILD APPROVED** (admin 2026-09-04)
> Scope: Read-only discovery + spec approved; **implementation to be planned in T92**
> Task: `tasks/T89-nexus-tab-spec.md` · Session: `docs/sessions/2026-09-03_T89_nexus_spec.md`

---

## 1. Document metadata

- **Created:** 2026-09-03
- **Status:** `DRAFT — REQUIRES ADMIN REVIEW`
- **Scope:** Read-only discovery + spec. No implementation approved, no code changes.
- **Documentation / source files consulted (READ-ONLY):**
  - `daoanh/places.html` — Nexus tab entry, panel, `renderNexusTab`, `_renderVisGraph` (live source).
  - `daoanh/app.py` — `api_nexus` route + node/edge construction (live source).
  - `daoanh/docs/tasktodo.md`, `daoanh/docs/progress.md` — project conventions, task numbering, prior tasks (T16/T36/T58 Nexus-related).
  - Existing task docs: `tasks/T16-nexus-points.md`, `tasks/T36-buddhanexus-parallel-passages.md`, `tasks/T58-nexus-point.md`.
  - Dashboard `data/progress_data.json` — task status registry.
  - **Excluded** (per scope): `_book/` (stale build), `.opencode/node_modules/`, `data/*` raw data, `.git/`.

**Verdict tags used:** `VERIFIED` = evidence from source code path+function; `OBSERVED` = seen on live UI only; `NOT FOUND — requires confirmation` = no evidence found.

---

## 2. Purpose

Nexus is a **per-entity knowledge graph**, NOT a whole-system graph loaded at once.

It starts from a single selected **root entity** (person OR place) and expands, through a shared
**event bridge** table, into linked **event → text/citation → time** nodes. The graph enables a user
to discover *evidenced* relationships among:

- **Person** (nhân vật) — root or linked via `person_place`
- **Place** (địa danh) — root or linked via `person_place`
- **Event** (sự kiện) — `place_founding`, `place_dissolved`, `person_place` ("cư trú tại / hiện diện")
- **Text / citation** (văn bản trích dẫn) — passage nodes derived from `cbeta_ref`
- **Time** (mốc thời gian) — year/era nodes derived from event `year`

Other entity types are added only if the actual schema confirms them — currently the schema defines
exactly these five groups.

---

## 3. Current observed UI

- The tab is labelled `🔥 Nexus` in the Dao Anh tab strip; opens panel `#tp-nexus` (`places.html:355`).
- Placeholder (when no entity selected): *“Chọn địa danh hoặc tăng nhân để xem đồ thị Nexus (thực thể → sự kiện → văn bản trích dẫn → mốc thời gian).”* (`places.html:356-357`)
- Recent UX observed on the live UI:
  - Graph shows groups for **Nhân vật / Địa danh / Sự kiện / Văn bản trích dẫn / Mốc thời gian**.
  - Legend/nhãn instructed: *“di chuột lên cạnh để xem trích dẫn nguồn thật”* (`places.html:3079`).
  - **OBSERVED — `58473 undefined`:** A number that looks like an entity id rendered where a label
    is expected was seen on the live UI near some place nodes / stats. **This is OBSERVED, not yet
    root-caused.** Evidence in code shows node labels render via `label || label_zh || id`
    (`places.html:2369`), so an id would only appear when both label fields are empty. No
    "58473" counter or statistics string exists in the source. The exact entity/context that
    produced `58473` still requires confirmation from a live request (`/daoanh/api/nexus/<id>`).
- User context: root entity is the currently selected place or person in the app (see §4 root flow).

---

## 4. Verified current architecture

| Hạng mục | Giá trị đã xác minh | Bằng chứng |
|---|---|---|
| Tab entry / selector / route | Button `data-t="nexus"`; panel `#tp-nexus` | `places.html:121`, `places.html:355` |
| Graph library | **vis.js** (`new vis.Network(...)`) | `places.html:2392` |
| Root context flow | `fetch(baseUrl + '/daoanh/api/nexus/' + encodeURIComponent(placeId) + '?type=' + entType)` | `places.html:1560-1564` |
| Node source | `event_text_link` (bridge) — via events query | `app.py:4798-4808` |
| Edge source | `from/to/label/ref/citation/derived` built in `api_nexus` | `app.py:4832-4863` |
| API route | `GET /daoanh/api/nexus/<entity_id>?type=person|place` | `app.py:4769-4770` |
| Data store / schema | SQLite; `event_text_link` + lookups `people`, `places_dila`, `namevi_map_places`, `marcus_reference` | `app.py:4782-4795`, `app.py:4867-4883` |
| Node types | `place`, `text`, `person`, `event`, `time` (group colors) | `places.html:2361` |
| Relation types | `cư trú tại` / `hiện diện`, `pháp duyên sáng lập` / `giải tán`, `trích dẫn`, `năm`, `đồng môn (derived)` | `app.py:4831-4861`, `places.html:2382` |
| Citation / evidence field | Edge `ref` / `citation` (from `cbeta_ref` / `source_ref` / `source_book`) → rendered as edge tooltip | `app.py:4861-4862`, `places.html:2389` |
| Existing empty / error handling | `ok:false|no center` → warning placeholder; `0 nodes` → `#nexus-empty` message | `places.html:3074-3086` |
| Existing graph limits / depth | **None** (no depth cap, no node limit found; center + all linked events) | `NOT FOUND — requires confirmation` |
| Duplicate-node handling | `seen_nodes` set dedupes node ids (`_add_node`) | `app.py:4811-4816` |
| Cycle / self-loop edge handling | **None found** — edges are not cycle-guarded | `NOT FOUND — requires confirmation` |
| `58473 undefined` root cause | Not present in source; runtime-only | `NOT FOUND — requires confirmation` |

---

## 5. Target user journey

1. User selects (or is viewing) an entity — a person or a place.
2. User opens the **Nexus** tab.
3. System receives root context as `entityType` (`person`/`place`) + `entityId`.
4. System calls `GET /daoanh/api/nexus/<id>?type=...` and loads a bounded graph.
5. Center (root) node is emphasized; verified relations fan out.
6. User clicks a linked node → detail panel opens (navigable nodes: person ↔ place).
7. User can set another node as root, or jump to the relevant deep tab via `selectPerson`/`selectItem`.
8. User uses filters/depth to explore further (filters/depth are **proposed**, not yet implemented).

---

## 6. Information architecture

### Header (proposed)
- "Nexus tri thức" title.
- Root name + entity type + canonical ID (from `center.label` / `center.id`).
- Source badges only when real data has a source.
- Reset root · Fit graph · Zoom in/out.
- Depth + node limit (proposed; currently unbounded).

### Legend and filters (legend VERIFIED; filters PROPOSED)
- **Legend (VERIFIED):** node colors by entity type — person `#c4891a`, place `#3a9e6e`, event `#8b5cf6`, text `#0b7a96`, time `#d97706` (`places.html:2361`); legend text at `places.html:3076-3079`.
- Node type filters, relation filters, source filters, evidence-only (default on), depth 1/2 (default), "include incomplete" off → **PROPOSED** (not implemented).

### Graph canvas (mostly VERIFIED)
- Root emphasized (gold ellipse, `places.html:2362-2366`).
- Color = entity type — **not** a claim about sect or correctness.
- Edge direction + relation label when data present (`arrows:'to'`, `places.html:2383`).
- Hover edge → citation/evidence tooltip (`title: e.ref`, `places.html:2389`).
- Node limit to avoid UI freeze → **PROPOSED** (currently none).
- Duplicate/cycle handling without crash → dedupe exists; cycle handling missing (§4, §10).

### Detail panel (PROPOSED)
Click navigable node currently routes to `selectPerson`/`selectItem` (`places.html:2401-2407`);
a richer detail panel (preferred label, aliases, canonical ID, relation-to-root, metadata-only-if-present,
sources/evidence, buttons "Xem chi tiết / Đặt làm root / Mở tab liên quan") is **PROPOSED**.

---

## 7. Node and edge semantics

### Node contract (VERIFIED — actual shape returned by `api_nexus` + rendered by `_renderVisGraph`)
| Field | Required | Meaning | Source/status |
|---|---|---|---|
| `id` | yes | unique node id (entity id, or prefixed `ev-…`/`time-…`/`txt-…`) | `app.py:4813-4818` |
| `label` | no | primary display label (vi) | `n.label || n.label_zh || n.id`, `places.html:2369` |
| `label_zh` | no | han/zh display label | computed in `_add_node`/fill, `app.py:4865-4883` |
| `group` | yes | entity type: `place`/`text`/`person`/`event`/`time` | `app.py:4817`, `places.html:2361` |
| `navigable` | no | if true, click routes to person/place depth | `app.py:4815`, `places.html:2406` |

> `entityId`/`entityType` as separate fields do **not** exist — `id` holds the canonical id and
> `group` holds the type. `relationId` not present. Edge fields follow.

### Edge contract (VERIFIED — actual shape)
| Field | Required | Meaning | Source/status |
|---|---|---|---|
| `from` | yes | source node id | `app.py:4832` |
| `to` | yes | target node id | `app.py:4832` |
| `label` | no | relation label (e.g. `cư trú tại`, `trích dẫn`, `năm`) | `app.py:4833-4861` |
| `ref` | no | citation / source ref string | `app.py:4834,4847,4851,4861` |
| `citation` | no | cbeta citation (text edges) — rendered as tooltip | `app.py:4862` |
| `derived` | no | true ⇒ Marcus-derived "đồng môn" edge (frontend-computed, not from API) | `places.html:2379` |
| `shared_teacher_label` | no | context for derived edges (frontend-computed) | `places.html:2388` |

> `relationType`, `source`, `evidence`, `relationId` as named fields do **not** exist in the API
> response; evidence is carried in `ref`/`citation`. `derived`/`shared_teacher_label` are computed
> on the frontend, not returned by `api_nexus`. Any consumer expecting those exact field names
> must map accordingly. If a full typed contract is desired, that is a **PROPOSED** design change.

---

## 8. Empty, partial, and error states

| State | Required message | Current status |
|---|---|---|
| No entity selected | `Chọn một nhân vật, địa danh, văn bản hoặc sự kiện để khám phá các liên hệ tri thức.` | **PROPOSED** (current placeholder is a similar text, `places.html:357`) |
| No verified relation | `Chưa có quan hệ Nexus đã xác minh cho [Tên thực thể].` | **PARTIAL** — empty-state exists (`#nexus-empty`, `places.html:362`) but message wording differs |
| Relation exists but node profile incomplete | `Có quan hệ nguồn nhưng hồ sơ thực thể liên quan chưa đầy đủ.` | **PROPOSED** (not implemented) |
| API / load error | `Không thể tải Nexus. Hãy thử lại.` | **PARTIAL** — `⚠ Lỗi tải dữ liệu.` placeholder, `places.html:3074` |
| Graph limited | `Kết quả bị giới hạn ở [N] node / depth [D]. Hãy dùng bộ lọc hoặc chọn một node để tiếp tục.` | **PROPOSED** (no limits exist yet) |

---

## 9. Data-integrity rules (PROPOSED policy — must hold in any implementation)

- No node/edge created by AI speculation.
- No two entities linked merely for similar name, same place, or same era.
- ID is the primary key; label is display-only.
- Never merge records with different IDs.
- Edge shown only when a relation/source record exists.
- Citation on an edge must come from real evidence (already true: `ref`/`citation` from `cbeta_ref`/`source_ref`).
- AI-written description must never be used as evidence.
- Missing data must show a warning or empty state — never autofill.

---

## 10. Existing issues and risk register

| ID | Observation | Evidence | Suspected area | Severity | Status |
|---|---|---|---|---|---|
| NEXUS-OBS-001 | Counter/label renders `undefined` (user reports `58473 undefined` near place nodes/stats) | OBSERVED on UI; label fallback `label||label_zh||id` (`places.html:2369`); no counter in source | Likely an empty `label`/`label_zh` on a place node falling back to numeric id; root cause not yet confirmed from a live response | Medium | Open — **requires confirmation** |
| NEXUS-RSK-001 | Graph dangerously large (no depth/node limit) | No limit logic found (§4) | `api_nexus` returns all linked events | High | **Mitigated — chốt mặc định Depth 2 / Node 200 (§14)** |
| NEXUS-RSK-002 | Duplicate / cycle edges | Dedupe node exists (`seen_nodes`, `app.py:4811-4816`); edge cycle handling absent | Edge construction | Medium | Open |
| NEXUS-RSK-003 | Edge without evidence | Some edges have `ref: None` (e.g. `person_place` stem edge, `app.py:4832`) | Edge contract (`ref` nullable) | Medium | Open |
| NEXUS-RSK-004 | Source/provider badge does not reflect real data | `source` is a fixed string (`app.py:4887`); collection-count badges not rendered per-source in Nexus (OBSERVED) | Header/badge layer | Low | Open |
| NEXUS-RSK-005 | Place nodes missing vi label → id shown | Label fill only triggers for missing labels with a lookup hit (`app.py:4867-4883`); miss → no label | Label backfill | Medium | Open (likely root of OBS-001) |

---

## 11. Phased delivery boundary

- **Phase 0 — verify (no code):**
  - In scope: confirm schema (`event_text_link` columns), API contract, exact label/evidence fields; capture one real `/api/nexus` response to root-cause NEXUS-OBS-001.
  - Out of scope: any code/UI change.
  - Gate: admin approves findings + locked contract.
- **Phase 1 — read-only root graph + empty states + detail panel:**
  - In scope: bounded render, correct empty/partial/error messages (§8), detail panel.
  - Out of scope: filters, deep-links, evidence flags.
  - Gate: Phase 0 contract approved.
- **Phase 2 — navigation, filters, depth/node limit, tab deep-links:**
  - In scope: node/relation/source filters, **depth + node limit (mặc định Depth 2 / Node 200 — đã chốt §14)**, set-as-root, jump to related tab.
  - Deep-link từ node sang **tất cả 16 tab chuyên môn** (đã chốt §14).
  - Out of scope: evidence-quality data work.
  - Gate: Phase 1 accepted + approval on limit defaults.
- **Phase 3 — evidence UI, data-quality flag, share/bookmark, test/QA:**
  - In scope: evidence display, incomplete-record flags, **nút share link + bookmark root-graph + trích xuất nguyên cây đồ thị (JSON/ảnh để chia Zalo/Email)** (đã chốt §14), regression/QA.
  - Out of scope: DB migration/refactor.
  - Gate: admin direction on which sources are primary evidence (đã chốt DILA/CBETA/FOSIZHI).

---

## 12. Acceptance criteria

- No crash when no root is selected.
- No render of `undefined`, `null`, or `[object Object]` on the UI (fixes NEXUS-OBS-001).
- No inferred node/edge.
- Each node has a real canonical ID.
- Edge has a real record/source when the schema provides one.
- No freeze on large/cycled graph (node limit + cycle guard).
- Empty / partial / error states clearly distinguished.
- Clicking a node does not lose root context.
- No database / data-source modification.
- QA evidence: console + network + UI captured.

---

## 13. Non-goals

- Do not load the entire knowledge base in a single graph.
- Not a data editor.
- Does not replace the Truyền Thừa tab.
- No LLM-generated relations.
- No backend migration / refactor in this SPEC.

---

## 14. Admin decisions (chốt 2026-09-04)

| # | Quyết định | Giá trị | Ghi chú |
|---|---|---|---|
| 1 | Default graph depth / node limit | **Depth 2, Node 200** | Phase 2 (dùng làm mặc định; user có thể mở rộng bằng bộ lọc) |
| 2 | Relation types hiển thị | **Ưu tiên có bằng chứng** | Relation có `ref`/`citation` hiển thị trước; phần khác vẫn hiển thị nhưng đánh dấu |
| 3 | Hiển thị quan hệ partial/unverified | **Có**, đánh dấu rõ | Không autofill, không suy diễn; có trạng thái rõ ràng |
| 4 | Primary evidence sources | **DILA, CBETA, FOSIZHI** | 3 nguồn chính; nguồn khác hiển thị nhưng hạ cấp nhãn |
| 5 | Deep-link từ node | **Tất cả 16 tab chuyên môn** | Node → tab tương ứng (Bản Đồ/Đại Tạng/.../Nexus); ※ lưu ý thực tế có 16 tab, không phải 15 |
| 6 | Bookmark / share root-graph | **Có** | Nút share link + bookmark root-graph; cho phép tăng ni **trích xuất nguyên cây đồ thị** (chia Zalo / Email / bookmark) |

---

## 15. Builder handoff

STATUS: **APPROVED + BUILD APPROVED** (admin 2026-09-04)
6 decisions locked (§14): Depth 2 / Node 200 · ưu tiên bằng chứng · show partial + đánh dấu · evidence DILA/CBETA/FOSIZHI · deep-link 16 tab · share/bookmark + trích xuất nguyên cây
NEXT STEP: Builder **đang triển khai T92** (Phase 0 no-code trước — root-cause `58473 undefined`, gate; rồi Phase 1-3, mỗi phase gate + commit riêng để revert từng phase).
Rollback base: commit `5300e0f` (trước build) — `git checkout 5300e0f -- daoanh/places.html daoanh/app.py`.
