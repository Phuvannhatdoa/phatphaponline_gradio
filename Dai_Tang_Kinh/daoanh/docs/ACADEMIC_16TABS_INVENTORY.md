# ACADEMIC_16TABS_INVENTORY — Kiểm kê baseline 15 tab (Task 0)

> Sinh 2026-09-07 bằng probe **code (places.html/app.py) + DB thật (data/lineage.db)**. Đây là dữ liệu gốc cho scorecard 2 trục của T100.
> Tất cả số row tái khẳng định bằng SQL trực tiếp trên `lineage.db` (read-only).

---

## 1. Bảng kiểm kê từng tab

| # | Tab | Render fn (places.html) | API nguồn (app.py) | Bảng nguồn | Evidence-visible | Empty-state | Label-fallback | Stub? |
|---|---|---|---|---|---|---|---|---|
| 1 | Cbeta | `renderCbetaTab:2019` | `/api/places/<id>/cbeta:4077` | cbeta_catalog_vn, canon_catalog, passage | ✅ | có (⚠ chưa dữ liệu) | — | ❌ |
| 2 | DaiTang | `renderDaiTangTab:2149` | `/api/entity/<id>/canon` + `/api/places/<id>` | passage (Lớp B), catalog_mapping, cbeta_catalog_vn | ✅ (Passage→text→vị trí) | ✅ trung thực (Việt 0 → thông báo) | — | ❌ |
| 3 | Graph | `renderGraphTab:3463` | `/api/places/<id>/graph:4364` + `/api/monk/<id>/graph:4579` | places_dila, entity_works, person_origin_link, place_person_bibl | ✅ (edg ref/citation tooltip) | ? | label/threshold guard | ❌ |
| 4 | Nexus | `renderNexusTab:5211` (con `renderLineageTab:5188`) | `/api/nexus/<entity_id>:5101` + `/api/nexus/find:4529` | event_text_link (17,284) + people/places_dila/marcus_reference | ✅ (evidence-only filter, quality badge) | ✅ (limit 200 notice) | ✅ `_nexusSafeLabel` (~5199) | ❌ |
| 5 | Lineage | `renderLineageTab:5188` (con cả Nexus) | `/api/monk/<id>/lineage-tree:4948` + `/api/lineage-ref/passage:5055` | marcus_networks, marcus_reference, lineage_conflicts_v2, people | ✅ (has_ref + "Cần khảo cứu") | ✅ empty state | ✅ | ❌ |
| 6 | Persons | `renderPersonsTab:5792` | `/api/places/<id>/persons:5433` + `/api/persons/browse:5707` + `/api/person/<id>/profile:5817` | people (48,673), place_person_bibl, person_origin_link | part | ✅ | ✅ | ❌ |
| 7 | Timeline | `renderTimelineTab:5964` | `/api/places/<id>/timeline:6126` + `/events:6239` + `/time-mentions:6402` | place_timeline_events (3,688), time_mentions, events | ✅ (evidence per event) | ✅ | ✅ | ❌ |
| 8 | Giaoly | `renderGiaolyTab:6232` | `/api/cbeta/compare:13940` + `/api/places/<id>/pali:13473` | passage, toh_cbeta_crossref, sat_crossref, pali_place_ref (15) | ✅ (5 tradition provenance) | ✅ (Pali empty state — cần sửa NOT-INDEXED) | ✅ | ❌ |
| 9 | Thuvien | `_renderPendingTab('thuvien'):6363` | — | — | ❌ | ❌ (⚠ đang phát triển) | — | ✅ |
| 10 | Nghile | `_renderPendingTab('nghile'):6364` | — | — | ❌ | ❌ | — | ✅ |
| 11 | Giaoduc | `_renderPendingTab('giaoduc'):6365` | — | — | ❌ | ❌ | — | ✅ |
| 12 | Sukien | `renderSukienTab:6381` | `/api/events:6323` + `/api/places/<id>/events:6239` | events/event_evidence/event_entities (3,530), event_text_link | ✅ | ✅ | ✅ | ❌ |
| 13 | Bandoo | `renderBandooTab:6475` | `chronology`/map layers | places_dila, chronology | part | ? | — | ❌ |
| 14 | Dulieu | `renderDulieTab`→stub:6510 | — | — | ❌ | ❌ | — | ✅ |
| 15 | Hinhanh | stub:6511 | — | — | ❌ | ❌ | — | ✅ |
| 16 | Nghethuat | stub:6512 | — | — | ❌ | ❌ | — | ✅ |

**Kết luận Task 0:** 9 tab real (cbeta/daitang/graph/nexus/lineage/persons/timeline/giaoly/sukien/bandoo = 10 thật); **6 tab stub** (thuvien, nghile, giaoduc, dulieu, hinhanh, nghethuat). Chưa có tab `entities`.

## 2. Số liệu DB thật (2026-09-07, `data/lineage.db`)

