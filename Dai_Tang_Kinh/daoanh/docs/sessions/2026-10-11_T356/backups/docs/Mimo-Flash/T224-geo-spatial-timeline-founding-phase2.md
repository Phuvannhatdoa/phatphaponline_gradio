---
task: tasks/T224-geo-spatial-timeline-founding-phase2.md
title: Geo-Spatial & Timeline Integration — Source Reuse Audit (Founding Date Phase 2)
former_id: T181
status: blocked
created: 2026-10-04
updated: 2026-10-04
module: GIS Places / Timeline / HOME
priority: medium
blocked_reason: >-
  Chờ SPEC + PROMPT gốc (đã mất) được tái tạo; plan này đã tự chứa đủ tiêu chí để chạy G1–G2.
  G3 chưa mở — Admin chốt hướng (a): nhóm E là giới hạn nguồn, không phải backlog.
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
riêng. Plan này **tự chứa** toàn bộ tiêu chí + SQL + số liệu đo sẵn.

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
2. **TEI không có markup ngày thành lập** (ASCII pattern ⇒ tin cậy):
   `foundingDate` = **0**, `founded` = **0** / 59.167.

Nội dung TEI là **namespace-prefixed**, dùng `ns0:` chứ không phải tên thẻ trần:

```xml
<ns0:place xmlns:ns0="http://www.tei-c.org/ns/1.0">
  <ns0:placeName>…</ns0:placeName>
  <ns0:note>…</ns0:note>
```

⚠️ Literal `<placeName` / `<TEI` / `<place` khớp **0 dòng**. Mọi regex phải dùng `ns0:`
hoặc parse XML theo namespace.

**`ns0:note` là boilerplate nguồn, không phải evidence:** mẫu 4.000 dòng chỉ **794** giá
trị khác nhau, `中研院歷史地名` chiếm ~78%. Văn bản mô tả thật nằm ở **cột `note`**
(15.919 giá trị khác nhau), và đó là **prose** ⇒ việc của **nhóm D**.

---

## G1 — Tiêu chí phân loại (tự chứa, có số đo)

**Thứ tự ưu tiên bắt buộc: `A1 > A2 > C > B > D > E`.** Mỗi place rơi vào **nhóm đầu
tiên** khớp ⇒ không đếm trùng.

⚠️ Cần precedence vì **22 place** có cả `geo_cross_ref` lẫn mốc thành lập; nếu cộng vô
tới sẽ vỡ tổng.

| Nhóm | Tiêu chí | Số place | % |
|---|---|---|---|
| **A1** | `EXISTS` event nguồn `wikidata` / `wikidata_p571` (**bằng chứng ngoài, kèm QID**) | **249** | 0,42% |
| **A2** | `EXISTS` event còn lại (suy luận từ era/dynasty/note) | **3.285** | 5,55% |
| **C** | `EXISTS` `geo_cross_ref`, **chưa** thuộc A | **85** | 0,14% |
| **B** | có **mốc thành lập** (regex §Regex, chưa thuộc A) | **226** | 0,38% |
| **D** | có `note` mô tả địa lý, **chưa** có mốc thành lập → **cần NLP** | **13.336** | 22,54% |
| **E** | không có gì ⇒ **giới hạn nguồn** (Admin chốt hướng **(a)**: không phải backlog) | **41.986** | 70,96% |
| | **TỔNG** | **59.167** | ✅ khớp `places_dila` |

### Vì sao tách A1 / A2

93% event là **suy luận**, không phải dữ liệu gốc. Gộp chung sẽ khiến Admin tưởng có
3.534 ngày thành lập *chắc chắn*.

| Nguồn event | place |
|---|---|
| `dila_era_name` | 1.471 |
| `dila_dynasty` | 851 |
| `dila_note` | 719 |
| `dila_note_regex` | 271 |
| `wikidata` / `wikidata_p571` | 115 / 139 |

⚠️ Chỉ **301 / 3.688** event có `source_ref` là QID/URL thật; phần còn lại là chuỗi nội bộ.

