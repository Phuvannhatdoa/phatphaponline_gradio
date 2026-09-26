---
id: T131
title: B2.1 REFINE: Source Governance + Compliance Gate + Extensible Adapter
priority: high
status: done
owner: AI Engineer (build) · Lee Tổng (phê chuẩn)
module: Governance
created: 2026-09-14
updated: 2026-09-18
---
# T131 — B2.1 REFINE: Source Governance + Compliance Gate + Extensible Adapter (map-lên-hệ-có-sẵn)

---

## 1. Context (AO — đã audit thật 2026-09-14)

Spec "B2.1 SOURCE GOVERNANCE + LICENSE COMPLIANCE GATE + EXTENSIBLE SOURCE ADAPTER CORE" được admin gửi để verify.
**Kết quả audit: spec KHÔNG khớp logic hiện tại (~70% đã tồn tại sẵn ở Build 3 T77/T78/T82); implement literal sẽ TRÙNG LẶP + XUNG ĐỘT vocabulary/table.** Được admin phê chuẩn chuyển thành task "refine" có kiến: **additive, 0 destructive, 0 rewrite** (tuân thủ §4 "reuse existing equivalent fields thay vì duplicate").

### Facts audit (đã verify thật)
- **`data_sources` = Source Registry thật** (13 dòng, 40+ cột governance): software/data/corpus/image license, license_url, redistribution/commercial/derivative flags, license_verified(0 hết)/license_verified_at/by, terms_status, version_policy, legal_status, data_license_status, integration_mode, legal_status_at_ingest… → đã cover gần hết target §4. **KHÔNG mở rộng `dataset_sources`** (legacy metadata 10 dòng/8 cột) để tránh 2 registry song song.
- **`gate/` package (T78, commit 389f99b, đã track+commit):** `status.py` LegalStatus máy trạng thái (DISCOVERED→AUDITING→VERIFIED→APPROVED→ACTIVE + UNKNOWN/REFERENCE_ONLY/BLOCKED/FROZEN, KHÔNG default=ACTIVE); `license.py` LicenseGate.checkSourcePermission → {allowed,status,reason,license,source_id,checked_at}, deterministic, rule-based, tách SOFTWARE vs CORPUS; `provenance.py` ProvenanceGate (bắt buộc source_id/source_uri/source_version/retrieved_at/content_hash/license_status/transformation/evidence_type, chặn "latest" làm pin); `analyzer.py` phân tích repo public.
- **`adapters/` package (T77):** base.py `SourceAdapter` (search/resolve/get_provenance/normalize/health_check/describe) + `ExtractedEvidence` (source_code/claim_type/subject/predicate/object_text/source_record_id/source_reference/source_url/retrieved_at/confidence/extra); `registry.py` SourceAdapterRegistry (data-driven từ data_sources, dispatch có license-gate firewall, source chưa đăng ký → UNKNOWN chặn); `bdrc/` adapter skeleton. Đều tracked+commit.
- **Endpoints §14 ĐỦ:** places_pending L2070, ai_judge L2186 (trả provenance + source_name/license/usage_level: Marcus→CC0/GREEN, DILA→CC BY-SA 4.0/YELLOW), translate_location L7567, namevi-map-places/save L8937, public/transliterate L9740, public/search L9859.
- **Frontend badge ✓:** places.html licenseBlock (source/license/note từ cbeta_catalog_vn.text_info), admin/source_check.html (UI thêm nguồn → AUDITING not-auto-ACTIVE), placevn.html T67 provenance editor.
- **Tests:** `tests/test_license_firewall.py` (16 test, DB temp) + `tests/test_real_data_license.py` (6 test, DB-copy thật). **NHƯNG `npm test` = node placeholder (2 dòng) — pytest governance KHÔNG chạy trong pipeline.** `npm run pipeline` = lint+test+e2e+e2e:runtime (e2e:runtime pre-known EPERM trên máy này; lint ESM warning pre-existing).

