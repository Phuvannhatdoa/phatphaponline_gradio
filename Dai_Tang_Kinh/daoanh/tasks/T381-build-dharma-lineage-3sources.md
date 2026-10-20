---
id: T381
title: Build 3-Source Dharma Lineage with Y-Fork Rendering (TTL + Marcus + DILA)
status: done
created: 2026-10-14T00:00:00Z
updated: 2026-10-15T00:00:00Z
owner: daoanh-debugger
plan_approved_at: 2026-10-14T00:00:00Z
revert: docs/ROLLBACK.md
outcome: >
  Inserted 393/399 TTL-only edges. 6 self-loops removed by QA round 2
  (root cause: vn_person_authority 1:N mappings). T415 will audit mapping
  ambiguities.
---

## REVISED PLAN (2026-10-14) — Admin chọn Option A: Reuse `lineage_edge_consensus`

**Lý do đổi:** `lineage_edge_consensus` (23,018 dòng, hệ thống T158) đã có sẵn cột
`dila_asserted`, `marcus_asserted`, `ttl_asserted`, `lineage_asserted`,
`agreeing_source_count`, `consensus_status`, `source_badge`. Tạo 3 bảng mới
(Phase 1 cũ) sẽ xung đột với T138/T152/T158. Chỉ cần ETL dữ liệu TTL vào cột
`ttl_asserted` (hiện tại = 0 cho toàn bộ 23,018 dòng).

**Phát hiện quan trọng khi audit (phải xử lý trong ETL):**
- `dharma_lineage_ttl_vn` (784 dòng) dùng `teacher_id`/`student_id` dạng
  `ex:monk/<slug>` (ví dụ `ex:monk/a_nan`).
- `lineage_edge_consensus` dùng `teacher_id`/`disciple_id` dạng DILA code
  `A######` (ví dụ `A000005`).
- Crosswalk bắt buộc 2 chặng: `ex:monk/<slug>` → bỏ prefix → tra
  `vn_person_authority.id = <slug>` → lấy `vn_person_authority.dila_id`
  → map vào `lineage_edge_consensus.teacher_id/disciple_id`.
- `vn_person_authority` có 1,511 dòng, chỉ 1,307 có `dila_id` không rỗng —
  một số slug TTL sẽ không có dila_id tương ứng → log mismatch, không fabricate.
- Route API đã tồn tại tại `app.py` dòng 6493
  (`api_monk_lineage_tree`), **chưa có** hàm `calculate_edge_color_and_divergence`
  — hàm này cần được tạo mới, không phải sửa hàm có sẵn.
- **Không có file `static/js/lineage-tree.js`** — phần render VisJS cây phả hệ
  nằm inline trong `daoanh/places.html` (grep xác nhận). Admin cần xác nhận lại
  đường dẫn frontend hoặc debugger tự xác định đúng vị trí trong `places.html`.

### 3 bước (revised)

1. **ETL TTL → `lineage_edge_consensus.ttl_asserted`**
   - Script: `daoanh/scripts/t381_etl_ttl_into_consensus.py`
   - Idempotent (re-run không duplicate), có `--dry-run` và log mismatch
     (teacher/student không crosswalk được).
   - UPDATE `ttl_asserted=1` cho dòng đã khớp; nếu teacher_id/disciple_id
     chưa tồn tại trong `lineage_edge_consensus` (TTL có cạnh mới mà
     DILA/Marcus chưa có) → cần quyết định: INSERT dòng mới hay bỏ qua
     (ghi rõ trong log, không tự quyết định âm thầm).
   - Báo cáo số dòng update thực tế (không phải số ước tính 784).

