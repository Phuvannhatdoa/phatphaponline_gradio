# ROADMAP_META_UPDATE.md — Hồ sơ Tự định danh Hệ thống (System Registry)

> **Bản đồ di sản** — task: `tasks/T116-system-registry-handover.md` · **Zero-Loss**: file này chỉ APPEND, không bao giờ xóa; tăng version thay vì ghi đè lịch sử.
> Bản v1.0 · 2026-09-09 · Registry điều hướng (no-copy): mọi số liệu chi tiết nằm ở SSOT được trỏ ở §4 — không tạo 2 nguồn sự thật.

## 1. MỤC TIÊU

Biến cấu trúc sống của dự án thành **hệ thống tự định danh (Self-documenting)** — bất kỳ
Agent/Developer nào cũng nắm được kiến trúc sau **một lần đọc**, không đoán mò, không lặp
lỗi cũ. File này = **Registry điều hướng + Handover**: báo phiên bản hệ thống, cảnh báo
"bẫy dữ liệu", và trỏ tới các SSOT — KHÔNG chép lại nội dung của chúng.

## 2. VERSION SNAPSHOT (2026-09-09)

| Hạng mục | Giá trị thật | Nguồn chân lý |
|---|---|---|
| Phiên bản hệ thống | **Git HEAD `0c9df6c`** (chuỗi commit là phiên bản; DB **không** lưu schema_version) | `git log` |
| Cơ sở dữ liệu | `data/lineage.db` · **133 bảng** (compliance dashboard đếm 132 — lệch do cách đếm, cosmetic) | `sqlite_master` |
| Assertions (claims) | **447,885** (`entity_claims`) | DB |
| Events | **3,530** (`events`) · provenance 3,530/3,530 (**100%** `events_provenance`) | DB |
| Assertion level (M7.2) | **0 claim** có `assertion_level` (metric hiện **fail** — data quality thật, không che) | `design_compliance.json` |
| Audit / Provenance | `entity_claims_audit.audit_id` = **hash SHA-256 64 hex** (content-hash) | DB |
| Glossary VI | `glossary_vi` **75.54%** (187,412/248,095) | `design_compliance.json` |
| Conflicts | 40,327 conflicts chờ admin · resolved 6 (0.01% bootstrap) | `design_compliance.json` |
| Dashboard | `data/progress_data.json` (regen: task=41 · done=10 · blocked=2 · 280 commits) | `scripts/build_progress_data.py` |

## 3. DATA TRAPS MAP — "bẫy dữ liệu" đã thống nhất (T79/T86/T108–T113)

> Đọc kỹ trước khi viết code — đây là những chỗ người sau hay mắc:

1. **`marcus_reference` cẩn trọng (T79/T51f):** `label`/`label_vi` là pháp danh chuẩn để hiển thị.
   Đừng hiển thị thẳng `people.name_zh` (thường là **thụy hiệu/tự hiệu** như `大鑒真空普覺圓明禪師`);
   `people.birth_year/death_year` **nhiễm số trang CBETA** → dùng `marcus_reference`.
2. **`people.name_zh` không hiển thị trực tiếp** — dùng canonical từ `marcus_reference.label` (xem `app.py` T51f/T86).
3. **`entity_claims.assertion_level` hiện = 0% (chưa fill)** — đừng giả định có; validation M7.2 đang fail đúng hiện trạng.
4. **NOT INDEXED convention (T86):** ref ngoài phạm vi → trả HONEST null, không hallucinate:
   `{"ok": true, "resolved": {"found": false, "message": "..."}}`. Giữ kiểu "báo không chỉ mục".
5. **Zero-ALTER tuyệt đối:** KHÔNG UPDATE/Xóa bảng gốc; mọi biến đổi = bảng dẫn xuất additive + View Adapter.
6. **Zero-RAM:** không nạp toàn bộ 2.000+ kinh văn; dùng COUNT aggregate/generator/byte-offset mapping.
7. **DB thật = `data/lineage.db`** (133 bảng). `daoanh.db`/`lineage.db` ở thư mục gốc là **rỗng (0 bảng)** — đừng trỏ nhầm.
8. **13 nguồn, không phải nhầm GRETIL** (GRETIL chưa đăng ký) · **Wikidata ≠ Wikipedia** · `ZQLOCAL` = DILA local.

## 4. NAVIGATION INDEX (SSOT — không copy, chỉ trỏ)