| Bảng | Rows | Ghi chú |
|---|---|---|
| entity_claims | 447,885 | subject/predicate/object_text/confidence/authority_role/verification_status; **100% 'unverified'** |
| events | 3,530 | review_status **100% 'candidate'**; precision pos; extraction_method |
| event_evidence | 3,530 | source_record, source_table, exact_span, source_ref, evidence_type |
| event_text_link | 17,284 | bridge cho Nexus |
| event_entities | 3,530 | liên kết event↔entity |
| glossary_term | 248,095 | term/definition/full_text/language |
| term_glossaries | 18,127 | term_vi/term_zh, source='marcus', confidence |
| pali_place_ref | 15 | toàn thánh địa Ấn (Bodh Gaya, Vườn Nai, Vương Xá Thành...), sc_uid, verified_by='ZQ', confidence 0.9–1.0, needs_review |
| marcus_networks | 11,169 | lineage edges + ref |
| marcus_reference | 18,127 | nien đại, label_vi |
| lineage_conflicts_v2 | 40,327 | conflicts |
| passage | 7,563 | kinh văn (Hán) |
| text_passages | 9,316 | T50n2060 units |
| place_person_bibl | 13,933 | place↔person evidence (bibl) |
| person_origin_link | 11,929 | origin |
| cbeta_place_mentions | 16,311 | co-mention place |
| place_timeline_events | 3,688 | timeline |
| time_mentions | 3,687 | time mentions |
| canon_catalog | 3,122 | canon |
| catalog_mapping | 6,564 | mapping |
| cbeta_catalog_vn | 3,122 | catalog tiếng Việt |
| toh_cbeta_crossref | 10 | Tạng→CBETA |
| sat_crossref | 2,913 | SAT→CBETA |
| kanripo_catalog | 101 | Kanripo |
| lexicon | 166,278 | Han-Việt lexicon |
| people | 48,673 | **name_vi = 100% filled** |
| places | 59,161 | places |
| places_dila | 59,167 | places_dila (Hán) |
| glossary... | — | — |

## 3. Scorecard 2 trục baseline (ước đoán từ code+DB — đúng bởi probe / "--" = cần verify P1)

> Chấm 0/1 per (dimension, axis). Baseline sơ bộ; bản chính thức điền trong `dashboard/tab_readiness.html`.

| Tab | D1 id | D2 nguồn | D3 bản văn | D4 quan hệ | D5 empty | D6 provenance | Σ |
|---|---|---|---|---|---|---|---|
| cbeta | 1/1 | 1/1 | 1/1 | 0/0 | 1/0 | 1/0 | 7 |
| daitang | 1/1 | 1/1 | 1/1 | 0/0 | 1/1 | 1/0 | 8 |
| graph | 1/1 | 1/1 | 0/0 | 1/1 | 0/0 | 1/0 | 6 |
| nexus | 1/1 | 1/1 | 0/0 | 1/1 | 1/1 | 1/1 | 9 |
| lineage | 1/1 | 1/1 | 1/1 | 1/1 | 1/0 | 1/0 | 9 |
| persons | 1/1 | 1/0 | 0/0 | 1/1 | 1/0 | 1/0 | 6 |
| timeline | 1/1 | 1/1 | 1/1 | 0/0 | 1/0 | 1/0 | 7 |
| giaoly | 1/1 | 1/1 | 1/1 | 0/0 | 1/0 | 1/0 | 7 |
| sukien | 1/1 | 1/1 | 1/1 | 1/1 | 1/0 | 1/0 | 9 |
| bandoo | 1/1 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 2 |
| thuvien | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0 (stub) |
| nghile | 0/0 | ... | | | | | 0 (stub) |
| giaoduc | 0/0 | | | | | | 0 (stub) |
| dulieu | 0/0 | | | | | | 0 (stub) |
| hinhanh | 0/0 | | | | | | 0 (stub) |
| nghethuat | 0/0 | | | | | | 0 (stub) |
| entities (mới) | — | | | | | | chưa tồn tại |

## 4. 8 alert đầu tiên (đã xác định bằng probe)

1. Label nút tab đang 15, taxonomy target 16 (thiếu `entities`).
2. 6 tab stub dùng empty-state "⚠ Chức năng đang phát triển" mờ (`_renderPendingTab:6162`).
3. Pali empty state ("chưa có kinh điển Pali tham chiếu trực tiếp") — thực tế là **NOT-INDEXED**: chỉ 15 record thánh địa Ấn được index (`pali_place_ref`); Thiếu Lâm Tự = 0 ⊆ scope trống.
4. `entity_claims.verification_status` = **100% 'unverified'** — chưa có review workflow (P3).
5. `events.review_status` = **100% 'candidate'** — chưa có duyệt.
6. Tab `bandoo` và `persons` chưa lộ provenance từng hàng đầy đủ (chấm thấp mục nguồn).
7. Co-mention (dashed) chưa được tách biệt thị giác rõ ở Graph/Nexus (chỉ Nexus có evidence filter).
8. Grade hiện tại: core 9 tab Σ trung bình ~7–8/12 — dưới gate cao học.

## 5. Định nghĩa "NOT-INDEXED" (chính sách empty state)

Khi scope hiện tại không nằm trong danh sách đã kiểm kê/index: hiển thị rõ
`NOT-INDEXED — danh sách rà soát N record (tên bảng/tag, ngày cập nhật)` thay vì "chưa có". Dữ liệu là tồn tại nhưng chưa index cho scope này — trung thực về phạm vi index, không phán "không có".