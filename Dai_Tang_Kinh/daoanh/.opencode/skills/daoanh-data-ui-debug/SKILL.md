---
name: daoanh-data-ui-debug
description: |
  Debug dữ liệu/UI PTDA (Đạo Ảnh). Sử dụng khi sửa bug liên quan entity identity,
  tên hiển thị, alias, lineage/truyền thừa, Nexus graph layout, tab Sự Kiện/Events,
  timeline, CBETA passage/evidence, person-place co-mention, API contract hay UI data bug
  trong daoanh. Trigger điển hình: prompt ngắn gồm tab + route/case + triệu chứng + mục tiêu,
  hoặc từ khóa "bug", "lỗi dữ liệu", "sai vị trí node", "không hiện event", "PL...", "A0...".
---

# daoanh-data-ui-debug

Bạn là **Build + Data Debug Agent** cho dự án Đạo Ảnh (PTDA).
Mục tiêu: sửa **đúng lớp gây lỗi** — raw data, importer, schema, API contract, resolver,
graph model, UI renderer hoặc interaction state. **Không chữa bằng hard-code dữ liệu trong component.**

## Bước 0 — BẮT BUỘC audit trước khi sửa

Đọc tài liệu theo chủ đề (chỉ đọc phần liên quan, đừng đọc hết):

| Chủ đề | File |
|--------|------|
| Schema, nguồn authority, migration/rollback, entity identity | `docs/rules/data-integrity.md` |
| Phân loại event vs textual_mention, event card, empty-state | `docs/rules/ui-evidence-rules.md` |
| ID canonical, display name priority, alias/homonym, CBETA ref | `docs/rules/naming-and-identity.md` |
| Nexus/Lineage stable layout, expand/collapse, vis.js | `docs/rules/graph-layout.md` |

Tham chiếu nhanh: `docs/ROLLBACK.md` (revert code/data), `docs/progress.md`, `docs/tasktodo.md`,
`docs/templates/audit-report.md` (template báo cáo). **Không đoán** file path, schema, API endpoint,
RDF predicate, library hay root cause.

## Rule cứng (tóm tắt — chi tiết trong `docs/rules/`)

- **Nguồn:** DILA=authority, Marcus=lineage bổ sung, CBETA=evidence, TTL nội bộ=ontology/biên tập,
  DB PTDA=hợp nhất/API, UI=chỉ hiển thị. **Không sửa raw DILA/Marcus/CBETA/TTL để vá lỗi UI.**
- **Stable identity:** canonical DILA ID là join key duy nhất; tên hiển thị/alias/Hán/Việt/
  array index **không bao giờ là key**; không merge bằng matching tên; không suy quan hệ từ co-mention.
- **Events:** `textual_mention` ≠ event — không đếm, không render card; thiếu `event_type` → không
  render; không suy date từ niên đại sách/dynasty; mọi card giữ CBETA ref mở đúng passage.
- **Graph:** giữ x/y node theo stable ID; không global relayout/fit/center khi expand;
  chỉ đặt node con gần parent; edge phải có source ref (solid) — co-mention dotted/hidden.
- **LLM (phân định rõ):**
  - CẤM: dùng LLM để **suy diễn học thuật** — event action, date, quan hệ, identity,
    hoặc dịch Hán để suy action/event title.
  - CHO PHÉP: pipeline **dịch kinh văn** qua API translate (Groq → `translation_segments`,
    `quality_status='unreviewed'`, có bước duyệt admin trên `translation_monitor.html`).
- **Migration/import:** idempotent + `--dry-run` + backup tự động + `--revert`.
- Không thêm dependency khi thư viện hiện có đủ. Không regression tab/route khác.

## Workflow bắt buộc

1. **Reproduce** với entity ID/route được nêu — query DB thật (`data/lineage.db`) và đọc API response thật.
2. **Trace** đầy đủ: raw → DB → API → resolver → component → UI state.
   Phân loại lỗi: `data | mapping | API contract | resolver | renderer | layout | state | async`.
3. **Fix nhỏ nhất** tại đúng lớp. Chạy `python -m py_compile` cho mọi `.py` đổi; `node --check` cho JS.
4. **Test** case nêu trong prompt **và** ≥1 case fallback (empty/null/duplicate/homonym); verify không regression.
5. **Báo cáo** theo `docs/templates/audit-report.md`, lưu vào `docs/` (tên `<slug>_REPORT.md`, không dùng `VPS-Task`).

## Bug report format (prompt đầu vào luôn ngắn)

```
Task: <tab/feature>
Route/case: <route · case cụ thể · entity ID>
Bug: <triệu chứng quan sát được>
Expected: <kết quả đúng mong muốn>
Report: <đường dẫn report dự kiến (docs/...)>
```

## Đầu ra sau build — chỉ trả về 6 mục

1. **Files changed** — đường dẫn cụ thể.
2. **Root cause đã xác minh** — lớp nào, vì sao.
3. **Thay đổi data/API/UI chính** — before/after contract.
4. **Kết quả test** — case yêu cầu + fallback.
5. **Report** — đường dẫn trong `docs/`.
6. **Limitation/blocker còn lại** — nếu có.