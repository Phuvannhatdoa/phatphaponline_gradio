---
id: T224
title: "Geo-Spatial & Timeline — Source Reuse Audit (phân loại A1/A2/C/B/D/E cho 59.167 DILA places)"
module: GIS Places / Timeline / HOME
priority: medium
status: done
doc_status: done
undone_reason: "Đã xong G0+G1+G2, đủ 5/5 acceptance. Admin chốt 2026-10-04: (1) nguồn toạ độ = DILA cấp → places_dila.geo_lat/lon là SSOT 98,84%, không xây enrich toạ độ, không chồng T121; (2) license BỎ QUA, sẽ update sau ở tầng HTML (T231 Source Hub / T230 catalog). G3 KHÔNG mở."
undone_until: ""
undone_action: "G0–G2 done lịch sử; refresh thuộc T356. Cohort55 T22 đã hết empty label_vi/self_ref, không sửa lại. Marker candidates không date. T22 giữ ETL timeline, T121 giữ geo, G3 deferred."
blocked_reason: ""
handoff_notes: >-
  G3 deferred; E không khớp audit predicates, không khẳng định toàn nguồn thiếu semantic.
  T356 chỉ JSON/CSV/ref/confidence, không ALTER/UPDATE/view DB. Local artifact có thể là
  evidence với excerpt/locator/version/hash, không bắt buộc nguồn ngoài mới. QID/tên/geo
  không auto-accept identity hoặc teacher/số đời. T230/T231 giữ catalog/quyền. Ba cột
  chgis_svid/tgaz_id/bdrc_id giữ nguyên.

owner: mimo-flash
created: 2026-10-04
updated: 2026-10-11
current_task: T356
g3_status: deferred
depends_on: [T22, T112, T121]
designed_by: mimo-flash
handoff_to: Admin
former_id: T181
plan_approved_at: "2026-10-04 (Admin duyệt: đổi ID sang T224, plan tự chứa, và hướng (a) cho nhóm E)"
revert: "docs-only: git revert --no-edit de114937f658ed9472288bc6d86588866c515ecf <sha_T224_pass2>; 0 DB, 0 code"
---

# T224 — Source Reuse Audit: phân loại 59.167 DILA places

**Plan đầy đủ:** `docs/Mimo-Flash/T224-geo-spatial-timeline-founding-phase2.md`
**Bản gốc đã bác (để đối chiếu):**
`docs/Mimo-Flash/X-T181-geo-spatial-timeline-founding-phase2-SUPERSEDED.md`

---

## 1. Vì sao đổi ID

`T181` đã thuộc task **CBETA Bulk Import**
(`tasks/T181-cbeta-bulk-import-lazy-translate.md`, `in_progress`, code
`scripts/t181_map_sigla.py`) — **khác task hoàn toàn, cùng ID**. Đổi sang **T224** (đã
kiểm 2 tầng: 0 task file, 0 tham chiếu prose). **Không đụng task CBETA.**

## 2. Vì sao viết lại, không chỉ sửa số

| Trích dẫn của plan cũ | Thực tế |
|---|---|
| `docs/GEO_SPATIAL_TIMELINE_SPEC.md` "APPROVED, kèm 5 fix review" | **không tồn tại** |
| `docs/Mimo-Flash/PROMPT-T181-source-reuse-audit.txt` | **không tồn tại** (repo có **0** file `PROMPT-*.txt`) |
| "số liệu đệm khớp SPEC §4" | không kiểm chứng được |

**Hệ quả:** tiêu chí phân loại **nằm trong prompt** ⇒ prompt mất ⇒ tiêu chí mất ⇒
nhóm **B suy ra sai**. Bài học (giống T222): **nhét tiêu chí vào thân plan**, không
tạo file prompt riêng.

## 3. Vì sao nhóm B cũ là sai

`places_dila.raw_xml` khác rỗng **59.167 / 59.167 = 100%** ⇒ tiêu chí *"có TEI/XML
marked-up evidence"* khớp **mọi dòng** ⇒ B = 59.167, D = E = 0. Thêm TEI **không có**
markup ngày thành lập: `foundingDate` = 0, `founded` = 0 / 59.167.

