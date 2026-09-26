# Session — Build Batch A+B (T112/T116/T118/T119/T121) 2026-09-10

**Commit:** `f73e3ce5` (+ fill hash-fill) · **Mode:** build (Lee: "Đồng ý build, lưu logs, git commit")

## Bối cảnh
Lee phê chuẩn **Batch B (build), A (docs/review), C (bug sync)** từ danh sách undone. Batch C
(BUG-012/BUG-014/T101 — Nexus marker/lag/5 bug) **hoãn sang đồng bộ agent ngoài**: các file đó
đang do tiến trình song song làm (in_progress), không đụng để tránh đè công sức (benchmark: lỗi
T99/73ea9e7a đã từng xoá file nhầm).

## Batch B — IMPLEMENTED (additive, 0 ALTER bảng nền, 0 migration, Zero-RAM LIMIT/OFFSET)

### B1 — T116 D-Ops O1 (backup)
- `scripts/daily_backup.py`: sqlite **online backup API** (`src.backup(dst)` — không lock DB lâu,
  bài học T58) → gzip (chunk 1MB) → sha256 verify → atomic replace → prune giữ **N=14 ngày** →
  ghi `docs/OPS_LOG.md` (append-only). Cron đề nghị `0 2 * * *`.
- Verify: `data/snap/lineage_20260910.db.gz` 340MB, `verify=OK` (magic gzip + header SQLite trong
  luồng giải nén). Snapshot git-ignored (`data/snap/`).
- **Bug phát hiện & sửa tại chỗ**: lúc đầu check magic bằng `gzip.open().read(4)` — SAI khái niệm
  (`gzip.open` trả LUỒNG ĐÃ GIẢI NÉN → not magic). Fix: đọc raw bytes + giải nén 16 bytes kiểm
  header `SQLite` (2 chiều).

### B2 — T112 D-Feedback
- Table additive `data_gap_requests` (UNIQUE(entity_type,entity_id,gap_type) — dedupe, 1 gap loại/entity).
- Auto-giệt: `_t112_record_gap` hook tại `/daoanh/api/entity/<id>/web-enrich` (không index được
  Wikipedia → `thieu_nguon`) + `/daoanh/api/places/<id>` (thiếu note_vi+dila_note+description_vi
  → `thieu_noidung`). Vòng "thuật: người dùng thấy thiếu dữ liệu → tự ghi yêu cầu → admin duyệt".
- `GET /daoanh/api/admin/data-gaps?status=&page=` + `POST .../data-gap/<id>/status` (ack|closed).
- KHÔNG tạo bảng `query_log` riêng (ráspec6: phủ qua data_gap_requests).

### B3 — T119 Unified Editor Dashboard
- `admin/editor-dashboard.html` (Tailwind, 6 tabs: Claims/Feedback/Data Gaps/Resolutions/Audit/Geo;
  stats bar; pagination; bulk actions). Được nạp qua route `/daoanh/admin/<path>` có sẵn.
- Endpoints: `GET /admin/entity-claims/unverified` (filters status/entity_type) ·
  `POST /admin/claims/bulk-review` (ids≤500, mỗi claim 1 dòng en_audit_log, trả audit_id) ·
  `GET /admin/resolutions/history` (resolutions_log 𝄘 lineage_conflicts_v2) ·
  `POST /api/feedback` (public, Gap 5) · `GET /admin/feedback` + status ·
  `GET /admin/editor-stats`.
- **Bug phát hiện & sửa**: `where`/`params` unpack sai (`["..."]` cho 1 phần tử) → 500; restructure.

### B4 — T118 Research Audit Tier (đợt 1)
- `GET /daoanh/api/admin/audit/trail?entity_ref=&page=` — en_audit_log append-only; mỗi dòng thêm
  `audit_id = en-<log_id>`.
- `GET /daoanh/api/public/export/citation?entity_id=&format=csl-json|bibtex&audit_id=` —
  resolver places_dila → dila_reference → people → entity_hub; CSL-JSON (array) / BibTeX.
- Đợt sau: audit_id xuyên toàn bộ export public, chữ ký bằng chứng (ghi trong tasks/T118).

### B5 — T121 Web Enrichment Geo (candidate-only HITL)
- `geo_cross_ref` thêm cột additive: `enrich_status(none|candidate|approved|rejected)`,
  `enrich_source_qid/lat/lon/elevation_m/checked_at`, `wikidata_lat/lon`, `elevation_m/source`.
