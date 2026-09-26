---
id: T139
title: "Zen Lineage Gateway (Đăng ký nguồn + Staging ETL + HITL Review + Edges)"
priority: high
status: in_progress
owner: AI Engineer (build) · Lee Tổng (HITL approve)
module: Ops / Sources / Governance / Lineage Tree
created: 2026-09-15
updated: 2026-09-22
---
# T139 — Zen Lineage Gateway (Đăng ký nguồn + Staging ETL + HITL Review + Edges)

- **Trạng thái:** IN_PROGRESS (Phase 2 completion 2026-09-22 — code DONE, chờ HITL approve thật)
- **Ngày:** 2026-09-15 (phase mới: 2026-09-22)
- **Người phê chuẩn:** Lee Tổng ("a) Đồng ý build + term: mã commit revert mọi bug")
- **Liên quan:** T137 (audit), T138 (render policy/edge assertion), T140 (ẩn/hiện Zen UI)
- **Mục tiêu:** Đăng ký Zen Lineage vào Source Registry đúng T131/T132 (Phase 0) + dựng
  Staging Gateway ETL an toàn (Phase 2, Zero-ALTER/Zero-RAM/license-gated) + HITL
  Review (Phase 3) + Edge Assertions L2 (Phase 4) — mọi thứ additively, revert được bằng git revert.

## 1. Bối cảnh (từ T137 audit V1)

- `data_sources` **chưa có dòng ZENLINEAGE** (gap T137 §10 hứa đăng ký).
- `source_staging` **chưa tồn tại**; `entity_source_ids` (CORE, 182,715) có sẵn
  `match_status/confidence/verified` cho candidate M3.
- Chiều dữ liệu: **Zen Lineage `teacher_id→student_id` = CÙNG CHIỀU Marcus** (ngược DILA)
  → khi ingest sẽ **corroborate L2 tự nhiên**, không tạo direction_mismatch.

## 2. Phase 0 — Đăng ký nguồn (ĐÃ XONG 2026-09-15)

- `POST /daoanh/api/admin/source-add` → `data_sources` **source_id=14** `ZENLINEAGE`:
  `integration_mode='BLOCKED'` · `legal_status='AUDITING'` · `license_verified=0`.
- SQL additive: `source_version='ec8357ed'` · `source_authority` **score=50 ·
  precedence_order=13 · implemented=0** (chỉ active sau license+HITL).
- `en_audit_log`: `source_add` + `source_authority_add` (editor t139_agent).

## 3. Phase 2 — ETL Staging Gateway (ĐÃ XONG 2026-09-15)

**`scripts/etl_zenlineage_stage.py`** (mới, DERIVED-only, Zero-RAM):
- `--dry-run`: validate counts vs audit → **556 masters / 578 transmissions / 25 schools /
  8,684 citations / 206 sources (5/5 khớp)**; báo `--apply` sẽ BỊ CHẶN.
- `--apply`: **license gate = SSOT đọc `data_sources.integration_mode`**; nếu != 'INGEST'
  → thoát 2 và in hướng mở license. Khi mở: backup → CREATE `source_staging` (PK
  source_code|row_type|source_entity_id, INSERT OR REPLACE idempotent) → backfill
  556 masters + 578 transmissions (tier A194/B342/C25/D17 + human_review_needed)
  → ghi `entity_source_ids` candidate (verified=0, entity_id=NULL).
- `--revert`: DROP `source_staging` + xóa entity_source_ids ZENLINEAGE verified=0.
- Bootstrap `find_zen_db`: ưu tiên `--zen-db`, fallback `%TEMP%\opencode\zenlineage_t137\zen.db`
  (T137 dựng) — Không cần npm/network cho dry-run.

## 4. Verification (ĐÃ CHẠY 2026-09-15)

- `py_compile scripts/etl_zenlineage_stage.py` → OK.
- `--dry-run` → 5/5 count khớp audit; gate báo BLOCKED đúng.
- `--apply` → bị chặn exit 2 (integration_mode=BLOCKED) — đúng thiết kế.
- `--revert` → no-op an toàn (chưa có gì) — idempotent.
- SQL staging dựng trên DB-in-memory (556 master + 578 transmission, tier khớp §5 audit).

## 5. Phase 2 completion 2026-09-22 — License mở + Apply + HITL + Edges

**Quyết định admin (Lee):** license **internal-only → INGEST** · scope **toàn bộ 556 masters**
(không giới hạn 18 Thiền-sư VN). Mọi bug fix revert được bằng commit.

### G0 — Mở license gate (DONE)
- `UPDATE data_sources SET integration_mode='INGEST', legal_status='INTERNAL_USE'
   WHERE source_code='ZENLINEAGE'` (+ en_audit_log: license_decision + source_license_open).