`ns0:note` là **boilerplate nguồn**: mẫu 4.000 dòng chỉ **794** giá trị khác nhau,
`中研院歷史地名` chiếm ~78%. Văn bản mô tả thật nằm ở **cột `note`** ⇒ là **prose** ⇒
**nhóm D**, không phải B.

> ⚠️ XML là **namespace-prefixed** (`<ns0:placeName>`, `<ns0:note>`). Literal
> `<placeName` / `<TEI` / `<place` khớp **0 dòng**.

## 4. Phân bố lịch sử 2026-10-04 (không dùng làm current)

Thứ tự ưu tiên **bắt buộc** `A1 > A2 > C > B > D > E` — cần vì **22 place** có cả
`geo_cross_ref` lẫn mốc thành lập.

| Nhóm | Tiêu chí | Số place | % |
|---|---|---|---|
| **A1** | bất kỳ event nguồn wikidata/wikidata_p571; không accepted/founding proof | **249** | 0,42% |
| **A2** | bất kỳ event còn lại; không mặc định suy luận | **3.285** | 5,55% |
| **C** | `EXISTS` `geo_cross_ref`, chưa thuộc A | **85** | 0,14% |
| **B** | marker note/raw_xml (始建於/創建/建於/建國), chưa thuộc A/C; không date | **226** | 0,38% |
| **D** | note khác rỗng, không khớp trước; không tự mở NLP | **13.336** | 22,54% |
| **E** | không khớp predicate trước ⇒ **giới hạn nguồn của audit** | **41.986** | 70,96% |
| | **TỔNG** | **59.167** | ✅ khớp `places_dila` |

**Tách A1/A2:** 3.285/3.534≈93% là tỷ lệ place A2, không event suy luận. 301/3.688 locator lịch sử là QID·property; không plain QID/accepted. Any-event không chứng minh founding.

**Mẫu số** = `places_dila` (59.167), **không phải** `places` (59.161).
`place_timeline_events` **không có cột `place_id`**; cột là `dila_id` → `places_dila.id`
(3.688/3.688 khớp, **không khai báo FK**).

## 5. Quyết định của Admin

**Hướng (a):** nhóm **E = giới hạn nguồn**, KHÔNG phải backlog ⇒ **không mở G3**.
Nếu chọn (b) thì E thành backlog 42k place và **chồng T121** (đang `in_progress`).

## 6. Phụ thuộc — snapshot lịch sử 2026-10-04

| Task | Bản cũ | Thật |
|---|---|---|
| **T22** | `in_progress` | ✓ đúng (Layer E Ollama chưa xong) |
| **T22.1** | ✅ DONE | file chỉ còn ở `tasks/backup/`, **không có status** |
| **T121** | 🟡 PENDING | **`in_progress`** — giữ Layer 3 (Wikidata lat/lon) |
| **T112** | 🚫 BLOCK | **`done`** — ràng buộc nhóm C là **license** 5 nguồn chưa rõ, không phải task blocked |

## 7. T22 đã đối soát 11-10

55 empty label_vi/self_ref là phát hiện lịch sử, hiện đều0; cohort55 đủ50 founding+5 era_mention. Không giao sửa lại. B226 lịch sử chỉ marker candidates; T356 B196, marker-without-founding282, không ETL.

## 8. 🛠 Bẫy kỹ thuật — bắt buộc đọc trước khi chạy

**Pattern CJK truyền qua PowerShell heredoc sẽ bị mangle thành `?` ⇒ trả 0 giả.**
Phiên review 2026-10-04 đã đo sai một vòng rồi phát hiện qua control.

- Mọi script phải dùng **`\uXXXX`** trong Python, hoặc để file UTF-8.
- **Luôn chạy 1 control** trước khi tin số: `建` phải ≈ **4.646**, `帝` ≈ **798**
  (`唐宋`≈36) là số lịch sử, không hard-code snapshot tương lai. Controls có timestamp để nhận diện lỗi encoding.

## 9. Acceptance / refresh T356

1. Ba report G2/plan tự chứa, không blocked bởi SPEC/PROMPT cũ thiếu.
2. Một bucket/ID, totals bằng places_dila cùng read transaction; sources×type cộng độc lập.
3. mode=ro/query_only/authorizer/total_changes=0, không trừ55 để proof0 write.
4. Any/founding/dissolved/marker riêng, history/current/schema/hash/command/manifest; D chỉ estimate.
5. T356 fixture/CLI tests và guard/dup:ids báo thật, không claimdup sạch/fullpipeline khi có duplicates lịch sử. G3 deferred.

