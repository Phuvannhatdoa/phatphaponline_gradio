# Session — 2026-09-14 T135 Doctrine-Retrieval-Conformance (Option A)

> Task: `tasks/T135-doctrine-retrieval-conformance.md` · Spec: `docs/RETRIEVAL_ENGINE_SPEC.md`
> Endpoint mới: `GET /daoanh/api/research/entity/<id>/audit-trail` (T118) · Backup: `docs/sessions/app.py.bak-t135-audit-trail.py`

## Bối cảnh
Admin gửi verify lần 2 đặc tả "Task T117: Doctrine Retrieval Engine" (body ghi "T115"). Audit thật (AO) → **verdict ~90% đã có**
(= T111 + T126 + T109/T118 + T113). Admin phê chuẩn **Option A**: không rebuild → đóng 2 GAP THẬT + ghi nhận deviation.

## P1 — Endpoint public Audit Trail bậc Tiến sĩ (đóng GAP #1 = T118)
Thêm route `GET /daoanh/api/research/entity/<entity_ref>/audit-trail` (sau `api_admin_audit_trail`, trước `_citation_lookup`):
- read-only, 0 ALTER, LIMIT 200 (Zero-RAM), tham số hoá.
- `_resolve_entity_id` → bộ pattern `entity_ref LIKE %ref%` từ {ref raw, canonical_label hub} × `en_audit_log` (append-only) → history kèm `audit_id=en-<log_id>`.
- `claims_audit`: entity_claims LEFT JOIN `entity_claims_audit` (audit_id SHA-256) LEFT JOIN data_sources → total/by_status/sample 20.
- `data_status: indexed|no_data` trung thực (chuỗi không khớp → no_data, không bịa).

**Verify (offline, read-only DB):**
- py_compile OK.
- Mô phỏng 3 nhóm: `A000005` (鑑堂) → eid 218333 · **2 history** (5 resolve T134 đúng 1 person này) · 7 claims → indexed · `PL000000023255` (Thiếu Lâm Tự) → 0 history · 38 claims → indexed · chuỗi không tồn tại → **no_data** ✓.

## P2 — `docs/RETRIEVAL_ENGINE_SPEC.md` (conformance thin, đóng GAP #2)
Ánh xạ spec→module đã-có + qui trình vận hành + bảng thẩm định 4 tiêu chí (cách verify từng dòng)
+ deviation persona-switcher tường minh vs auto-detect + ghi rõ KHÔNG PROJECT_STATUS.md + số board mapping.

## P3 — Task + trạng thái + dashboard
- Task file `tasks/T135-doctrine-retrieval-conformance.md` (frontmatter id T135, status in_progress, owner).
- tasktodo: **T135 ACTIVE** đầu mục · **T118 ✅ DONE (impl trong T135)** · **T117 ✅ CONFORMANCE VERIFIED** (sửa dòng mojibake cũ).
- Dashboard regen → kỳ vọng 56 tasks.

## Restart :5000 — CHỜ ADMIN (như T134)
app.py có thêm route nhưng PID 5012 Access denied với shell → admin restart:
```powershell
# từ thư mục daoanh
python start_servers.py
# hoặc tắt app.py cũ rồi:
python app.py
# verify nhanh:
Invoke-RestMethod "http://127.0.0.1:5000/daoanh/api/research/entity/A000005/audit-trail" | ConvertTo-Json -Depth 5
```
kỳ vọng `data_status=indexed`, `history` 2 rows, `claims_audit.total=7`.

## Tiếp theo
- Admin restart :5000 + live check audit-trail + Lee regression editor-dashboard → T119 done.
- Batch T131/T132/T130 sau phân tích tích hợp.

## Files
- Mới: `tasks/T135-doctrine-retrieval-conformance.md`, `docs/RETRIEVAL_ENGINE_SPEC.md`, `docs/sessions/2026-09-14_t135-doctrine-retrieval-conformance.md`.
- Sửa: `app.py` (+1 route), `docs/tasktodo.md` (T135 ACTIVE, T118 DONE, T117 conformance), `data/progress_data.json` + dashboard (regen).
- Backup: `docs/sessions/app.py.bak-t135-audit-trail.py`.