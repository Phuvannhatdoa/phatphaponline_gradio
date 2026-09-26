# ACADEMIC_16TABS_IMPLEMENTATION_PLAN — Kế hoạch chi tiết (đã phê chuẩn)

> **Trạng thái:** ✅ PHÊ CHUẨN 2026-09-07 (admin duyệt "cả khung · phân đôi cùng tab · chấm 2 trục").
> Task: `tasks/T100-academic-16-tabs-framework.md` · Baseline: `docs/ACADEMIC_16TABS_INVENTORY.md` · Session: `docs/sessions/2026-09-07_academic_16tabs_plan.md`

---

## 1. Bối cảnh

Đạo Ảnh mở lướt 15 tab nhưng nhiều tab là stub ("⚠ Chức năng đang phát triển"), empty-state mơ hồ, một số nội dung hiển thị thiếu nguồn (provenance). Mục tiêu dài hạn là hệ tra cứu **học thuật 3 cấp** cho tăng ni Phật tử:
- **Cử nhân:** đọc được, dễ hiểu, không sai lệch.
- **Cao học:** truy được nguồn, đối chiếu được, hiểu sai lệch giữa truyền thống.
- **Tiến sĩ:** mọi khẳng định trỏ về bản văn/DB, tái lập được, kiểm toán được.

## 2. Ba quyết định admin (chốt cứng)

1. **Cả khung** — áp dụng ACADEMIC_3_LEVELS_16_TABS_V1 cho toàn bộ 16 tab (không chỉ tab GIÁO LÝ).
2. **Phân đôi cùng tab** — tab GIÁO LÝ giữ nguyên khối "Đối Chiếu Tam Tạng", thêm khối "Giáo lý Phật học" ngay trong cùng tab. Không tạo tab mới cho giáo lý.
3. **Chấm điểm 2 trục** — `data-exists` / `UI-displays` theo từng dimension, mỗi trục chấm 0/1 kèm bằng chứng **code + DB** (thay cho "5.5/10" chủ quan). Công thức: điểm tab = Σ 6 dimension × 2 trục.

## 3. Mô hình chấm điểm 2 trục

Mỗi tab chấm theo **6 dimension × 2 trục** (tối đa 12):

| Dimension | `data-exists` (DB có? trỏ đúng bảng, verified count) | `UI-displays` (code render hiển thị? :line, empty-state, fallback) |
|---|---|---|
| D1 Identity | entity ID canonical + label Việt (`_daSafeLabel`) | nút tab + header hiển thị ID thật |
| D2 Nguồn & citation | source/ref cột trong bảng (cbeta_ref, source_ref, etc.) | chip/badge nguồn hiển thị |
| D3 Bản văn/evidence | passage/evidence rows đếm được | đoạn kinh/trích dẫn render + link "Đọc trong Đại Tạng" |
| D4 Quan hệ | edge/co-mention trong bảng | cạnh/tooltip/drawer hiển thị |
| D5 Empty state | trạng thái "chưa có" xác định được | empty-state trung thực (NOT-INDEXED / danh sách rà soát) |
| D6 Provenance/QA | confidence + verification_status + source | huy hiệu DIRECT/THEMATIC/SCHOLARLY + claim drawer |

Per-trục scoring: `1` = bằng chứng code+DB xác minh · `0` = không có/không trung thực · `null` = ngoài phạm vi tab (khi đó trục 0 và ghi rõ).

**Cấp học thuật:**
- Cử nhân ≥ 6/12 · Cao học ≥ 9/12 · Tiến sĩ = 12/12 + dataset_version + export JSON-LD.
- Release gate: toàn hệ ≥ 8/12 trung bình · **core 9 tab ≥ 9/12** (graph/nexus/lineage/persons/timeline/giaoly/sukien/daitang/entity).

## 4. Lược đồ 16 tab (target taxonomy)