## 10. Revert

- Docs-only: `git revert --no-edit de114937f658ed9472288bc6d86588866c515ecf <sha_T224_pass2>`
- G3 (tương lai): script `--revert` + DB backup pattern T157.

## Đối soát T356 — snapshot hiện hành 2026-10-11

Hợp đồng chạy được: [T356](../tasks/T356-t224-readonly-audit-contract.md) · [script](../scripts/t356_t224_readonly_audit.py) · [summary](../docs/sessions/2026-10-11_T356/audit-current-t356/summary.json) · [manifest](../docs/sessions/2026-10-11_T356/audit-current-t356/manifest.json) · [session](../docs/sessions/2026-10-11_T356/README.md).

Số đo ở các phần trước là **historical_reference_only, 2026-10-04**. Bảng sau là **current_read_transaction**, timestamp `2026-10-11T02:11:48.789914+00:00`, definition `t356-t224-legacy-partition-v2`; số cũ không phải hằng số nghiệm thu.

| Chỉ số | Lịch sử 04-10 | Snapshot 11-10 |
|---|---:|---:|
| places_dila / places / geo_cross_ref | 59.167 / 59.161 / 190 | 59.167 / 59.161 / 190 |
| Event rows / place có bất kỳ event | 3.688 / 3.534 | 4.386 / 3.544 |
| A1 / A2 / C / B / D / E | 249 / 3.285 / 85 / 226 / 13.336 / 41.986 | 249 / 3.295 / 85 / 196 / 13.353 / 41.989 |

Cùng read transaction: tổng membership = tổng bucket = **59.167**, mỗi ID đúng một bucket. `has_founding_event` **2.502**, `has_dissolved_event` **41**; **1.042** place có event nhưng không founding; **4** dissolved-only đều ở A1. **282** marker-without-founding qua các bucket, B chỉ **196** do precedence. A1/A2 không đồng nghĩa founding/accepted.

Tổng source × event_type độc lập **4.386**; wikidata **155** tách wikidata_p571 **146**. Ref kinds: **301 qid_property**, **4.064 internal**, **21 missing**; confidence kinds: **3.854 label**, **532 numeric**. QID·property chỉ là locator ứng viên. Score chỉ nhận số hữu hạn 0..1, giữ raw; không so sánh TEXT với 0.8.

Baseline T22 dila_founding_phase2 vẫn **55**: 50 founding + 5 era_mention, empty label_vi **0**, self_ref **0**. Lỗi cohort55 cũ đã được T22 sửa; không giao sửa lại hoặc nâng accepted. Baseline báo riêng, **không trừ khỏi totals**.

Proof: URI mode=ro, query_only=1, authorizer chỉ đọc, total_changes=0, một read transaction, fetchmany(256). Schema SHA `699a3374ed0a02ade671ace68cb3cdf3d793856f605c644e9d837431addaec38` là fingerprint schema, không hash toàn DB/WAL. Marker 始建於/創建/建於/建國 trong note **hoặc** raw_xml chỉ là lexical candidate, không date. Không parse/copy toàn XML; parser TEI tương lai phải dùng URI http://www.tei-c.org/ns/1.0, không khóa prefix ns0.

G0–G2 không blocked bởi SPEC/PROMPT bị mất; plan và T356 tự chứa tiêu chí. **G3 deferred**, không DDL/DML/ALTER/view DB/full importer/NLP/API. D hiện 13.353 note, 735.360 ký tự, heuristic 459.600 token / 8k phải ceil **58** trước overhead/output; không phải giá API/context budget hoặc quyền LLM.

T22 giữ ETL timeline, T121 giữ geo/HITL, T230/T231 giữ catalog/quyền/Source Hub. Local DILA artifact có thể là evidence khi có excerpt + locator + version/hash; không bắt buộc nguồn ngoài mới. QID/tên/geo không auto-accept semantic identity hoặc suy teacher/số đời/hệ đếm. G3 cần Admin giao scope, chứng cứ, dry-run/backup/rollback và QA riêng.