### Các GAP thật (chỉ làm 5 điều này)
1. **Gate thiếu operation theo spec:** CONTENT_READ, DERIVED_DATA, EXPORT, METADATA_READ (hiện: READ_METADATA/DOWNLOAD/STORE_RAW/TRANSFORM/DERIVE/INGEST/REDISTRIBUTE/COMMERCIAL_USE). Result thiếu `usage_level` + `restrictions[]`.
2. **Registry mới có 13/25** nguồn spec §9; thiếu 13: DDBC, VRI/Tipitaka, THL, Treasury of Lives, BuddhaNexus, PTS, IDP, GRETIL, DSBC, OCBS, BGIS, MITRA/DharmaMitra, READ(Gandhāran). Cả 13 hiện hành `license_verified=0` → theo §5 tự động REVIEW_REQUIRED (chặn ingest).
3. **Adapter core thiếu method:** get_metadata/get_entity/get_evidence/get_source_version (spec §7).
4. **Tests spec §13 A–L chưa đủ + governance tests chưa vào pipeline.**
5. (duy trì) data_sources.usage_level không có cột — bổ sung additive view/column cho spec §5 vocabulary (GREEN/YELLOW/RED/REVIEW_REQUIRED).

## 2. Pha thiết kế (additive — thứ tự)

### Pha 1 — Registry inventory 13→26 (spec §9)
- Script `scripts/build_t131_register_sources.py` (idempotent, chạy lại an toàn): INSERT OR IGNORE 13 dòng missing trong `data_sources` (source_code, source_name, source_type, authority_scope, legal_status='UNKNOWN', data_license_status='UNKNOWN'/'AUDITING' theo mức tin, integration_mode='BLOCKED', license_verified=0, license_url=NULL, capability '[]', active=1, enabled=1 — **KHÔNG bịa license**).
- Mọi nguồn chưa verify → REVIEW_REQUIRED theo gate (chặn ALL ingest, chỉ metadata/reference).
- KHÔNG đụng 13 dòng legacy; chỉ thêm dòng mới. Đếm trước/sau ghi vào log.

### Pha 2 — Gate operation aliases + usage_level/restrictions (spec §6, §5)
- `gate/license.py`: thêm vào OPERATIONS: `METADATA_READ`, `CONTENT_READ`, `CONTENT_STORE`, `DERIVED_DATA`, `EXPORT` (additive alias).
  - Quyết định rule: METADATA_READ ≡ READ_METADATA; CONTENT_READ ≡ STORE_RAW/READ_METADATA (quyền content so với raw store); CONTENT_STORE ≡ STORE_RAW; DERIVED_DATA ≡ DERIVE; EXPORT ≡ REDISTRIBUTE. (Thực hiện qua mapping `_OP_ALIASES`, KHÔNG đổi các op cũ.)
- Add `usage_level` (GREEN/YELLOW/RED/REVIEW_REQUIRED) + `restrictions[]` vào dict trả về — **derived deterministic từ legal_status/data_license_status/integration_mode**:
  - REVIEW_REQUIRED = legal_status in {UNKNOWN, AUDITING, DISCOVERED} hoặc license_verified=0;
  - GREEN = legal_status=ACTIVE + data_license_status in {APPROVED,ACTIVE} + license_verified=1;
  - YELLOW = REFERENCE_ONLY (metadata/reference OK, raw blocked);
  - RED = BLOCKED/FROZEN.
- KHÔNG thay cột/giá trị DB; chỉ hàm. Backward-compatible (thêm key, không bỏ key cũ).
- Frontend `admin/source_check.html` + `places.html delay` — overload tối thiểu, chỉ *đọc*. KHÔNG sửa UI layout (spec §15).

### Pha 3 — Adapter core methods (spec §7)
- `adapters/base.py`: thêm `get_metadata(record_id)`, `get_entity(record_id)`, `get_evidence(record_id)`, `get_source_version()` với **default fallback** gọi search/resolve (KHÔNG phá các adapter hiện có); ghi rõ tính "capability-based" (adapter có thể override).
- Registry dispatch giữ nguyên; evaluate qua test J.