| Tab target | Gộp từ tab cũ | Loại |
|---|---|---|
| Tripitaka · CBETA | cbeta + daitang | gộp |
| Đồ Thị · Graph | graph | giữ |
| Nexus | nexus | giữ |
| Truyền Thừa | lineage | giữ |
| Nhân Vật | persons | giữ |
| Niên Đại | timeline | giữ |
| Giáo Lý (phân đôi) | giaoly | mở rộng |
| Sự Kiện | sukien | giữ |
| Bản Đồ | bandoo | giữ |
| Thư Viện | thuvien | real hóa |
| Nghi Lễ | nghile | real hóa |
| Giáo Dục | giaoduc | real hóa |
| Dữ Liệu | dulieu | real hóa |
| Hình Ảnh | hinhanh | real hóa |
| Nghệ Thuật | nghethuat | real hóa |
| **Entities (thực thể tổng hợp)** | — | **MỚI** |

> **Quyết định UI mặc định:** GIỮ label nút tab hiện tại (bookmark/người quen vị trí), bổ sung ngữ cảnh trong panel. Đổi label hẳn = quyết định riêng.

## 5. Bảng tái sử dụng dữ liệu (đã probe DB thật 2026-09-07)

| Nhu cầu | Bảng dùng được | Số row hiện tại |
|---|---|---|
| Evidence claims | `entity_claims` (subject/predicate/object_text/confidence/verification_status/authority_role) | 447,885 |
| Event evidence | `events` + `event_evidence` + `event_entities` (review_status='candidate', precision) | 3,530 |
| Event↔kinh văn | `event_text_link` (bridge cho Nexus) | 17,284 |
| Glossary thuật ngữ | `glossary_term` (term/definition/full_text) | 248,095 |
| Glossary per-source | `term_glossaries` (term_vi/term_zh, source='marcus') | 18,127 |
| Pali tham chiếu | `pali_place_ref` (15 thánh địa Ấn, sc_uid, verified_by='ZQ', confidence) | 15 |
| Đối chiếu | `toh_cbeta_crossref` (10) · `sat_crossref` (2,913) · `kanripo_catalog` (101) | — |
| Place↔kinh | `place_person_bibl` (13,933) · `cbeta_place_mentions` (16,311) · `cbeta_place_mention_stats` (26,484) | — |
| Person↔Place | `person_origin_link` (11,929) · `place_timeline_events` (3,688) | — |
| Lineage | `marcus_networks` (11,169) · `marcus_reference` (18,127) · `lineage_conflicts_v2` (40,327) | — |
| Canon | `canon_catalog` (3,122) · `catalog_mapping` (6,564) · `cbeta_catalog_vn` (3,122) · `passage` (7,563) | — |
| Lexicon | `lexicon` (166,278) · `hanviet_fallback` (8,650) | — |

**Dữ liệu thật đáng lưu ý:**
- `people.name_vi` = **100%** (48,673/48,673) — docs cũ ghi 0% là lỗi thời.
- `entity_claims.verification_status` = **100% 'unverified'** (447,885) → policy cho P3.
- `entity_claims.claim_type` phân bố: coordinates 175,441 · mentioned_in 13,933 · lineage_teacher/student 11,166 · same_as 148 ...
- `events.review_status` = 100% 'candidate' (chưa có luồng duyệt) → P3.
- Tab GIÁO LÝ đã real (`renderGiaolyTab` places.html:6232; `api_cbeta_compare` app.py:13940; Pali `GET /api/places/<id>/pali` app.py:13473) — Thiếu Lâm Tự có **0** Pali ref (15 record đều là thánh địa Ấn).

## 6. Contract hiển thị chung (shared)

