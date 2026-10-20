---
task: tasks/T224-geo-spatial-timeline-founding-phase2.md
title: Geo-Spatial & Timeline Integration — Source Reuse Audit (Founding Date Phase 2)
former_id: T181
status: done
created: 2026-10-04
updated: 2026-10-11
current_task: T356
g3_status: deferred
module: GIS Places / Timeline / HOME
priority: medium
blocked_reason: ""
---

# T224 — Geo-Spatial & Timeline Integration (Source Reuse Audit)

> ⚠️ **Đổi ID: `T181` → `T224`.** `T181` đã bị chiếm bởi task **khác** —
> `tasks/T181-cbeta-bulk-import-lazy-translate.md` (CBETA Bulk Import, `in_progress`,
> code `scripts/t181_map_sigla.py`, entry `tasktodo.md:91`). Plan cũ cùng ID là
> **Geo-Spatial** ⇒ **trùng ID hoàn toàn**, không phải trùng tên.
> **Không** đụng `tasks/T181-cbeta-*` (task đang chạy của session khác).

## Vì sao phải viết lại (không chỉ sửa số)

Bản `T181-…md` cũ trích **3 tài liệu không tồn tại**:

| Trích dẫn cũ | Thực tế |
|---|---|
| `docs/GEO_SPATIAL_TIMELINE_SPEC.md` "APPROVED, kèm 5 fix review" | **không có** trong đĩa lẫn HEAD |
| `docs/Mimo-Flash/PROMPT-T181-source-reuse-audit.txt` | **không có** — repo có **0** file `PROMPT-*.txt` |
| "Layer 1–3 của SPEC", "số liệu đệm khớp SPEC §4" | không kiểm chứng được |

⇒ Toàn bộ **tiêu chí phân loại nằm trong prompt**, không nằm trong plan. Prompt mất ⇒
tiêu chí mất ⇒ nhóm **B rơi vào hiểu sai** ⇒ thành 100% (xem §Bên dưới).

**Bài học áp dụng** (giống T222): **nhét tiêu chí vào thân plan**, không tạo file prompt
riêng. Plan tự chứa tiêu chí và số đo lịch sử; [T356](../../tasks/T356-t224-readonly-audit-contract.md) bổ sung SQL/script chạy được. SPEC/PROMPT cũ không phải blocker G0–G2.

---

## Mục tiêu

**Source Reuse Audit (G0–G2):** phân loại **59.167** DILA places thành nhóm để đo đúng
khối lượng việc còn lại, thay vì cào đại trà — đóng góp lớp Không gian–Thời gian cho
bức tranh tích hợp (cạnh Phả hệ + Đại tạng).

> **Đính chính phạm vi:** bản cũ ghi *"Thực thi Layer 1–3 của SPEC"* nhưng Scope chỉ có
> G0–G2. **Layer 3 (Wikidata lat/lon) là việc của T121**, đang `in_progress` ⇒
> **không** thuộc task này.

---

## G0 — Baseline đo sẵn (read-only, đã verify 2026-10-04)

SSOT `data/lineage.db`, kết nối **`file:…?mode=ro`**.

| Bảng / cột | Số | Ghi chú |
|---|---|---|
| `places` | **59.161** | **không** phải mẫu số audit |
| `places_dila` | **59.167** | ✅ **mẫu số** của task này |
| `places_dila.raw_xml` khác rỗng | **59.167 / 59.167 = 100%** | ⚠️ xem §B |
| `places_dila.note` khác rỗng | **17.085** | 15.919 giá trị khác nhau |
| `place_timeline_events` | **3.688 rows** | distinct `dila_id` = **3.534** |
| `geo_cross_ref` | **190 rows** | |

⚠️ **`place_timeline_events` KHÔNG có cột `place_id`**; cột là `dila_id` và join vào
**`places_dila.id`** (3.688/3.688 khớp). Bảng **không khai báo FK**. Query sai cột sẽ
lỗi `no such column: place_id`.

