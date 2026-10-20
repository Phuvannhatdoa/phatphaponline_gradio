---
task: tasks/T224-geo-spatial-timeline-founding-phase2.md
report: G2-1 SOURCE_REUSE_AUDIT
title: "Source Reuse Audit — phân loại 59.167 DILA places (A1/A2/C/B/D/E)"
status: done
updated: 2026-10-11
current_task: T356
created: 2026-10-04
measured_at: 2026-10-04
db: data/lineage.db (read-only, file:...?mode=ro)
record: data/t224_g0_measurements.json
---

# T224 · G2-1 — Source Reuse Audit

**Đọc kèm:** `docs/Mimo-Flash/T224-geo-spatial-timeline-founding-phase2.md` (plan, tự chứa)
**Số đo gốc:** `data/t224_g0_measurements.json` — sinh bằng 1 script authoritative, tổng khớp tuyệt đối.

> ⚠️ **0 write DB.** Toàn bộ số dưới đây đọc qua `file:...?mode=ro`. Không có `INSERT`/
> `UPDATE`/`CREATE`. Cột nào cũng đối chiếu bằng **control** (xem §6).

---

## 1. Baseline lịch sử 2026-10-04 (G0)

| Đối tượng | Số | Ghi chú |
|---|---:|---|
| `places_dila` | **59.167** | ✅ **mẫu số** của audit · PK `id` **unique** (59167 = distinct) |
| `places` | 59.161 | **không** dùng làm mẫu số — khác 6 dòng |
| `places_dila.raw_xml` khác rỗng | 59.167 (100%) | ⚠️ không dùng làm tiêu chí — xem §3 |
| `places_dila.note` khác rỗng | 17.085 | 15.919 giá trị khác nhau |
| `place_timeline_events` | 3.688 rows / **3.534** distinct `dila_id` | không có FK |
| `geo_cross_ref` | 190 rows | |

---

## 2. Phân bố A1/A2/C/B/D/E (historical 2026-10-04)

Thứ tự ưu tiên **`A1 > A2 > C > B > D > E`** — mỗi place vào **nhóm đầu tiên** khớp.

| Nhóm | Tiêu chí | Place | % |
|---|---|---:|---:|
| **A1** | bất kỳ event nguồn wikidata/wikidata_p571; không accepted/founding proof | **249** | 0,421% |
| **A2** | bất kỳ event còn lại; không mặc định suy luận | **3.285** | 5,552% |
| **C** | có `geo_cross_ref`, chưa có event | **85** | 0,144% |
| **B** | marker candidate note/raw_xml, chưa có event/xref; không date | **226** | 0,382% |
| **D** | note khác rỗng, chưa khớp nhóm trước; không tự mở NLP | **13.336** | 22,540% |
| **E** | không khớp predicate trước ⇒ **giới hạn nguồn của audit** | **41.986** | 70,962% |
| | **TỔNG** | **59.167** | ✅ khớp `places_dila` |

### Vì sao phải có precedence

**22 place** khớp cả tiêu chí C lẫn tiêu chí B. Không ép thứ tự ⇒ tổng vỡ.
Ưu tiên **C trước B** vì cross-ref là mapping có chủ đích, còn regex B chỉ là chữi từ khoá.

### Vì sao tách A1 / A2

3.285/3.534≈93% là tỷ lệ place A2, không phải event suy luận. Năm source gắn phương pháp suy luận cộng **3.372/3.688=91,43%** (đính chính phép cộng, không đánh giá semantic từng event):

| `source` | Event | Loại |
|---|---:|---|
| `dila_era_name` | 1.471 | suy luận (tên đời) |
| `dila_dynasty` | 851 | suy luận (triều đại) |
| `dila_note` | 719 | suy luận (mô tả) |
| `dila_note_regex` | 276 | suy luận (regex note) |
| `dila_founding_phase2` | 55 | suy luận (regex note) |
| `dila_fosizhi` | 15 | ngoài (Fosi Zhi) |
| `wikidata` | 155 | ngoài, locator QID·property |
| `wikidata_p571` | 146 | ngoài, locator QID·property |
| **Tổng độc lập** | **3.688** | đủ 8 source |

⚠️ Any-event không chứng minh founding; không gộp A1+A2 thành 3.534 ngày thành lập chắc chắn.

---

## 3. Vì sao nhóm B cũ (plan T181) là sai — bằng chứng

Plan cũ định nghĩa B = *"Có TEI/XML marked-up evidence trong `raw_xml`/`note`"*.

1. **`raw_xml` khác rỗng 59.167/59.167 = 100%** ⇒ "có mã XML" là tautology, khớp mọi dòng.
   Theo nghĩa đen, B = 59.167 và D = E = **0**.
