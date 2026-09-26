---
id: T136
title: Conflict-Engine-Conformance: CONFLICT_ENGINE_SPEC + resolve pick|merge|reject + Authority Score
priority: high
status: in_progress
owner: AI Engineer (build) · Lee Tổng (phán quyết HITL)
module: Ops / Governance / Conflict
created: 2026-09-14
updated: 2026-09-14
---
# T136 — Conflict-Engine-Conformance (spec "T115/T109 Lineage Consensus"): CONFLICT_ENGINE_SPEC + merge/reject + Authority Score

---

## 1. Context (AO — audit thật 2026-09-14, Lee phê chuẩn đề xuất tối ưu 2026-09-14)

Spec "Task T115: Lineage Consensus Engine" (body ghi "Task T109") được admin gửi verify.
**Verdict: ~85–90% ĐÃ TỒN TẠI SẴN = board T109 (Provenance & Conflict Workflow, DONE) + fix T134.**
Lee phê chuẩn đề xuất tối ưu (giữ mọi điều kiện dự án: additive · 0 ALTER · 0 rebuild · HITL-only · Zero-RAM):
3 việc — spec doc thin + đóng 2 GAP THẬT (merge/reject + Authority Score) + ghi lệch quy chiếu.

### Đã có sẵn (verified 2026-09-14 — KHÔNG làm lại)
- **Flagging:** `lineage_conflicts_v2` 40,327 rows (40,316 open sau T134) — admin-only (`admin/conflicts.html` + `/daoanh/api/admin/lineage-conflicts`).
- **Detection:** `src_python/db/deep_conflict_analysis.py` — batch ETL DILA↔Marcus tập thầy/trò (INSERT L141). Scope = lineage; thuộc tính chung → `conflict_pending` (0 rows, **T132**).
- **Comparative UI:** `admin/conflicts.html` song song DILA↔MARCUS + last_verdict/editor/time.
- **Audit Trail:** `en_audit_log` append-only + `audit_id` SHA-256 + T135 public `GET /daoanh/api/research/entity/<id>/audit-trail`.
- **Timeline resolutions:** **`resolutions_log` 0 INSERT ever** (bảng mồ côi, T134) → `resolutions/history` fix UNION `en_audit_log`.

### GAP THẬT (đóng trong T136)
1. **Resolution thiếu gộp/bác bỏ:** `POST .../resolve` chỉ `winner_source_id ∈ dila|marcus` → chưa "giữ cả hai" / "bác bỏ cả hai" (đặc tả §2 yêu cầu đủ 3).
2. **Authority Score chưa hiển thị** trong bảng đối chiếu (đặc tả §2 yêu cầu "Nguồn A (Giá trị, Authority Score)").
3. **`CONFLICT_ENGINE_SPEC.md` chưa tồn tại** (A2 cũ "KHÔNG tạo" — **lệnh admin hiện tại chồng quyết định cũ**): tạo conformance thin (pattern T133/T135).

### Lệch quy chiếu ghi rõ vào spec (không code)
- `resolutions_log` → **`en_audit_log`** (bảng resolutions_log không ghi; timeline T134 UNION đủ).
- **Data Lock** = **show+mark** (transparency) — KHÔNG ẩn (deviation có chủ đích, đã phê chuẩn).
- Detection scope = lineage; thuộc tính chung = T132. "Canonical" không tồn tại (verification_status).
- KHÔNG PROJECT_STATUS.md (SSOT tasktodo+dashboard).

## 2. Pha (additive — thứ tự)

### P1 — `docs/CONFLICT_ENGINE_SPEC.md` (conformance thin)
Ánh xạ spec→module đã-có + qui trình HITL 4 bước + bảng thẩm định 5 tiêu chí (cách verify từng dòng) + §4 điều chỉnh quy chiếu.

### P2 — Resolve mở rộng `resolution_type ∈ pick|merge|reject` (backend + UI)
- `app.py` `admin_lineage_conflict_resolve`: `resolution_type` mặc định `pick` (tương thích caller cũ); merge → new_value `both` + rank `DILA+MARCUS` + notes `T136 merge: giu ca hai`; reject → `rejected` + `NONE` + `T136 reject: bac bo ca hai`; luôn ghi `en_audit_log` (editor·created_at·reason·evidence·authority_rank).
- `admin/conflicts.html`: thêm 2 nút **«⟷ Giữ cả hai»** (merge) · **«✗ Bác bỏ cả hai»** (reject) → `resolveConflict(id, winner, idSafe, resolutionType)`; msg nhận biết từng loại.

### P3 — Authority Score trong bảng đối chiếu
`conflicts.html` + `_SRC_SCORE = {DILA:100, MARCUS:60}` (read-only map theo `source_authority`) → chip "DILA · n · score 100" / "Marcus · n · score 60".

### P4 — Task + trạng thái + dashboard
Task file + session doc + tasktodo (T136 ACTIVE đầu mục; cập nhật note T109 bỏ "KHÔNG tạo CONFLICT_ENGINE_SPEC.md") + backup trước edit + regen dashboard → kỳ vọng **57 tasks · 68%**.

## 3. Non-goals (KHÔNG làm)
- ❌ KHÔNG chuyển Data Lock sang ẩn (giữ show+mark). ❌ KHÔNG seed conflict thuộc tính chung (T132). ❌ KHÔNG ghi `resolutions_log`. ❌ KHÔNG tạo PROJECT_STATUS.md. ❌ KHÔNG xóa/hồi quy history. ❌ KHÔNG đụng detection engine.

## 4. Acceptance
- py_compile app.py OK + mô phỏng 3 resolution_type trên DB copy (pick→rank DILA · merge→rank DILA+MARCUS/new_value both · reject→NONE/rejected) + node --check conflicts.html OK.
- conflicts.html: 4 nút (Dùng DILA/Dùng Marcus/Giữ cả hai/Bác bỏ cả hai) + chip Authority Score.
- `docs/CONFLICT_ENGINE_SPEC.md` tồn tại, thin; §4 điều chỉnh quy chiếu đủ.
- tasktodo T136 ACTIVE + session doc + dashboard 57 tasks.

## 5. Risks
- Restart :5000 chờ admin (PID 5012 Access denied) — verify offline trước.
- Caller cũ không gửi `resolution_type` → mặc định pick (test tương thích trong mô phỏng).
- Groq không liên quan (0 LLM).

## 6. Rollback
- app.py 1 hàm (backup `.bak-t136-conflict-engine.py`) · conflicts.html (backup `.bak-t136.html`) · docs additive · temp-index policy (real git index không đụng).