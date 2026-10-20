---
task: tasks/T224-geo-spatial-timeline-founding-phase2.md
report: G2-3 EVIDENCE_EVENT_MODEL
title: "Evidence/Event Model — hiện trạng place_timeline_events và khoảng trống"
status: done
updated: 2026-10-11
current_task: T356
created: 2026-10-04
measured_at: 2026-10-04
db: data/lineage.db (read-only)
---

# T224 · G2-3 — Evidence / Event Model

**Mục đích:** mô tả đúng **event đang có** và **evidence thật sự đi kèm**, để quyết
định có cần bảng `place_timeline_evidence` (DERIVED) như plan G3 dự tính hay không.

> G0–G2 đã hoàn tất lịch sử; T356 chỉ audit read-only. G3 deferred. Bảng04-10 dưới đây không phải current và không đặt cổng bắt buộc có nguồn ngoài mới.

---

## 1. Schema / fill rate lịch sử 2026-10-04

`place_timeline_events` — **3.688 rows**, 11 cột:

| Cột | Kiểu | Fill rate | Ghi chú |
|---|---|---:|---|
| `id` | INTEGER | — | PK |
| `dila_id` | TEXT | 100% | ⚠️ **không có FK** tới `places_dila.id` |
| `event_type` | TEXT | 100% | 2 giá trị: `founding` 3.647 · `dissolved` 41 |
| `year` | INTEGER | 100% | |
| `year_end` | INTEGER | **0%** | 🔴 **0% ở snapshot04-10; không kết luận hiện hành** |
| `label_zh` | TEXT | 99,97% | |
| `label_vi` | TEXT | **1,0%** (36/3.688) | 🔴 gần như trống |
| `source` | TEXT | 100% | 8 nguồn |
| `source_ref` | TEXT | 100% | ⚠️ xem §3 |
| `confidence` | TEXT | 100% | 🔴 xem §4 |
| `created_at` | TEXT | — | |

**Index:** `idx_pte_dila(dila_id)` · `idx_pte_source(source)`
**FK:** ❌ **không có** — `dila_id` chỉ *tình cờ* khớp 3.688/3.688 với `places_dila.id`.
Query sai cột sẽ lỗi `no such column` (đã gặp ở T201: `places_dila` có PK `id`,
**không** có cột `dila_id`).

---

## 2. Phân bố nguồn × loại event

| `source` | `founding` | `dissolved` | Tổng | Loại evidence |
|---|---:|---:|---:|---|
| `dila_era_name` | 1.471 | 0 | 1.471 | suy luận |
| `dila_dynasty` | 851 | 0 | 851 | suy luận |
| `dila_note` | 719 | 0 | 719 | suy luận |
| `dila_note_regex` | 276 | 0 | 276 | suy luận |
| `dila_founding_phase2` | 55 | 0 | 55 | suy luận |
| `dila_fosizhi` | 15 | 0 | 15 | ngoài |
| `wikidata_p571` | 146 | 0 | 146 | **ngoài + QID** |
| `wikidata` | 114 | **41** | 155 | **ngoài + QID** |

⇒ Đính chính số học: năm source gắn phương pháp suy luận cộng **3.372/3.688=91,43%**. Phân loại source lịch sử không tự đánh giá semantic từng event; không trộn với tỷ lệ place A2≈93%.

---

## 3. Source_ref — provenance lịch sử, cần locator/version

| Dạng | Số | Đánh giá |
|---|---:|---|
| Locator QID·property (`Q…·P…`) | **301** | cú pháp ứng viên; không plain QID/accepted |
| URL (`http…`) | **0** | ⚠️ không URL nào |
| Tự tham chiếu (`source_ref = source`) | **55** | 🔴 **vô nghĩa** |
| Breadcrumb nội bộ (`PL…·note·regex`) | **3.332** | có thể làm provenance khi artifact/excerpt/version/hash giải được |

Mẫu breadcrumb: `PL000000000184·note·regex`