---

## §B — Vì sao nhóm B cũ là sai (bằng chứng)

Nhóm B cũ định nghĩa *"Có TEI/XML marked-up evidence"* ⇒ với `raw_xml` 100% khác rỗng thì
**B khớp mọi dòng**, D = E = 0. Hai lý do:

1. **`raw_xml` 100% phân bố** ⇒ tiêu chí "có mã XML" là tautology, không đo được gì.
2. **Không thấy hai literal markup trong phép đo 04-10** (không phải khảo sát semantic toàn TEI):
   `foundingDate` = **0**, `founded` = **0** / 59.167.

Nội dung TEI là **namespace-prefixed**, dùng `ns0:` chứ không phải tên thẻ trần:

```xml
<ns0:place xmlns:ns0="http://www.tei-c.org/ns/1.0">
  <ns0:placeName>…</ns0:placeName>
  <ns0:note>…</ns0:note>
```

⚠️ Literal `<placeName` / `<TEI` / `<place` khớp **0 dòng**. Parser TEI tương lai dùng namespace URI http://www.tei-c.org/ns/1.0, không khóa prefix ns0. T356 chỉ dò marker văn bản, không parse XML.

**Mẫu ns0:note chủ yếu là boilerplate nguồn; không tự chứng minh founding:** mẫu 4.000 dòng chỉ **794** giá
trị khác nhau, `中研院歷史地名` chiếm ~78%. Văn bản mô tả thật nằm ở **cột `note`**
(15.919 giá trị khác nhau, đo 04-10). Local artifact có thể là evidence khi excerpt/locator/version/hash hỗ trợ assertion; không mặc định mọi prose thuộc D.

---

## G1 — Tiêu chí phân loại (bảng số lịch sử 2026-10-04)

**Thứ tự ưu tiên bắt buộc: `A1 > A2 > C > B > D > E`.** Mỗi place rơi vào **nhóm đầu
tiên** khớp ⇒ không đếm trùng.

⚠️ Cần precedence vì **22 place** có cả `geo_cross_ref` lẫn mốc thành lập; nếu cộng vô
tới sẽ vỡ tổng.

| Nhóm | Tiêu chí | Số place | % |
|---|---|---|---|
| **A1** | EXISTS bất kỳ event nguồn wikidata/wikidata_p571; không accepted/founding proof | **249** | 0,42% |
| **A2** | EXISTS bất kỳ event còn lại; không mặc định suy luận | **3.285** | 5,55% |
| **C** | `EXISTS` `geo_cross_ref`, **chưa** thuộc A | **85** | 0,14% |
| **B** | marker candidate note hoặc raw_xml, chưa thuộc A/C; không date | **226** | 0,38% |
| **D** | note khác rỗng, không khớp nhóm trước; không tự mở NLP | **13.336** | 22,54% |
| **E** | không khớp predicate trước ⇒ **giới hạn nguồn của audit** (Admin chốt hướng **(a)**: không phải backlog) | **41.986** | 70,96% |
| | **TỔNG** | **59.167** | ✅ khớp `places_dila` |

### Vì sao tách A1 / A2

3.285/3.534≈93% là tỷ lệ **place A2**, không phải event suy luận. Source/type phải đo riêng; any-event không chứng minh founding chắc chắn.

| Nguồn event | place |
|---|---|
| `dila_era_name` | 1.471 |
| `dila_dynasty` | 851 |
| `dila_note` | 719 |
| `dila_note_regex` | 271 |
| `wikidata` / `wikidata_p571` | 115 / 139 |

⚠️ Chỉ **301 / 3.688** event có `source_ref` là locator QID·property; phần còn lại là chuỗi nội bộ. Cú pháp không chứng minh semantic identity.

### Regex nhóm B — đã đo, KHÔNG rỗng

Bảng marker lịch sử đo note; tiêu chí B phải dò **note hoặc raw_xml** (G2-1 có 6 raw-only). Marker không phải date.