2. **Không thấy hai literal markup trong phép đo 04-10**; không suy ra toàn TEI thiếu thông tin founding. `foundingDate` = **0**, `founded` = **0**
   (pattern ASCII ⇒ tin cậy tuyệt đối).
3. **Mẫu ns0:note chủ yếu boilerplate nguồn, không tự chứng minh founding:** mẫu 4.000 dòng chỉ **794**
   giá trị khác nhau; `中研院歷史地名` chiếm ~78%; mẫu đầu đều là `廣大之陸上人文地理區域`.
4. **Văn bản mô tả thật nằm ở cột `note`** (15.919 giá trị khác nhau) — đó là **prose**
   ⇒ việc của **nhóm D**, không phải B.

**Định nghĩa lại (đã đo):** B = `note` **hoặc** `raw_xml` chứa một trong
`始建於` · `創建` · `建於` · `建國`.

| Mốc | Số place (độc lập, chưa loại trùng) |
|---|---:|
| `始建於` | 215 |
| `建於` | 482 |
| `創建` | 242 |
| `建國` | 30 |
| **B sau dedupe + loại trùng A/C** | **226** |

Trong 226 place của B, **6** có marker chỉ nằm ở `raw_xml` (`note` rỗng) ⇒ regex bắt buộc
quét **cả hai** cột.

---

## 4. Nhóm D — ước lượng khối lượng NLP

| Chỉ số | Giá trị |
|---|---:|
| Số place | **13.336** |
| Tổng ký tự `note` | **733.814** |
| Ước lượng token (~1,6 ký tự/token) | **~458.633** |
| Số batch ~8.000 token | **58** (ceil, trước overhead/output) |
| Độ dài: median / p90 / max | 42 / 123 / **1.740** |

**Đánh giá:** 458.633 token chỉ là heuristic 1,6 ký tự/token; ceil(458.633/8.000)=58 trước overhead/output. Không có cơ sở gọi đây là một prompt rẻ hoặc quyền chạy LLM. Audit chỉ xuất estimate; không mass NLP/API.

---

## 5. Nhóm E — đây là **giới hạn nguồn**, không phải việc chưa làm

Admin đã chốt **hướng (a)**. Cơ sở:

| Trong 41.986 place của E | Số | % của E |
|---|---:|---:|
| **vẫn có `name_zh`** (tên Hán) | 41.982 | 99,99% |
| **vẫn có `name`** (tên la-tinh) | 41.980 | 99,99% |
| **vẫn có `raw_xml`** (khung TEI) | 41.986 | 100,00% |
| **vẫn có `note_category`** | 41.986 | 100,00% |
| **vẫn có `district`** | 41.950 | 99,91% |
| **vẫn có lat/lon** | 41.928 | **99,86%** |
| có `listbibl` (danh mục kinh) | 1.201 | 2,86% |

⇒ E không khớp predicate audit ở snapshot04-10, vẫn có tên/toạ độ/phân loại. Không suy ra toàn XML hoặc mọi nguồn DILA thiếu semantic founding; E không tự là backlog.

Đây là **giới hạn của nguồn dữ liệu**, không phải backlog kỹ thuật ⇒ **không mở G3**.

---

## 6. Bẫy kỹ thuật — **bắt buộc** control trước khi tin số

**Pattern CJK truyền qua PowerShell heredoc bị mangle thành `?` ⇒ `LIKE '%始建於%'`
trả 0 giả.** Phiên review 2026-10-04 đã dính lỗi này, suýt kết luận nhầm "B rỗng".

Control bắt buộc trước mọi lần đo CJK:

| Pattern | Giá trị lịch sử 04-10 |
|---|---:|
| `建` | 4.646 |
| `帝` | 798 |
| `唐宋` | 36 |

**Cả 3 bằng 0 ⇒ pattern đã chết, đừng tin kết quả.** Mọi script phải dùng `\uXXXX`
trong Python hoặc để file UTF-8.

---

## 7. Đề xuất / ranh giới hiện hành

1. Refresh bằng T356; A1/A2 không accepted founding.
2. B lịch sử226 chỉ marker candidates; current B196, marker-without-founding282 qua các bucket. T22 giữ ETL; cohort55 lỗi cũ đã sửa, không giao lại.
3. D chỉ text/estimate; G3 deferred, không NLP/API tự động.
4. Local DILA artifact có thể là evidence với excerpt/locator/version/hash; không bắt buộc nguồn ngoài mới.
5. Ref/confidence chỉ projection CSV, không ALTER/UPDATE/view DB.

## 8. Revert

Docs-only: `git revert --no-edit de114937 66b5ca2` (xoá 3 file `docs/T224_*.md`).
`data/t224_g0_measurements.json` additive — xoá file là đủ. **0 DB.**

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
