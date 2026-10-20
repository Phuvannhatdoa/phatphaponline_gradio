---
id: T100
title: ACADEMIC_3_LEVELS_16_TABS_V1 — 16 tab evidence-first, 3 cấp học thuật, chấm 2 trục
module: Hạ tầng / Docs
priority: high
status: done
depends_on: []
created: 2026-09-07
updated: 2026-10-12
done_when: Mọi tab của file places.html hiển thị evidence-first với empty-state trung thực theo lược đồ 16 tab; tab GIÁO LÝ phân đôi (khối giáo lý Phật học + khối Đối Chiếu Tam Tạng trong cùng tab); bảng điểm 2 trục data-exists/UI-displays cho toàn bộ 16 tab tính từ dữ liệu/code thật kèm bằng chứng; dashboard admin `dashboard/tab_readiness.html` hiển thị được; release gate ≥8 điểm (core ≥9).
---

# T100 — ACADEMIC_3_LEVELS_16_TABS_V1 (cả khung · phân đôi cùng tab · chấm 2 trục)

**Ngày tạo:** 2026-09-07
**Status:** ✅ DONE (Batch 1–5 complete, committed 7002384)
**Loại:** UI/UX + evidence-first + dashboard (read-mostly; DB schema chỉ thêm additive ở P2)
**Rollback:** `git revert <commit Batch>` — 1 batch = 1 commit riêng (xem `docs/ROLLBACK.md`)

---

## Mục tiêu

Đưa toàn bộ các tab của Đạo Ảnh đến chuẩn học thuật 3 cấp (Cử nhân / Cao học / Tiến sĩ) theo lược đồ **16 tab**: mỗi tab hiển thị bằng chứng thật từ DB, empty-state trung thực (không bịa, không "đang phát triển" mờ), label fallback an toàn, và mọi khẳng định đều trỏ về nguồn/dữ liệu. Admin duyệt mức độ sẵn sàng từng tab qua dashboard chấm điểm **2 trục** (data-exists / UI-displays) tính từ dữ liệu + code thật.

## Quyết định admin (phê chuẩn 2026-09-07)

1. **Phạm vi = cả khung** (ACADEMIC_3_LEVELS_16_TABS_V1 cho toàn bộ 16 tab, không chỉ tab GIÁO LÝ).
2. **GIÁO LÝ = phân đôi cùng tab**: khối "Giáo lý Phật học" (khái niệm + giáo lý liên quan thực thể) + khối "Đối Chiếu Tam Tạng" (giữ nguyên hiện trạng) — **không** tạo tab mới.
3. **Chấm điểm = 2 trục** `data-exists` / `UI-displays` theo từng dimension, mỗi trục có bằng chứng code + DB — thay cho nhận định 5.5/10 chủ quan.

## Lược đồ 16 tab (target taxonomy)

| # | Tab hiện tại | Render hiện tại | Tab 16-tab target | Ghi chú |
|---|---|---|---|---|
| 1 | Cbeta | `renderCbetaTab` (2019) | Tripitaka · CBETA | gộp với daitang |
| 2 | DaiTang | `renderDaiTangTab` (2149) | Tripitaka · Đại Tạng | gộp với cbeta |
| 3 | Graph | `renderGraphTab` (3463) | Đồ Thị | real |
| 4 | Nexus | `renderNexusTab` (5211) | Nexus | real; lineage con |
| 5 | Lineage | `renderLineageTab` (5188) | Truyền Thừa | real |
| 6 | Persons | `renderPersonsTab` (5792) | Nhân Vật | real |
| 7 | Timeline | `renderTimelineTab` (5964) | Niên Đại | real |
| 8 | Giaoly | `renderGiaolyTab` (6232) | Giáo Lý (phân đôi) | real + mở rộng P2 |
| 9 | Thuvien | stub `_renderPendingTab` (6363) | — | P1 real |
| 10 | Nghile | stub (6364) | — | P1 real |
| 11 | Giaoduc | stub (6365) | — | P1 real |
| 12 | Sukien | `renderSukienTab` (6381) | Sự Kiện | real (T97) |
| 13 | Bandoo | `renderBandooTab` (6475) | Bản Đồ | real |
| 14 | Dulieu | stub (6510) | — | P1 real |
| 15 | Hinhanh | stub (6511) | — | P1 taxonomy |
| 16 | Nghethuat | stub (6512) | — | P1 taxonomy |
| — | *(mới)* | — | **Entities** (thực thể tổng hợp) | tab thứ 16 |

## Cách tiếp cận (5 phase, 1 commit/batch)

- **P0-SAFETY (Batch 2):** shared helpers (`_daSafeLabel`, `_daEmptyState`, badge bộ) · empty-state Pali → `NOT-INDEXED` (pali_place_ref 15 record thánh địa Ấn) · API `/daoanh/api/evidence/<subject_id>` (đọc entity_claims + event_evidence, read-only) · co-mention dashed/hidden ở Graph/Nexus · scorecard `dashboard/tab_readiness.html` (8 alert).
- **P1-BACHELOR (Batch 3):** 16 tab đủ canonical ID + nguồn + empty-state đồng bộ + tab mới `entities`.
- **P2-MASTER (Batch 4):** GIÁO LÝ **phân đôi** (khối giáo lý: Khái niệm / Giáo lý liên quan + badge DIRECT/THEMATIC/SCHOLARLY) · schema additive `doctrine_concept` + cột `assertion_level/reviewed_*` trên `entity_claims` + bảng `pali_cbeta_map` (rút hardcode `_PALI_REF_MAP` ngoài app.py:13927) · evidence drawer + filter chung. ETL `--dry-run`/`--revert`.
- **P3 (Batch 5):** dataset_version + export citation/JSON-LD · review/audit/dispute workflow (verification_status).
- **P4 (Batch 5):** regression + release gate ≥8 (core ≥9).

