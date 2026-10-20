# Session 2026-09-14 — T136 Conflict-Engine-Conformance (CONFLICT_ENGINE_SPEC + resolve pick|merge|reject + Authority Score)

## Context
Admin gửi spec "Task T115: Lineage Consensus Engine" (body ghi "Task T109", header **SỐ COLLIDE** với board T115 = Source Authority Matrix DONE).
**Audit thật (ˇplan mode) → verdict: ~85–90% ĐÃ TỒN TẠI SẴN** — bản chất đặc tả = **board T109 (Provenance & Conflict Workflow, DONE) + fix T134**.
Lee phê chuẩn đề xuất tối ưu (additive · 0 ALTER · 0 rebuild · HITL-only) → **T136 active**.

## Đã có sẵn (verified 2026-09-14, không làm lại)
- Detection: `src_python/db/deep_conflict_analysis.py` batch ETL DILA↔Marcus tập thầy/trò (INSERT L141) — `lineage_conflicts_v2` 40,327 (40,316 open sau T134).
- Flagging/admin-only: `admin/conflicts.html` + `GET /daoanh/api/admin/lineage-conflicts` (app.py L10573).
- Audit Trail: `en_audit_log` append-only (action `resolve_lineage_conflict`/`claim_review`/…) + `audit_id` SHA-256 + **T135 public endpoint**.
- Timeline `resolutions/history`: **`resolutions_log` 0 INSERT ever (bảng mồ côi) → T134 fix UNION en_audit_log**.
- Data Lock = **show+mark** (chip `is_conflict=1 AND resolved=0`, `_t86_person_conflict` app.py:5050) — deviation minh bạch.
- Test kháng: `conflict_pending` 0 rows → detection thuộc tính chung thuộc **T132**.

## GAP THẬT đóng (đúng promise)
### P1 — doc (conformance thin)
`docs/CONFLICT_ENGINE_SPEC.md` (mới): ánh xạ ĐÃ-CÓ (Detection/Flagging/UI/Resolution/Audit/Data Lock/resolutions_log) + HITL 4 bước + bảng thẩm định 5 tiêu chí (cách verify từng dòng) + §4 điều chỉnh quy chiếu (resolutions_log→en_audit_log · Data Lock show+mark · detection scope→T132 · không "Canonical").

### P2 — resolve mở rộng pick|merge|reject (backend + UI)
`app.py` `admin_lineage_conflict_resolve` (L10636): nhận `resolution_type` (mặc định `pick` — caller cũ không gửi vẫn chạy ✓).
- `pick`: winner dila|marcus → rank DILA/MARCUS → notes `… | T109 winner=<n>` (giữ y hệt phiên bản trước — additive).
- `merge`: new_value `both` · rank `DILA+MARCUS` · notes `T136 merge: giu ca hai`.
- `reject`: new_value `rejected` · rank `NONE` · notes `T136 reject: bac bo ca hai`.
Luôn UPDATE `resolved=1` + **1 dòng `en_audit_log`** (editor·created_at·reason·evidence `dila_count=…, marcus_count=… | resolution_type=…`·authority_rank). `dila_data/marcus_data` bất biến (minh chứng gốc).
`admin/conflicts.html`: + 2 nút **«⟷ Giữ cả hai»** / **«✗ Bác bỏ cả hai»** → `resolveConflict(id, winner, idSafe, resolutionType)` (default pick); message nhận biết loại phán quyết.

### P3 — Authority Score
`conflicts.html` `_SRC_SCORE = {DILA: 100, MARCUS: 60}` (read-only map theo `source_authority`, không query per-conflict) → chip `DILA · n · score 100` / `Marcus · n · score 60`.

### P4 — trạng thái
`tasks/T136-conflict-engine-conformance.md` · session này · tasktodo T136 ACTIVE đầu mục + **T109 note cũ "KHÔNG tạo CONFLICT_ENGINE_SPEC.md" bị chồng (LỆNH MỚI Lee)** bằng Python (dòng có mojibake — không edit được bằng regex thủ công).

## Kỹ thuật (đã verified)
- py_compile app.py OK.
- Mô phỏng 3 resolution_type trên **DB COPY** (data/lineage.db → temp; KHÔNG đụng DB thật; row_factory=Row — lỗi tuple indices trong run 1 là lỗi script sim, không phải app):
  - pick conflict#3 → dila · rank DILA · audit 44011 · notes `reason pick | T109 winner=dila`
  - merge conflict#4 → both · DILA+MARCUS · audit 44012 · notes `reason merge | T136 merge: giu ca hai`
  - reject conflict#5 → rejected · NONE · audit 44013 · notes `reason reject | T136 reject: bac bo ca hai`
- node --check (script trích từ conflicts.html) → OK.

## Backups (trước mọi edit)
- `docs/sessions/app.py.bak-t136-conflict-engine.py` (862,544 B)
- `docs/sessions/conflicts.html.bak-t136.html` (9,889 B)

## Chờ admin / bàn giao tiếp
1. **Restart :5000** (PID 5012 Stop-Process Access denied — tài khoản cao hơn) để live-verify: resolve 4 dạng + `resolutions/history` (tổng=5 từ T134) + audit-trail A000005.
2. HITL phán quyết conflict thật: **Lee Tổng** dùng 4 nút (Dùng DILA / Dùng Marcus / Giữ cả hai / Bác bỏ cả hai).
3. Sau restart: **Lee regression T119 + T134 + T135** → đóng T119/135; T131/T132 batch khi đủ.

## Rollback
- app.py: backup `.bak-t136-conflict-engine.py` (restore 1 hàm).
- conflicts.html: backup `.bak-t136.html`.
- docs/tasktodo/session: README additive — git history.
- Commits: temp-index-only; real git index không đụng.