- **`_daSafeLabel(n) = n.label_vi || n.label || n.label_zh || n.id`** — template từ `_nexusSafeLabel` (places.html ~5199).
- **`_daEmptyState(taxonomy, scope)`** — trả khối trung thực: scope hiện tại + số record/biết được + "NOT-INDEXED" khi chưa index + không bao giờ "đang phát triển" mờ.
- **Badge bộ:** `DIRECT` (khớp trực tiếp, chứng cứ có) · `THEMATIC` (lim chủ đề, thuật ngữ glossary) · `SCHOLARLY` (phân tích liên văn bản, cần kể provenance).
- **Claim drawer:** 1 mẫu hiển thị `entity_claims` (predicate, object_text, confidence, verification_status, authority_role, source_reference) + 1 mẫu `event_evidence` (source_record, exact_span, evidence_type).

## 7. Các phase triển khai (1 commit/batch — revert thuận tiện)

- **P0-SAFETY (Batch 2):** helpers chung · empty-state Pali `NOT-INDEXED` · `/daoanh/api/evidence/<subject_id>` (read-only) · co-mention dashed/hidden · `dashboard/tab_readiness.html`.
- **P1-BACHELOR (Batch 3):** 16 tab đủ ID/nguồn/empty-state · tab mới `entities` · mock case-study các tab stub.
- **P2-MASTER (Batch 4):** GIÁO LÝ phân đôi · schema additive `doctrine_concept` + cột `assertion_level`/`reviewed_*` trên `entity_claims` + bảng `pali_cbeta_map` (rút hardcode) · evidence drawer + filter.
- **P3 (Batch 5):** dataset_version · export citation/JSON-LD · review/audit/dispute.
- **P4 (Batch 5):** regression toàn phần · release gate ≥8 (core ≥9).

## 8. Dashboard admin

- Trang mới `dashboard/tab_readiness.html` (theme dark-slate/amber, model `dashboard_process.html`).
- 2 bảng dữ liệu: tiến độ task (`GET /daoanh/api/progress/dashboard`) + scorecard `data/tab_readiness.json` (sinh tự động từ script `scripts/build_tab_readiness.py`, đo code + DB thật).
- **8 alert:** (1) tab label 15→16 không khớp taxonomy · (2) empty-state "đang phát triển" còn sót · (3) label không an toàn (`label||label_zh||id` raw) · (4) entity_claims 100% unverified · (5) events 100% candidate · (6) tab không có API route nguồn · (7) co-mention chưa tách thị giác · (8) grade <8 (core <9).

## 9. Rủi ro & quyết định mở

| # | Rủi ro | Xử lý |
|---|---|---|
| R1 | Đổi label nút tab 15→16 làm bookmark/user nhầm | **Giữ label hiện tại**, thêm ngữ cảnh panel (mặc định). Đổi hẳn cần admin quyết |
| R2 | Glossary 248K dùng làm "giáo lý" có thể trộn thuật ngữ vs khái niệm | P2 whitelist dictionary cho khái niệm giáo lý; THEMATIC badge |
| R3 | Luồng review cần phân vai (admin vs tăng ni) | P3 thiết kế verification_status policy; hiện 100% 'unverified' |
| R4 | verification_status lộ claim "unverified" với user | Hiển thị rõ "Chưa kiểm chứng" + cho phép dispute; không xóa |
| R5 | No live server :5000 | Kiểm chứng py_compile + node --check + code review; live-test sau restart |

## 10. Thứ tự thực thi (batch)

Batch 1 (này) = Task 0 inventory + P0 kickoff docs → **Batch 2 P0** → **Batch 3 P1** → **Batch 4 P2** → **Batch 5 P3+P4**. Mỗi batch = 1 commit riêng, `git revert <commit>` là đủ để về trước.

## 11. Verbatim 3 mục admin đã chốt (nguồn quyết định)

1. "Cả khung" — không chỉ tab GIÁO LÝ.
2. "Phân đôi cùng tab" — giáo lý + Đối Chiếu Tam Tạng trong cùng tab GIÁO LÝ.
3. "Ok 2 trục chấm" — scoring 2 trục data-exists/UI-displays thay vì điểm chủ quan.