# T67 — HITL Canonical Decision + Audit Log + Provenance (Implementation)

**Ngày:** 2026-08-30
**Build:** TGS Build 1 Acceptance — commit 2/4 (sau c629238 task-plan, trước T68)
**Trạng thái:** ✅ DONE (runtime verified)

## Mục tiêu
Biến Đạo Ảnh từ "SQLite editor" (chỉ INSERT OR REPLACE namevi_map_places + UPDATE places_pending.name_vi)
thành hệ thống **quyết định canonical** có đầy đủ provenance (ai/khi nào/đổi gì/nguồn/trạng thái).

## Việc đã làm

### T67a — Bảng mới (scripts/build_canonical_tables.py, idempotent)
- `canonical_decision` (entity_ref PK, canonical_name_vi, source_id, authority_rank, confidence,
  verification_status, decision_note, evidence_citations JSON, editor, decided_at, updated_at; idx status)
- `en_audit_log` (log_id PK AUTOINCREMENT, entity_ref, action, field_name, old_value, new_value,
  evidence_sources JSON, authority_rank, editor, verification_status, created_at; idx entity_ref)
- Backup an toàn pre-T67: `sqlite3.Connection.backup()` (không chạm WAL) → `%TEMP%\opencode\lineage_pre_T67_20260830_014511.db`

### T67b — backend (app.py)
- `_persist_canonical_decision(conn, dila_id, action, field_name, old, new, ...)` — upsert canonical_decision +
  append en_audit_log + chuyển `entity_hub.status='verified'` CHỈ khi `mark_verified=True`.
- **`_resolve_place_id(conn, dila_id)`** — CHỐT lỗi id-match: frontend gửi id đã blanket-pad
  (`ensure_long_id` → PL + 12 digits) nhưng `entity_hub.canonical_label`/`places_pending.id` có thể là dạng raw
  ngắn hơn. Hàm resolve ra id THỰC tồn tại để khớp đúng canonical_label (flip status) + entity_ref nhất quán.
- `save_mapping` — gọi helper với `mark_verified = (verification_status in ('verified','canonical'))`.
- `auto_save_name` — gọi helper với `mark_verified=False` (auto KHÔNG tự verify).
- Endpoint mới `GET /daoanh/api/admin/place/<id>/canonical` (T67c) — trả decision + history + entity_hub status.

### T67d — frontend (admin/placevn.html)
- Capture `window.__ADMIN_EMAIL__` từ `/daoanh/api/login/check` (trả về email).
- Panel "Quyết định Canonical (HITL)": dropdown verification_status (pending/needs_review/verified/canonical)
  + input editor (provenance).
- Payload save thêm `editor` + `verification_status` + `evidence_citations` (CBETA refs trích từ DILA bibls
  qua regex `CBETA ([A-Z]\d+n\d+_\w+)`).
- Thêm icon `shield-check` vào ICON_SVGS.

## Verify runtime (đã chạy thật qua HTTP)
- **Admin-approve** PL000000000314 (十剎海寺, CBETA X77n1524_p0400a12):
  - `canonical_decision` → verified, editor daoanh.tester@gmail.com, evidence ["X77n1524_p0400a12"], admin_approved
  - `en_audit_log` → 1 dòng (log_id=1, action=approve)
  - `entity_hub.status` → active **→ verified** ✅
- **Auto** PL000000000001 (闊悉多國): ghi `needs_review`/`auto_transliterate`, audit update,
  `entity_hub` **giữ 'active'** (KHÔNG tự verify) ✅ — khớp yêu cầu "chỉ admin duyệt mới verified".
- `GET .../place/<id>/canonical` trả đủ decision + history + hub status ✅
- py_compile OK; `npm run test` ✅; `npm run e2e` placevn.html Script Block 2 (JSX) Syntax OK ✅;
  lint (ESM get_format lỗi sẵn có, script exit 0); e2e:runtime EPERM trên file artifact Playwright (môi trường).

## Thay đổi file
- `app.py` — helper + resolve + save_mapping/auto_save_name + endpoint GET canonical
- `admin/placevn.html` — session email capture + panel HITL + payload save + icon
- `scripts/build_canonical_tables.py` — T67a (đã commit trước? chưa — commit chung lần này)
- `tasks/T67-*.md`, `docs/tasktodo.md`, `data/progress_data.json`, `docs/sessions/2026-08-30_T67_..._impl.md`

## Lưu ý / quyết định
- ID normalization: frontend pad 12 chữ số, DB `places_pending.id`/`entity_hub.canonical_label` có thể raw/padded.
  `_resolve_place_id` xử lý cả 2; queue DILA hiện tại chủ yếu dạng padded 14-char.
- `entity_hub` WHERE dùng `canonical_label` (không dùng entity_id INT) — đúng mô hình liên kết.
- Additive, reversible: chỉ ADD 2 bảng mới + thêm logic ghi; `DROP TABLE canonical_decision/en_audit_log` để revert.

## Next
T68 — Source Authority Matrix + resolve_canonical + Place Conflict (seed `source_authority`
DILA=100>CBETA=80>SAT=75>Marcus=60>CHGIS=58>BDRC=40=FoJin=40>Wikidata=25; tạo `conflict_pending`).