| Chủ đề | SSOT |
|---|---|
| Hiến pháp dữ liệu + Schema + M7.2 (9 metric compliance) | `docs/SCHEMA_DESIGN.md` |
| Đăng ký 13 nguồn + trạng thái Active/Pending (§5 quyết định chờ duyệt, §6 đối chiếu) | `docs/SOURCE_REGISTRY.md` |
| Luật Trọng Tài conflict (score → precedence 0-based · tie → pool admin · Level L1≥80/L2 45–75/L3<45) | `docs/SOURCE_AUTHORITY_MATRIX.md` |
| QA compliance baseline (`design_compliance.json` — 5 pass/3 fail/1 warn) | repo + `docs/SCHEMA_DESIGN.md` M7.2 |
| Task đang mở + đóng | `docs/tasktodo.md` · `docs/roadmap.md` · `tasks/*.md` (frontmatter = nguồn dashboard) |
| Lệnh rollback từng thay đổi | `docs/ROLLBACK.md` |
| Nhật ký phiên | `docs/sessions/*.md` |

## 5. META-GOVERNANCE (Operating Protocol)

- **Zero-Loss Rule:** không bao giờ xóa tài liệu cũ; cập nhật = append + bump version (git commit hash là nguồn version).
- **Auto-Sync:** mọi thay đổi cấu trúc DB phải phản ánh ngược vào `docs/SCHEMA_DESIGN.md` — đây là quy ước chạy sẵn của mỗi release (không phải milestone).
- **Regen Dashboard:** sau mỗi thay đổi task/docs chạy `python scripts/build_progress_data.py`.
- **Phê duyệt:** conflicts chỉ do **Lee Tổng (Admin)** phê qua `admin/conflicts.html` — Agent không tự quyết.
- **Revert mọi thứ:** `git revert --no-edit <hash>` — mỗi thay đổi có row trong `docs/ROLLBACK.md`.
- **Đặc tả chồng lấn → KHÔNG tạo file SPEC trùng (rá 2026-09-09):** đặc tả "T117 Doctrine Retrieval
  Engine" mô tả lại **T100+T111+T113 (đã DONE)**; "T109 Conflict Engine" mô tả lại T109 (đã DONE);
  "T114 Roadmap Meta-Update" → T116. Chủ sở hữu = task gốc; ghi `[ráspec <date>]` vào tasktodo thay vì
  tạo `RETRIEVAL_ENGINE_SPEC.md`/`CONFLICT_ENGINE_SPEC.md`/`PROJECT_STATUS.md` (SSOT = tasktodo/roadmap).
- **Bậc Tiến sĩ — Audit Trail API chưa có (chờ T118):** `en_audit_log` (editor/evidence/created_at) +
  `entity_claims_audit.audit_id` là **admin-only**; evidence response chưa kèm `audit_id`.
  Kế hoạch T118 = `GET /daoanh/api/research/entity/<id>/audit-trail` additive read-only (đúng đặc tả
  "Full Assertion Object + Audit Trail"), **để sau — Track 2**.
- **Curation workflow = T100+T109 infrastructure (ráspec 2026-09-09):** HITL 3 bước (review →
  acceptance → commit) đã có: `entity_claims.verification_status` + `POST /claims/<id>/review` +
  `resolutions_log` + `en_audit_log` + `admin/conflicts.html` + `admin/bio-review.html` (approve/
  reject/bulk-approve pattern). 4 UI convenience gaps còn thiếu = **task T119** (pending Track 2):
  (1) unverified claims list endpoint; (2) bulk claim review; (3) unified editor dashboard;
  (4) resolution history viewer. KHÔNG tạo `CURATION_WORKFLOW_SPEC.md` (trùng các file đã có).
- **QA/Compliance (Khảo khóa) = task T113 (ráspec 2026-09-09):** bộ đo `scripts/verify_design_compliance.py`
  + `data/design_compliance.json` (9 metric M7.2, read-only) + dashboard Data Quality + UAT 3 persona
  (Phần A QA live) đã xây xong. Claim reviewed = 0% (fail thật) — vòng khép: **T119** nâng metric sau
  khi T113 đóng alert #4/#5. Citation: BibTeX có trong `dtCopyCite` (tối giản), **CSL-JSON CHƯA có** +
  Audit ID chưa public → cả 2 thuộc **T118** (Research Audit Tier, mở rộng 2026-09-09).
  KHÔNG tạo `QA_COMPLIANCE_SPEC.md` (A2: SSOT = SCHEMA_DESIGN M7.2).