⇒ Locator nội bộ cần giải đến raw_xml/note, excerpt và artifact version/hash để tái kiểm. Local DILA artifact có thể là evidence, không bắt buộc URL ngoài. Breadcrumb chưa đóng băng là gap provenance.

⚠️ 3.332 breadcrumb có nghĩa là **đổi `note` là mất đường truy vết** của event đã có.

---

## 4. 🔴 `confidence` — 1 cột, 2 hệ, 16 giá trị

| Hệ | Giá trị | Số |
|---|---|---:|
| **Nhãn ngữ nghĩa** | `dynasty_range` | 844 |
| | `era_name_exact` | 764 |
| | `regex_note` | 714 |
| | `era_name_midpoint` | 707 |
| | `verified` | 122 |
| **Điểm số** | `0.85` | 194 |
| | `0.88` | 117 |
| | `0.75` | 69 |
| | `0.9` | 55 |
| | `0.90` | 27 |
| | `0.7` | 26 |
| | `0.72` | 25 |
| | `0.8` | 11 |
| | `0.5` | 7 |
| | `0.616` | 5 |
| | `0.595` | 1 |

🔴 **Vấn đề gốc:** cột `confidence` đang lưu **hai thứ khác nhau** — *phương pháp suy
luận* (`era_name_exact`) lẫn *độ tin cậy* (`0.85`). Có thể phân loại bằng cú pháp trong projection read-only. WHERE confidence > 0.8 trên TEXT có thể cho nhãn lọt vì affinity/collation; CAST đơn thuần cũng không chứng minh score hợp lệ. T356 chỉ numeric hữu hạn0..1, tách label/numeric/missing/truncated và giữ raw; verified không accepted.

Ngoài ra `0.9` và `0.90` **cùng giá trị, khác chuỗi** — 2 nhóm tách phát sinh từ 2 script.

**Hệ quả cho plan cũ:** ràng buộc *"mọi row NLP = `confidence='candidate'`"* (đã bỏ khỏi
T224) sẽ ép lại dữ liệu legacy hiện có và trộn thêm hệ thứ ba.

**T356 thực hiện:** source_ref_kind/legacy_confidence_kind và raw confidence nằm trong CSV derived, không phải cột DB mới/migration. Giữ confidence base. Không DDL/ALTER/UPDATE/view DB; schema sidecar tương lai thuộc G3 giao riêng.

---

## 5. T22 — phát hiện lịch sử đã sửa

04-10 báo55/55 empty label_vi/self_ref, label_zh là tên place. Đây là gap chất lượng, không vi phạm DDL chỉ vì cột TEXT được khai báo (nullable). T356 hiện55 row:50 founding+5 era_mention,0 empty label_vi/0 self_ref. Không giao sửa lại hoặc nâng accepted từ nhãn.

---

## 6. G3 deferred — không tạo place_timeline_evidence

Không tạo bảng chỉ sao chép locator chưa đóng băng. Không bắt buộc nguồn ngoài mới: raw/local DILA hỗ trợ evidence khi có excerpt/locator/version/hash và assertion semantics. Source reuse audit không mở ETL/accepted.

Nếu Admin mở G3 riêng: cần scope/ownership, guard identity/dila_id, evidence_method/score qua sidecar hoặc schema được duyệt, provenance tái kiểm, HITL reviewed_by/reviewed_at, dry-run/backup/rollback. Không yêu cầu tách cột base trong khi T82 freeze.

## 7. T356 đã làm, chỉ đọc

- Ref kinds qid/qid_property/url/internal/self_ref/missing/truncated dùng cú pháp chặt, không auto-verify identity.
- Confidence raw phân numeric hữu hạn0..1/label/missing/truncated; CSV, không DB view.
- Source×event_type tổng độc lập và membership cùng read transaction; không claim semantic corpus audit hay tìm mọi duplicate event.
- Baseline55 T22 riêng, không trừ totals; lỗi cũ đã hết. T230/T231 giữ catalog/quyền, T121 giữ geo.

## 8. Revert

Docs-only: `git revert --no-edit <sha>`. **0 DB.**

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
