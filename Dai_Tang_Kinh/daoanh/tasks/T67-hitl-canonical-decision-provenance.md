---
id: T67
title: "HITL Canonical Decision + Audit Log + Provenance (P0-1)"
module: DILA Integration Layer
priority: high
status: done
depends_on: [T58]
created: 2026-08-30
updated: 2026-08-30
done_when: >
  Khi admin bấm Save trong Đạo Ảnh, hệ thống ghi quyết định canonical có đầy đủ provenance:
  ai (editor), khi nào (decided_at), đổi gì (field/old/new), nguồn bằng chứng (evidence_citations),
  trạng thái xác minh (verification_status), và chuyển entity_hub.status sang 'verified'.
  Không còn là "SQLite editor" chỉ ghi name_vi.
---

# T67 — HITL Canonical Decision + Audit Log + Provenance

## Mục tiêu
Biến Đạo Ảnh từ "SQLite editor" (chỉ `INSERT OR REPLACE namevi_map_places` + `UPDATE places_pending.name_vi`)
thành **hệ thống quyết định canonical** — mỗi lần admin duyệt phải ghi lại đầy đủ provenance.
Đây là mắt xích bắt buộc để nâng verdict Build 1 từ CONDITIONALLY ACCEPTED lên ACCEPTED.

## Hiện Trạng (Codebase)
- `save_mapping` (app.py:7271) — chỉ ghi `namevi_map_places` + `places_pending.name_vi`; không lưu ai/khi nào/thay đổi gì/nguồn/trạng thái.
- `auto_save_name` (app.py:7290) — tương tự; `source='auto_generated'`, confidence 0.5.
- Bằng chứng gap: `namevi_map_places.source='manual'` = 3 rows; `entity_hub.status` = 'active' 100% (0 verified); `entity_source_ids.verified` = 0/167,008; `entity_claims.verification_status` = 'unverified' 100%.
- `entity_hub.entity_id` = số nguyên surrogate liên kết DILA qua `canonical_label='PL…'`; `entity.entity_id` = 'PL…' string.
- `dataset_sources` (10) — catalog nguồn có `usage_level`; `data_sources` (5) có `authority_scope`.
- React admin UI: `admin/placevn.html` (React 18, createRoot :1760) hiển thị evidence (CBETA/CBDB/Wiki/TEI) nhưng save chỉ gửi name/form.

## Khoảng Trống (Gap)
- Không có bảng ghi quyết định canonical (who/when/what/evidence/verification_state).
- Không có audit log bất biến.
- Save không đẩy verification_status lên `entity_hub`.
- UI không thu thập `editor` + `verification_status` + hiển thị `evidence_citations` trong quyết định.

## Thiết Kế (additive, reversible, backward-compatible)

### Bảng mới 1 — `canonical_decision` (1 dòng / entity — trạng thái hiện tại)
`CREATE TABLE IF NOT EXISTS canonical_decision (
  entity_ref TEXT PRIMARY KEY,          -- 'PL…'
  canonical_name_vi TEXT,
  source_id INTEGER REFERENCES dataset_sources(id),
  authority_rank TEXT,
  confidence REAL,
  verification_status TEXT,             -- pending|needs_review|verified|canonical
  decision_note TEXT,
  evidence_citations TEXT,              -- JSON list (cbeta_ref / source_book)
  editor TEXT,
  decided_at TEXT,
  updated_at TEXT
)`

### Bảng mới 2 — `en_audit_log` (append-only, bất biến)
`CREATE TABLE IF NOT EXISTS en_audit_log (
  log_id INTEGER PRIMARY KEY AUTOINCREMENT,
  entity_ref TEXT,
  action TEXT,                          -- create|update|approve
  field_name TEXT,
  old_value TEXT,
  new_value TEXT,
  evidence_sources TEXT,                -- JSON
  authority_rank TEXT,
  editor TEXT,
  verification_status TEXT,
  created_at TEXT
)`

### app.py — nâng cấp `save_mapping` + `auto_save_name` (giữ API contract cũ)
- Sau khi ghi `namevi_map_places`: upsert `canonical_decision` + append `en_audit_log` + chuyển `entity_hub.status='verified'`.
- Builder helper `_persist_canonical_decision(conn, dila_id, action, field, old_v, new_v)`.
- **Chỉ verified khi admin thực sự duyệt** (KHÔNG backfill bulk) — khớp quyết định đã chốt với admin.
- Endpoint mới: `GET /daoanh/api/admin/place/<id>/canonical` → trả decision hiện tại.

### Frontend `admin/placevn.html` (React)
- Panel "Quyết định Canonical": hiển thị `authority_rank`, `verification_status` (dropdown), `evidence_citations`.
- Payload save thêm `editor` (từ session) + `verification_status`.
- Giữ nguyên mọi panel evidence hiện tại (CBETA/CBDB/Wiki/TEI) — chúng là nguồn để quyết định.

## Subtasks
- [x] T67a: Tạo 2 bảng `canonical_decision` + `en_audit_log` (script idempotent `scripts/build_canonical_tables.py`)
- [x] T67b: `_persist_canonical_decision()` + nâng cấp save_mapping/auto_save_name trong app.py
- [x] T67c: Endpoint `GET /daoanh/api/admin/place/<id>/canonical`
- [x] T67d: React panel "Quyết định Canonical" + editor/verification_status trong payload save
- [x] T67e: Verify runtime (save → audit_log có dòng + entity_hub.status='verified') + py_compile
- [x] T67f: tasktodo.md + session log + git commit

## Kết quả (verified 2026-08-30)
- Tạo 2 bảng mới (`canonical_decision`, `en_audit_log`) — idempotent, UTF-8, đã xác minh tồn tại.
- `_persist_canonical_decision()` dùng `_resolve_place_id()` để khớp đúng `entity_hub.canonical_label` (xử lý id raw/padded) — CHỐT lỗi id-match.
- Runtime admin-approve (PL000000000314): `canonical_decision` (verified, editor, evidence ["X77n1524_p0400a12"]) + `en_audit_log` 1 dòng + `entity_hub.status` active→**verified**. ✅
- Runtime auto (PL000000000001): ghi `needs_review`/`auto_transliterate`, `entity_hub` **giữ 'active'** (KHÔNG self-verify). ✅
- `GET /daoanh/api/admin/place/<id>/canonical` trả decision + history + hub status. ✅
- py_compile OK; test ✅; e2e placevn.html Script Block 2 (JSX) Syntax OK.

## Revert
- Drop 2 bảng mới (`DROP TABLE canonical_decision; DROP TABLE en_audit_log;`) — reversible.
- Không sửa schema bảng nguồn; chỉ ADD thêm bảng mới + thêm logic ghi vào trong hàm save (giữ API cũ).
