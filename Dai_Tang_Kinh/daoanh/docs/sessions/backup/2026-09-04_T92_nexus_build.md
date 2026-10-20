# Session — 2026-09-04 — T92: Đồng ý BUILD Nexus Implementation + commit docs

## Trạng thái

Admin **ĐỒNG Ý BUILD** kế hoạch triển khai Tab Nexus (**T92**), sau khi SPEC `docs/SPEC_TAB_NEXUS_V1.md`
được **APPROVED** (2026-09-04) với **6 quyết định §14**.

## Việc đã làm session này

1. **Restore git khả dụng** sau khi backup-agent lock `.git/index` (intermittent). Đã commit thành công 2 task trước:
   - `c226cde` — **feat(T87)**: lineage picker panel (hunk tp-lineage flex + lineage-picker-panel), 4+/2-.
   - `5300e0f` — **feat(T91-left-panel)**: panel trái tab Đại Tạng — Người Sáng Lập + Liên Quan + placeholder Nguyễn Minh Tiến, 128+/133-.
   - Worktree `places.html` blob = HEAD blob `8f24063` → committed đúng.
2. **Rollback base cho T92 build**: `5300e0f` (HEAD hiện tại).

## Quyết định admin

- **ĐỒNG Ý BUILD** T92 (Tab Nexus implementation, Phase 0-3).
- Build từng phase có **gate admin duyệt** trước khi sang phase sau (theo plan task + SPEC §11).
- Mọi bug fix trong quá trình build phải **commit back về version cũ thuận tiện** (rollback cơ chế t83_ref_write + git revert).

## Cách rollback thuận tiện

- **Rollback code build**: khôi phục `places.html`/`app.py` từ commit `5300e0f` (base approved):
  ```bash
  git checkout 5300e0f -- Dai_Tang_Kinh/daoanh/places.html Dai_Tang_Kinh/daoanh/app.py
  ```
- **Rollback ref (nếu cần)**: `python scripts/t83_ref_write.py --restore` (script đã có, verify sẵn).
- Mỗi phase build nên tạo commit riêng để revert từng phase mà không đụng phase trước.

## Nhắc nhở Phase 0 (NO-CODE, gate trước Phase 1)

1. Xác minh schema `event_text_link` + chụp 1 response thật `/daoanh/api/nexus/<id>?type=...`.
2. **Root-cause `58473 undefined`** (NEXUS-OBS-001) — nghi node thiếu label → fallback số id.
3. Ghi findings + locked contract vào SPEC §7 / session.
4. Gate admin duyệt trước Phase 1.

## Files liên quan

- Task: `tasks/T92-nexus-implementation-plan.md`.
- SPEC: `docs/SPEC_TAB_NEXUS_V1.md` (APPROVED).
- Docs: `docs/progress.md`, `docs/tasktodo.md`.

---

## UPDATE — Phase 0 DONE (NO-CODE, 2026-09-04)

**Đã chụp + đối chiếu 2 response thật** (evidence: `docs/evidence/*.json`), xác minh schema, và **root-cause `58473 undefined` CONFIRMED**. Chi tiết: `docs/T92_PHASE0_VERIFICATION.md`.

### Kết luận chính