| Mốc | Số place |
|---|---|
| `始建於` | 215 |
| `建於` | 482 |
| `創建` | 242 |
| `建國` | 30 |
| *(tổng sau dedupe, chưa ở A)* | **226** |

> 🛠 **Bắt buộc khi chạy script:** pattern CJK **phải viết `\uXXXX` trong Python**
> hoặc để file UTF-8. Truyền CJK literal qua PowerShell heredoc sẽ **mangle thành `?`**
> và trả **0 giả** — đã xảy ra trong chính phiên review này.
> Ghi control cùng timestamp; 4.646/798 là số lịch sử, không hard-code nghiệm thu DB tương lai.

---

## Quyết định của Admin (2026-10-04)

### Quyết định 1 — **nguồn toạ độ là của DILA cấp** ✅

**`places_dila.geo_lat` / `geo_long` là SSOT cho toạ độ** (58.480/59.167 = **98,84%** có
giá trị — DILA cung cấp khi nạp).

⇒ `geo_cross_ref.enrich_lat` / `enrich_lon` (chỉ **9** row) là **dữ liệu dẫn xuất**, **không**
phải nguồn sự thật. `elevation_m` = **0** là dữ liệu hoàn toàn mới, chưa nguồn nào cấp.

**Hệ quả bắt buộc:**
1. **Không** xây pipeline enrich toạ độ mới — đã có 98,84%.
2. **Không** chồng **T121** (Wikidata lat/lon, `in_progress`) ở phần này nữa.
3. Mọi đọc toạ độ phải đi từ `places_dila`, **không** từ `geo_cross_ref`.

### Quyết định 2 — **bỏ qua vụ license, sẽ cập nhật sau trên HTML** ⏸

Admin chốt 2026-10-04: **không xử lý license trong T224** — sẽ cập nhật ở tầng HTML
(Source Hub admin page, **T231**; danh mục nguồn **T230**).

⇒ **3 cột cross-ref rỗng giữ nguyên**: `chgis_svid` · `tgaz_id` · `bdrc_id` **0 row**, không
xoá, không điền. **Không** coi là blocker của T224.

**Bối cảnh để người sau không tìm lại từ đầu** (đo 2026-10-04, `data_sources` 14 nguồn):

| Cột | Có giá trị |
|---|---|
| `repository_url` | **1 / 14** (chỉ ZENLINEAGE) |
| `license_verified` / `license_url` / `license_spdx` / `data_license` | **0 / 14** |
| `origin_url` | 4 / 14 (CBETA, DILA, MARCUS, Wikidata) |

**CHGIS · TGAZ · BDRC · FoJin không có URL nào** ⇒ đường *"tra license qua GitHub link"* không
áp dụng được cho 4 nguồn này.

**Tiền lệ đúng ý Admin** (để tận dụng khi làm trên HTML):
`kanripo_catalog.github_repo` → `license` = **CC BY-SA 4.0** (từng repo một) ·
`cbeta_catalog_vn.license_url` → **3.122** dòng trỏ creativecommons.org ·
`place_wiki_snapshots.license` = CC BY-SA 4.0.

**Khi làm trên HTML:** mỗi nguồn cần **link + ngày + người xác minh**; **không** điền license
từ trí nhớ. `T18` đã kết luận BDRC *"SKIP hoàn toàn"* — có thể áp cho CHGIS + TGAZ.

---

## Ràng buộc

