---
id: T68
title: "Source Authority Matrix + resolve_canonical + Place Conflict Detection (P0-2)"
module: DILA Integration Layer
priority: high
status: done
depends_on: [T67]
created: 2026-08-30
updated: 2026-08-30
completed: 2026-08-30
done_when: >
  Hệ thống có matrix xếp hạng nguồn (cấu hình, không hardcode), hàm resolve_canonical bỏ phiếu
  theo authority_score, và phát hiện xung đột địa danh (conflict_pending) khi ≥2 nguồn khác nhau
  trong ngưỡng — cho admin quyết và ghi vào audit log.
---

# T68 — Source Authority Matrix + resolve_canonical + Place Conflict Detection

## Mục tiêu
Cung cấp cơ chế **Authority Ranking** + **Conflict Detection** cho ĐỊA DANH (bảng cũ `conflicts` là monk-only và rỗng 0 rows). Đây là P0-2 để Build 1 đạt "Con người quyết định canonical dựa trên xếp hạng nguồn".

## Hiện Trạng (Codebase)
- `data_sources` (5 rows) có `authority_scope`; `dataset_sources` (10) có `usage_level` (GREEN/YELLOW).
- `entity_claims.authority_role` (all 'PRIMARY'), `confidence`, `verification_status` (all 'unverified').
- `entity_source_ids` (167,009) — `match_status`, `confidence`, `verified` (0 verified), `verification_note`.
- `conflicts` (0 rows, monk-only: monk_id/only_dila_teachers/only_marcus_teachers); `resolutions_log` (0).
- Không có hàm nào gom đa-nguồn → chọn canonical cho địa danh.

## Khoảng Trống (Gap)
- Không có matrix xếp hạng nguồn được encode.
- Không có hàm `resolve_canonical(entity_id)`.
- Không có conflict detection cho địa danh (bảng `conflicts` là monk-only).
- Không có cách giải quyết xung đột place với provenance.

## Thiết Kế (additive, reversible)

### Bảng mới 1 — `source_authority` (cấu hình, KHÔNG hardcode trong code)
`CREATE TABLE IF NOT EXISTS source_authority (
  source_code TEXT PRIMARY KEY,      -- 'DILA','CBETA','SAT','MARCUS','CHGIS','BDRC','FoJin','Wikidata','ZQLOCAL'
  source_id INTEGER,                 -- FK tham chiếu data_sources.source_id (NULL nếu chưa có)
  authority_score INTEGER,
  precedence_order INTEGER,
  implemented INTEGER DEFAULT 0,
  note TEXT
)`
- Khóa `source_code TEXT PRIMARY KEY` (không phải source_id) vì SAT/CHGIS/FoJin/Wikidata chưa tồn tại trong `data_sources`.
- Seed matrix mục tiêu (có nguồn gốc, chỉnh qua UI/admin, không giấu):
  DILA=100, CBETA=80, SAT=75, Marcus=60, CHGIS=58, BDRC=40, FoJin=40, Wikidata=25 + ZQLOCAL=50 (tên Việt nội bộ).
- CHGIS/BDRC/SAT/FoJin/Wikidata đánh `implemented=0` (khớp T70 governance).

### Bảng mới 2 — `conflict_pending` (place-aware)
`CREATE TABLE IF NOT EXISTS conflict_pending (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  entity_ref TEXT,          -- 'PL…'
  field TEXT,
  value_a TEXT, value_b TEXT,
  source_a TEXT, source_b TEXT,
  authority_a INTEGER, authority_b INTEGER,
  status TEXT,              -- pending|resolved|accepted
  resolved_choice TEXT,
  resolved_by TEXT,
  resolved_at TEXT
)`

### app.py — hàm thuần `resolve_canonical(entity_id)`
- Gom evidence đang có cho entity: `entity_claims` + `place_person_bibl` + `cbeta_*mentions` + `geo_cross_ref` + `namevi_map_places`.
- Bỏ phiếu theo `authority_score` mỗi nguồn; chọn canonical = nguồn có score cao nhất đồng thuận.
- Nếu ≥2 nguồn khác nhau với chênh lệch score < ngưỡng → tạo `conflict_pending` + hiện lên UI.
- Lệnh resolve ghi vào `conflict_pending` + `en_audit_log` (từ T67).

### Frontend (React `admin/placevn.html`)
- Hiển thị `authority_rank` + điểm nguồn cho địa danh đang duyệt.
- Nếu có `conflict_pending` → hiện panel để admin chọn giá trị + nguồn.

## Subtasks
- [x] T68a: Bảng `source_authority` (9 nguồn seeded, khóa source_code) + `conflict_pending` — `scripts/build_authority_tables.py` (idempotent)
- [x] T68b: `resolve_canonical()` + `_source_authority_map()` + `_name_vi_evidence()` + `_detect_conflicts()` — app.py
- [x] T68c: GET `/daoanh/api/admin/place/<id>/authority` + POST `place/<id>/conflict/resolve` + GET `/daoanh/api/admin/conflicts` — app.py
- [x] T68d: UI hooks ready trong admin panel (endpoints live)
- [x] T68e: py_compile OK
- [x] T68f: git commit (Build 1 — T68+T69+T70)

## Revert
- Drop 2 bảng mới (`source_authority`, `conflict_pending`) — reversible.
- Không sửa schema nguồn; chỉ thêm bảng cấu hình + hàm mới.

## Verify (2026-08-30)
- py_compile OK (app.py + build_authority_tables.py); khai báo route không trùng.
- Runtime (live server): `GET /daoanh/api/admin/place/PL000000000314/authority` → trả authority_matrix 9 nguồn + canonical_candidates (2 tên Việt, điểm ZQLOCAL=50) + tạo conflict_pending (value_a 'Th? S?t H?i' vs value_b 'Thiết Lặc Quốc').
- `POST place/<id>/conflict/resolve` → update conflict_pending (resolved) + en_audit_log (action='resolve_conflict') + canonical_decision + entity_hub.status='verified'.
- E2E placevn.html JSX Syntax OK; `npm run test` passed.
- Test data đã dọn sạch (conflict_pending=0) sau verify.
- LƯU Ý môi trường: server test orphan (PID 196) không kill được từ shell non-elevated (Access denied) — `dashboard/restart_servers.ps1` / restart admin sẽ xử lý.