- `license_verified` vẫn = 0 (không tự kết luận license) — ghi quyết định admin.

### G1 — Apply staging (DONE 2026-09-22, backup `lineage_t139_20260922_102327.db`)
- `python -X utf8 scripts/etl_zenlineage_stage.py --apply --zen-db <zen.db>` → **556 masters +
  578 transmissions** (1,134 rows) vào `source_staging`.
- **Deviation (đã chốt):** `entity_source_ids.entity_id NOT NULL` → KHÔNG ghi candidate
  entity_id=NULL. **Candidate pool nằm nguyên trong `source_staging`** (row_type='master');
  `entity_source_ids` chỉ ghi KHI HITL approve (entity_id thật, verified=1,
  match_status='approved'). Tập staging file `etl_zenlineage_stage.py` đã sửa:
  `stage_candidates()` → `print_candidate_pool()` (read-only đếm).

### G2 — HITL Review API + UI (DONE)
- **Bảng DERIVED `zenlineage_review`** (CREATE TABLE IF NOT EXISTS, PK
  `source_entity_id`, cột status/dila_person_id/entity_hub_id/confidence/editor/note/timestamps)
  — 0 ALTER base.
- **API (app.py, additive, sau `_iso_now` — các route `/daoanh/api/admin/zenlineage/*`):**
  - `GET /candidates?page&limit&filter=all|pending|approved|rejected&q=` — liệt kê candidate
    pool từ `source_staging`, join `zenlineage_review`, kèm `suggestions[]` (gợi ý DILA person
    token-match qua `people.name_zh/vi/en/ja` + `entity_hub` resolve entity_hub_id, top 5).
  - `POST /candidate/<slug>/approve {dila_id, confidence, editor}` — resolve entity_hub
    (insert nếu thiếu PERSON row), ghi `zenlineage_review` approven + `entity_source_ids`
    (DELETE cũ rồi INSERT — bảng không có UNIQUE(source,source_entity_id)) + en_audit_log.
  - `POST /candidate/<slug>/reject {note, editor}` — chỉ ghi review rejected.
  - `POST /candidate/<slug>/unset` — hủy quyết định (về pending), xóa esi ZENLINEAGE.
  - `GET /stats` — tổng/approved/pending/rejected + tier A–D transmissions.
- **UI: `admin/zenlineage_review.html`** (mới) — bảng candidate + thẻ gợi ý DILA (click chọn,
  Approve kèm confidence, Reject kèm note, Hủy quyết định), stats cards, filter, pager,
  editor name trong localStorage. Nav: `admin/index.html` thêm mục "Zen Lineage HITL Review".
- **Fix bug trong build:** `_zen_suggest` lỗi "No item with that key" vì SELECT thiếu
  `p.name_en` (đã thêm), bổ sung dò đa-token + Hán tự substring scoring + dedupe dila_id.

### G3 — Edge assertions L2 (DONE — ETL `scripts/etl_zenlineage_edges.py`)
- `--dry-run`/`--apply`/`--revert`. Gate SSOT đọc `data_sources.integration_mode` (INGEST →
  cho chạy). Backup riêng `lineage_t139_edges_<ts>.db`.
- Chỉ tạo edge khi **CẢ 2 đầu** (teacher+student) có mapping HITL approved:
  `entity_source_ids (source='ZENLINEAGE', match_status='approved', verified=1) JOIN entity_hub
   ON canonical_label=dila_id` → edge_key `Z|<teacher_slug>|<student_slug>` →
  `lineage_edge_assertions` source_code='ZENLINEAGE' trust_level='L2' mapping_verified=1
  relation_type='da:isTeacherOf' raw_relation_type=tr_type (primary/secondary/dharma/disputed)
  — chiều teacher→student CÙNG Marcus → corroborate L2, không direction_mismatch.
- **Idempotent:** DELETE toàn bộ assertions ZENLINEAGE cũ trước rồi INSERT lại (bảng không
  có UNIQUE pair) — chạy lại ra cùng kết quả.
- **Test thực (mock approve → apply → apply lại → revert → cleanup):** 0 approved → 0 edge;
  mock 2 slug 1 đầu → 0 edge (mapping chặt TRUE); mock 3 slug (mazu-daoyi/linji-yixuan/
  baizhang-huaihai approved) → **đúng 1 edge `Z|mazu-daoyi|baizhang-huaihai`
  A000001→A000003, L2, mapping_verified=1**; apply lặp → vẫn 1 (idempotent);
  revert + cleanup esi/review → **DB sạch** (esi_ZEN [ ], review [ ], ZEN edges 0).