2. **Y-Fork color logic trong API** `/daoanh/api/monk/<id>/lineage-tree`
   - Viết hàm mới `calculate_edge_color_and_divergence(edge_row)` trong `app.py`
     gần route `api_monk_lineage_tree` (dòng ~6493).
   - Quy tắc màu:
     - 3 nguồn giống nhau → GREEN solid
     - TTL + 1 nguồn khác → GREEN solid
     - Marcus + DILA (không có TTL) → PURPLE solid
     - Chỉ Marcus → YELLOW dashed, `is_divergence=true`
     - Chỉ DILA → BLUE dashed, `is_divergence=true`
   - Thêm `tree_status: {has_divergence, divergence_count}` vào response.
   - Không phá vỡ contract hiện tại (`sources`, `trust_level`, `rejected`,
     `source_badge`, `agreeing_source_count`, `consensus_status` đã có sẵn
     trong response — field mới phải cộng thêm, không đổi tên field cũ).

3. **Frontend VisJS rendering**
   - Xác định đúng file (có thể là `places.html` inline script, không phải
     `static/js/lineage-tree.js` như đề xuất ban đầu).
   - Áp màu cạnh theo field mới từ API, dashed cho divergence.
   - Legend GREEN/YELLOW/BLUE/PURPLE khi có divergence.
   - Y-fork warning + badge nguồn trong detail panel khi click person.

### Testing bắt buộc
- Query thật: `SELECT * FROM lineage_edge_consensus WHERE dila_asserted=1 AND
  marcus_asserted=1 AND (ttl_asserted=0 OR ttl_asserted=1)` để tìm case thật
  có phân kỳ 3 nguồn — không fabricate demo case.
- PRAGMA quick_check OK sau ETL.
- Không drop bảng, không đổi schema cột hiện có.

---

## FOLLOW-UP FIX (2026-10-14) — 3 lỗi từ daoanh-qa report

**Nguồn:** báo cáo QA sau khi build Y-Fork (phần trên). 3 lỗi được ghi nhận, 1 lỗi hoãn.

### LỖI 1 — places.html: Y-Fork Legend sai
- **Triệu chứng:** Chú thích ghi "vàng = ≥2 nguồn liền" (sai — vàng hiện tại nghĩa
  là Marcus-only dashed). Legend chỉ hiện khi `has_divergence=true`; cây
  `A000005` toàn cạnh PURPLE (Marcus+DILA), không có divergence → legend
  không hiện luôn, user không biết màu nghĩa gì.
- **Route/case tái hiện:** `places.html`, cây lineage của `A000005`.
- **Nguyên nhân nghi ngờ:** điều kiện ẩn/hiện legend gắn sai với
  `has_divergence` thay vì luôn hiện; text legend cũ (vàng liền/cam đứt)
  không khớp với màu thực tế sau khi thêm PURPLE ở T381 gốc.
- **Vị trí xác nhận (dòng số chính xác):**
  - Dòng 586: `<div id="lineage-yfork-legend" style="display:none" ...>` —
    xóa `style="display:none"`.
  - Dòng 6512-6513 (hàm `_t381RenderYForkLegend`):
    `box.style.display = hasDiv ? 'block' : 'none';` — sửa thành luôn
    `box.style.display = 'block';`.
  - Dòng 568-571: 2 dòng chú thích sai ("Nét liền vàng — ≥2 nguồn xác nhận",
    "Nét đứt cam — 1 nguồn") — xóa hoặc comment vì không khớp thực tế T381
    (vàng = Marcus-only DASHED, không phải "liền"; không có "cam" trong
    bảng màu thực tế).
- **Phạm vi sửa:**
  - Xóa `style="display:none"` ở dòng 586 và bỏ điều kiện `has_divergence`
    ở dòng 6512-6513 — legend luôn hiện (`'block'`).
  - Xóa 2 dòng chú thích sai ở dòng 568-571.
  - Thêm đúng text nếu còn thiếu: "Tím (Purple) = Marcus + DILA", "Vàng
    (Yellow) dashed = Marcus only", "Xanh (Blue) dashed = DILA only" (giữ
    GREEN solid nếu đã có text đúng).
- **done_when:** mở `places.html`, bất kỳ cây lineage nào cũng thấy legend
  Y-fork hiện sẵn với đúng 4 màu/kiểu nét mô tả đúng nghĩa thực tế.

