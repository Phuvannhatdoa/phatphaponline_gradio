# T92 Phase 0 — Nexus Verification Report (no-code)

**Date:** 2026-09-04
**Status per SPEC §11 / T92:** Phase 0 **DONE** — findings + locked contract sẵn sàng cho **gate admin** trước Phase 1.
**Rollback base:** commit `5300e0f` (trước build). Phase 0 thuần **NO-CODE** → không có thay đổi code, chỉ docs.

---

## 1. Thu thập response thật (evidence)

2 API calls qua gateway `http://127.0.0.1:8080/daoanh/api/nexus/<id>?type=...` (cả 2 → HTTP 200, giống hệt qua :5000):

| Route | Status | Evidence file |
|-------|--------|---------------|
| `GET /daoanh/api/nexus/PL000000023255?type=place` (Thiếu Lâm Tự) | 200 | `docs/evidence/2026-09-04_nexus_PL000000023255.json` |
| `GET /daoanh/api/nexus/A005671?type=person` (Pháp Dũng) | 200 | `docs/evidence/2026-09-04_nexus_A005671.json` |

```
PL000000023255 (place): 93 nodes {person:25, event:34, text:31, time:3}, 99 edges
A005671 (person):       54 nodes {place:18, event:18, text:18}, 54 edges
```

## 2. Schema `event_text_link` (verified DB `data/lineage.db`)

14 cột:
`id, event_type, entity_type, entity_id, related_id, related_name, cbeta_ref, source_book, source_table, source_ref, source_id, year, confidence, created_at`

Phân bố event (17,284 rows):
- `person_place` 13,933
- `place_founding` 3,310
- `place_dissolved` 41

## 3. Root-cause `58473 undefined` (NEXUS-OBS-001 / RSK-005) — CONFIRMED

### Nguyên nhân gốc: `entity_id = NULL` trên `person_place`

- **3,475 / 13,933 (≈25%)** `person_place` rows có **`entity_id = NULL`** (chỉ biết `related_id`=place + `related_name`=tên Hán).
- Trong `api_nexus`, nhánh place-center (app.py:5068-5069):
  ```python
  _add_node(ev['entity_id'], None, None, 'person', navigable=True)
  ```
  → khi `entity_id=None` tạo node `{id: None, label: None, label_zh: None}`.
- Backfill (app.py:5107-5115) chạy `WHERE id = None` → không tìm được → label vẫn `None`.
- Frontend fallback (places.html:2542) `label: n.label || n.label_zh || n.id` → khi cả 3 falsy → vis.js render **"undefined"**. (Số `58473` = id-fallback surface khi label thiếu nhưng id còn; ở đây id cũng null nên ra chữ "undefined".)

### Dedup che số lượng

Place graph `PL000000023255` có **7 / 31** `person_place` null-entity, nhưng `_add_node` dedup bằng `seen_nodes` theo `id` (app.py:5046) → cùng `id=None` nên chỉ **1** null node xuất hiện trong response (93 nodes). Điều này khớp bộ phân tích: đúng 1 node `{id:None, group:person, navigable:True}`.

## 4. Kanji label cho null entity (có thể phục hồi)

`related_name` luôn có giá trị (13,933/13,933). VD `PL000000000002`: `related_name='善無畏'`.  
→ **Fix tiềm năng (Phase 1)**: khi `entity_id` null, dùng `related_name` làm label + không navigable (không có id để chuyển sang hồ sơ). Hoặc **skip node** null-entity.

## 5. Edge không bằng chứng

- `PL000000023255`: 31/99 edges không `ref` & không `citation` (edge `—` từ center→event `place_person_bibl`).
- `A005671`: 18/54 edges tương tự.
→ Ủng hộ quyết định §14.2 "ưu tiên relation có bằng chứng" + chip evidence (Phase 1/2 render).

## 6. Contract locked (đối chiếu SPEC §7)

Node thật: `{id, label, label_zh, group(place|person|event|text|time), navigable}` — đúng.  
Edge thật: `{from, to, label, ref, citation}` — đúng (thêm `derived`/`shared_teacher_label` tính frontend).  
Hạn chế: `text` node label hiện generic `T50 — Taisho Tripiṭaka` (src `_nexus_title_for_sigla`), chưa phải tựa sách chi tiết.

## 7. Gate admin (trước Phase 1)

Quyết định cần admin chốt trước khi Build Phase 1:

- **A. Xử lý null `entity_id`:** (1) dùng `related_name` làm label + không navigable, hay (2) skip node hoàn toàn (giảm nhiễu)?
- **B. Node limit mặc định Phase 1:** chốt `Node 200` (SPEC §14.1) — thông báo "giới hạn N node".
- **C. Edge không bằng chứng:** label `—` — giữ (trung thực) hay ẩn dưới filter "include unverified" (mặc định off)?

## 8. Rollback

Phase 0 **NO-CODE** → không rollback code. Rollback toàn T92 build khi cần: `git checkout 5300e0f -- daoanh/places.html daoanh/app.py`.

## Files

- Evidence: `docs/evidence/2026-09-04_nexus_PL000000023255.json`, `docs/evidence/2026-09-04_nexus_A005671.json`.
- Task: `tasks/T92-nexus-implementation-plan.md`.
- SPEC: `docs/SPEC_TAB_NEXUS_V1.md`.
- Session: `docs/sessions/2026-09-04_T92_nexus_build.md`.