### G4 — source_authority.implemented=1 (DONE)
- `UPDATE source_authority SET implemented=1 WHERE source_code='ZENLINEAGE'` (+ en_audit_log
  source_authority_update). score=50, precedence=13 giữ nguyên.

### G5 — UI Pháp mạch hiện Zen (DONE — places.html, additive)
- Inspector "Nguồn ghi nhận": thêm dòng **`✓ Zen Lineage (đối chiếu L2)`** + raw_type + ref
  **chỉ khi có assertion ZEN** (policy T140 "Ẩn Zen" → T139 "hiện khi HITL duyệt").
  Kèm nút `HITL Mapping Zen Lineage ↗` → admin/zenlineage_review.html.
- Legend 2 chỗ: "Zen hiện ẩn"/"Zen ẩn" → "Zen (đối chiếu L2, hiện khi HITL duyệt)".
- Backend `_t138_edge_assertions` vốn trả `sources[]` generic (MARCUS/DILA/ZENLINEAGE tự nhiên)
  — 0 đổi.

## 6. Verification (2026-09-22 — đã chạy)

- `py_compile app.py` + `scripts/etl_zenlineage_edges.py` → OK.
- Flask test client: stats 200 · candidates (all/pending/approved/rejected) 200 · approve
  (mazu-daoyi→A000001, entity_hub 218329) 200 · unset 200 · stats về 0 sau unset.
- `node --check` zenlineage_review.html + places.html → OK.
- `npm run pipeline`: guard/lint/test/test:uat/test:compliance/e2e PASS
  (e2e:runtime EPERM + lint placevn.html ESM pre-existing — ghi nhận sẵn).

## 7. Còn lại (chờ HITL thật)

- Admin dùng `admin/zenlineage_review.html` (hoặc API) duyệt từng master → 556 candidate
  pending. Approve càng nhiều → edge ZENLINEAGE L2 càng phủ rộng.
- Sau khi approve nhiều: `python scripts/etl_zenlineage_edges.py --apply` (gate đã mở,
  idempotent, có backup) → UI Pháp mạch hiện ✓ Zen + bấm HITL Mapping ↗.
- Restart :5000 để route + places.html mới có hiệu lực.

## 8. Risks

- Static export `public/api/masters.json` chỉ publish-subset (465) — kênh tĩnh thiếu
  tier; **kênh đầy đủ 556 bắt buộc dùng zen.db (@ ec8357ed)** — script đã ưu tiên.
- `find_zen_db` fallback dựa %TEMP% Windows — path cứng dễ hỏng trên máy khác.
- Gợi ý DILA là token-match sơ khai (homonym phổ biến) — HITL phải đọc kỹ tiểu sử trước
  khi Approve; broadcast Zen tên quen có thể gợi ý sai person.

## 9. Rollback

- Phase 2 completion code: `git revert <commit-t139-phase2>` (additive files: app.py sections,
  admin/zenlineage_review.html, admin/index.html nav, scripts/etl_zenlineage_edges.py,
  scripts/lint-check.ps1, places.html, task file này).
- Phase 2 completion DB (các bước đảo ngược):
  1. `python scripts/etl_zenlineage_edges.py --revert` (xóa assertions ZENLINEAGE).
  2. `DELETE FROM entity_source_ids WHERE source='ZENLINEAGE'` + `DELETE FROM zenlineage_review`.
  3. `python scripts/etl_zenlineage_stage.py --revert` (DROP source_staging).
  4. `UPDATE source_authority SET implemented=0 WHERE source_code='ZENLINEAGE'`.
  5. `UPDATE data_sources SET integration_mode='BLOCKED', legal_status='AUDITING'
     WHERE source_code='ZENLINEAGE'`.
- Backup files: `lineage_t139_20260922_102327.db` (trước G1) · `lineage_t139_edges_*.db`
  (từng lần apply G3). Hoàn nguyên thủ công từ backup nếu muốn.

## Files
- `scripts/etl_zenlineage_stage.py` (Phase 2, sửa deviation candidate pool)
- `scripts/etl_zenlineage_edges.py` (Phase 4, mới)
- `app.py` (Phase 3 API — routes /daoanh/api/admin/zenlineage/*)
- `admin/zenlineage_review.html` (Phase 3 UI, mới) · `admin/index.html` (nav +1)
- `places.html` (Phase 5 inspector + legend)
- `scripts/lint-check.ps1` (+zenlineage_review.html)
- `docs/ZEN_LINEAGE_INTEGRATION_AUDIT_V1.md` §15 (trạng thái Phase 2 completion)
- `docs/ROLLBACK.md` (row T139 Phase 2 completion) · `docs/tasktodo.md` (T139 phase 2 done)
- session doc (mới) · dashboard regen