### LỖI 2 — chiều đi lên chỉ hiện 1 thầy (KHÔNG SỬA — chờ admin quyết)
- **Triệu chứng:** Tree hướng lên (teacher) chỉ render 1 thầy dù dữ liệu có
  thể có nhiều nguồn khác nhau cho thầy.
- **Quyết định:** đây là design limitation đã biết, admin chưa quyết hướng
  xử lý → giữ `deferred`, không đụng trong vòng fix này.

### LỖI 3 — app.py: 500 khi `ttl_persons` không tồn tại
- **Triệu chứng:** Query ID không có trong bảng `people` → code fallback
  query bảng `ttl_persons` → bảng này không tồn tại trong DB thực tế →
  lỗi SQLite "no such table" không được bắt → trả 500 Internal Server
  Error thay vì 404 Not Found.
- **Route/case tái hiện:** `/daoanh/api/monk/<id>/lineage-tree` với ID
  không tồn tại trong `people`.
- **Vị trí xác nhận (dòng số chính xác):** `app.py` hàm
  `api_monk_lineage_tree`, dòng 6552-6553 (query
  `SELECT 1 FROM ttl_persons WHERE id = ?`).
- **Phạm vi sửa:** bọc truy vấn `ttl_persons` trong try/except
  `sqlite3.OperationalError` → set `ttl_check = None` khi lỗi (bảng không
  tồn tại), để code tiếp tục luồng xử lý "không tìm thấy" bình thường và
  trả 404 Not Found, không để lộ stack trace 500.
  Lưu ý: dòng 6714 (ancestor-spine) và 6780 (root-ancestor) có lỗi tương tự
  nhưng NGOÀI SCOPE lần fix này — để sau.
- **done_when:** gọi API với ID rác → nhận 404 JSON thay vì 500; các ID
  hợp lệ vẫn trả 200 như cũ (không regression).

### Việc phụ — cập nhật log thực thi
- File: `docs/sessions/2026-10-14/T381_EXECUTION_LOG.md`.
- Thay số liệu matched cũ "149/784 matched" bằng số liệu đúng: "553 khớp
  crosswalk, 149 dòng update consensus, 399 không có dòng consensus, 229
  lệch, 2 thầy trống".
- Không phải fix code — chỉ sửa tài liệu để khớp số liệu thật đã chạy.

### Decision 5 (2026-10-15) — 399 TTL edges không có dòng consensus: ĐÃ QUYẾT ĐỊNH + ĐÃ THỰC HIỆN
- Admin quyết định: INSERT 399 cạnh này vào `lineage_edge_consensus` với
  `consensus_status='ttl_only'` (tách biệt khỏi cạnh đã có ≥2 nguồn, dễ
  review sau) — không còn là "Limitation" treo.
- Script: `scripts/t381_insert_ttl_only_edges.py` (`--dry-run`/`--apply`,
  idempotent, có backup tự động).
- Kết quả: `lineage_edge_consensus` 23,018 → 23,417 dòng (+399), 0 duplicate,
  `PRAGMA quick_check=ok`, idempotent test (chạy `--apply` lần 2) → 0 dòng mới.
- Log đầy đủ: `docs/sessions/2026-10-14/T381_EXECUTION_LOG.md`, mục
  "Bước 4 (Decision 5, 2026-10-15)".

### Decision 5 — QA round 2 (2026-10-15): 6 dòng lỗi trong 399 ttl_only vừa insert
- **Nguồn:** `daoanh-qa` kiểm chứng kết quả insert 399 dòng ở Decision 5, báo
  CHƯA ĐẠT vì 6/399 dòng lỗi.
- **LỖI A — 5 cạnh self-loop** (`teacher_id = disciple_id`), do crosswalk gộp
  nhầm 2 slug TTL khác nhau vào cùng 1 DILA id trong `vn_person_authority`.
  5 id trong `lineage_edge_consensus`: 23030 (A000108), 23145 (A008431),
  23150 (A026988), 23158 (A010985), 23305 (A014491).
