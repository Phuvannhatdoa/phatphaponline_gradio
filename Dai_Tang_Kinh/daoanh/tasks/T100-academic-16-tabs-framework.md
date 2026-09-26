---
id: T100
title: ACADEMIC_3_LEVELS_16_TABS_V1 — 16 tab evidence-first, 3 cấp học thuật, chấm 2 trục
module: Hạ tầng / Docs
priority: high
status: in_progress
depends_on: []
created: 2026-09-07
updated: 2026-09-07
done_when: Mọi tab của file places.html hiển thị evidence-first với empty-state trung thực theo lược đồ 16 tab; tab GIÁO LÝ phân đôi (khối giáo lý Phật học + khối Đối Chiếu Tam Tạng trong cùng tab); bảng điểm 2 trục data-exists/UI-displays cho toàn bộ 16 tab tính từ dữ liệu/code thật kèm bằng chứng; dashboard admin `dashboard/tab_readiness.html` hiển thị được; release gate ≥8 điểm (core ≥9).
---

# T100 — ACADEMIC_3_LEVELS_16_TABS_V1 (cả khung · phân đôi cùng tab · chấm 2 trục)

**Ngày tạo:** 2026-09-07
**Status:** ⏳ In progress (Batch 1 + **Batch 2 P0-SAFETY DONE** 1d8770da + **Batch 3 P1-BACHELOR DONE** 2026-09-07)
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

### Batch 4 — P2-MASTER
- [ ] GIÁO LÝ phân đôi: khối giáo lý (Khái niệm giáo lý / Giáo lý liên quan thực thể) + khối Đối Chiếu Tam Tạng giữ nguyên + badge DIRECT/THEMATIC/SCHOLARLY
- [ ] Schema additive: `doctrine_concept` + cột `assertion_level`/`reviewed_*` trên `entity_claims` + bảng `pali_cbeta_map` (rút `_PALI_REF_MAP` app.py:13927)
- [ ] Evidence drawer + filter chung áp dụng toàn bộ tab
- [ ] ETL `--dry-run`/`--revert` + backup DB
- [ ] Tests + docs + commit riêng

### Batch 5 — P3 + P4
- [ ] dataset_version + export citation/JSON-LD
- [ ] Review/audit/dispute (verification_status policy — hiện 100% 'unverified')
- [ ] Regression toàn phần + release gate ≥8 (core ≥9)
- [ ] Tests + docs + commit riêng

## Blockers (hiện tại: KHÔNG)
- Không. Server :5000 đang bị khóa (không chạy) → kiểm chứng ở mức py_compile + node --check + pytest/code review; live-test khi admin restart.