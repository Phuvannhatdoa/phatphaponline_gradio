# Session — 2026-09-08 · T109 Provenance Compliance & Conflict Workflow

**Kiểu phiên:** Build — code + DB (additive Zero-ALTER). **T109** (bản vẽ đã duyệt T108; điều lệnh check07; phương án C đã Lee Tổng phê chuẩn).
**Trạng thái:** Done — đã build hoàn chỉnh (ETL applied + endpoints + UI + pipeline PASSED).
**Commit:** đã ghi trong ROLLBACK §1.

## 3b. Kết quả build (verification 2026-09-08)
- **ETL `--dry-run`**: events=3,530 · match places_dila=3,530 (**100.0%**) · entity_claims=447,885 → audit_id dự kiến. Base không đổi.
- **ETL `--apply`** (backup `lineage_t109_20260908_163506.db` 1.31 GB): entity_claims_audit **447,885** (audit_id NULL/empty = **0**) · events_provenance **3,530/3,530** (thiếu = 0) · views v_assertions + v_events_full ✓.
- **Idempotent**: chạy lại `--apply` → audit_id giữ nguyên, count không đổi (INSERT OR REPLACE on SHA-256 content-hash).
- **Revert**: `--revert` DROP 2 view + 2 bảng dẫn xuất, **base không đổi** (entity_claims=447,885 · events=3,530) → apply lại khôi phục. Rollback tiện lợi chứng minh được.
- **API offline (app.app_context + mock request)**: 
  - `GET lineage-conflicts` → status ok, count=5, total_open=**40,321**.
  - `POST resolve`(conflict id=1, winner=dila) → audit `en_audit_log` log_id=(6) action=`resolve_lineage_conflict` verification=`verified`, conflict→resolved=1; **revert trạng thái DB thủ công OK**.
  - `POST claim/1/review`(verified/high) → audit `claim_review`, `audit_id` trả về; **revert OK**.
- **Pipeline**: `npm run pipeline` → lint PASSED · test PASSED · e2e (placevn/index/dashboard) PASSED; e2e:runtime playwright EPERM volume **pre-existing** (không liên quan T109).
- Log audit test state được revert sạch (13 → 3 log như ban đầu); mang tính minh chứng idempotent + rollback.

## 1. Quyết định phê chuẩn (trước khi build)
- check07 (điều lệnh vận hành T108) chỉ tiếp nhận **main ideas**: KHÔNG DROP/ALTER bảng base · Adapter = SQL View · Source_id bắt buộc · NOT-INDEXED trung thực · ERD trình Admin trước code · **Chất lượng > tốc độ**.
- BỎ: filename `PROJECT_STATUS.md` (không tồn tại — dùng tasktodo/progress/dashboard) · "set T108 Doing" (T108 đã done).
- Lean Data audit (yêu cầu Cố vấn): ERD chỉ 10 bảng; phát hiện **bảng ma `cbeta_text_catalog`** (không tồn tại) → gỡ; **`text_passages` "~115k" SAI → 9,316**; **`dataset_sources` legacy → demote** (chỉ `data_sources` + `source_authority` trong v2 Schema). Không "ôm bảng rác".
- Phương án C (tối ưu): **Zero-ALTER** — mọi thứ mới = bảng dẫn xuất + SQL View; conflicts review dùng `en_audit_log` (bảng ĐÃ CÓ — không tạo `conflicts_review`).

## 2. Khảo sát verified (read-only, 2026-09-08)
- `events` (3,530, event_type duy nhất 'founding', extraction_method='imported', review_status='candidate'): **100% event place id = `places_dila.id`** (JOIN `SUBSTR(event_id,13)`) → backfill events_provenance toàn bộ, nguồn DILA.
- `places_dila` (59,167): có `note` (17,085 non-empty) + `listbibl` (6,390) → source_citation khả dụng.
- `entity_claims` (447,885): cols `claim_id`(PK int) · `entity_id`(= hub int, vd 100001) · `source_id`(0 NULL) · `predicate`/`object_text` · `claim_type`(6) · `assertion_level`/`reviewed_by`/`reviewed_at` (T100, NULL 100%).
- `en_audit_log` tồn tại (3 rows): `log_id, entity_ref, action, field_name, old_value, new_value, evidence_sources, authority_rank, editor, verification_status, created_at` → dùng làm nhật ký conflict review (Lean).
- `lineage_conflicts_v2` (40,327): có `resolved` (int) + `notes` — **KHÔNG** có `reviewed_by`/`reviewed_at` → không ALTER; verdict ghi `en_audit_log` + `resolved=1`.
- Route cũ `/api/conflicts` + `/api/resolve_conflict` ĐÃ TỒN TẠI (app.py) — T109 **kế thừa, không sửa** (Code Preservation); thêm endpoint `/daoanh/admin/*` mới.

## 3. Deliverables
- `scripts/etl_t109_provenance.py` — `--dry-run/--apply/--revert` + backup; tạo bảng dẫn xuất `entity_claims_audit`, `events_provenance` + View `v_assertions`, `v_events_full`; Zero-RAM (generator/chunk); idempotent (INSERT OR REPLACE).
- app.py: `GET /daoanh/api/admin/lineage-conflicts` · `POST /daoanh/api/admin/lineage-conflicts/<id>/resolve` · `POST /daoanh/api/admin/claims/<claim_id>/review`.
- `admin/conflicts.html` — UI nhẹ (fetch, addEventListener, không inline handler).
- Docs: SCHEMA_DESIGN (ERD fix cbeta_text_catalog/text_passages 9,316/dataset_sources demote/Adapter-view) · tasks/T109 (scope Zero-ALTER) · tasktodo/progress/roadmap · session này.

## 4. Sự cố môi trường
- ID resolution của `events` ↔ `places_dila`: event_id `ev:founding:PL…` → SUBSTR(13) khớp `places_dila.id` (PL…15 ký tự). entity_claims.entity_id là hub int (100001) — KHÁC không gian id events/places → backfill events KHÔNG dùng claims, dùng places_dila trực tiếp.
- Nhắc lại mọi commit qua temp-index (`b4_commit.py`); verify blob bằng `git hash-object` (CRLF/LF) chứ không sha1 raw.
- Port :5000 blocked → verify hoàn toàn offline (gọi hàm trực tiếp / import module).

## 5. Tiếp theo
- T109 review: Lee Tổng dùng `admin/conflicts.html` giải quyết conflict → `en_audit_log` accumulate; verify `npm run pipeline` PASS; compliance chạy ở T113 (7 metrics M7.2).
- T110 → T111 → T112 → T113 → T114.