- **LỖI B — 1 cạnh đảo chiều tạo vòng 2 nút:** id 23159 `A003868 → A010427`
  (ttl_only, mới insert) ngược với id 6913 `A010427 → A003868`
  (`confirmed_2plus`, 3/4 nguồn) đã xác nhận multi-source trước đó.
- **Phạm vi sửa:**
  1. Backup DB → `docs/sessions/2026-10-15/lineage.db.backup_before_fix_qa_round2_t381`.
  2. DELETE đúng 6 id trên (verify `consensus_status='ttl_only'` và
     `migration_marker='T381_TTL_ONLY_INSERT_20261015'` trước khi xóa).
  3. Sửa `scripts/t381_insert_ttl_only_edges.py`: skip self-loop
     (`teacher_dila_id == disciple_dila_id`), skip khi đã có dòng chiều
     ngược cùng `relation_type` (bất kể consensus_status) — log mọi case skip.
  4. KHÔNG re-run toàn bộ insert (393/399 dòng còn lại hợp lệ, giữ nguyên).
  5. Verify: count = 23411, ttl_only = 393, self-loop = 0, không còn cặp
     2 chiều trùng relation_type, `PRAGMA quick_check=ok`, re-run `--apply`
     lần nữa → 0 dòng mới (idempotent).
  6. Cập nhật `T381_EXECUTION_LOG.md` mục "Bước 4b (QA round 2 fix,
     2026-10-15)".
- **done_when:** đúng 6 số liệu verify trên đều khớp, `py_compile` script
  không lỗi, QA round 3 xác nhận ĐẠT.

### Verify bắt buộc sau khi sửa LỖI 1 + LỖI 3
- `python -m py_compile app.py` — không lỗi.
- `node --check places.html` — không lỗi (nếu Node có sẵn local).
- QA (`daoanh-qa`) kiểm: legend hiện đúng mọi trường hợp (có/không
  divergence), API trả 404 đúng cho ID rác, không regression route khác.

---

## ORIGINAL PLAN (đã thay bằng Option A trên) — giữ lại để tham khảo lịch sử

Build dharma lineage visualization engine that renders 3 independent sources (TTL, Marcus, DILA) with Y-fork branching logic:
- **Green trunk**: Consensus (all 3 sources agree OR TTL confirms)
- **Yellow branch**: Marcus-only relationships
- **Blue branch**: DILA-only relationships
- **Mixed**: Partial agreement (some edges green, some branches)

**Philosophy**: Always drawable — no data loss, flexibility for any source configuration.

---

## Core Logic: Y-Fork Spirit

```
Consensus (all 3 same):
  A ─────[GREEN solid]───── B

Divergence (all 3 different):
  A ─[GREEN]──→ B
  C ─[YELLOW]─→ B
  D ─[BLUE]───→ B

Mixed (partial same):
  A ─[GREEN]──→ B  (all agree)
  A ─[GREEN]──→ C  (TTL + Marcus)
  D ─[YELLOW]─→ C  (Marcus extra)
  E ─[BLUE]───→ C  (DILA extra)
```

---

## Done When

### Phase 1: Database Schema (3 tables)
- [ ] Create `dharma_lineage_ttl_vn` (1,106 rows from TTL)
- [ ] Create `dharma_lineage_marcus` (X rows from Marcus source)
- [ ] Create `dharma_lineage_dila` (46,004 rows from DILA)
- [ ] Add indexes on teacher_id, student_id
- [ ] Verify row counts match expected

### Phase 2: Y-Fork Logic
- [ ] Implement `is_divergence` flag calculation
  - If Marcus ≠ TTL → divergence=true
  - If DILA ≠ TTL → divergence=true
  - Else divergence=false
- [ ] Color mapping algorithm:
  - 3 sources same → GREEN
  - TTL + 1 other → GREEN
  - Marcus + DILA (no TTL) → PURPLE
  - Marcus only → YELLOW
  - DILA only → BLUE
- [ ] Confidence score blending (multi-source)