- `GET /admin/geo-enrich/candidates` · `POST /admin/geo-enrich` (admin approve → upsert main fields,
  confidence='verified', từ đó `/places/unified` nhặt ngay) · `POST /admin/geo-enrich/<id>/status`.
- `scripts/enrich_places.py` (cron, --limit/--run): places_dila thiếu toạ độ ∩ chưa enrich → Wikidata
  `wbsearchentities` + **P625 (globecoordinate) + P2044 (elevation)** → chỉ ghi `candidate`
  (KHÔNG tự set wikidata_qid chính thức — đúng Zero-Loss T109 mô hình HITL).

## Batch A — docs/review
- `tasks/T116-system-registry-handover.md` → **status: done** (Lee phê duyệt Registry — Batch A);
  D-Ops O1 IMPLEMENTED note.
- `tasks/T112/T118/T119/T121` → **status: in_progress** + mục "Xây dựng Batch B" (endpoints, files).
- `tasks/T113` → append **"Batch A — Lee review"**: GIỮ in_progress (QA giữ trung thực — chờ
  claims_reviewed>0 qua T119 bulk-review UI + xử lý conflicts mở 40,321). KHÔNG tự đóng.
- `docs/SOURCE_REGISTRY.md` §5 → ghi approval Batch A (5 BLOCK · 3 DEFER · 1 REFERENCE_ONLY giữ).
- `docs/tasktodo.md` → 5 marker build (✓ T116/T112 · ⚙ T118/T119/T121). Chú ý: nhiều dòng tasktodo
  hiện có mojibake `?` do ghi lossy của tiến trình ngoài — CHỈ thêm marker, KHÔNG sửa lại content lỗi.
- `docs/ROADMAP_META_UPDATE.md` §5 thêm luật "Build Batch A+B (2026-09-10, reverte…)" + §2 line
  (task=41 · done=8 · blocked=2 · 269 commits).

## Batch C — hoãn & ghi nhận
- BUG-012 (persistent marker refire) · BUG-014 (Nexus giật/lag khi mở hồ sơ DILA) · T101 (5 lỗi
  Nexus) — đều thuộc tiến trình song song, in_progress trên disk (file ngoài). Đồng bộ rồi mới xử.
- Phát hiện index git có staged-deletions của file chính tôi (T116/T118/T119/T121, sessions, v.v.)
  từ agent ngoài — commit bằng `b4_commit.py` (temp index, cô lập) **không đụng** index ngoài;
  sau commit đã `git add` lại các file riêng của tôi để gỡ cờ "deleted" đang chờ ở index.

## Smoke test (Flask test_client, DB sạch sau)
- 200: editor-stats / data-gaps / unresolved / audit/trail / citation (csl+bib, PL000000000048) /
  geo candidates (58986) / resolutions / bulk-review (verified 1 claim → audit en-*).
- 201: POST /api/feedback. 500 → sau fix: 200 (claims unverified 447,884).
- Cleanup: revert claim #1 ~ 'unverified', xoá feedback test, xoá en_audit_log editor='smoke-test'
  → claims_verified=0, feedback=0.

## Verification
- `npm run lint` **PASS** · `npm run test` **PASS** · `npm run e2e` **PASS** (đã thêm
  `editor-dashboard.html` vào `scripts/e2e-test.js` pages).
- Board: 41 task · done=8 · blocked=2 · 269 commits (git log master).
- Blob hash MATCH các file chính · 0 placeholder `f73e3ce5` sau fill.

## Rollback (mọi bug revert tiện lợi)
- Code: `git revert --no-edit <A-hash>` (docs+DASH là 1 commit: revert 1 lệnh).
- DB: 4 bảng additive (data_gap_requests/user_feedback + 10 cột geo_cross_ref) = `DROP`/ALTER trả về
  (không ảnh hưởng bảng nền; backup SQLite daily mới: `data/snap/lineage_20260910.db.gz`).
- Snapshot DB khôi phục theo §3 ROLLBACK.

## Việc kế tiếp
- Lee review hồi quy trên :5000: editor-dashboard.html + `/api/feedback` + citation export +
  geo candidates → đóng T112/T118/T119/T121 (in_progress→done).
- Chạy `scripts/enrich_places.py --limit=50 --run` lần đầu (sinh candidate), rồi Lee duyệt trong UI.
- Cấu hình cron daily backup + enrich trên máy chủ (nginx/systemd hay Task Scheduler).
- Đồng bộ Batch C (BUG-012/014, T101) với agent ngoài; T113 đóng khi claims_reviewed>0.