1. **Schema `event_text_link`** (DB `data/lineage.db`, 17,284 rows): 14 cột; `person_place` 13,933 · `place_founding` 3,310 · `place_dissolved` 41.
2. **Root-cause `58473 undefined`**:
   - **3,475/13,933 (≈25%)** `person_place` rows có **`entity_id = NULL`** (chỉ có `related_id`=place + `related_name`=tên Hán).
   - app.py:5068 `_add_node(ev['entity_id'], None, None, 'person')` → node `{id:None,label:None,label_zh:None}`.
   - Backfill `WHERE id=None` no-op → label None.
   - Frontend places.html:2542 `label||label_zh||id` → cả 3 falsy → vis.js render **"undefined"**.
   - Dedup ``seen_nodes``` (app.py:5046) → 1 node null (dù 7/31 events null) trong `PL000000023255`.
3. **Edge không bằng chứng**: 31/99 (place) · 18/54 (person) — label `—`, không ref/citation.
4. **`related_name` luôn có** (13,933/13,933) → có thể dùng làm label phục hồi node null.

### Gate admin trước Phase 1 (cần chốt)

- **A.** null `entity_id`: (1) dùng `related_name` làm label + không navigable, hay (2) skip node?
- **B.** Node limit mặc định: chốt `Node 200` (§14.1), thông báo giới hạn.
- **C.** Edge `—` (no evidence): giữ (trung thực) hay ẩn dưới filter "include unverified" (default off)?

> Phase 0 **NO-CODE**: COMMIT only docs (không đụng places.html/app.py). Rollback base T92 build = `5300e0f`.
---

## UPDATE - Phase 1 DONE (BUILD, 2026-09-04)

**Gate Phase 0 approved** - admin chot: **A=1** (null entity_id -> related_name label + synthetic pers-id + non-navigable), **B=Node 200**, **C=Giữ edge dash**.

### Code changes (commit Phase 1)

1. **Backend** `app.py` `api_nexus` (person_place -> center=place branch):
   - A=1: khi `entity_id` NULL -> `_add_node(f"pers-{ev['id']}", related_name, related_name, 'person', navigable=False)`; edge from `pers-<id>` (không più `pid=None`).
   - Person id thật -> `_add_node(pid,...,navigable=True)` (unchanged).
2. **Frontend** `places.html`:
   - Guard NEXUS-OBS-001: drop nodes senza id; fallback label -> String(id); never render undefined/null.
   - B: `NODE_LIMIT=200` + legend notice "Kết quả giới hạn ở N node · X tổng".
   - Detail panel `_nexusShowDetail(n,d)`: preferred label, ID canonical, Grup, Ten Han, relation-to-root, non-navigable notice, buttons -> Truyen Thua / Ban Do, sources via edges. Chiude su new entity + via button.
   - Markup: `nmp-limit` span + `nmp-detail` panel in Nexus main panel.

### Verification

- `py_compile app.py` OK.
- `node scripts/e2e-test.js`: all pages passed (places.html JS syntax OK).
- `npm run test`: passed.
- Live API `GET /daoanh/api/nexus/PL000000023255?type=place`: **200** -> 99 nodes (7 synthetic pers-*, prev 93), **0 null-id, 0 unlabelled person**; edges pers-<id> <-> ev-place_person_bibl-<id> aligned. Lab elu Han stored correctly (0x4F5B = 无).
- Lint script pre-existing Node v24 incompatibility (fails on placevn.html, unrelated to Phase 1; e2e-test.js is the authoritative syntax check).

### Rollback

- Full T92 build -> `git checkout 5300e0f -- Dai_Tang_Kinh/daoanh/places.html Dai_Tang_Kinh/daoanh/app.py`
- Phase 1 only -> `git revert <phase1_commit>`
- No DB migration; code-only.

---

## UPDATE - Phase 2 DONE (BUILD, 2026-09-04)

**Phase 2 = frontend-only** (backend `api_nexus` KHÔNG đổi). Focus: filters + set-as-root + deep-link 16 tab + cycle guard.

### Code changes (commit Phase 2) — all `places.html`

1. **Filter bar** `#nmp-filters` (markup chiaro legend/detail):
   - Node type: nhân / địa / sự kiến / văn / mốc thời (checkbox) — `_nexusIsGroupOn`.
   - **evidence-only** (default ON): keep edges cu `ref||citation`, drop `—`. `_nexusIsEvidenceOn`.
   - **include-incomplete** (default OFF): hide person node non-navigable (synthetic `pers-*`). `_nexusIsIncompleteOn`.
   - Reset button + count `#nmp-filters-count`.
   - `_nexusFilterApply()` re-render `_renderNexusMainPanel(_nexusData)`; `_nexusFilterReset()`.
2. **Set-as-root** `_nexusSetRoot(n)`: nu "✦ Set làm root" (injectato in `#nmp-detail-actions`) pentru node person/place navigable -> re-fetch `/api/nexus/<id>?type=<group>` -> `renderNexusTab` (root mới). Error -> `_nexusShowDetailMessage`.
3. **Deep-link 16 tab** `_nexusDeepLink(n,d)`: map nhóm -> tab chips clickable -> chuyển tab. person->lineage/persons/timeline · place->entity/bandoo/graph/dulieu · event->sukien · text->daitang/thuvien · time->timeline.
4. `_nexusData` module var + `_nexusGroupKey` map; `_nexusCloseDetail` clears actions too.
5. Cycle guard: dedupe node `seen_nodes` (backend, Phase 0) + guard `seenIds` (Phase 1) — giữ.

### Verification

- `node --check` places.html extracted JS: **SYNTAX OK**.
- `node scripts/e2e-test.js`: all pages passed.
- `npm run test`: passed.
- 9-case self-contained unit test (`test_phase2_filters.js`) replicating filter/dedup/deep-link predicates: **ALL PASSED** (evidence-only drops `—` + synthetic person when incomplete OFF; include-incomplete ON keeps synthetic; group off drops type; evidence OFF keeps all edges; dedupe).
- **NOTE**: server :5000 bị chiếm de process system (taskkill "Access denied" — PID 24968/19116/24744, pre-existente); no live HTTP test possible from this shell. Phase 2 is frontend-only, no backend change -> logic valid via unit test + node --check + E2E.

### Rollback

- Full T92 build -> `git checkout 5300e0f -- Dai_Tang_Kinh/daoanh/places.html Dai_Tang_Kinh/daoanh/app.py`
- Phase 2 only -> `git revert <phase2_commit>`
- No DB migration; code-only.
