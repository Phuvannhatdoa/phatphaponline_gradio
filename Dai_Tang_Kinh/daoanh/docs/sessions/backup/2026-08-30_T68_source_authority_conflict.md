# T68 — Source Authority Matrix + Resolve Canonical + Place Conflict Detection (Implementation)

**Ngày:** 2026-08-30
**Build:** TGS Build 1 Acceptance — commit 3/4 (sau T67, trước T69)
**Trạng thái:** ✅ DONE (runtime verified)

## Mục tiêu
Xây dựng **nền tảng authority ranking** cho địa danh: 1) bảng `source_authority` (9 nguồn, seed minh bạch),
2) hàm `resolve_canonical()` chọn tên canonical theo thứ tự ưu tiên nguồn, 3) `_detect_conflicts()` phát hiện
xung đột tên Việt giữa các nguồn, ghi `conflict_pending` để admin HITL xử lý. Tất cả additive + reversible
(không đụng schema nguồn, DILA/CBETA bất biến).

## Việc đã làm

### T68a — Bảng cấu hình mới (`scripts/build_authority_tables.py`, idempotent)
- `source_authority(source_code TEXT PRIMARY KEY, source_id INTEGER, authority_score INTEGER,
  precedence_order INTEGER, implemented INTEGER DEFAULT 0, note TEXT)`
  - Khóa `source_code` (không phải source_id) vì SAT/CHGIS/FoJin/Wikidata chưa có trong `data_sources`.
  - Seed 9 nguồn: DILA=100(CBETA=80(SAT=75(MARCUS=60(CHGIS=58(ZQLOCAL=50(BDRC=40(FoJin=40(Wikidata=25.
  - CHGIS/BDRC/FoJin/SAT/Wikidata đánh `implemented=0` (khớp T70 governance).
- `conflict_pending(id PK AUTOINCREMENT, entity_ref, value_a, value_a_source, value_b, value_b_source, status,
  resolved_value, decided_at, editor)`
- `INSERT OR IGNORE` + sync `source_id` từ `data_sources` — an toàn chạy lại nhiều lần.
- Backup an toàn pre-T68: `sqlite3.Connection.backup()` (không chạm WAL).

### T68b/c — backend (app.py)
- `_source_authority_map(conn)` — đọc authority_matrix từ bảng (KHÔNG hardcode).
- `_name_vi_evidence(conn, ref, a_map)` — gộp các tên Việt + nguồn + authority cho 1 địa danh.
- `_detect_conflicts(conn, ranked, ref)` — so value_a vs value_b, chèn `conflict_pending` khi lệch.
- `resolve_canonical(...)` — helper chọn canonical theo precedence_order/authority_score.
- `GET /daoanh/api/admin/place/<id>/authority` — trả authority_matrix + canonical_candidates +
  conflicts (auto-trigger `_detect_conflicts` + commit).
- `POST /daoanh/api/admin/place/<id>/conflict/resolve` — ghi `en_audit_log`(action='resolve_conflict') +
  upsert `canonical_decision` + flip `entity_hub.status='verified'`.
- `GET /daoanh/api/admin/conflicts` (`list_conflicts`) — danh sách pending toàn cục.

### T68d — UI hooks (admin/placevn.html)
- State: `authorityData` / `authorityLoading` / `resolvingConflict`; helpers `loadAuthority` / `resolveConflict`.
- Panel "Xếp hạng nguồn & Xung đột (T68)" sau khu vực HITL T67 (trước "Vị trí (3 Lớp RAG)").
- Thêm icon `scale` + `alert-triangle` vào `ICON_SVGS`.

## Runtime verify (đã dọn test data)
- `GET .../place/PL000000000314/authority` → authority_matrix 9 nguồn + canonical_candidates
  (2 tên Việt; điểm ZQLOCAL=50) + tạo conflict_pending (value_a 'Th? S?t H?i' vs value_b).
- `POST .../conflict/resolve` → update conflict_pending + en_audit_log + canonical_decision + entity_hub verified.
- Sau verify: dọn conflict_pending (0), en_audit_log về 2 rows (T67), canonical_decision khôi phục T67 ban đầu.

## Kiểm tra
- py_compile OK (app.py, build_authority_tables.py); route không trùng.
- `npm run lint` exit 0 (ESM get_format là false-positive môi trường, đã ghi nhận).
- `npm run test` ✅; `npm run e2e` ✅ (placevn.html JSX Syntax OK).

## LƯU Ý MÔI TRƯỜNG
- Server test orphan (PID 196) giữ port 5000 không kill được từ shell non-elevated ("Access denied").
  Dùng `dashboard/restart_servers.ps1` (đủ quyền) để xử lý.
- Backup pre-T68 tại `%TEMP%\opencode\`.

## Revert
- Drop 2 bảng mới (`source_authority`, `conflict_pending`) — reversible.
- Không sửa schema nguồn; chỉ thêm bảng cấu hình + hàm mới.