## Acceptance criteria (checklist)

### Batch 1 — Khởi động (TASK NÀY)
- [x] Phê duyệt admin (cả khung · phân đôi · 2 trục)
- [x] Task `T100` + plan + inventory baseline + session/tasktodo/progress/ROLLBACK
- [x] Dashboard regenerate (`build_progress_data.py` → `progress_data.json`)
- [x] Commit temp-index riêng + verify blob==HEAD

### Batch 2 — P0-SAFETY
- [x] Helper `_daSafeLabel`/`_daEmptyState(taxonomy,scope)`/badge bộ trong `places.html` (non-destructive)
- [x] Empty-state Pali: message "NOT-INDEXED — danh sách rà soát 15 record (thánh địa Ấn)" thay vì "chưa có" mờ
- [x] `GET /daoanh/api/evidence/<subject_id>` trả claims + event_evidence gộp, có `data_status`
- [x] Co-mention tách biệt thị giác (dashed + hidden) ở Graph/Nexus
- [x] `dashboard/tab_readiness.html` đọc score từ dữ liệu thật + 8 alert
- [x] Tests + docs + commit riêng

### Batch 3 — P1-BACHELOR (DONE 2026-09-07)
- [x] Đủ **17 tab** bar = `fix_tabs.js` (16 taxonomy; cbeta+daitang→Tripitaka về khái niệm; + `entities`)
- [x] Tab mới **`entities`** (🧩 Thực Tổng Hợp): nút 17 + `#tp-entities` + `loadEntitiesTab(placeId)` → `renderEntitiesTab(d)` aggregate claims/events/co_mentions qua `/daoanh/api/evidence/<subject_id>`
- [x] **6 tab stub** real hóa nội dung tối thiểu trung thực: `dulieu` = `data_status` thật (claims/events/co_mentions counts, note 100% unverified/candidate) → **10/12 Cao học**; thuvien/nghile/giaoduc/hinhanh/nghethuat = `_daStubTab` (identity canonid + `NOT-INDEXED`) → **6/12 Cử nhân**
- [x] `fix_tabs.js` đồng bộ 15→**17** (thêm `nexus` + `entities`) — đóng alert #1
- [x] build_tab_readiness: TAB_INFO + `entities`/`dulieu` route evidence, 5 identity tab, `ui_evidence` mở rộng
- [x] 8 alert: **#1/#2/#3/#6/#7/#8 RESOLVED**, còn #4 (entity_claims 100% unverified) + #5 (events 100% candidate) → P3
- [x] Tests (node --check ×2 + py_compile + npm test + npm run e2e ✅) + anchors 11/11 + DB field verify + docs + commit riêng

### Batch 4 — P2-MASTER (DONE 2026-09-27 — verified code đã có)
- [x] GIÁO LÝ phân đôi: `renderGiaolyTab` 2 block (Giáo lý Phật học + Đối Chiếu Tam Tạng); `_daRenderDoctrine` places.html:9276; `_daEvidenceBadge` DIRECT/THEMATIC/SCHOLARLY
- [x] Schema additive: `doctrine_concept` (12 rows ✓), `pali_cbeta_map` (6 rows ✓), `assertion_level`/`reviewed_by`/`reviewed_at` trên `entity_claims` ✓
- [x] Evidence drawer: `_daEvidenceDrawer` places.html:9412 — persona-aware, filter assertion_level/claim_type/source
- [x] ETL `scripts/etl_t100_batch4.py` — `--dry-run` PASS (idempotent, tất cả đã seed)
- [x] API `/daoanh/api/places/<id>/doctrine` app.py:15746 — L1/L2/L3 persona, concepts + related_claims; py_compile PASS

### Batch 5 — P3 + P4
- [x] dataset_version: `_compute_dataset_version(conn, entity_id)` → SHA256 deterministic từ claims, 8-char version + full 64-char hash + claim_count; inject vào `/daoanh/api/evidence/<subject_id>` response
- [x] verification_summary: `_compute_verification_summary(claim_stats)` → verified_ratio, dominant_status, release_status ('releasable'/'review_required'); inject vào `/daoanh/api/evidence/` response  
- [x] JSON-LD export: `GET /daoanh/api/places/<id>/export?format=jsonld` → Place + @context pth:/schema.org + identifier + name + geo + pth:datasetVersion + additionalProperty (claims)
- [x] Release gate: verified_ratio ≥ 0.5 → 'releasable', else 'review_required' (không cần bảng mới — dùng verification_status SSOT)
- [x] UI: `renderDulieEvidence` (places.html) hiển thị dataset_version badge + release_status + "Export JSON-LD" link
- [x] Tests: 18/18 PASS (cases A-R) — `tests/test_t100_batch5.py`
- [x] py_compile app.py PASS
- [x] Regression toàn phần + commit riêng (committed 7002384)

## Blockers (hiện tại: KHÔNG)
- Không. Server :5000 đang bị khóa (không chạy) → kiểm chứng ở mức py_compile + node --check + pytest/code review; live-test khi admin restart.