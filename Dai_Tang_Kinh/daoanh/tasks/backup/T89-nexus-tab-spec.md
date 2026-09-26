---
id: T89
title: Tab Nexus — Read-only Discovery + SPEC (SPEC_TAB_NEXUS_V1)
module: Nexus Visualization
priority: medium
status: done
depends_on: []
created: 2026-09-03
updated: 2026-09-04
done_date: 2026-09-04
done_when: Tạo `docs/SPEC_TAB_NEXUS_V1.md` (15 mục: metadata, purpose, observed UI, verified architecture, user journey, IA, node/edge contract, empty/partial/error, data-integrity, risk register, phases, acceptance, non-goals, admin questions, builder handoff) với bằng chứng VERIFIED/OBSERVED/NOT-FOUND từ code thật; ghi rõ `58473 undefined` là OBSERVED chưa root-cause; cập nhật tasktodo/progress/dashboard; admin duyệt 2026-09-04 (§14 chốt 6 quyết định) → chuyển giao Builder qua T92
---

# T89 — Tab Nexus: Read-only Discovery + SPEC

## Mục tiêu
Đây là nhiệm vụ **Documentation/QA (no-code)** theo yêu cầu admin: khảo sát **READ-ONLY** tab
`🔥 Nexus` (Đạo Ảnh) và viết một SPEC kỹ thuật + UX chi tiết để **Builder Agent** phát triển/fix
ở phase sau. **Không** sửa source code, HTML/CSS/JS/Python/DB/JSON/TTL/config/service; không tạo
subtask; không gọi Builder; chỉ tạo đúng 1 tài liệu Markdown đầu ra + docs cập nhật.

## Các bước thực hiện (đã hoàn thành — xem bản thân)
1. **Đọc quy ước dự án + docs**: `AGENTS.md`, `docs/tasktodo.md`, `docs/progress.md`, `docs/opencode-directives.md`.
2. **Tìm entry point tab Nexus (READ-ONLY)** — xác minh bằng code thật:
   - Tab entry: button `data-t="nexus"` + panel `#tp-nexus` → `places.html:121`, `places.html:355`.
   - Root context flow: `fetch('/daoanh/api/nexus/' + id + '?type=' + entType)` → `places.html:1560-1564`.
   - Render: `renderNexusTab()` (`places.html:3068`) → `_renderVisGraph()` (`places.html:2360-2409`).
   - Graph lib: **vis.js** (`new vis.Network`, `places.html:2392`).
   - Backend: `GET /daoanh/api/nexus/<entity_id>?type=person|place` → `app.py:4769` `api_nexus`.
   - Node/edge source: `event_text_link` (bridge) + lookup `people`/`places_dila`/`namevi_map_places`/`marcus_reference` → `app.py:4798-4816, 4821-4883`.
   - Node types (`group`): `place/text/person/event/time` → `places.html:2361`.
   - Relation types: `cư trú tại`/`hiện diện`, `pháp duyên sáng lập`/`giải tán`, `trích dẫn`, `năm`, `đồng môn (derived)` → `app.py:4831-4861`.
   - Edge evidence: `ref`/`citation` (`cbeta_ref`/`source_ref`/`source_book`) → tooltip `title: e.ref` → `app.py:4861-4862`, `places.html:2389`.
   - Dedupe node: `seen_nodes` set → `app.py:4811-4816`.
   - Label fallback: `label || label_zh || id` → `places.html:2369`.
3. **`58473 undefined`**: KHÔNG có trong source (chỉ thấy trong 1 file backup JSON không liên quan
   `docs/sessions/2026-08-20/backup_name_vi_before_hanviet_expansion.json`). Node label render qua
   `label||label_zh||id`; không có counter thống kê nào. → ghi đúng **OBSERVED, chưa root-cause**
   (nghi khả năng place node thiếu `label`/`label_zh` fallback ra id số; cần 1 response thật xác nhận).
4. **Viết `docs/SPEC_TAB_NEXUS_V1.md`** (đầy đủ 15 mục, bảng Rated architecture, risk register
   `NEXUS-OBS-001`…`NEXUS-RSK-005`, phases 0-3, acceptance, non-goals, admin questions, builder handoff).

## Sửa lỗi logic so với nhiệm vụ gốc (đã thống nhất với admin)
- **Phản đối mâu thuẫn**: nhiệm vụ nói "chỉ đọc `docs/`" nhưng bắt buộc điền VERIFIED từ code. Đã
  sửa phạm vi → "READ-ONLY + được đọc source liên quan tab Nexus (`places.html`, `app.py`)".
- **Loại trừ nguồn stale**: không đọc `_book/` (bản build cũ), `.opencode/node_modules/`, `data/*`, `.git`.
- **Contract thật** (không bịa field ví dụ): node `{id,label,label_zh,group,navigable}`; edge
  `{from,to,label,ref,citation,derived,shared_teacher_label}`. `entityId/entityType/relationId/source`
  không tồn tại như field riêng — ghi rõ trong spec.

## Sản phẩm đầu ra
- `docs/SPEC_TAB_NEXUS_V1.md` — SPEC (sản phẩm chính).
- `tasks/T89-nexus-tab-spec.md` — task doc này.
- `docs/sessions/2026-09-03_T89_nexus_spec.md` — session log.
- `docs/tasktodo.md`, `docs/progress.md` — cập nhật entry T89.
- Dashboard `data/progress_data.json` — regen + sửa trạng thái T86/T87 `in_progress` → `done`.

## Tests / Verify
- SPEC là Markdown — không có test chạy; đối chiếu mọi đường dẫn trong spec với source thật
  (`places.html`, `app.py`) bằng `Select-String`/đọc trực tiếp.
- Không thực thi lint/test/e2e vì không có thay đổi code.

## Rollback
```bash
python scripts/t83_ref_write.py --restore
```
(Đưa `refs/heads/master` về SHA trước T89 = `31b5117e`.)

## Next / Ghi chú
- Sau khi admin duyệt SPEC, tạo PLAN triển khai riêng (Phase 0: verify schema + 1 response thật để
  root-cause `58473`). Không làm trong SPEC này.