### Pha 4 — Tests spec §13 A–L + pipeline (spec §13, §16)
- `tests/test_b21_governance.py` (chạy trên **bản copy DB thật** — không đụng data/lineage.db):
  - A: DILA source (data_sources id=1, dataset_sources DILA_Authority) readable.
  - B: Marcus_fojin readable.
  - C: GREEN source (usage_level=GREEN + license_verified → ACTIVE) cho phép op được declared.
  - D: YELLOW/REFERENCE_ONLY cho metadata nhưng chặn CONTENT_STORE/INGEST.
  - E: RED/BLOCKED chặn op bị cấm.
  - F: REVIEW_REQUIRED/UNKNOWN/AUDITING chặn INGEST.
  - G: ai_judge endpoint (gọi qua app test) backward compatible.
  - H: frontend places.html load OK (node --check) — E2E sẵn có.
  - I: DILA IDs (places_dila.id) byte-for-byte không đổi (snapshot hash trước/sau).
  - J: thêm source mới (temp DB) không đụng schema canonical (entity_hub/entity_claims).
  - K: third-party license không bị ghi đè (license_summary giữ riêng software/corpus).
  - L: mọi evidence mới (ProvenanceGate) phải đủ provenance fields.
- package.json: thêm `"test:gov": "python -m pytest tests/test_b21_governance.py tests/test_license_firewall.py tests/test_real_data_license.py -q"` và gắn vào `pipeline` chuỗi.

### Pha 5 — Backups + backup thủ tục + docs + dashboard
- Snapshot trước khi đổi: `[System.IO.File]::Copy` app.py/places.html → `docs/sessions/*.bak-t131-...` ; DB: `data/lineage_backup_t131.db` (git-ignored như các backup khác).
- Session doc `docs/sessions/2026-09-14_t131-b21-source-governance-refine.md`; cập nhật tasktodo; `python -X utf8 scripts/build_progress_data.py` regen dashboard.
- Chỉ commit qua temp-index `%TEMP%\opencode\b4_commit.py` khi user yêu cầu (real git index đang có staged deletions external — không đụng).

## 3. Non-goals (KHÔNG làm — bảo vệ Build1)
- KHÔNG mở rộng/đổi `dataset_sources` (reuse `data_sources`).
- KHÔNG sửa ai_judge / namevi-map-places / translate_location / public endpoints / placevn.html / places.html layout / DILA IDs / đồng canonical.
- KHÔNG destructive migration (0 ALTER drop, 0 DELETE), KHÔNG mock/fake data, KHÔNG assign license từ "public GitHub".
- KHÔNG default ACTIVE; mọi nguồn mới = BLOCKED/chưa verify.

## 4. Acceptance (map spec §19 → hiện trạng + task)
- A ✓ hiện trạng, giữ nguyên; B ✓ (giữ DILA IDs); C ✓ data_sources giữ nguyên (chỉ thêm dòng mới); D ✓ registry extensible (T77 + Pha 1), E ✓ gate deterministic (T78 + Pha 2), F ✓ UNKNOWN/AUDITING chặn INGEST (đã đúng + test F); G ✓ CHỈ sau Pha 2 (usage_level derived); H ✓ raw-block + metadata-ok (REFERENCE_ONLY + test D); I ✓ ProvenanceGate + test L; J ✓ endpoints nguyên vẹn (test G/regression); K ✓ frontend giữ (H); L ✓ pipeline PASS (chạy pipeline; e2e:runtime EPERM pre-existing ghi nhận); M ✓ new source 21+ không đụng schema canonical (test J); N ✓ không ghi đè license (test K); O ✓ 0 destructive; P ✓ no mock; Q ✓ license_verified + license_url cho nguồn verify (hiện tất cả chưa verify → REVIEW_REQUIRED — đúng).

## 5. Risks
- Database-copy tests nặng nếu DB lớn → dùng copy temp + sample.
- pytest có thể chưa cài trong npm env → kiểm tra `python -m pytest` sẵn; nếu thiếu, test:gov dùng unittest-compatible runner.
- e2e:runtime EPERM pre-existing → báo trong report, không phá pipeline.

## 6. Rollback
- Scripts đều idempotent (INSERT OR IGNORE); gate/adapter file đổi additive; revert từ backup t131 nếu cần. Không dữ liệu bị xóa.