### Phase 3: API Updates
- [ ] Update `/daoanh/api/monk/<id>/lineage-tree` to:
  - Query 3 tables (dharma_lineage_ttl_vn, marcus, dila)
  - Merge results with color-coding
  - Return `is_divergence` flag per edge
  - Return `sources` array per edge
- [ ] Enrich response with tree_status (has_divergence, divergence_count)

### Phase 4: Frontend Rendering
- [ ] Update VisJS graph rendering:
  - Color edges by source
  - Dashed style for divergence edges
  - Solid style for consensus edges
- [ ] Add legend (GREEN/YELLOW/BLUE colors)
- [ ] Add Y-fork warning when divergence detected
- [ ] Show source badges (TTL ✓ Marcus ✓ DILA ✓)
- [ ] Display confidence scores

### Phase 5: Detail Panel (Click person)
- [ ] Show "Primary Teacher (Official)" section
  - Green edges only (TTL baseline)
- [ ] Show "Alternative Teachers" section
  - Yellow/Blue edges (Marcus/DILA branches)
- [ ] Show source breakdown:
  - TTL: X relationships
  - Marcus: Y relationships
  - DILA: Z relationships
- [ ] Y-fork status indicator

### Phase 6: Verification
- [ ] Test with `minh_hai_phap_bao` (demo case):
  - [ ] Teacher edge consensus (Thạch Liêm)
  - [ ] Students Y-fork branches (Thiệt Diệu/Thiệt Mẫn/Thiệt Thọ)
  - [ ] Colors correct (GREEN/YELLOW/BLUE)
  - [ ] is_divergence flags correct
- [ ] Test consensus case (all 3 same)
- [ ] Test divergence case (all 3 different)
- [ ] Test partial agreement (mixed)
- [ ] PRAGMA quick_check: OK
- [ ] No data loss: all 3 sources preserved

### Phase 7: Documentation & Commit
- [ ] Create T381_IMPLEMENTATION_PLAN.md (detailed steps)
- [ ] Create T381_EXECUTION_LOG.md (during build)
- [ ] Update ROLLBACK.md with T381 entry
- [ ] Git commit with attribution
- [ ] Update dashboard

---

## Critical Requirements

1. **No data loss**: All 3 sources always available (even if divergent)
2. **TTL priority**: Green trunk represents TTL (official baseline)
3. **Y-fork visualization**: Branching shows source differences visually
4. **Confidence tracking**: Each edge has confidence score
5. **Audit trail**: Which source provided each relationship
6. **Always drawable**: No "unrenderable" cases exist

---

## Demo Case: Minh Hải Pháp Bảo

**Person ID**: `minh_hai_phap_bao`

**Expected Results (After T381)**:

Teachers:
- TTL: Thạch Liêm ✓
- Marcus: Thạch Liêm ✓
- DILA: Thạch Liêm ✓
→ Result: 1 GREEN trunk (all agree)

Students:
- TTL: Thiệt Diệu ✓
- Marcus: Thiệt Diệu, Thiệt Mẫn
- DILA: Thiệt Diệu, Thiệt Thọ
→ Result: Y-fork (GREEN trunk for Thiệt Diệu, YELLOW/BLUE for alternatives)

---

## Resources

- Implementation plan: `docs/sessions/2026-10-14/T381_IMPLEMENTATION_PLAN.md`
- Session log: `docs/sessions/2026-10-14/T381_EXECUTION_LOG.md`
- Demo case: `minh_hai_phap_bao` (vn_person_authority id)
- Schema: `dharma_lineage_ttl_vn`, `dharma_lineage_marcus`, `dharma_lineage_dila`
- API: `/daoanh/api/monk/<id>/lineage-tree`
- Rollback: `docs/ROLLBACK.md`

---

## Related Tasks

- **T380**: Khôi phục 4 bảng (DONE)
- **T382+**: Other infrastructure tasks
- **Future**: Dharma transmission visualization, conflict resolution UI

---

## Attribution

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