- **Web Enrichment vào DILA = task T121 (ráspec4 2026-09-09; T120 "Unified Lookup" cùng đặc tả do tiến
  trình song song tạo — T121 BỔ TRỢ):** đặc tả "auto-fetch Wikipedia/Wikidata" đối chiếu → ~90% infra
  ĐÃ CÓ (`web_enrichment_cache` 1 row · `place_wiki_snapshots` · `/daoanh/api/admin/wiki/fetch` ·
  `/entity/<id>/web-enrich*` · `geo_cross_ref` 181 QID bridge · `places_dila` 58,480 tọa độ · Leaflet
  `placevn.html` · `/places/unified`). SỬA lỗi logic đặc tả: example PL…053 "Na Ha Lê Thành"→Q1997494
  Jalalabad **tự gộp = vi phạm T109 Zero-Loss** → chỉ sinh candidate, admin Approve/Reject, merge
  `owl:sameAs`. Delta thật (T121) = Wikidata P625+P2044 elevation (additive `geo_cross_ref`) · admin
  enrich-queue (pattern bio-review) · cron `enrich_places.py` candidate-only. **KHÔNG tạo bảng
  `places_enriched`/`external_refs` (SSOT).**
- **Quản trị Tri thức & Đào tạo = phân mảnh (ráspec5 2026-09-09 — đặc tả nhầm header "T118"):**
  Academic Scaffolding = **T111** (DONE) · tách Canonical/Draft = **T100/T108** (kiến trúc) ·
  Learning Path + Curation Registry/Knowledge Packages = **T59** spec-holder (+**T119** editor đóng gói)
  · **Feedback Loop = T112 D-Feedback** (`data_gap_requests` additive: NOT INDEXED → yêu cầu bổ sung →
  admin report → ưu tiên 8 nguồn). KHÔNG tạo `KNOWLEDGE_MGMT_SPEC.md`/`PROJECT_STATUS.md` (A2).
- **Deployment/Ops = T116 spec-holder (ráspec6 2026-09-09 — đặc tả nhầm header "T119"):**
  Live Monitoring (query_log) = **T112 D-Feedback** (không bảng trùng) · maintenance cadence
  (`verify_design_compliance.py` = **T113**, đặc tả ghi "T117" SAI) · System Hardening = server.py
  :5001 + login/check + `deploy/nginx.conf` (public read-only không auth — chính sách giữ) ·
  Beta/Data Freeze/Disaster Recovery + **Daily Database Snapshot** backup = **T116 D-Ops** ·
  Support Feedback Inbox (`user_feedback` + `POST /api/feedback`) = **T119 Gap 5**.
  KHÔNG tạo `DEPLOYMENT_SPEC.md`/`PROJECT_STATUS.md` (A2).
- **Build Batch A+B (2026-09-10, Lee phê chuẩn — reverte:** mỗi đợt commit: `git revert --no-edit <A-hash>`):
  T116 → **DONE** + D-Ops O1 (`scripts/daily_backup.py` + `docs/OPS_LOG.md`, verified) · T112 §5 phê duyệt
  + D-Feedback IMPLEMENTED (`data_gap_requests` + hook + `/api/admin/data-gaps`) · T119 IMPLEMENTED
  (`admin/editor-dashboard.html` + claims/bulk-review/resolutions/feedback/editor-stats) · T118 đợt 1
  (audit/trail + citation csl-json|bibtex) · T121 candidate-only (`geo-enrich*` + `enrich_places.py`).
  T113 GIỮ in_progress (QA metric chờ claims_reviewed>0 qua T119); Batch C (BUG-012/014, T101) đồng bộ
  agent ngoài, chưa đụng file tiến trình song song.
- **Build Batch D (2026-09-10, Lee phê chuẩn — reverte:** mỗi đợt commit, xem ROLLBACK §2):
  T118 đợt 2 (`audit_id` xuyên export csl-json|bibtex + `signature` sha256 evidence) · T73 tab Bio Review
  (`/api/admin/bio-review/*` + editor-dashboard, apply → `people.bio_vi` HITL 2 bước) · T121 runfront
  (9 candidate ghi, timeout mạng — cron tiếp) · docs hygiene (BUG-009 CLOSED-as-duplicate ≡ marker-icons;
  stub T51→T53 / T52-analytics→T54 move `tasks/backup/`; task T122 driver mới).
- **Build Batch E1 (2026-09-10, Lee phê chuẩn — reverte:** `git revert --no-edit 3c50ec50`):
  **T112 → DONE** (Lee duyệt §5 8 nguồn) → dependency T120 cleared · **T120 Phase C IMPLEMENTED**
  (`GET /api/v1/entity/<id>/lookup`, 5-layer reuse tables — read-only, 0 bảng mới; smoke 4 case PASS) ·
  mới `docs/ADMIN_REVIEW_DASHBOARD.md` (17 items cần admin confirm). Chờ Lee xác nhận → đóng T120/T122.

---
*Registry v1.0 — phê duyệt kèm task T116 (`tasks/T116-system-registry-handover.md`).*