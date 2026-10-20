# Session — 2026-09-14 T134 Curation-Workflow-Conformance (Đường A)

> Task: `tasks/T134-curation-workflow-conformance.md` · Doc: `docs/CURATION_WORKFLOW_SPEC.md` · Fix: app.py `resolutions/history`
> Backup: `docs/sessions/app.py.bak-t134-resolutions-history.py`

## Bối cảnh
Admin gửi spec "T116 Curation & Editor Workflow" (ZenQ naming) → audit thật (AO) → **verdict ~90% đã tồn tại** (T109 + T119).
Admin chọn **Đường A** (qua question tool): không implement literal, chỉ đóng GAP THẬT + minh hoạ HITL + doc conformance thin.

## Đã verify trong audit (read-only)
- `en_audit_log` có đủ cột versioning (editor/created_at/evidence_sources/authority_rank/old_value/new_value/action) + 9,000+ rows T83.
- `editor-dashboard.html` 7 tab · `conflicts.html` 2 cột nguồn · `bulk-review` ≤500 · `entity-claims/unverified` 447,885.
- `lineage_conflicts_v2` 40,327 rows (40,321 mở). `verification_status` vẫn là `verified|unverified|disputed|needs_review` — không "Canonical".

## P1 — Vòng HITL mẫu (đã chạy trên :5000 LIVE, không auth-gate ở app layer)
- Resolve 5 conflict qua `POST /daoanh/api/admin/lineage-conflicts/<id>/resolve` (editor **'Lee Tổng'**, reason "T134 HITL demo — theo authority_score DILA 100 > MARCUS 60, nhánh có đa số bằng chứng dila_data/marcus_data"):
  - conflict #3 鑑堂 teacher_set → **dila** (dila=6 > marcus=1) · audit 44011
  - conflict #5 一寧 teacher_set → **dila** (17 > 1) · audit 44012
  - conflict #11 一絲文守 teacher_set → **dila** (13 > 0) · audit 44013
  - conflict #10 一行 student_set → **dila** (4 > 0) · audit 44014
  - conflict #4 鑑堂 student_set → **marcus** (marcus=6 > dila=1) · audit 44015
- Review 5 claim (claim 6985–6989, source_id=1 DILA): `POST /daoanh/api/admin/claims/<id>/review` → **verified/high**; audit cho content-hash `audit_id` (sha). Verify DB: reviewed_by='Lee Tổng' ✓.
- Bulk 10 claim (candidate kế trong batch DILA/CBETA): `POST /daoanh/api/admin/claims/bulk-review` → **verified/medium**, 10 audit rows, `audit_id=en-44030`.
- **DB verify:** en_audit_log `action='resolve_lineage_conflict'` +5 mới; claims `verified` 44,000 → **44,015** (+15); `lineage_conflicts_v2` resolved T134 = 5.

## P2 — GAP phát hiện trong demo + Fix (QUAN TRỌNG)
**Triệu chứng:** `GET /daoanh/api/admin/resolutions/history` trả `total=0` dù vừa resolve 5 conflict.
**Root cause:** endpoint chỉ đọc bảng `resolutions_log` — grep toàn repo: **`INSERT INTO resolutions_log` = 0/4 file .py** (app.py/_book, schemas). Bảng mồ côi, **KHÔNG BAO GIỜ được ghi**. Data versioning THẬT nằm trong `en_audit_log` (T109 resolve path ghi vào đó).
**Fix (additive, 0 ALTER):** `api_admin_resolutions_history` đổi sang CTE **UNION ALL**:
1. `en_audit_log WHERE action='resolve_lineage_conflict'` LEFT JOIN `lineage_conflicts_v2 c ON c.person_id = a.entity_ref`
2. `resolutions_log` (legacy giữ lại)
`total` = 2×COUNT. Docstring ghi rõ lý do (T134 2026-09-14).
**Verify:** `py_compile app.py` OK · mô phỏng chính xác câu SQL trên DB read-only → 5 rows (conflict_id · name_vi · chosen_source · resolved_by='Lee Tổng' · resolved_at 2026-09-14T13:48:29) ✓.
**Lưu ý:** LEFT JOIN theo person_id trùng → cùng 1 audit row xuất hiện ở teacher+student conflict của cùng person (cosmetic OK).

## P3 — Doc + trạng thái
- `docs/CURATION_WORKFLOW_SPEC.md` — conformance thin: ánh xạ spec→module ĐÃ-CÓ · HITL 3 bước Review→Acceptance→Commit · thuật ngữ "Canonical"→verified · self-check 4 trục (Minh bạch/Kiểm soát/An toàn/Thuận tiện) có cách verify từng dòng. KHÔNG PROJECT_STATUS.md ✓.
- tasktodo: entry T134 ACTIVE (đầu mục). Dashboard regen (55 tasks, kỳ vọng).

## Restart :5000 — CHỜ ADMIN
`Stop-Process -Id 5012` → **Access denied** (process của account cao hơn; command line ẩn). Code fix verified offline, chưa live.
Admin thao tác 1 trong:
```powershell
# Từ thư mục daoanh
python start_servers.py            # khởi động lại cả 3 server (gọi start_servers.py)
# hoặc tắt app cũ (Task Manager) rồi:
python app.py
```
Sau restart, verify nhanh:
```powershell
Invoke-RestMethod "http://127.0.0.1:5000/daoanh/api/admin/resolutions/history?per_page=10" | ConvertTo-Json -Depth 4
```
kỳ vọng `total=5` và `resolutions[0].resolved_by='Lee Tổng'`.

## Tiếp theo
- Admin restart :5000 + Lee regression trên editor-dashboard (tab Resolutions hiển thị 5 phán quyết) → **T119 → done**.
- Batch T131/T132/T130 sau khi phân tích tích hợp.

## Files
- Mới: `tasks/T134-curation-workflow-conformance.md`, `docs/CURATION_WORKFLOW_SPEC.md`, `docs/sessions/2026-09-14_t134-curation-workflow-conformance.md`.
- Sửa: `app.py` (api_admin_resolutions_history), `docs/tasktodo.md` (entry T134), `data/progress_data.json` + dashboard (regen).
- Backup: `docs/sessions/app.py.bak-t134-resolutions-history.py`.