- **0 write DB** — audit read-only qua `?mode=ro`.
- 0 mass NLP · 0 `ALTER` bảng base (T82 freeze) · 0 ghi đè `raw_xml` / `note`.
- Nguồn `implemented=0` (CHGIS/TGAZ/BDRC/Wikidata…) chỉ **cross-ref**, không ghi vào bảng gốc.
- T356 chỉ derived files trong output dir rõ ràng, không ghi đè. Rollback docs có hashguard; backup/revert ETL áp dụng khi G3 mở riêng.
- ⚠️ **`confidence` không nhất quán** — bảng có **16 giá trị** trộn *nhãn ngữ nghĩa*
  (`dynasty_range`, `era_name_exact`, `era_name_midpoint`, `regex_note`, `verified`) lẫn
  *điểm số* (`0.5` … `0.9`). Ràng buộc cũ *"mọi row NLP = `confidence='candidate'`"* đã
  sửa: giữ nguyên dữ liệu hiện có, **không** ép tên cột mới trước khi có migration.

### Baseline báo riêng, không trừ totals

55 row dila_founding_phase2 có từ T22 trước T224. Proof 0 write dựa mode=ro/query_only/authorizer/total_changes=0, không trừ55 khỏi counts. Current cohort55 không empty label_vi/self_ref; không sửa lại.

## G2 — Report

`docs/T224_SOURCE_REUSE_AUDIT_PLAN.md` · `docs/T224_IDENTITY_HUB_PLAN.md` ·
`docs/T224_EVIDENCE_EVENT_MODEL.md` — trình Admin **trước** mọi code.

## G3+ — CHƯA MỞ

ETL additive (DERIVED `place_timeline_evidence`), HITL queue, coverage target.
**Không mở** cho tới khi Admin duyệt khối lượng D. Phần lat/lon thuộc **T121**.

---

## Dependencies (snapshot lịch sử 2026-10-04; không phải status hiện hành)

| Task | Trạng thái THẬT | Ghi chú |
|---|---|---|
| **T22** | `in_progress` | Layer E (Ollama `raw_xml`) chưa xong; chủ sở hữu 55 row |
| **T22.1** | file **chỉ còn ở `tasks/backup/`** | plan cũ ghi "✅ DONE" — không có ở `tasks/`, không có status |
| **T121** | **`in_progress`** (không phải PENDING) | giữ phần Wikidata lat/lon = Layer 3 |
| **T112** | **`done`** | kết luận: *"5 BLOCK (BDRC/SAT/CHGIS/FoJin/TGAZ — legal chưa rõ)"* ⇒ ràng buộc nhóm C là **license**, không phải task blocked |

---

## T22 — phát hiện lịch sử đã đối soát 11-10

04-10 báo55 empty label_vi/self_ref và226 marker candidates. T22 đã sửa cohort55 (50founding+5era_mention;0empty/0self_ref). Không giao sửa lại. 226 chỉ marker worklist lịch sử, không ngày; T356 refresh audit, không ETL T22.

## Acceptance (G1–G2 / refresh T356)

1. Một CASE/membership mỗi ID; totals bằng places_dila trong cùng read transaction.
2. mode=ro/query_only/authorizer/total_changes=0, không trừbaseline55.
3. Any-event/founding/dissolved/xref/marker riêng; controls có timestamp, marker không date/accepted.
4. Sources×type cộng độc lập; history/current/ref/confidence/schema/hash/command/manifest đầy đủ.
5. Ba report G2 liên kếtT356; D chỉ estimate/G3deferred; T22/T121 giữownership.
6. Fixture/CLI tests vàguard/dup:ids báo thật; không claimdup sạch/fullpipeline khi còn duplicate lịch sử.

## Revert

- Docs: `git revert --no-edit <sha>` (xem `docs/ROLLBACK.md`).
- G3 (tương lai): script `--revert` + DB backup pattern T157.

## Đối soát T356 — snapshot hiện hành 2026-10-11

Hợp đồng chạy được: [T356](../../tasks/T356-t224-readonly-audit-contract.md) · [script](../../scripts/t356_t224_readonly_audit.py) · [summary](../../docs/sessions/2026-10-11_T356/audit-current-t356/summary.json) · [manifest](../../docs/sessions/2026-10-11_T356/audit-current-t356/manifest.json) · [session](../../docs/sessions/2026-10-11_T356/README.md).

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