### Regex nhóm B — đã đo, KHÔNG rỗng

Đo trên `note` (escape Unicode để không bị shell mangle):

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
> **Luôn chạy 1 control** (`建` phải ≈4.646, `帝` ≈798) để chứng minh pattern còn sống.

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
- Mọi script additive / idempotent / có `--revert`.
- ⚠️ **`confidence` không nhất quán** — bảng có **16 giá trị** trộn *nhãn ngữ nghĩa*
  (`dynasty_range`, `era_name_exact`, `era_name_midpoint`, `regex_note`, `verified`) lẫn
  *điểm số* (`0.5` … `0.9`). Ràng buộc cũ *"mọi row NLP = `confidence='candidate'`"* đã
  sửa: giữ nguyên dữ liệu hiện có, **không** ép tên cột mới trước khi có migration.

### Baseline phải loại trừ

`place_timeline_events` **đã có 55 row** `source='dila_founding_phase2'`, tạo ngày
**2026-09-01** (việc của T22, **trước** T224). Khi kiểm "0 dòng mới" phải **loại trừ 55 row
này**, nếu không sẽ tưởng audit đã ghi DB.

---

## G2 — Report

`docs/T224_SOURCE_REUSE_AUDIT_PLAN.md` · `docs/T224_IDENTITY_HUB_PLAN.md` ·
`docs/T224_EVIDENCE_EVENT_MODEL.md` — trình Admin **trước** mọi code.

## G3+ — CHƯA MỞ

ETL additive (DERIVED `place_timeline_evidence`), HITL queue, coverage target.
**Không mở** cho tới khi Admin duyệt khối lượng D. Phần lat/lon thuộc **T121**.

---

## Dependencies (đã verify 2026-10-04)

| Task | Trạng thái THẬT | Ghi chú |
|---|---|---|
| **T22** | `in_progress` | Layer E (Ollama `raw_xml`) chưa xong; chủ sở hữu 55 row |
| **T22.1** | file **chỉ còn ở `tasks/backup/`** | plan cũ ghi "✅ DONE" — không có ở `tasks/`, không có status |
| **T121** | **`in_progress`** (không phải PENDING) | giữ phần Wikidata lat/lon = Layer 3 |
| **T112** | **`done`** | kết luận: *"5 BLOCK (BDRC/SAT/CHGIS/FoJin/TGAZ — legal chưa rõ)"* ⇒ ràng buộc nhóm C là **license**, không phải task blocked |

---

## Phát hiện phụ — ghi nhận cho T22, KHÔNG làm trùng

- **55/55 row** `source='dila_founding_phase2'` có **`label_vi` RỖNG** và `source_ref` tự
  tham chiếu (`= dila_founding_phase2`). T22 khai `label_vi` trong schema ⇒ đây là **lỗi
  nội bộ T22**, không phải trạng thái hợp lệ. T22 còn `in_progress` ⇒ **chủ sở hữu**.
- **226 place** có mốc thành lập nhưng chưa có event ⇒ gấp 4× 55 row của T22.
  Đây là **worklist** cho T22 Layer D/E.

---

## Acceptance (G1–G2)

1. Report A1/A2/C/B/D/E phủ đủ **59.167**, tổng **khớp tuyệt đối** `places_dila`.
2. **0 write DB** — verify bằng `?mode=ro` + đối chiếu count trước/sau (loại 55 row baseline).
3. Mọi regex CJK có **1 control pass** (`建`/`帝`) chứng minh không bị mangle.
4. Ước lượng khối lượng **nhóm D** (13.336) → trình Admin **trước G3**.
5. 3 file report đúng tên `docs/T224_*.md`.
6. `npm run dup:ids` sạch — T224 không trùng ID nào.

---

## Revert

- Docs: `git revert --no-edit <sha>` (xem `docs/ROLLBACK.md`).
- G3 (tương lai): script `--revert` + DB backup pattern T157.